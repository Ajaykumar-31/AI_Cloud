import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';

const AIConfiguration = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <nav className="bg-indigo-800 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex-shrink-0 font-bold text-xl">IntelliDC</div>
            <div className="flex items-center space-x-4">
              <Link to="/dashboard" className="text-sm hover:text-indigo-200">Overview</Link>
              <Link to="/ai-config" className="text-sm font-medium hover:text-indigo-200">AI Config</Link>
              <button onClick={() => {logout(); navigate('/signin')}} className="bg-indigo-600 px-3 py-1 rounded text-sm">Logout</button>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-grow py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">AI Decision Engine Configuration</h1>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <p className="text-gray-500">Configure weighting and scoring limits for AI recommendations here.</p>
        </div>
      </main>
    </div>
  );
};
export default AIConfiguration;
