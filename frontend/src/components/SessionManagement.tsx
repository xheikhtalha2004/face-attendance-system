/**
 * Session Management Component
 * Manual session creation, activation, and verification with timestamps
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/apiConfig';

interface Course {
  id: number;
  courseId: string;
  courseName: string;
  professorName: string;
}

interface Session {
  id: number;
  courseId: number;
  courseName: string;
  professorName: string;
  status: 'SCHEDULED' | 'ACTIVE' | 'COMPLETED' | 'CANCELLED';
  startsAt: string;
  endsAt: string;
  createdAt: string;
  autoCreated: boolean;
}

export const SessionManagement: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('');

  // Form state for creating new session
  const [newSession, setNewSession] = useState({
    courseId: '',
    startsAt: '',
    endsAt: ''
  });

  useEffect(() => {
    fetchCourses();
    fetchSessions();
  }, []);

  const fetchCourses = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/courses`);
      setCourses(response.data);
    } catch (error) {
      console.error('Error fetching courses:', error);
    }
  };

  const fetchSessions = async (status?: string) => {
    try {
      setLoading(true);
      let url = `${API_BASE_URL}/sessions`;
      if (status) {
        url += `?status=${status}`;
      }
      const response = await axios.get(url);
      setSessions(response.data);
      setMessage(null);
    } catch (error: any) {
      console.error('Error fetching sessions:', error);
      setMessage('Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async () => {
    if (!newSession.courseId || !newSession.startsAt || !newSession.endsAt) {
      setMessage('❌ Please fill all required fields');
      return;
    }

    // Validate times
    const startTime = new Date(newSession.startsAt);
    const endTime = new Date(newSession.endsAt);
    if (endTime <= startTime) {
      setMessage('❌ End time must be after start time');
      return;
    }

    try {
      const response = await axios.post(`${API_BASE_URL}/sessions/manual/create`, {
        courseId: parseInt(newSession.courseId),
        startsAt: startTime.toISOString(),
        endsAt: endTime.toISOString()
      });

      setMessage('✅ Session created successfully');
      setNewSession({ courseId: '', startsAt: '', endsAt: '' });
      await fetchSessions(filterStatus || '');
    } catch (error: any) {
      console.error('Error creating session:', error);
      setMessage(error.response?.data?.error || 'Failed to create session');
    }
  };

  const handleActivateSession = async (sessionId: number) => {
    try {
      await axios.put(`${API_BASE_URL}/sessions/${sessionId}/activate`);
      setMessage('✅ Session activated');
      await fetchSessions(filterStatus || '');
    } catch (error: any) {
      console.error('Error activating session:', error);
      setMessage(error.response?.data?.error || 'Failed to activate session');
    }
  };

  const handleEndSession = async (sessionId: number) => {
    if (!window.confirm('End this session now?')) return;

    try {
      await axios.put(`${API_BASE_URL}/sessions/${sessionId}/end`);
      setMessage('✅ Session ended');
      await fetchSessions(filterStatus || '');
    } catch (error: any) {
      console.error('Error ending session:', error);
      setMessage(error.response?.data?.error || 'Failed to end session');
    }
  };

  const handleCancelSession = async (sessionId: number) => {
    if (!window.confirm('Cancel this session?')) return;

    try {
      await axios.put(`${API_BASE_URL}/sessions/${sessionId}/cancel`);
      setMessage('✅ Session cancelled');
      await fetchSessions(filterStatus || '');
    } catch (error: any) {
      console.error('Error cancelling session:', error);
      setMessage(error.response?.data?.error || 'Failed to cancel session');
    }
  };

  const handleVerifyData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/sessions/verify-data`);
      const data = response.data;
      const summary = data.summary;

      const verificationMessage = `✅ Data Verification:
- Total Sessions: ${summary.totalSessions}
- Active: ${summary.activeCount}
- Completed: ${summary.completedCount}
- Scheduled: ${summary.scheduledCount}
- Cancelled: ${summary.cancelledCount}
- Total Attendance Records: ${summary.totalAttendanceRecords}
- Sessions without end time: ${summary.sessionsWithoutEndTime}`;

      setMessage(verificationMessage);
    } catch (error: any) {
      console.error('Error verifying data:', error);
      setMessage('❌ Failed to verify data');
    }
  };

  const getStatusColor = (status: string) => {
    const colors: { [key: string]: string } = {
      'SCHEDULED': 'bg-yellow-100 text-yellow-800',
      'ACTIVE': 'bg-green-100 text-green-800',
      'COMPLETED': 'bg-blue-100 text-blue-800',
      'CANCELLED': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Session Management</h2>

      {message && (
        <div className={`p-4 rounded whitespace-pre-line ${
          message.includes('✅') || message.includes('Data Verification') 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          {message}
        </div>
      )}

      {/* Create New Session */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Create Manual Session</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <select
            value={newSession.courseId}
            onChange={(e) => setNewSession({ ...newSession, courseId: e.target.value })}
            className="border rounded px-3 py-2"
          >
            <option value="">Select Course</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.courseId} - {course.courseName}
              </option>
            ))}
          </select>
          
          <input
            type="datetime-local"
            value={newSession.startsAt}
            onChange={(e) => setNewSession({ ...newSession, startsAt: e.target.value })}
            placeholder="Start Time"
            className="border rounded px-3 py-2"
          />
          
          <input
            type="datetime-local"
            value={newSession.endsAt}
            onChange={(e) => setNewSession({ ...newSession, endsAt: e.target.value })}
            placeholder="End Time"
            className="border rounded px-3 py-2"
          />
          
          <button
            onClick={handleCreateSession}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Create Session
          </button>
        </div>
      </div>

      {/* Filter and Verify */}
      <div className="flex gap-2 flex-wrap">
        <select
          value={filterStatus}
          onChange={(e) => {
            setFilterStatus(e.target.value);
            fetchSessions(e.target.value);
          }}
          className="border rounded px-3 py-2"
        >
          <option value="">All Statuses</option>
          <option value="SCHEDULED">Scheduled</option>
          <option value="ACTIVE">Active</option>
          <option value="COMPLETED">Completed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>

        <button
          onClick={handleVerifyData}
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
        >
          Verify Data & Timestamps
        </button>

        <button
          onClick={() => fetchSessions(filterStatus || '')}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          Refresh
        </button>
      </div>

      {/* Sessions List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-6 text-center">Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="p-6 text-center text-gray-600">No sessions found</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-2 text-left text-sm font-semibold">Course</th>
                <th className="px-4 py-2 text-left text-sm font-semibold">Starts At</th>
                <th className="px-4 py-2 text-left text-sm font-semibold">Ends At</th>
                <th className="px-4 py-2 text-left text-sm font-semibold">Status</th>
                <th className="px-4 py-2 text-left text-sm font-semibold">Type</th>
                <th className="px-4 py-2 text-left text-sm font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.id} className="border-t hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-semibold">{session.courseName}</div>
                    <div className="text-sm text-gray-600">{session.professorName}</div>
                  </td>
                  <td className="px-4 py-3 text-sm">{formatDateTime(session.startsAt)}</td>
                  <td className="px-4 py-3 text-sm">{formatDateTime(session.endsAt)}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-sm font-medium ${getStatusColor(session.status)}`}>
                      {session.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {session.autoCreated ? '🤖 Auto' : '👤 Manual'}
                  </td>
                  <td className="px-4 py-3 space-x-1">
                    {session.status === 'SCHEDULED' && (
                      <button
                        onClick={() => handleActivateSession(session.id)}
                        className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        Activate
                      </button>
                    )}
                    {session.status === 'ACTIVE' && (
                      <button
                        onClick={() => handleEndSession(session.id)}
                        className="px-2 py-1 text-xs bg-orange-600 text-white rounded hover:bg-orange-700"
                      >
                        End
                      </button>
                    )}
                    {['SCHEDULED', 'ACTIVE'].includes(session.status) && (
                      <button
                        onClick={() => handleCancelSession(session.id)}
                        className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <p className="text-sm text-gray-600">
        Total Sessions: <strong>{sessions.length}</strong>
      </p>
    </div>
  );
};

export default SessionManagement;
