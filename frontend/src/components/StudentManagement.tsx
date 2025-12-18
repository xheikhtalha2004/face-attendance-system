/**
 * Student Management Component
 * View, edit, and delete registered students
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/apiConfig';

interface Student {
  id: number;
  name: string;
  rollNumber: string;
  email?: string;
  phone?: string;
  department?: string;
  createdAt: string;
}

export const StudentManagement: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<Partial<Student>>({});

  useEffect(() => {
    fetchStudents();
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
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(student.id, student.name)}
                        className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
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
