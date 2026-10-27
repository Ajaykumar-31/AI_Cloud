import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { iotService } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const IoTMonitoring = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [data, setData] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const deviceId = 'esp32_001';

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [latestRes, histRes] = await Promise.all([
        iotService.getLatestThingSpeak(deviceId),
        iotService.getDeviceHistoricalReadings(deviceId, { limit: 50 })
      ]);
      setData(latestRes.data);
      
      // Sort historical data oldest to newest for Recharts
      const sortedHist = (histRes.data || []).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
      
      // Format timestamps for display
      const formattedHist = sortedHist.map(item => ({
        ...item,
        timeLabel: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }));
      setHistoricalData(formattedHist);
      setLastRefreshed(new Date());
    } catch (err) {
      console.error("Error fetching IoT data:", err);
      if (err.response && err.response.status === 401) {
        logout();
        navigate('/signin');
      } else {
        setError(err.message || 'Failed to fetch IoT data');
      }
    } finally {
      setLoading(false);
    }
  }, [deviceId, logout, navigate]);

  useEffect(() => {
    fetchData();
    const intervalId = setInterval(fetchData, 30000);
    return () => clearInterval(intervalId);
  }, [fetchData]);

  const handleLogout = () => {
    logout();
    navigate('/signin');
  };

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
              <Link to="/dashboard" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">Overview</Link>
              <Link to="/iot-monitoring" className="text-sm text-white font-medium relative after:absolute after:bottom-[-20px] after:left-0 after:w-full after:h-0.5 after:bg-indigo-400">IoT Monitoring</Link>
              
              <div className="border-l border-slate-700 h-6 mx-2"></div>
              
              <span className="text-xs font-semibold bg-indigo-500/20 text-indigo-300 px-3 py-1 rounded-full border border-indigo-500/30 shadow-[0_0_10px_rgba(99,102,241,0.2)]">{user?.role || 'Admin'}</span>
              <span className="text-sm hidden sm:block font-medium">{user?.name}</span>
              <button 
                onClick={handleLogout}
                className="bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 px-4 py-2 rounded-lg text-sm transition-all duration-200"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-grow relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <div className="flex justify-between items-center mb-6">
            <div>
                <h2 className="text-3xl font-bold text-white tracking-tight">IoT Sensor Monitoring</h2>
                <p className="text-slate-400 mt-1">Real-time telemetry for <span className="text-indigo-400 font-mono">{deviceId}</span></p>
            </div>
            <button 
                onClick={fetchData} 
                disabled={loading}
                className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 shadow-[0_0_15px_rgba(79,70,229,0.3)]"
            >
                <span>{loading ? 'Refreshing...' : 'Manual Refresh'}</span>
            </button>
        </div>

        {error && (
            <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 px-4 py-3 rounded-lg mb-6">
                <p><strong>Error:</strong> {error}</p>
            </div>
        )}

        <div className="bg-slate-900/60 backdrop-blur-lg p-8 rounded-2xl border border-white/5 shadow-2xl">
            {loading && !data ? (
                <div className="flex justify-center items-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
                </div>
            ) : data ? (
                <>
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-end mb-8 border-b border-white/10 pb-4">
                        <div className="space-y-1">
                            <p className="text-sm text-slate-400">Device ID: <span className="text-slate-200 font-mono">{data.device_id}</span></p>
                            <p className="text-sm text-slate-400">Entry ID: <span className="text-slate-200 font-mono">{data.thingspeak_entry_id}</span></p>
                        </div>
                        <div className="mt-4 sm:mt-0 text-right">
                            <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Latest Timestamp</p>
                            <p className="text-slate-300">{new Date(data.timestamp).toLocaleString()}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* Temperature Card */}
                        <div className="bg-slate-950/50 border border-orange-500/20 p-6 rounded-xl hover:bg-orange-500/10 hover:border-orange-500/40 transition-all duration-300 group">
                            <div className="flex justify-between items-start mb-4">
                                <h3 className="font-semibold text-orange-400 uppercase tracking-widest text-xs">Temperature</h3>
                            </div>
                            <div className="flex items-baseline space-x-2">
                                <p className="text-white text-4xl font-black group-hover:scale-105 origin-left transition-transform duration-300">{data.temperature ?? '--'}</p>
                                <span className="text-slate-400 font-medium">°C</span>
                            </div>
                        </div>

                        {/* Humidity Card */}
                        <div className="bg-slate-950/50 border border-cyan-500/20 p-6 rounded-xl hover:bg-cyan-500/10 hover:border-cyan-500/40 transition-all duration-300 group">
                            <div className="flex justify-between items-start mb-4">
                                <h3 className="font-semibold text-cyan-400 uppercase tracking-widest text-xs">Humidity</h3>
                            </div>
                            <div className="flex items-baseline space-x-2">
                                <p className="text-white text-4xl font-black group-hover:scale-105 origin-left transition-transform duration-300">{data.humidity ?? '--'}</p>
                                <span className="text-slate-400 font-medium">%</span>
                            </div>
                        </div>

                        {/* Current Card */}
                        <div className="bg-slate-950/50 border border-yellow-500/20 p-6 rounded-xl hover:bg-yellow-500/10 hover:border-yellow-500/40 transition-all duration-300 group">
                            <div className="flex justify-between items-start mb-4">
                                <h3 className="font-semibold text-yellow-400 uppercase tracking-widest text-xs">Current</h3>
                            </div>
                            <div className="flex items-baseline space-x-2">
                                <p className="text-white text-4xl font-black group-hover:scale-105 origin-left transition-transform duration-300">{data.current ?? '--'}</p>
                                <span className="text-slate-400 font-medium">A</span>
                            </div>
                        </div>

                        {/* Power Card */}
                        <div className="bg-slate-950/50 border border-emerald-500/20 p-6 rounded-xl hover:bg-emerald-500/10 hover:border-emerald-500/40 transition-all duration-300 group">
                            <div className="flex justify-between items-start mb-4">
                                <h3 className="font-semibold text-emerald-400 uppercase tracking-widest text-xs">Power</h3>
                            </div>
                            <div className="flex items-baseline space-x-2">
                                <p className="text-white text-4xl font-black group-hover:scale-105 origin-left transition-transform duration-300">{data.power ?? '--'}</p>
                                <span className="text-slate-400 font-medium">W</span>
                            </div>
                        </div>
                    </div>
                    
                    {historicalData.length > 0 && (
                        <div className="mt-8 bg-slate-950/50 border border-white/10 p-6 rounded-xl">
                            <h3 className="text-lg font-semibold text-white mb-6">Historical Telemetry</h3>
                            <div className="h-80 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={historicalData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                        <XAxis dataKey="timeLabel" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                                        <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                                        <Tooltip 
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }}
                                            itemStyle={{ color: '#e2e8f0' }}
                                        />
                                        <Legend wrapperStyle={{ paddingTop: '20px' }} />
                                        <Line type="monotone" dataKey="temperature" name="Temp (°C)" stroke="#f97316" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
                                        <Line type="monotone" dataKey="humidity" name="Humidity (%)" stroke="#06b6d4" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
                                        <Line type="monotone" dataKey="current" name="Current (A)" stroke="#eab308" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
                                        <Line type="monotone" dataKey="power" name="Power (W)" stroke="#10b981" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}
                </>
            ) : (
                <div className="text-center py-10">
                    <p className="text-slate-400">No data available.</p>
                </div>
            )}
        </div>
      </main>
    </div>
  );
};

export default IoTMonitoring;
