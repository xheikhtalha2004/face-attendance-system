/**
 * Export CSV Button Component
 * Allows downloading session attendance as CSV
 */
import React from 'react';
import { API_BASE_URL } from '../utils/apiConfig';

interface ExportButtonProps {
    sessionId: number;
    courseName?: string;
}

export const ExportButton: React.FC<ExportButtonProps> = ({ sessionId, courseName }) => {
    const handleExport = () => {
        const url = `${API_BASE_URL}/sessions/${sessionId}/export`;
        window.open(url, '_blank');
    };

    return (
        <button
            onClick={handleExport}
            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 font-semibold inline-flex items-center gap-2"
        >
            <span>📥</span>
            <span>Export CSV</span>
        </button>
    );
};
