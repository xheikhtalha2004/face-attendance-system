/**
 * Student Self-Registration Form
 * Allows students to register themselves with facial enrollment and course selection
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/apiConfig';
import { MultiFrameEnrollment } from './MultiFrameEnrollment';

interface Course {
    id: number;
    courseId: string;
    courseName: string;
    professorName: string;
}

export const StudentRegistrationForm: React.FC = () => {
    const [step, setStep] = useState<'form' | 'enrollment'>('form');
    const [formData, setFormData] = useState({
        name: '',
        studentId: '',
        email: '',
        selectedCourses: [] as number[]
    });
    const [courses, setCourses] = useState<Course[]>([]);
    const [validationMessage, setValidationMessage] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [tempStudentId, setTempStudentId] = useState<number | null>(null);
    const [enrollmentFrames, setEnrollmentFrames] = useState<string[]>([]);

    useEffect(() => {
        loadCourses();
    }, []);

    const loadCourses = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/courses`);
            setCourses(response.data);
        } catch (error) {
            console.error('Error loading courses:', error);
        }
    };

    const validateStudentId = async (id: string) => {
        if (id.length < 10) {
            setValidationMessage('');
            return;
        }

        try {
            const response = await axios.get(`${API_BASE_URL}/register/validate-id/${id}`);
            if (response.data.validFormat && response.data.available) {
                setValidationMessage('✓ Valid and available');
            } else if (!response.data.validFormat) {
                setValidationMessage('❌ Invalid format (use SPXX-BCS-XXX)');
            } else {
                setValidationMessage('❌ Already registered');
            }
        } catch (error) {
            console.error('Validation error:', error);
        }
    };

    const handleStudentIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value.toUpperCase();
        setFormData({ ...formData, studentId: value });
        validateStudentId(value);
    };

    const toggleCourse = (courseId: number) => {
        const selected = formData.selectedCourses;
        if (selected.includes(courseId)) {
            setFormData({
                ...formData,
                selectedCourses: selected.filter(id => id !== courseId)
            });
        } else {
            setFormData({
                ...formData,
                selectedCourses: [...selected, courseId]
            });
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!formData.name || !formData.studentId) {
            alert('Please fill in all required fields');
            return;
        }

        if (formData.selectedCourses.length === 0) {
            alert('Please select at least one course');
            return;
        }

        setSubmitting(true);

        try {
            // First, start webcam capture for enrollment
            setStep('enrollment');
        } catch (error) {
            console.error('Registration error:', error);
            setSubmitting(false);
        }
    };

    const handleEnrollmentFrames = (frames: string[]) => {
        setEnrollmentFrames(frames);
    };

    const completeRegistration = async (frames: string[]) => {
        try {
            const response = await axios.post(`${API_BASE_URL}/register/student`, {
                name: formData.name,
                studentId: formData.studentId,
                email: formData.email,
                frames: frames,
                selectedCourses: formData.selectedCourses
            });

            alert(response.data.message);

            // Reset form
            setFormData({
                name: '',
                studentId: '',
                email: '',
                selectedCourses: []
            });
            setStep('form');
            setSubmitting(false);
        } catch (error: any) {
            console.error('Registration error:', error);
            alert(`Registration failed: ${error.response?.data?.error || error.message}`);
            setStep('form');
            setSubmitting(false);
        }
    };

    if (step === 'enrollment') {
        return (
            <EnrollmentCapture
                studentName={formData.name}
                onComplete={(frames) => completeRegistration(frames)}
                onCancel={() => {
                    setStep('form');
                    setSubmitting(false);
                }}
            />
        );
    }

    return (
        <div className="min-h-screen bg-gray-100 py-8 px-4">
            <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8">
                <h1 className="text-3xl font-bold mb-6 text-center">Student Registration</h1>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Name */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">
                            Full Name <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                            placeholder="e.g., Alice Smith"
                            required
                        />
                    </div>

                    {/* Student ID */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">
                            Student ID <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            value={formData.studentId}
                            onChange={handleStudentIdChange}
                            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                            placeholder="SPXX-BCS-XXX (e.g., SP21-BCS-001)"
                            required
                        />
                        {validationMessage && (
                            <p className={`text-sm mt-1 ${validationMessage.includes('✓') ? 'text-green-600' : 'text-red-600'}`}>
                                {validationMessage}
                            </p>
                        )}
                    </div>

                    {/* Email */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">
                            Email (Optional)
                        </label>
                        <input
                            type="email"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                            placeholder="alice@example.com"
                        />
                    </div>

                    {/* Course Selection */}
                    <div>
                        <label className="block text-sm font-semibold mb-2">
                            Select Courses <span className="text-red-500">*</span>
                        </label>
                        <div className="border rounded-lg p-4 max-h-64 overflow-y-auto space-y-2">
                            {courses.length === 0 ? (
                                <p className="text-gray-500 text-sm">No courses available</p>
                            ) : (
                                courses.map(course => (
                                    <label key={course.id} className="flex items-center p-2 hover:bg-gray-50 rounded cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={formData.selectedCourses.includes(course.id)}
                                            onChange={() => toggleCourse(course.id)}
                                            className="mr-3 w-4 h-4"
                                        />
                                        <div>
                                            <div className="font-medium">{course.courseName}</div>
                                            <div className="text-sm text-gray-600">
                                                {course.courseId} - {course.professorName}
                                            </div>
                                        </div>
                                    </label>
                                ))
                            )}
                        </div>
                        <p className="text-sm text-gray-600 mt-2">
                            Selected: {formData.selectedCourses.length} course(s)
                        </p>
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={submitting}
                        className="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 disabled:bg-gray-300"
                    >
                        {submitting ? 'Processing...' : '📸 Continue to Facial Enrollment'}
                    </button>
                </form>

                {/* Info Box */}
                <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="font-semibold mb-2">ℹ️ What happens next?</h4>
                    <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
                        <li>You'll be taken to facial enrollment (15 frames captured)</li>
                        <li>Your face data will be securely stored</li>
                        <li>You'll be enrolled in your selected courses</li>
                        <li>You can then attend classes with automatic face recognition</li>
                    </ol>
                </div>
            </div>
        </div>
    );
};

// Enrollment Capture Component (simplified wrapper)
interface EnrollmentCaptureProps {
    studentName: string;
    onComplete: (frames: string[]) => void;
    onCancel: () => void;
}

const EnrollmentCapture: React.FC<EnrollmentCaptureProps> = ({ studentName, onComplete, onCancel }) => {
    const [frames, setFrames] = useState<string[]>([]);
    const videoRef = React.useRef<HTMLVideoElement>(null);
    const canvasRef = React.useRef<HTMLCanvasElement>(null);
    const [capturing, setCapturing] = useState(false);
    const [progress, setProgress] = useState(0);

    React.useEffect(() => {
        startWebcam();
        return () => stopWebcam();
    }, []);

    const startWebcam = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
        } catch (error) {
            console.error('Webcam error:', error);
            alert('Failed to access webcam');
        }
    };

    const stopWebcam = () => {
        if (videoRef.current?.srcObject) {
            (videoRef.current.srcObject as MediaStream).getTracks().forEach(track => track.stop());
        }
    };

    const captureFrames = async () => {
        if (!videoRef.current || !canvasRef.current) return;

        setCapturing(true);
        const captured: string[] = [];
        const canvas = canvasRef.current;
        const video = videoRef.current;
        const ctx = canvas.getContext('2d')!;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        for (let i = 0; i < 15; i++) {
            ctx.drawImage(video, 0, 0);
            captured.push(canvas.toDataURL('image/jpeg', 0.9));
            setProgress(((i + 1) / 15) * 100);
            if (i < 14) await new Promise(r => setTimeout(r, 200));
        }

        setFrames(captured);
        setCapturing(false);
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full">
                <h2 className="text-2xl font-bold mb-4">Facial Enrollment: {studentName}</h2>

                <div className="relative bg-black rounded-lg overflow-hidden mb-4">
                    <video ref={videoRef} autoPlay playsInline muted className="w-full" />
                    <canvas ref={canvasRef} className="hidden" />
                    {capturing && (
                        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                            <div className="bg-white p-4 rounded-lg">
                                <div className="w-64 h-4 bg-gray-300 rounded-full">
                                    <div className="h-full bg-blue-500" style={{ width: `${progress}%` }} />
                                </div>
                                <p className="mt-2 text-center">{Math.round(progress)}%</p>
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex gap-2 justify-end">
                    <button onClick={onCancel} className="px-4 py-2 border rounded" disabled={capturing}>
                        Cancel
                    </button>
                    {frames.length === 0 ? (
                        <button
                            onClick={captureFrames}
                            disabled={capturing}
                            className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                        >
                            📸 Start Capture
                        </button>
                    ) : (
                        <>
                            <button onClick={() => setFrames([])} className="px-4 py-2 border rounded">
                                Retake
                            </button>
                            <button
                                onClick={() => onComplete(frames)}
                                className="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                            >
                                ✓ Submit
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};
