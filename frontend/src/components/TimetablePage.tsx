/**
 * Timetable Management Page
 * Weekly grid view + course creation form
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/apiConfig';

interface Course {
  id: number;
  courseId: string;
  courseName: string;
  professorName: string;
  isActive: boolean;
}

interface TimeSlot {
  id: number;
  dayOfWeek: string;
  slotNumber: number;
  courseId: number;
  courseName: string;
  professorName: string;
  startTime: string;
  endTime: string;
  lateThresholdMinutes: number;
  isActive: boolean;
}

interface TimetableData {
  [day: string]: {
    [slotNum: string]: TimeSlot;
  };
}

const DAYS = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'];
const SLOT_TIMES = {
  1: { start: '08:30', end: '09:50' },
  2: { start: '09:50', end: '11:10' },
  3: { start: '11:10', end: '12:30' },
  4: { start: '13:30', end: '14:50' },
  5: { start: '14:50', end: '16:10' }
};

export const TimetablePage: React.FC = () => {
  const [timetable, setTimetable] = useState<TimetableData>({});
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingSlot, setEditingSlot] = useState<{ day: string; slot: number } | null>(null);
  const [selectedCourse, setSelectedCourse] = useState<number | null>(null);
  const [newCourse, setNewCourse] = useState({ courseId: '', courseName: '', professorName: '', description: '' });
  const [savingCourse, setSavingCourse] = useState(false);
  const [courseMessage, setCourseMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchTimetable();
    fetchCourses();
  }, []);

  const fetchTimetable = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/timetable`);
      setTimetable(response.data);
    } catch (error) {
      console.error('Error fetching timetable:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCourses = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/courses`);
      setCourses(response.data);
    } catch (error) {
      console.error('Error fetching courses:', error);
    }
  };

  const handleSlotClick = (day: string, slotNumber: number) => {
    setEditingSlot({ day, slot: slotNumber });
    const existingSlot = timetable[day]?.[slotNumber];
    setSelectedCourse(existingSlot?.courseId || null);
  };

  const handleSaveSlot = async () => {
    if (!editingSlot || selectedCourse === null) return;

    try {
      const slotTime = SLOT_TIMES[editingSlot.slot as keyof typeof SLOT_TIMES];

      await axios.post(
        `${API_BASE_URL}/timetable/slots`,
        {
          dayOfWeek: editingSlot.day,
          slotNumber: editingSlot.slot,
          courseId: selectedCourse,
          startTime: slotTime.start,
          endTime: slotTime.end,
          lateThresholdMinutes: 5
        }
      );

      await fetchTimetable();
      setEditingSlot(null);
      setSelectedCourse(null);
    } catch (error) {
      console.error('Error saving slot:', error);
      alert('Failed to save time slot');
    }
  };

  const handleDeleteSlot = async (slotId: number) => {
    if (!confirm('Remove this course from the timetable?')) return;

    try {
      await axios.delete(`${API_BASE_URL}/timetable/slots/${slotId}`);
      await fetchTimetable();
    } catch (error) {
      console.error('Error deleting slot:', error);
      alert('Failed to delete time slot');
    }
  };

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCourse.courseId || !newCourse.courseName || !newCourse.professorName) {
      setCourseMessage('Please fill course code, name, and professor.');
      return;
    }

    setSavingCourse(true);
    setCourseMessage(null);
    try {
      console.log('Sending course data:', {
        courseId: newCourse.courseId.trim(),
        courseName: newCourse.courseName.trim(),
        professorName: newCourse.professorName.trim(),
        description: newCourse.description.trim() || undefined
      });
      
      const response = await axios.post(`${API_BASE_URL}/courses`, {
        courseId: newCourse.courseId.trim(),
        courseName: newCourse.courseName.trim(),
        professorName: newCourse.professorName.trim(),
        description: newCourse.description.trim() || undefined
      });
      
      console.log('Course creation response:', response.data);
      setCourseMessage('Course added successfully.');
      setNewCourse({ courseId: '', courseName: '', professorName: '', description: '' });
      await fetchCourses();
    } catch (error: any) {
      console.error('Error creating course:', error);
      console.error('Response status:', error.response?.status);
      console.error('Response data:', error.response?.data);
      console.error('Error message:', error.message);
      setCourseMessage(error.response?.data?.error || error.message || 'Failed to add course');
    } finally {
      setSavingCourse(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading timetable...</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
        <h1 className="text-3xl font-bold">Weekly Timetable</h1>
        <button
          onClick={fetchTimetable}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Refresh
        </button>
      </div>

      {/* Course creator */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Add a Course</h3>
        <form className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3" onSubmit={handleCreateCourse}>
          <input
            type="text"
            placeholder="Course Code (e.g., CS-101)"
            value={newCourse.courseId}
            onChange={(e) => setNewCourse({ ...newCourse, courseId: e.target.value })}
            className="border rounded px-3 py-2"
            required
          />
          <input
            type="text"
            placeholder="Course Name"
            value={newCourse.courseName}
            onChange={(e) => setNewCourse({ ...newCourse, courseName: e.target.value })}
            className="border rounded px-3 py-2"
            required
          />
          <input
            type="text"
            placeholder="Professor Name"
            value={newCourse.professorName}
            onChange={(e) => setNewCourse({ ...newCourse, professorName: e.target.value })}
            className="border rounded px-3 py-2"
            required
          />
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Description (optional)"
              value={newCourse.description}
              onChange={(e) => setNewCourse({ ...newCourse, description: e.target.value })}
              className="border rounded px-3 py-2 flex-1"
            />
            <button
              type="submit"
              disabled={savingCourse}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-300"
            >
              {savingCourse ? 'Saving...' : 'Add'}
            </button>
          </div>
        </form>
        {courseMessage && <p className="text-sm mt-2 text-gray-700">{courseMessage}</p>}
      </div>

      {/* Timetable Grid */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gray-100">
              <th className="border p-3 text-left font-semibold">Time</th>
              {DAYS.map(day => (
                <th key={day} className="border p-3 text-center font-semibold">
                  {day}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.entries(SLOT_TIMES).map(([slotNum, times]) => (
              <tr key={slotNum} className="hover:bg-gray-50">
                <td className="border p-3 bg-gray-50">
                  <div className="font-medium">Slot {slotNum}</div>
                  <div className="text-sm text-gray-600">
                    {times.start} - {times.end}
                  </div>
                </td>
                {DAYS.map(day => {
                  const slot = timetable[day]?.[slotNum];
                  return (
                    <td
                      key={`${day}-${slotNum}`}
                      className="border p-3 cursor-pointer hover:bg-blue-50 transition"
                      onClick={() => handleSlotClick(day, parseInt(slotNum))}
                    >
                      {slot ? (
                        <div className="space-y-1">
                          <div className="font-semibold text-blue-600">
                            {slot.courseName}
                          </div>
                          <div className="text-sm text-gray-600">
                            {slot.professorName}
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteSlot(slot.id);
                            }}
                            className="text-xs text-red-500 hover:text-red-700"
                          >
                            Remove
                          </button>
                        </div>
                      ) : (
                        <div className="text-center text-gray-400">
                          + Add Course
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Edit Slot Modal */}
      {editingSlot && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">
              Edit {editingSlot.day} - Slot {editingSlot.slot}
            </h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Select Course:</label>
              <select
                value={selectedCourse || ''}
                onChange={(e) => setSelectedCourse(parseInt(e.target.value))}
                className="w-full border rounded px-3 py-2"
              >
                <option value="">-- Select Course --</option>
                {courses.map(course => (
                  <option key={course.id} value={course.id}>
                    {course.courseName} ({course.professorName})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setEditingSlot(null);
                  setSelectedCourse(null);
                }}
                className="px-4 py-2 border rounded hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSlot}
                disabled={selectedCourse === null}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Break Time Indicator */}
      <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
        <p className="text-sm text-yellow-800">
          <strong>Break Time:</strong> 12:30 - 13:30 (60 minutes)
        </p>
      </div>
    </div>
  );
};

