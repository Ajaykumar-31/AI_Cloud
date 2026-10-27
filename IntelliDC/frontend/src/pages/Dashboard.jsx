import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { serverService, iotService, alertService, aiService } from '../services/api';
import { Server, Activity, AlertTriangle, Cpu, Droplets, Zap, ShieldAlert, Cpu as CpuIcon } from 'lucide-react';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [data, setData] = useState({
    servers: [],
    devices: [],
    alerts: [],
    recommendations: [],
    latestReading: null,
  });
  const [loading, setLoading] = useState(true);

  const handleLogout = () => {
    logout();
    navigate('/signin');
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [serversRes, devicesRes, alertsRes, recsRes] = await Promise.all([
        serverService.getServers().catch(() => ({ data: [] })),
        iotService.getDevices().catch(() => ({ data: [] })),
        alertService.getAlerts().catch(() => ({ data: [] })),
        aiService.getRecommendations().catch(() => ({ data: [] })),
      ]);

      const servers = serversRes.data.servers || serversRes.data || [];
      const devices = devicesRes.data.devices || devicesRes.data || [];
      const alerts = alertsRes.data.alerts || alertsRes.data || [];
      const recommendations = recsRes.data.recommendations || recsRes.data || [];

      let latestReading = null;
      if (devices.length > 0) {
        // Fetch reading for first device
        try {
          const readingRes = await iotService.getLatestThingSpeak(devices[0].device_id);
          latestReading = readingRes.data;
        } catch (e) {
          console.error("No IoT reading available", e);
        }
      }

      setData({
        servers,
        devices,
        alerts,
        recommendations,
        latestReading,
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const onlineServers = data.servers.filter(s => s.status !== 'critical').length;
  const criticalAlerts = data.alerts.filter(a => a.severity === 'CRITICAL' && a.status === 'NEW').length;
  const highRiskServers = data.servers.filter(s => s.status === 'critical').length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex flex-col font-sans selection:bg-indigo-500/30">
      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5 pointer-events-none"></div>
      <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-indigo-900/20 to-transparent pointer-events-none"></div>

      <nav className="relative z-10 bg-slate-900/50 backdrop-blur-md border-b border-white/10 sticky top-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex-shrink-0 font-extrabold text-2xl bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400 tracking-tight">
              IntelliDC
            </div>
            <div className="flex items-center space-x-6">
              <Link to="/dashboard" className="text-sm text-white font-medium relative after:absolute after:bottom-[-20px] after:left-0 after:w-full after:h-0.5 after:bg-indigo-400">Overview</Link>
              <Link to="/infrastructure" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">Infrastructure</Link>
              <Link to="/workloads" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">Workloads</Link>
              <Link to="/alerts" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">Alerts</Link>
              <Link to="/iot-monitoring" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">IoT</Link>
              <Link to="/ai-recommendations" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">AI</Link>
              
              <div className="border-l border-slate-700 h-6 mx-2"></div>
              
              <span className="text-xs font-semibold bg-indigo-500/20 text-indigo-300 px-3 py-1 rounded-full border border-indigo-500/30 shadow-[0_0_10px_rgba(99,102,241,0.2)]">{user?.role}</span>
              <button onClick={handleLogout} className="bg-slate-800 hover:bg-slate-700 border border-slate-700 px-4 py-2 rounded-lg text-sm transition-all duration-200">Logout</button>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-grow relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <div className="bg-slate-900/60 backdrop-blur-lg p-8 rounded-2xl border border-white/5 shadow-2xl mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-3xl font-bold text-white tracking-tight">Command Center</h2>
            <button onClick={fetchDashboardData} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm transition-colors">
              Refresh Data
            </button>
          </div>
          <p className="text-slate-400 max-w-3xl mb-8">
            Real-time telemetry, AI-driven workload orchestration, and global infrastructure health monitoring.
          </p>
          
          {loading ? (
             <div className="text-center py-10 animate-pulse text-slate-400">Loading infrastructure data...</div>
          ) : (
            <>
              {/* Top KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-slate-950/50 border border-indigo-500/20 p-5 rounded-xl hover:bg-indigo-500/10 transition-all duration-300">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-indigo-400 uppercase tracking-widest text-xs">Total Servers</h3>
                    <Server size={18} className="text-indigo-400" />
                  </div>
                  <p className="text-white text-3xl font-black">{data.servers.length}</p>
                  <p className="text-xs text-slate-500 mt-2">{onlineServers} online</p>
                </div>

                <div className="bg-slate-950/50 border border-emerald-500/20 p-5 rounded-xl hover:bg-emerald-500/10 transition-all duration-300">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-emerald-400 uppercase tracking-widest text-xs">IoT Devices</h3>
                    <Activity size={18} className="text-emerald-400" />
                  </div>
                  <p className="text-white text-3xl font-black">{data.devices.length}</p>
                  <p className="text-xs text-slate-500 mt-2">Active connections</p>
                </div>

                <div className="bg-slate-950/50 border border-rose-500/20 p-5 rounded-xl hover:bg-rose-500/10 transition-all duration-300">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-rose-400 uppercase tracking-widest text-xs">Critical Alerts</h3>
                    <ShieldAlert size={18} className="text-rose-400" />
                  </div>
                  <p className="text-white text-3xl font-black">{criticalAlerts}</p>
                  <p className="text-xs text-slate-500 mt-2">Requires immediate attention</p>
                </div>

                <div className="bg-slate-950/50 border border-amber-500/20 p-5 rounded-xl hover:bg-amber-500/10 transition-all duration-300">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-amber-400 uppercase tracking-widest text-xs">High Risk Nodes</h3>
                    <AlertTriangle size={18} className="text-amber-400" />
                  </div>
                  <p className="text-white text-3xl font-black">{highRiskServers}</p>
                  <p className="text-xs text-slate-500 mt-2">Based on AI scoring</p>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Environmental IoT Status */}
                <div className="bg-slate-950/50 border border-white/5 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Latest Environmental Telemetry</h3>
                  {data.latestReading ? (
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-slate-900 p-4 rounded-lg border border-white/5">
                        <div className="flex items-center mb-2"><Activity size={16} className="text-rose-400 mr-2"/> <span className="text-xs text-slate-400 uppercase">Temperature</span></div>
                        <div className="text-2xl font-bold text-white">{data.latestReading.temperature}°C</div>
                      </div>
                      <div className="bg-slate-900 p-4 rounded-lg border border-white/5">
                        <div className="flex items-center mb-2"><Droplets size={16} className="text-cyan-400 mr-2"/> <span className="text-xs text-slate-400 uppercase">Humidity</span></div>
                        <div className="text-2xl font-bold text-white">{data.latestReading.humidity}%</div>
                      </div>
                      <div className="bg-slate-900 p-4 rounded-lg border border-white/5">
                        <div className="flex items-center mb-2"><Zap size={16} className="text-amber-400 mr-2"/> <span className="text-xs text-slate-400 uppercase">Power</span></div>
                        <div className="text-2xl font-bold text-white">{data.latestReading.power} W</div>
                      </div>
                      <div className="bg-slate-900 p-4 rounded-lg border border-white/5">
                        <div className="flex items-center mb-2"><Activity size={16} className="text-emerald-400 mr-2"/> <span className="text-xs text-slate-400 uppercase">Current</span></div>
                        <div className="text-2xl font-bold text-white">{data.latestReading.current} A</div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-slate-500 py-8 text-center bg-slate-900 rounded-lg">No telemetry data available</div>
                  )}
                </div>

                {/* AI Recommendations */}
                <div className="bg-slate-950/50 border border-white/5 rounded-xl p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-white">Recent AI Recommendations</h3>
                    <Link to="/ai-recommendations" className="text-xs text-indigo-400 hover:text-indigo-300">View All</Link>
                  </div>
                  <div className="space-y-3">
                    {data.recommendations.filter(r => r.status === 'NEW').slice(0, 3).length > 0 ? (
                      data.recommendations.filter(r => r.status === 'NEW').slice(0, 3).map((rec, i) => (
                        <div key={i} className="bg-slate-900 p-3 rounded-lg border border-indigo-500/20 border-l-4 border-l-indigo-500">
                          <div className="flex justify-between">
                            <h4 className="font-semibold text-sm text-indigo-100">{rec.summary}</h4>
                            <span className="text-xs text-indigo-400">{rec.priority}</span>
                          </div>
                          <p className="text-xs text-slate-400 mt-1 truncate">{rec.suggested_action}</p>
                        </div>
                      ))
                    ) : (
                      <div className="text-slate-500 py-8 text-center bg-slate-900 rounded-lg">No pending recommendations</div>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
