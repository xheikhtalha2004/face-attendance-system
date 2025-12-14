/**
 * Enhanced Multi-frame Enrollment Component
 * Captures 10-20 frames from webcam, shows quality feedback, sends to backend
 */
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/apiConfig';

interface EnrollmentProps {
    studentId: number;
    studentName: string;
    onComplete: () => void;
    onCancel: () => void;
}

export const MultiFrameEnrollment: React.FC<EnrollmentProps> = ({
    studentId,
    studentName,
    onComplete,
    onCancel
}) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);

    const [isCapturing, setIsCapturing] = useState(false);
    const [capturedFrames, setCapturedFrames] = useState<string[]>([]);
    const [status, setStatus] = useState<string>('Click Start to begin enrollment');
    const [progress, setProgress] = useState(0);
    const [processing, setProcessing] = useState(false);

    const TARGET_FRAMES = 15;
    const CAPTURE_INTERVAL = 200; // 200ms between frames

    useEffect(() => {
        startWebcam();
        return () => {
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

            setStatus('Webcam ready. Click Start Capture to begin.');
        } catch (error) {
            console.error('Error accessing webcam:', error);
            setStatus('❌ Failed to access webcam. Please check permissions.');
        }
    };

    const stopWebcam = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            const stream = videoRef.current.srcObject as MediaStream;
            stream.getTracks().forEach(track => track.stop());
        }
    };

    const captureFrames = async () => {
        if (!videoRef.current || !canvasRef.current) return;

        setIsCapturing(true);
        setStatus('Capturing frames... Please keep your face centered');
        setCapturedFrames([]);
        setProgress(0);

        const frames: string[] = [];
        const canvas = canvasRef.current;
        const video = videoRef.current;
        const context = canvas.getContext('2d');

        if (!context) return;

        // Set canvas size to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        for (let i = 0; i < TARGET_FRAMES; i++) {
            // Capture frame
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const frameData = canvas.toDataURL('image/jpeg', 0.9);
            frames.push(frameData);

            // Update progress
            setProgress(((i + 1) / TARGET_FRAMES) * 100);
            setStatus(`Capturing... ${i + 1}/${TARGET_FRAMES} frames`);

            // Wait before next capture
            if (i < TARGET_FRAMES - 1) {
                await new Promise(resolve => setTimeout(resolve, CAPTURE_INTERVAL));
            }
        }

        setCapturedFrames(frames);
        setIsCapturing(false);
        setStatus(`✓ Captured ${TARGET_FRAMES} frames. Click Submit to process.`);
    };

    const submitEnrollment = async () => {
        setProcessing(true);
        setStatus('Processing frames on server...');

        try {
            const response = await axios.post(
                `${API_BASE_URL}/students/${studentId}/enroll-frames`,
                {
                    frames: capturedFrames,
                    maxEmbeddings: 10
                },
                {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );

            setStatus(
                `✅ Success! Saved ${response.data.embeddingsSaved} embeddings ` +
                `(${response.data.validFrames}/${response.data.totalFrames} frames passed quality check)`
            );

            // Wait a bit to show success message
            setTimeout(() => {
                onComplete();
            }, 2000);
        } catch (error: any) {
            console.error('Enrollment error:', error);
            setStatus(
                `❌ Enrollment failed: ${error.response?.data?.error || error.message}`
            );
            setProcessing(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-3xl w-full max-h-screen overflow-y-auto">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-2xl font-bold">
                        Multi-frame Enrollment: {studentName}
                    </h2>
                    <button
                        onClick={onCancel}
                        className="text-gray-500 hover:text-gray-700 text-2xl"
                        disabled={processing}
                    >
                        ×
                    </button>
                </div>

                {/* Video Preview */}
                <div className="relative mb-4 bg-black rounded-lg overflow-hidden">
                    <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="w-full h-auto"
                    />
                    <canvas ref={canvasRef} className="hidden" />

                    {/* Progress Overlay */}
                    {isCapturing && (
                        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                            <div className="bg-white rounded-lg p-6 text-center">
                                <div className="text-xl font-bold mb-2">Capturing...</div>
                                <div className="w-64 h-4 bg-gray-300 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-blue-500 transition-all duration-200"
                                        style={{ width: `${progress}%` }}
                                    />
                                </div>
                                <div className="mt-2 text-sm text-gray-600">
                                    {Math.round(progress)}% complete
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Status Message */}
                <div className="mb-4 p-4 bg-gray-100 rounded-lg">
                    <p className="text-sm">{status}</p>
                </div>

                {/* Frame Thumbnails */}
                {capturedFrames.length > 0 && (
                    <div className="mb-4">
                        <h3 className="text-sm font-semibold mb-2">
                            Captured Frames ({capturedFrames.length}):
                        </h3>
                        <div className="flex gap-2 overflow-x-auto pb-2">
                            {capturedFrames.map((frame, index) => (
                                <img
                                    key={index}
                                    src={frame}
                                    alt={`Frame ${index + 1}`}
                                    className="w-20 h-20 object-cover rounded border"
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2 justify-end">
                    <button
                        onClick={onCancel}
                        className="px-4 py-2 border rounded hover:bg-gray-100"
                        disabled={processing}
                    >
                        Cancel
                    </button>

                    {capturedFrames.length === 0 ? (
                        <button
                            onClick={captureFrames}
                            disabled={isCapturing}
                            className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
                        >
                            {isCapturing ? 'Capturing...' : '📸 Start Capture'}
                        </button>
                    ) : (
                        <>
                            <button
                                onClick={() => {
                                    setCapturedFrames([]);
                                    setProgress(0);
                                    setStatus('Click Start Capture to try again');
                                }}
                                disabled={processing}
                                className="px-4 py-2 border rounded hover:bg-gray-100"
                            >
                                🔄 Retake
                            </button>
                            <button
                                onClick={submitEnrollment}
                                disabled={processing}
                                className="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-300"
                            >
                                {processing ? 'Processing...' : '✓ Submit Enrollment'}
                            </button>
                        </>
                    )}
                </div>

                {/* Instructions */}
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded text-sm">
                    <h4 className="font-semibold mb-2">📋 Instructions:</h4>
                    <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>Keep your face centered and well-lit</li>
                        <li>Look directly at the camera</li>
                        <li>Avoid extreme head angles</li>
                        <li>We'll capture {TARGET_FRAMES} frames over {(TARGET_FRAMES * CAPTURE_INTERVAL) / 1000} seconds</li>
                        <li>The system will automatically select the best {10} quality images</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};
