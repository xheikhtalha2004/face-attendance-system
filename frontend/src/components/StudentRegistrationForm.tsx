/**
 * Student Self-Registration Form
 * Collects basic info, course selection, and multi-frame facial enrollment
 */
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/apiConfig';

interface Course {
  id: number;
  courseId: string;
  courseName: string;
  professorName: string;
}

type Step = 'form' | 'capture';

export const StudentRegistrationForm: React.FC = () => {
  const [step, setStep] = useState<Step>('form');
  const [formData, setFormData] = useState({
    name: '',
    studentId: '',
    email: '',
    department: '',
    selectedCourses: [] as number[],
  });
  const [courses, setCourses] = useState<Course[]>([]);
  const [validationMessage, setValidationMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [captureSession, setCaptureSession] = useState(0); // forces new capture component

  const DEPARTMENTS = [
    'Computer Science',
    'Software Engineering',
    'Electrical Engineering',
    'Artificial Intelligence',
    'Business Administration',
    'Mathematics',
    'Physics',
  ];

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
      setValidationMessage(null);
      return;
    }

    try {
      const response = await axios.get(`${API_BASE_URL}/register/validate-id/${id}`);
      if (response.data.validFormat && response.data.available) {
        setValidationMessage({ type: 'success', text: 'ID format is valid and available' });
      } else if (!response.data.validFormat) {
        setValidationMessage({ type: 'error', text: 'Invalid format (use SPXX-BCS-XXX, e.g. SP21-BCS-001)' });
      } else {
        setValidationMessage({ type: 'error', text: 'This student ID is already registered' });
      }
    } catch (error) {
      console.error('Validation error:', error);
      setValidationMessage({ type: 'error', text: 'Could not validate ID. Check network and try again.' });
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
        selectedCourses: selected.filter((id) => id !== courseId),
      });
    } else {
      setFormData({
        ...formData,
        selectedCourses: [...selected, courseId],
      });
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name || !formData.studentId || !formData.department) {
      alert('Please fill in all required fields including department');
      return;
    }

    if (formData.selectedCourses.length === 0) {
      alert('Please select at least one course');
      return;
    }

    setSubmitting(true);
    setCaptureSession((prev) => prev + 1);
    setStep('capture');
  };

  const completeRegistration = async (frames: string[]) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/register/student`, {
        name: formData.name,
        studentId: formData.studentId,
        email: formData.email,
        department: formData.department,
        frames: frames,
        selectedCourses: formData.selectedCourses,
      });

      alert(response.data.message);

      setFormData({
        name: '',
        studentId: '',
        email: '',
        department: '',
        selectedCourses: [],
      });
      setStep('form');
    } catch (error: any) {
      console.error('Registration error:', error);
      alert(`Registration failed: ${error.response?.data?.error || error.message}`);
      setStep('form');
    } finally {
      setSubmitting(false);
    }
  };

  if (step === 'capture') {
    return (
      <EnrollmentCapture
        key={captureSession}
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
        <h1 className="text-3xl font-bold mb-3 text-center">Student Registration</h1>
        <p className="text-gray-600 text-center mb-6">
          Enter your details, choose courses, then capture a quick facial scan to complete enrollment.
        </p>

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
              <p className={`text-sm mt-1 ${validationMessage.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                {validationMessage.text}
              </p>
            )}
          </div>

          {/* Department */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              Department <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 bg-white"
              required
            >
              <option value="">Select department</option>
              {DEPARTMENTS.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-semibold mb-2">Email (Optional)</label>
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
                courses.map((course) => (
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
            <div className="flex items-center justify-between text-sm text-gray-600 mt-2">
              <span>Selected: {formData.selectedCourses.length} course(s)</span>
              {formData.selectedCourses.length > 0 && (
                <button
                  type="button"
                  className="text-blue-600 hover:underline"
                  onClick={() => setFormData({ ...formData, selectedCourses: [] })}
                >
                  Clear selection
                </button>
              )}
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300"
          >
            {submitting ? 'Preparing capture...' : 'Continue to Facial Enrollment'}
          </button>
        </form>

        {/* Info Box */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="font-semibold mb-2">What happens next?</h4>
          <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
            <li>We will capture 12–15 frames from your webcam.</li>
            <li>Only the best-quality frames are stored and linked to your profile.</li>
            <li>Your selected courses are attached automatically.</li>
            <li>After submission you can use face recognition to mark attendance.</li>
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
  const [status, setStatus] = useState('Ready to capture 12 frames. Keep your face centered and well lit.');

  const TARGET_FRAMES = 12;

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
      alert('Failed to access webcam. Please allow camera permissions and try again.');
      onCancel();
    }
  };

  const stopWebcam = () => {
    if (videoRef.current?.srcObject) {
      (videoRef.current.srcObject as MediaStream).getTracks().forEach((track) => track.stop());
    }
  };

  const captureFrames = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    setCapturing(true);
    setStatus('Capturing frames... hold still');
    const captured: string[] = [];
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    for (let i = 0; i < TARGET_FRAMES; i++) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      captured.push(canvas.toDataURL('image/jpeg', 0.9));
      setProgress(((i + 1) / TARGET_FRAMES) * 100);
      if (i < TARGET_FRAMES - 1) {
        await new Promise((r) => setTimeout(r, 180));
      }
    }

    setFrames(captured);
    setStatus(`Captured ${captured.length} frames. Review and submit or retake.`);
    setCapturing(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-3xl w-full max-h-screen overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-2xl font-bold">Facial Enrollment</h2>
            <p className="text-gray-600 text-sm">Capturing frames for {studentName}</p>
          </div>
          <button onClick={onCancel} className="text-gray-500 hover:text-gray-700 text-xl" disabled={capturing}>
            ×
          </button>
        </div>

        <div className="relative bg-black rounded-lg overflow-hidden mb-4">
          <video ref={videoRef} autoPlay playsInline muted className="w-full" />
          <canvas ref={canvasRef} className="hidden" />
          {capturing && (
            <div className="absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center">
              <div className="bg-white p-4 rounded-lg shadow">
                <div className="text-center font-semibold mb-2">Capturing...</div>
                <div className="w-64 h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500" style={{ width: `${progress}%` }} />
                </div>
                <p className="mt-2 text-sm text-gray-600">{Math.round(progress)}% complete</p>
              </div>
            </div>
          )}
        </div>

        <div className="mb-4 p-3 bg-gray-50 border rounded-lg text-sm text-gray-700">{status}</div>

        {frames.length > 0 && (
          <div className="mb-4">
            <h4 className="font-semibold mb-2 text-sm">Captured frames ({frames.length})</h4>
            <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
              {frames.map((frame, index) => (
                <img key={index} src={frame} alt={`Frame ${index + 1}`} className="w-full h-20 object-cover rounded border" />
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-2 justify-end">
          <button onClick={onCancel} className="px-4 py-2 border rounded" disabled={capturing}>
            Back
          </button>
          {frames.length === 0 ? (
            <button
              onClick={captureFrames}
              disabled={capturing}
              className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300"
            >
              {capturing ? 'Capturing...' : 'Start Capture'}
            </button>
          ) : (
            <>
              <button
                onClick={() => {
                  setFrames([]);
                  setProgress(0);
                  setStatus('Ready to capture again.');
                }}
                className="px-4 py-2 border rounded"
              >
                Retake
              </button>
              <button
                onClick={() => onComplete(frames)}
                className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                disabled={capturing || frames.length < 5}
              >
                Submit {frames.length >= 5 ? '' : '(need 5+ frames)'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
