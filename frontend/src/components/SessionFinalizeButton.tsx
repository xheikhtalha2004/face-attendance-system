/**
 * Session Finalize Button Component
 * Allows manual finalization of active session
 */
import React, { useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../utils/apiConfig';

interface Session {
    id: number;
    courseName: string;
    status: string;
}

interface FinalizeButtonProps {
    session: Session | null;
    onFinalized: () => void;
}

export const SessionFinalizeButton: React.FC<FinalizeButtonProps> = ({ session, onFinalized }) => {
    const [finalizing, setFinalizing] = useState(false);

    if (!session || session.status === 'COMPLETED') {
        return null;
    }

    const handleFinalize = async () => {
        if (!confirm(`Finalize session for ${session.courseName}? This will mark absent students.`)) {
            return;
        }

        setFinalizing(true);

        try {
            const response = await axios.post(`${API_BASE_URL}/sessions/${session.id}/finalize`);

            alert(
                `✓ Session finalized!\n\n` +
                `Present: ${response.data.presentCount}\n` +
                `Absent: ${response.data.absentCount}\n` +
                `Total Enrolled: ${response.data.totalEnrolled}`
            );

            onFinalized();
        } catch (error: any) {
            console.error('Finalize error:', error);
            alert(`Failed to finalize: ${error.response?.data?.error || error.message}`);
        } finally {
            setFinalizing(false);
        }
    };

    return (
        <button
            onClick={handleFinalize}
            disabled={finalizing}
            className="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:bg-gray-300 font-semibold"
        >
            {finalizing ? 'Finalizing...' : '🏁 Finalize Session'}
        </button>
    );
};
