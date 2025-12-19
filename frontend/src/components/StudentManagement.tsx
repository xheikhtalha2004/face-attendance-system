/**
 * Student Management Component
 * View, edit, and delete registered students
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/apiConfig';
import { MultiFrameEnrollment } from './MultiFrameEnrollment';

interface Student {
  id: number;
  name: string;
  rollNumber: string;
  email?: string;
  phone?: string;
  department?: string;
  createdAt: string;
}

interface Course {
  id: number;
  courseId: string;
  courseName: string;
  professorName: string;
}

interface Enrollment {
  id: number;
  courseId: number;
  courseName: string;
  professorName: string;
}

export const StudentManagement: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<Partial<Student>>({});
  const [viewingEnrollments, setViewingEnrollments] = useState<number | null>(null);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [updatingFaceId, setUpdatingFaceId] = useState<number | null>(null);

  useEffect(() => {
    fetchStudents();
    fetchCourses();
  }, []);

  const fetchStudents = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/students`);
      setStudents(response.data);
      setMessage(null);
    } catch (error: any) {
      console.error('Error fetching students:', error);
      setMessage('Failed to load students');
    } finally {
      setLoading(false);
    }
  };

  const fetchCourses = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/courses`);
      setAllCourses(response.data);
    } catch (error: any) {
      console.error('Error fetching courses:', error);
    }
  };

  const fetchEnrollments = async (studentId: number) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/students/${studentId}/enrollments`);
      setEnrollments(response.data);
      setViewingEnrollments(studentId);
    } catch (error: any) {
      console.error('Error fetching enrollments:', error);
      setMessage('Failed to load enrollments');
    }
  };

  const handleEnrollInCourse = async (studentId: number, courseId: number) => {
    try {
      await axios.post(`${API_BASE_URL}/students/${studentId}/enroll`, { courseId });
      setMessage('✅ Student enrolled in course');
      await fetchEnrollments(studentId);
    } catch (error: any) {
      console.error('Error enrolling student:', error);
      setMessage(error.response?.data?.error || 'Failed to enroll student');
    }
  };

  const handleUnenroll = async (studentId: number, enrollmentId: number) => {
    if (!window.confirm('Are you sure you want to unenroll from this course?')) return;

    try {
      await axios.delete(`${API_BASE_URL}/enrollments/${enrollmentId}`);
      setMessage('✅ Unenrolled successfully');
      await fetchEnrollments(studentId);
    } catch (error: any) {
      console.error('Error unenrolling:', error);
      setMessage(error.response?.data?.error || 'Failed to unenroll');
    }
  };

  const handleUpdateFaceData = (studentId: number) => {
    setUpdatingFaceId(studentId);
  };

  const completeFaceUpdate = async (frames: string[], studentId: number) => {
    try {
      await axios.post(`${API_BASE_URL}/students/${studentId}/update-face`, { frames });
      setMessage('✅ Facial data updated successfully');
      setUpdatingFaceId(null);
    } catch (error: any) {
      console.error('Error updating face data:', error);
      setMessage(error.response?.data?.error || 'Failed to update facial data');
      setUpdatingFaceId(null);
    }
  };

  const handleEdit = (student: Student) => {
    setEditingId(student.id);
    setEditForm(student);
  };

  const handleSaveEdit = async () => {
    if (!editingId) return;

    try {
      await axios.put(`${API_BASE_URL}/students/${editingId}`, {
        name: editForm.name,
        rollNumber: editForm.rollNumber,
        email: editForm.email,
        phone: editForm.phone,
        department: editForm.department
      });

      setMessage('✅ Student updated successfully');
      setEditingId(null);
      setEditForm({});
      await fetchStudents();
    } catch (error: any) {
      console.error('Error updating student:', error);
      setMessage(error.response?.data?.error || 'Failed to update student');
    }
  };

  const handleDelete = async (studentId: number, studentName: string) => {
    if (!window.confirm(`Are you sure you want to delete ${studentName}? This action cannot be undone.`)) {
      return;
    }

    try {
      const response = await axios.delete(`${API_BASE_URL}/students/${studentId}`);
      setMessage(`✅ ${response.data.deletedStudent.name} deleted successfully`);
      await fetchStudents();
    } catch (error: any) {
      console.error('Error deleting student:', error);
      setMessage(error.response?.data?.error || 'Failed to delete student');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading students...</div>;
  }

  if (updatingFaceId) {
    const student = students.find(s => s.id === updatingFaceId);
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Update Facial Data - {student?.name}</h2>
          <button
            onClick={() => setUpdatingFaceId(null)}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Cancel
          </button>
        </div>
        <MultiFrameEnrollment
          studentName={student?.name || ''}
          onComplete={(frames) => completeFaceUpdate(frames, updatingFaceId)}
          onCancel={() => setUpdatingFaceId(null)}
        />
      </div>
    );
  }

  if (viewingEnrollments !== null) {
    const student = students.find(s => s.id === viewingEnrollments);
    const enrolledCourseIds = enrollments.map(e => e.courseId);
    const availableCourses = allCourses.filter(c => !enrolledCourseIds.includes(c.id));

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Enrolled Courses - {student?.name}</h2>
          <button
            onClick={() => setViewingEnrollments(null)}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Back to Students
          </button>
        </div>

        {message && (
          <div className={`p-4 rounded mb-4 ${message.includes('✅') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            {message}
          </div>
        )}

        {/* Current Enrollments */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Current Enrollments ({enrollments.length})</h3>
          {enrollments.length === 0 ? (
            <p className="text-gray-500">Not enrolled in any courses</p>
          ) : (
            <div className="space-y-2">
              {enrollments.map((enrollment) => (
                <div key={enrollment.id} className="flex items-center justify-between p-3 border rounded">
                  <div>
                    <p className="font-medium">{enrollment.courseName}</p>
                    <p className="text-sm text-gray-600">{enrollment.courseId} - {enrollment.professorName}</p>
                  </div>
                  <button
                    onClick={() => handleUnenroll(viewingEnrollments, enrollment.id)}
                    className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                  >
                    Unenroll
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Available Courses to Enroll */}
        {availableCourses.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Available Courses ({availableCourses.length})</h3>
            <div className="space-y-2">
              {availableCourses.map((course) => (
                <div key={course.id} className="flex items-center justify-between p-3 border rounded">
                  <div>
                    <p className="font-medium">{course.courseName}</p>
                    <p className="text-sm text-gray-600">{course.courseId} - {course.professorName}</p>
                  </div>
                  <button
                    onClick={() => handleEnrollInCourse(viewingEnrollments, course.id)}
                    className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                  >
                    Enroll
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-4">Student Management</h2>
        
        {message && (
          <div className={`p-4 rounded mb-4 ${message.includes('✅') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            {message}
          </div>
        )}

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold">Name</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Roll Number</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Email</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Phone</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Department</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                editingId === student.id ? (
                  <tr key={student.id} className="border-t bg-blue-50">
                    <td className="px-6 py-3">
                      <input
                        type="text"
                        value={editForm.name || ''}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        className="border rounded px-2 py-1 w-full"
                      />
                    </td>
                    <td className="px-6 py-3">
                      <input
                        type="text"
                        value={editForm.rollNumber || ''}
                        onChange={(e) => setEditForm({ ...editForm, rollNumber: e.target.value })}
                        className="border rounded px-2 py-1 w-full"
                      />
                    </td>
                    <td className="px-6 py-3">
                      <input
                        type="email"
                        value={editForm.email || ''}
                        onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                        className="border rounded px-2 py-1 w-full"
                      />
                    </td>
                    <td className="px-6 py-3">
                      <input
                        type="tel"
                        value={editForm.phone || ''}
                        onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                        className="border rounded px-2 py-1 w-full"
                      />
                    </td>
                    <td className="px-6 py-3">
                      <input
                        type="text"
                        value={editForm.department || ''}
                        onChange={(e) => setEditForm({ ...editForm, department: e.target.value })}
                        className="border rounded px-2 py-1 w-full"
                      />
                    </td>
                    <td className="px-6 py-3 space-x-2">
                      <button
                        onClick={handleSaveEdit}
                        className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="px-3 py-1 bg-gray-400 text-white rounded text-sm hover:bg-gray-500"
                      >
                        Cancel
                      </button>
                    </td>
                  </tr>
                ) : (
                  <tr key={student.id} className="border-t hover:bg-gray-50">
                    <td className="px-6 py-3">{student.name}</td>
                    <td className="px-6 py-3">{student.rollNumber}</td>
                    <td className="px-6 py-3 text-sm text-gray-600">{student.email || '-'}</td>
                    <td className="px-6 py-3 text-sm text-gray-600">{student.phone || '-'}</td>
                    <td className="px-6 py-3 text-sm text-gray-600">{student.department || '-'}</td>
                    <td className="px-6 py-3 space-x-2">
                      <button
                        onClick={() => handleEdit(student)}
                        className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                        title="Edit basic info"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => fetchEnrollments(student.id)}
                        className="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700"
                        title="View/manage enrolled courses"
                      >
                        Courses
                      </button>
                      <button
                        onClick={() => handleUpdateFaceData(student.id)}
                        className="px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700"
                        title="Update facial data"
                      >
                        Face
                      </button>
                      <button
                        onClick={() => handleDelete(student.id, student.name)}
                        className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                        title="Delete student"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                )
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-sm text-gray-600 mt-4">
          Total Students: <strong>{students.length}</strong>
        </p>
      </div>
    </div>
  );
};

export default StudentManagement;
