/**
 * Enhanced Live Recognition Component
 * Shows K-of-N progress, verification states, and session info
 */
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface RecognitionProgress {
    matched: number;
    required: number;
    total: number;
    progress: number;
}

interface SessionInfo {
    id: number;
    courseName: string;
    professorName: string;
}

type RecognitionState = 'idle' | 'detecting' | 'verifying' | 'confirmed' | 'no_match';

const EnhancedRecognition: React.FC = () => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);

    const [state, setState] = useState<RecognitionState>('idle');
    const [studentName, setStudentName] = useState<string>('');
    const [confidence, setConfidence] = useState<number>(0);
    const [progress, setProgress] = useState<RecognitionProgress | null>(null);
    const [session, setSession] = useState<SessionInfo | null>(null);
    const [message, setMessage] = useState<string>('Starting camera...');
    const [isActive, setIsActive] = useState(false);

    const recognitionInterval = useRef<number | null>(null);

    useEffect(() => {
        startWebcam();
        fetchActiveSession();

        return () => {
            stopRecognition();
            stopWebcam();
        };
    }, []);

    const startWebcam = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 }
            });

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }

            setState('idle');
            setMessage('Camera ready. Click Start Recognition to begin.');
        } catch (error) {
            console.error('Error accessing webcam:', error);
            setMessage('❌ Failed to access webcam');
        }
    };

    const stopWebcam = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            const stream = videoRef.current.srcObject as MediaStream;
            stream.getTracks().forEach(track => track.stop());
        }
    };

    const fetchActiveSession = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get(`${API_URL}/api/sessions/active`, {
                headers: { Authorization: `Bearer ${token}` }
            });

            if (response.data.active) {
                setSession(response.data.session);
            }
        } catch (error) {
            console.error('Error fetching session:', error);
        }
    };

    const startRecognition = () => {
        if (!videoRef.current || !canvasRef.current) return;

        setIsActive(true);
        setState('detecting');
        setMessage('Scanning for faces...');

        // Process frame every 200ms (5 FPS)
        recognitionInterval.current = window.setInterval(() => {
            processFrame();
        }, 200);
    };

    const stopRecognition = () => {
        setIsActive(false);
        setState('idle');
        setMessage('Recognition stopped');

        if (recognitionInterval.current) {
            clearInterval(recognitionInterval.current);
            recognitionInterval.current = null;
        }
    };

    const processFrame = async () => {
        if (!videoRef.current || !canvasRef.current) return;

        const canvas = canvasRef.current;
        const video = videoRef.current;
        const context = canvas.getContext('2d');

        if (!context) return;

        // Capture frame
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        const frameData = canvas.toDataURL('image/jpeg', 0.8);

        try {
            const token = localStorage.getItem('token');
            const response = await axios.post(
                `${API_URL}/api/recognize`,
                { image: frameData },
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            const result = response.data;

            if (result.confirmed) {
                // Confirmed recognition
                setState('confirmed');
                setStudentName(result.studentName);
                setConfidence(result.confidence);
                setMessage(result.message);

                // Stop recognition after confirmation
                setTimeout(() => {
                    stopRecognition();
                }, 3000);
            } else if (result.verifying) {
                // In verification process
                setState('verifying');
                setStudentName(result.studentName);
                setConfidence(result.confidence);
                setProgress(result.progress);
                setMessage(result.message);
            } else if (result.recognized === false) {
                // No match or quality issue
                setState('detecting');
                setMessage(result.message || 'No face detected');
                setProgress(null);
            }
        } catch (error: any) {
            console.error('Recognition error:', error);
            setMessage('Recognition error: ' + (error.response?.data?.error || error.message));
        }
    };

    return (
        <div className="container mx-auto p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">Live Face Recognition</h1>
                <div className="flex gap-2">
                    {!isActive ? (
                        <button
                            onClick={startRecognition}
                            className="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                        >
                            ▶️ Start Recognition
                        </button>
                    ) : (
                        <button
                            onClick={stopRecognition}
                            className="px-6 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                        >
                            ⏹️ Stop
                        </button>
                    )}
                </div>
            </div>

            {/* Session Info */}
            {session && (
                <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded">
                    <h3 className="font-semibold text-blue-900">Active Session</h3>
                    <p className="text-blue-800">
                        {session.courseName} - {session.professorName}
                    </p>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Video Feed */}
                <div className="space-y-4">
                    <div className={`relative rounded-lg overflow-hidden border-4 ${state === 'confirmed' ? 'border-green-500' :
                        state === 'verifying' ? 'border-yellow-500' :
                            state === 'detecting' ? 'border-blue-500' :
                                'border-gray-300'
                        }`}>
                        <video
                            ref={videoRef}
                            autoPlay
                            playsInline
                            muted
                            className="w-full h-auto bg-black"
                        />
                        <canvas ref={canvasRef} className="hidden" />

                        {/* State Indicator Overlay */}
                        <div className={`absolute top-4 right-4 px-4 py-2 rounded-full font-semibold ${state === 'confirmed' ? 'bg-green-500 text-white' :
                            state === 'verifying' ? 'bg-yellow-500 text-black' :
                                state === 'detecting' ? 'bg-blue-500 text-white' :
                                    'bg-gray-500 text-white'
                            }`}>
                            {state.toUpperCase()}
                        </div>
                    </div>

                    {/* Status Message */}
                    <div className={`p-4 rounded-lg ${state === 'confirmed' ? 'bg-green-100 border border-green-300' :
                        state === 'verifying' ? 'bg-yellow-100 border border-yellow-300' :
                            'bg-gray-100 border border-gray-300'
                        }`}>
                        <p className="text-sm">{message}</p>
                    </div>
                </div>

                {/* Recognition Info Panel */}
                <div className="space-y-4">
                    {/* Student Info */}
                    {studentName && (
                        <div className="bg-white rounded-lg shadow p-6">
                            <h3 className="text-lg font-semibold mb-2">Recognized Student</h3>
                            <p className="text-2xl font-bold text-blue-600">{studentName}</p>
                            <p className="text-sm text-gray-600 mt-1">
                                Confidence: {(confidence * 100).toFixed(1)}%
                            </p>
                        </div>
                    )}

                    {/* K-of-N Progress */}
                    {progress && state === 'verifying' && (
                        <div className="bg-white rounded-lg shadow p-6">
                            <h3 className="text-lg font-semibold mb-3">Verification Progress</h3>

                            <div className="space-y-3">
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span>Matches: {progress.matched} / {progress.required}</span>
                                        <span>{Math.round(progress.progress * 100)}%</span>
                                    </div>
                                    <div className="w-full h-6 bg-gray-200 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-yellow-400 to-green-500 transition-all duration-300"
                                            style={{ width: `${Math.min(progress.progress * 100, 100)}%` }}
                                        />
                                    </div>
                                </div>

                                <div className="text-sm text-gray-600">
                                    <p>Window: {progress.total} frames</p>
                                    <p className="mt-1">
                                        {progress.required - progress.matched} more match{progress.required - progress.matched !== 1 ? 'es' : ''} needed
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Instructions */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold mb-3">Instructions</h3>
                        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                            <li>Ensure good lighting</li>
                            <li>Look directly at the camera</li>
                            <li>Keep your face centered</li>
                            <li>Stay still during verification</li>
                            <li>Requires {5} consecutive matches to confirm</li>
                        </ul>
                    </div>

                    {/* Stats */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-semibold mb-3">System Status</h3>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-600">State:</span>
                                <span className="font-medium">{state}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Active:</span>
                                <span className={`font-medium ${isActive ? 'text-green-600' : 'text-gray-400'}`}>
                                    {isActive ? 'Yes' : 'No'}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Processing Rate:</span>
                                <span className="font-medium">~5 FPS</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default EnhancedRecognition;
