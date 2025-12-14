/**
 * Session Attendance Table Component
 * Shows one row per student with real-time status updates
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Download, FileText } from 'lucide-react';
import { API_BASE_URL } from '../utils/apiConfig';

interface AttendanceRecord {
    id: string;
    studentId: string;
    studentName: string;
    checkInTime: string | null;
    lastSeenTime: string | null;
    status: 'PRESENT' | 'LATE' | 'ABSENT';
    confidence: number;
    courseName: string;
    professorName: string;
}

interface SessionAttendanceProps {
    sessionId?: number;
    autoRefresh?: boolean;
    refreshInterval?: number;
}

export const SessionAttendanceTable: React.FC<SessionAttendanceProps> = ({
    sessionId,
    autoRefresh = true,
    refreshInterval = 5000
}) => {
    const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeSessionId, setActiveSessionId] = useState<number | null>(sessionId || null);
    const [sessionInfo, setSessionInfo] = useState<any>(null);

    useEffect(() => {
        if (!sessionId) {
            fetchActiveSession();
        }
    }, [sessionId]);

    useEffect(() => {
        if (activeSessionId) {
            fetchAttendance();

            if (autoRefresh) {
                const interval = setInterval(fetchAttendance, refreshInterval);
                return () => clearInterval(interval);
            }
        }
    }, [activeSessionId, autoRefresh, refreshInterval]);

    const fetchActiveSession = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/sessions/active`);

            if (response.data.active) {
                setActiveSessionId(response.data.session.id);
                setSessionInfo(response.data.session);
            } else {
                setLoading(false);
            }
        } catch (error) {
            console.error('Error fetching active session:', error);
            setLoading(false);
        }
    };

    const fetchAttendance = async () => {
        if (!activeSessionId) return;

        try {
            const response = await axios.get(
                `${API_BASE_URL}/sessions/${activeSessionId}/attendance`
            );

            setAttendance(response.data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching attendance:', error);
            setLoading(false);
        }
    };

    const formatTime = (timestamp: string | null) => {
        if (!timestamp) return '-';
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'PRESENT':
                return 'bg-green-100 text-green-800 border-green-300';
            case 'LATE':
                return 'bg-yellow-100 text-yellow-800 border-yellow-300';
            case 'ABSENT':
                return 'bg-red-100 text-red-800 border-red-300';
            default:
                return 'bg-gray-100 text-gray-800 border-gray-300';
        }
    };

    const handleExport = async (format: 'csv' | 'excel') => {
        if (!activeSessionId) return;

        try {
            const response = await axios.get(
                `${API_BASE_URL}/sessions/${activeSessionId}/export?format=${format}`,
                { responseType: 'blob' }
            );

            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `attendance_session_${activeSessionId}.${format === 'csv' ? 'csv' : 'xlsx'}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error exporting attendance:', error);
            alert('Failed to export attendance data. Please try again.');
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-gray-500">Loading attendance...</div>
            </div>
        );
    }

    if (!activeSessionId) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-center">
                    <p className="text-xl text-gray-600 mb-2">No Active Session</p>
                    <p className="text-sm text-gray-500">
                        Please create a session or wait for auto-session from timetable
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow">
            {/* Session Header */}
            {sessionInfo && (
                <div className="p-4 border-b bg-blue-50">
                    <div className="flex justify-between items-start">
                        <div>
                            <h2 className="text-xl font-bold text-blue-900">
                                {sessionInfo.courseName}
                            </h2>
                            <p className="text-sm text-blue-700">
                                Professor: {sessionInfo.professorName} |
                                Started: {formatTime(sessionInfo.startsAt)}
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => handleExport('csv')}
                                className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-50 transition text-sm font-medium"
                                title="Export to CSV"
                            >
                                <FileText className="w-4 h-4" />
                                CSV
                            </button>
                            <button
                                onClick={() => handleExport('excel')}
                                className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-50 transition text-sm font-medium"
                                title="Export to Excel"
                            >
                                <Download className="w-4 h-4" />
                                Excel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Stats Summary */}
            <div className="p-4 border-b bg-gray-50">
                <div className="grid grid-cols-4 gap-4 text-center">
                    <div>
                        <div className="text-2xl font-bold text-gray-900">{attendance.length}</div>
                        <div className="text-xs text-gray-600">Total</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-green-600">
                            {attendance.filter(a => a.status === 'PRESENT').length}
                        </div>
                        <div className="text-xs text-gray-600">Present</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-yellow-600">
                            {attendance.filter(a => a.status === 'LATE').length}
                        </div>
                        <div className="text-xs text-gray-600">Late</div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-red-600">
                            {attendance.filter(a => a.status === 'ABSENT').length}
                        </div>
                        <div className="text-xs text-gray-600">Absent</div>
                    </div>
                </div>
            </div>

            {/* Attendance Table */}
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead className="bg-gray-100 border-b">
                        <tr>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                                Student
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                                Status
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                                Check-in Time
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                                Last Seen
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                                Confidence
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y">
                        {attendance.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                                    No attendance records yet
                                </td>
                            </tr>
                        ) : (
                            attendance.map((record) => (
                                <tr key={record.id} className="hover:bg-gray-50">
                                    <td className="px-4 py-3">
                                        <div className="font-medium text-gray-900">
                                            {record.studentName}
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            ID: {record.studentId}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full border ${getStatusBadge(record.status)}`}>
                                            {record.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-700">
                                        {formatTime(record.checkInTime)}
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-700">
                                        {formatTime(record.lastSeenTime)}
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-blue-500"
                                                    style={{ width: `${record.confidence * 100}%` }}
                                                />
                                            </div>
                                            <span className="text-xs text-gray-600">
                                                {(record.confidence * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Auto-refresh Indicator */}
            {autoRefresh && (
                <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500 flex items-center justify-between">
                    <span>🔄 Auto-refreshing every {refreshInterval / 1000}s</span>
                    <span>Last updated: {new Date().toLocaleTimeString()}</span>
                </div>
            )}
        </div>
    );
};
