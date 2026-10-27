import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import SignIn from './pages/SignIn';
import Dashboard from './pages/Dashboard';
import Infrastructure from './pages/Infrastructure';
import Workloads from './pages/Workloads';
import Alerts from './pages/Alerts';
import AIRecommendations from './pages/AIRecommendations';
import Reports from './pages/Reports';
import IoTDevices from './pages/IoTDevices';
import IoTMonitoring from './pages/IoTMonitoring';
import Settings from './pages/Settings';
import AIConfiguration from './pages/AIConfiguration';
import './index.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Route */}
          <Route path="/signin" element={<SignIn />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/infrastructure" element={<Infrastructure />} />
            <Route path="/workloads" element={<Workloads />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/ai-recommendations" element={<AIRecommendations />} />
            <Route path="/ai-config" element={<AIConfiguration />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/iot-devices" element={<IoTDevices />} />
            <Route path="/iot-monitoring" element={<IoTMonitoring />} />
            <Route path="/settings" element={<Settings />} />
            {/* Add more protected routes here */}
          </Route>

          {/* Redirect root to dashboard (or signin if not authenticated) */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* Catch all */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
