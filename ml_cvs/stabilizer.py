"""
Recognition Stabilizer - K-of-N Multi-frame Confirmation
Prevents false positives by requiring multiple confirmations before marking attendance
"""
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
import numpy as np


# Configuration
K_MATCHES_REQUIRED = 5  # Minimum matches needed
N_FRAME_WINDOW = 10  # Rolling window size
AGGREGATION_METHOD = 'median'  # median or mean
COOLDOWN_SECONDS = 120  # 2 minutes cooldown after confirmation


class RecognitionStabilizer:
    """
    Implements K-of-N voting for stable face recognition
    Requires K matches out of last N frames before confirming identity
    """
    
    def __init__(self, k: int = K_MATCHES_REQUIRED, n: int = N_FRAME_WINDOW, 
                 cooldown_seconds: int = COOLDOWN_SECONDS):
        """
        Initialize stabilizer
        
        Args:
            k: Minimum matches required (e.g., 5)
            n: Frame window size (e.g., 10)
            cooldown_seconds: Cooldown period after confirmation
        """
        self.k = k
        self.n = n
        self.cooldown_seconds = cooldown_seconds
        
        # Rolling buffer of observations (max size = n)
        self.observation_buffer = deque(maxlen=n)
        
        # Track confirmed students with cooldown
        self.confirmed_students = {}  # {student_id: last_confirmed_time}
    
    def update(self, student_id: int, similarity: float, timestamp: datetime = None):
        """
        Add new observation to rolling window
        
        Args:
            student_id: Detected student ID (or None if no match)
            similarity: Similarity score (0-1, higher = better match)
            timestamp: Observation timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        observation = {
            'student_id': student_id,
            'similarity': similarity,
            'timestamp': timestamp
        }
        
        self.observation_buffer.append(observation)
    
    def get_confirmed(self) -> Optional[Tuple[int, float]]:
        """
        Check if any student meets K-of-N confirmation threshold
        
        Returns:
            (student_id, aggregated_similarity) if confirmed, else None
        """
        if len(self.observation_buffer) < self.k:
            # Not enough observations yet
            return None
        
        # Count occurrences per student
        student_observations = {}
        
        for obs in self.observation_buffer:
            sid = obs['student_id']
            if sid is None:
                continue  # Skip non-matches
            
            if sid not in student_observations:
                student_observations[sid] = []
            
            student_observations[sid].append(obs['similarity'])
        
        # Find student with >= K matches
        for student_id, similarities in student_observations.items():
            if len(similarities) >= self.k:
                # Check cooldown
                if self._in_cooldown(student_id):
                    continue
                
                # Aggregate similarity scores
                if AGGREGATION_METHOD == 'median':
                    agg_similarity = float(np.median(similarities))
                else:  # mean
                    agg_similarity = float(np.mean(similarities))
                
                return (student_id, agg_similarity)
        
        return None
    
    def _in_cooldown(self, student_id: int) -> bool:
        """
        Check if student is in cooldown period
        
        Args:
            student_id: Student ID to check
        
        Returns:
            True if still in cooldown
        """
        if student_id not in self.confirmed_students:
            return False
        
        last_confirmed = self.confirmed_students[student_id]
        elapsed = (datetime.now() - last_confirmed).total_seconds()
        
        return elapsed < self.cooldown_seconds
    
    def mark_confirmed(self, student_id: int):
        """
        Mark student as confirmed (starts cooldown timer)
        
        Args:
            student_id: Student ID that was confirmed
        """
        self.confirmed_students[student_id] = datetime.now()
    
    def get_progress(self, student_id: int) -> Dict:
        """
        Get confirmation progress for a specific student
        
        Args:
            student_id: Student ID to check
            
        Returns:
            Dict with matched count, total window, and progress ratio
        """
        count = sum(1 for obs in self.observation_buffer if obs['student_id'] == student_id)
        
        return {
            'matched': count,
            'total': self.n,
            'required': self.k,
            'progress': count / self.k if self.k > 0 else 0.0,
            'confirmed': count >= self.k
        }
    
    def clear_buffer(self):
        """Clear observation buffer (use when starting new session)"""
        self.observation_buffer.clear()
    
    def reset_cooldowns(self):
        """Reset all cooldown timers (use at start of new class)"""
        self.confirmed_students.clear()
    
    def get_candidate_stats(self) -> Dict:
        """
        Get statistics about current candidates in buffer
        
        Returns:
            Dict mapping student_id -> observation count
        """
        stats = {}
        for obs in self.observation_buffer:
            sid = obs['student_id']
            if sid is None:
                continue
            stats[sid] = stats.get(sid, 0) + 1
        
        return stats


class MultiStudentStabilizer:
    """
    Extension of RecognitionStabilizer to track multiple students simultaneously
    Useful when multiple faces detected in frame
    """
    
    def __init__(self, k: int = K_MATCHES_REQUIRED, n: int = N_FRAME_WINDOW,
                 cooldown_seconds: int = COOLDOWN_SECONDS):
        """
        Initialize multi-student stabilizer
        
        Args:
            k: Minimum matches required per student
            n: Frame window size
            cooldown_seconds: Cooldown period after confirmation
        """
        # Create separate stabilizer for each student position in frame
        self.stabilizers = {}  # {student_id: RecognitionStabilizer}
        self.k = k
        self.n = n
        self.cooldown_seconds = cooldown_seconds
    
    def update_multiple(self, detections: list):
        """
        Update with multiple face detections from single frame
        
        Args:
            detections: List of (student_id, similarity) tuples
        """
        timestamp = datetime.now()
        
        for student_id, similarity in detections:
            if student_id not in self.stabilizers:
                self.stabilizers[student_id] = RecognitionStabilizer(
                    k=self.k, n=self.n, cooldown_seconds=self.cooldown_seconds
                )
            
            self.stabilizers[student_id].update(student_id, similarity, timestamp)
    
    def get_all_confirmed(self) -> list:
        """
        Get all students that meet confirmation threshold
        
        Returns:
            List of (student_id, similarity) tuples for confirmed students
        """
        confirmed = []
        
        for student_id, stabilizer in self.stabilizers.items():
            result = stabilizer.get_confirmed()
            if result:
                sid, sim = result
                confirmed.append((sid, sim))
                stabilizer.mark_confirmed(sid)
        
        return confirmed
    
    def clear_all(self):
        """Clear all stabilizer buffers"""
        for stabilizer in self.stabilizers.values():
            stabilizer.clear_buffer()


# Convenience function
def create_stabilizer(k=5, n=10, cooldown=120):
    """Create and return RecognitionStabilizer instance"""
    return RecognitionStabilizer(k=k, n=n, cooldown_seconds=cooldown)
