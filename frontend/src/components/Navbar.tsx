import React from 'react';
import { Home, Settings } from 'lucide-react';

interface NavbarProps {
  onNavigate: (view: string) => void;
  currentView: string;
}

const Navbar: React.FC<NavbarProps> = ({ onNavigate, currentView }) => {
  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center cursor-pointer" onClick={() => onNavigate('home')}>
            <div className="flex-shrink-0 flex items-center gap-2">
              <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold shadow-md">
                FA
              </div>
              <span className="text-xl font-bold text-gray-900 tracking-tight">FaceAttend Pro</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Main Navigation */}
            <div className="hidden md:flex gap-2">
              <button
                onClick={() => onNavigate('dashboard')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${currentView === 'dashboard' ? 'text-indigo-600 bg-indigo-50' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => onNavigate('recognition')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${currentView === 'recognition' ? 'text-indigo-600 bg-indigo-50' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  }`}
              >
                Recognition
              </button>
              <button
                onClick={() => onNavigate('testing')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${currentView === 'testing' ? 'text-indigo-600 bg-indigo-50' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  }`}
              >
                Testing
              </button>
              <button
                onClick={() => onNavigate('attendance')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${currentView === 'attendance' ? 'text-indigo-600 bg-indigo-50' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  }`}
              >
                Attendance
              </button>
              <button
                onClick={() => onNavigate('registration')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${currentView === 'registration' ? 'text-indigo-600 bg-indigo-50' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  }`}
              >
                Register
              </button>
              <button
                onClick={() => onNavigate('timetable')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${currentView === 'timetable' ? 'text-indigo-600 bg-indigo-50' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  }`}
              >
                Timetable
              </button>
              <button
                onClick={() => onNavigate('reports')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${currentView === 'reports' ? 'text-indigo-600 bg-indigo-50' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  }`}
              >
                Reports
              </button>
              <button
                onClick={() => onNavigate('students')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${currentView === 'students' ? 'text-indigo-600 bg-indigo-50' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  }`}
              >
                Students
              </button>
              <button
                onClick={() => onNavigate('sessions')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${currentView === 'sessions' ? 'text-indigo-600 bg-indigo-50' : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                  }`}
              >
                Sessions
              </button>
            </div>

            <div className="h-6 w-px bg-gray-200 mx-1"></div>

            {/* Icon Navigation */}
            <button
              onClick={() => onNavigate('home')}
              className={`p-2 rounded-md transition-colors ${currentView === 'home' ? 'text-indigo-600 bg-indigo-50' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                }`}
              title="Home"
            >
              <Home className="w-5 h-5" />
            </button>

            <button
              onClick={() => onNavigate('settings')}
              className={`p-2 rounded-md transition-colors ${currentView === 'settings' ? 'text-indigo-600 bg-indigo-50' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                }`}
              title="Settings"
            >
              <Settings className="w-5 h-5" />
            </button>

            <div className="h-6 w-px bg-gray-200 mx-1"></div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
