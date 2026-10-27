import React, { useState, useEffect } from 'react';
import { reportService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { BarChart2, TrendingUp, Activity, Cpu, HardDrive, Network, Database } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Reports = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setError(null);
      const response = await reportService.getInfrastructureReport({ range: '30d' });
      setData(response.data);
    } catch (error) {
      console.error('Failed to fetch reports', error);
      if (error.response && error.response.status === 401) {
        logout();
        navigate('/signin');
      }
      if (error.response?.status === 404 || error.response?.status === 501) {
        setError('Reporting module is not yet implemented on the backend.');
      } else {
        setError('Failed to fetch report data.');
      }
    } finally {
      setLoading(false);
    }
  };

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
              <Link to="/infrastructure" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">Infrastructure</Link>
              <Link to="/alerts" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">Alerts</Link>
              <Link to="/reports" className="text-sm text-white font-medium relative after:absolute after:bottom-[-20px] after:left-0 after:w-full after:h-0.5 after:bg-indigo-400">Reports</Link>
              
              <div className="border-l border-slate-700 h-6 mx-2"></div>
              
              <span className="text-xs font-semibold bg-indigo-500/20 text-indigo-300 px-3 py-1 rounded-full border border-indigo-500/30 shadow-[0_0_10px_rgba(99,102,241,0.2)]">{user?.role || 'Admin'}</span>
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

      <main className="flex-grow py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full relative z-10">
        <div className="mb-8 flex items-center gap-3 border-b border-white/5 pb-4">
            <BarChart2 size={32} className="text-indigo-500 drop-shadow-md" />
            <div>
              <h1 className="text-3xl font-bold text-white tracking-tight">Analytics & Reports</h1>
              <p className="text-slate-400 text-sm mt-1">Aggregated telemetry insights over 30 days.</p>
            </div>
        </div>
        
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
          </div>
        ) : error ? (
           <div className="bg-slate-900/60 backdrop-blur-lg p-12 rounded-2xl border border-white/5 text-center shadow-xl">
            <BarChart2 size={48} className="mx-auto text-indigo-500/30 mb-4" />
            <h3 className="text-xl font-bold text-slate-300 mb-2">Integration Point</h3>
            <p className="text-slate-400">{error}</p>
          </div>
        ) : (
          <div className="bg-slate-900/60 backdrop-blur-lg p-8 rounded-2xl border border-white/5 shadow-2xl">
             <h2 className="text-lg font-semibold text-white mb-6 uppercase tracking-wider text-sm flex items-center">
                 <Activity size={16} className="text-indigo-400 mr-2" />
                 Infrastructure Averages (30 days)
             </h2>
             <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
                <div className="bg-slate-950/50 p-6 rounded-xl border border-indigo-500/20 hover:border-indigo-500/40 transition-colors group">
                    <p className="text-xs text-indigo-400 font-semibold uppercase tracking-widest flex items-center mb-2">
                        <Cpu size={14} className="mr-1" /> Avg CPU
                    </p>
                    <p className="text-3xl font-black text-white group-hover:scale-105 origin-left transition-transform">
                        {data?.overall_avg_cpu != null ? `${data.overall_avg_cpu.toFixed(1)}%` : '--'}
                    </p>
                </div>
                <div className="bg-slate-950/50 p-6 rounded-xl border border-fuchsia-500/20 hover:border-fuchsia-500/40 transition-colors group">
                    <p className="text-xs text-fuchsia-400 font-semibold uppercase tracking-widest flex items-center mb-2">
                        <Database size={14} className="mr-1" /> Avg RAM
                    </p>
                    <p className="text-3xl font-black text-white group-hover:scale-105 origin-left transition-transform">
                        {data?.overall_avg_ram != null ? `${data.overall_avg_ram.toFixed(1)}%` : '--'}
                    </p>
                </div>
                <div className="bg-slate-950/50 p-6 rounded-xl border border-emerald-500/20 hover:border-emerald-500/40 transition-colors group">
                    <p className="text-xs text-emerald-400 font-semibold uppercase tracking-widest flex items-center mb-2">
                        <HardDrive size={14} className="mr-1" /> Avg Storage
                    </p>
                    <p className="text-3xl font-black text-white group-hover:scale-105 origin-left transition-transform">
                        {data?.overall_avg_storage != null ? `${data.overall_avg_storage.toFixed(1)}%` : '--'}
                    </p>
                </div>
                <div className="bg-slate-950/50 p-6 rounded-xl border border-cyan-500/20 hover:border-cyan-500/40 transition-colors group">
                    <p className="text-xs text-cyan-400 font-semibold uppercase tracking-widest flex items-center mb-2">
                        <Network size={14} className="mr-1" /> Avg Network
                    </p>
                    <p className="text-3xl font-black text-white group-hover:scale-105 origin-left transition-transform">
                        {data?.overall_avg_network != null ? `${data.overall_avg_network.toFixed(1)}%` : '--'}
                    </p>
                </div>
             </div>
             
             <h2 className="text-lg font-semibold text-white mb-6 uppercase tracking-wider text-sm flex items-center">
                 <TrendingUp size={16} className="text-indigo-400 mr-2" />
                 CPU Trend
             </h2>
             {data?.cpu_trend?.length > 0 ? (
                <div className="h-80 w-full bg-slate-950/50 border border-white/5 rounded-xl p-4">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data.cpu_trend}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} domain={[0, 100]} />
                            <Tooltip 
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#f1f5f9' }}
                                itemStyle={{ color: '#818cf8' }}
                            />
                            <Line type="monotone" dataKey="value" stroke="#818cf8" strokeWidth={3} dot={{r: 4, fill: '#0f172a', strokeWidth: 2}} activeDot={{r: 6, fill: '#818cf8'}} name="CPU %" />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
             ) : (
                <div className="h-40 w-full bg-slate-950/50 border border-white/5 rounded-xl flex items-center justify-center text-slate-500">
                    No historical trend data available yet.
                </div>
             )}
          </div>
        )}
      </main>
    </div>
  );
};

export default Reports;
