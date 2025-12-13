/**
 * Timetable Management Page
 * Weekly grid view for managing course schedule (5 slots × 5 days)
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

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

  useEffect(() => {
    fetchTimetable();
    fetchCourses();
  }, []);

  const fetchTimetable = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/timetable`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTimetable(response.data);
    } catch (error) {
      console.error('Error fetching timetable:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCourses = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/courses`, {
        headers: { Authorization: `Bearer ${token}` }
      });
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
      const token = localStorage.getItem('token');
      const slotTime = SLOT_TIMES[editingSlot.slot as keyof typeof SLOT_TIMES];

      await axios.post(
        `${API_URL}/api/timetable/slots`,
        {
          dayOfWeek: editingSlot.day,
          slotNumber: editingSlot.slot,
          courseId: selectedCourse,
          startTime: slotTime.start,
          endTime: slotTime.end,
          lateThresholdMinutes: 5
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Refresh timetable
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
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/timetable/slots/${slotId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      await fetchTimetable();
    } catch (error) {
      console.error('Error deleting slot:', error);
      alert('Failed to delete time slot');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading timetable...</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Weekly Timetable</h1>
        <button
          onClick={fetchTimetable}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          🔄 Refresh
        </button>
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
                            🗑️ Remove
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
          ☕ <strong>Break Time:</strong> 12:30 - 13:30 (60 minutes)
        </p>
      </div>
    </div>
  );
};
