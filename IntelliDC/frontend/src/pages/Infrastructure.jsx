import React, { useState, useEffect } from 'react';
import { serverService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { Activity, Server, AlertCircle, CheckCircle, Search, Plus, X, BarChart2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Infrastructure = () => {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [selectedServer, setSelectedServer] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/signin');
  };

  const fetchServers = async () => {
    try {
      const response = await serverService.getServers();
      setServers(response.data.servers || response.data || []);
    } catch (error) {
      console.error('Failed to fetch servers', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServers();
  }, []);

  const handleMockMetric = async (serverId) => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const mockData = {
        cpu_usage: Math.floor(Math.random() * 100),
        memory_usage: Math.floor(Math.random() * 100),
        storage_usage: Math.floor(Math.random() * 100),
      };
      await serverService.postServerMetrics(serverId, mockData);
      fetchServers(); // Refresh list to get new status/metrics
      if (selectedServer && selectedServer.id === serverId) {
        fetchMetrics(serverId); // Refresh chart if modal open
      }
    } catch (error) {
      console.error('Failed to insert mock metric', error);
    }
  };

  const handleAddServer = async () => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const mockServer = {
        server_name: `srv-${Math.floor(Math.random() * 1000)}`,
        hostname: `host-${Math.floor(Math.random() * 100)}.local`,
        ip_address: `192.168.1.${Math.floor(Math.random() * 255)}`,
        status: "healthy",
        cpu_usage: 0, memory_usage: 0, storage_usage: 0, network_usage: 0, uptime: 100
      };
      await serverService.createServer(mockServer);
      fetchServers();
    } catch (error) {
      console.error('Failed to add server', error);
    }
  };

  const fetchMetrics = async (serverId) => {
    try {
      const response = await serverService.getServerMetrics(serverId);
      const metricsList = response.data.metrics || response.data || [];
      const formattedData = metricsList.map(m => ({
        time: new Date(m.timestamp).toLocaleTimeString(),
        cpu: m.cpu_usage,
        ram: m.memory_usage
      }));
      setMetrics(formattedData);
    } catch (error) {
      console.error('Failed to fetch metrics', error);
    }
  };

  const openModal = (server) => {
    setSelectedServer(server);
    setMetrics([]);
    fetchMetrics(server.id);
    setModalOpen(true);
  };

  const filteredServers = servers.filter(s => {
    const matchesSearch = s.server_name.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter === 'all' || s.status === filter;
    return matchesSearch && matchesFilter;
  });

  const avgCpu = servers.length ? (servers.reduce((acc, s) => acc + s.cpu_usage, 0) / servers.length).toFixed(1) : 0;
  const avgRam = servers.length ? (servers.reduce((acc, s) => acc + s.memory_usage, 0) / servers.length).toFixed(1) : 0;
  const healthyCount = servers.filter(s => s.status === 'healthy').length;
  const warningCount = servers.filter(s => s.status === 'warning').length;
  const criticalCount = servers.filter(s => s.status === 'critical').length;

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
              <Link to="/infrastructure" className="text-sm text-white font-medium relative after:absolute after:bottom-[-20px] after:left-0 after:w-full after:h-0.5 after:bg-indigo-400">Infrastructure</Link>
              <Link to="/workloads" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">Workloads</Link>
              <Link to="/alerts" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">Alerts</Link>
              
              <div className="border-l border-slate-700 h-6 mx-2"></div>
              
              <span className="text-xs font-semibold bg-indigo-500/20 text-indigo-300 px-3 py-1 rounded-full border border-indigo-500/30 shadow-[0_0_10px_rgba(99,102,241,0.2)]">{user?.role}</span>
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
      
      <main className="flex-grow py-8 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-7xl mx-auto">
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-4xl font-bold text-white tracking-tight">Infrastructure Node Matrix</h1>
            <p className="text-slate-400 text-sm mt-2">Real-time telemetry and health metrics across the cluster.</p>
          </div>
          <button 
            onClick={handleAddServer}
            className="group relative inline-flex items-center justify-center px-6 py-2.5 font-medium text-white transition-all duration-200 bg-indigo-600 rounded-xl hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600 focus:ring-offset-slate-900 overflow-hidden"
          >
            <span className="absolute inset-0 w-full h-full -mt-1 rounded-lg opacity-30 bg-gradient-to-b from-transparent via-transparent to-black"></span>
            <span className="relative flex items-center">
              <Plus size={18} className="mr-2 group-hover:rotate-90 transition-transform duration-300" />
              Provision Node
            </span>
          </button>
        </div>

        {/* Dashboard Cards */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
          {[
            { label: 'Total Nodes', value: servers.length, icon: Server, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
            { label: 'Healthy', value: healthyCount, icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
            { label: 'Warning', value: warningCount, icon: AlertCircle, color: 'text-amber-400', bg: 'bg-amber-500/10' },
            { label: 'Critical', value: criticalCount, icon: Activity, color: 'text-rose-400', bg: 'bg-rose-500/10' },
            { label: 'Avg CPU', value: `${avgCpu}%`, icon: Activity, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
            { label: 'Avg RAM', value: `${avgRam}%`, icon: Activity, color: 'text-fuchsia-400', bg: 'bg-fuchsia-500/10' },
          ].map((stat, idx) => (
             <div key={idx} className="bg-slate-900/60 backdrop-blur-lg p-5 rounded-2xl border border-white/5 shadow-xl hover:border-white/10 hover:bg-slate-800/60 transition-all duration-300 col-span-2 md:col-span-1 group">
              <div className="flex justify-between items-start">
                <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider">{stat.label}</h3>
                <div className={`p-2 rounded-lg ${stat.bg} group-hover:scale-110 transition-transform duration-300`}>
                  <stat.icon className={stat.color} size={18} />
                </div>
              </div>
              <div className="mt-4 flex items-baseline">
                <span className="text-4xl font-black text-white tracking-tight">{stat.value}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Toolbar */}
        <div className="bg-slate-900/60 backdrop-blur-lg p-4 rounded-t-2xl border border-white/5 flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-2.5 text-slate-500" size={18} />
            <input 
              type="text" 
              placeholder="Search by hostname or IP..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2 w-full bg-slate-950/50 border border-slate-700/50 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-slate-200 placeholder-slate-500 transition-all"
            />
          </div>
          <div className="flex p-1 bg-slate-950/50 rounded-xl border border-slate-800/50">
            {['all', 'healthy', 'warning', 'critical'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-1.5 text-sm font-medium rounded-lg capitalize transition-all duration-200 ${
                  filter === f 
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/20' 
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="bg-slate-900/60 backdrop-blur-lg rounded-b-2xl border border-white/5 border-t-0 overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-950/50 text-slate-400 text-xs uppercase tracking-widest border-b border-white/5">
                  <th className="px-6 py-5 font-semibold">Node Identity</th>
                  <th className="px-6 py-5 font-semibold">Status</th>
                  <th className="px-6 py-5 font-semibold">CPU Load</th>
                  <th className="px-6 py-5 font-semibold">Memory</th>
                  <th className="px-6 py-5 font-semibold">Storage</th>
                  <th className="px-6 py-5 font-semibold">Risk Index</th>
                  <th className="px-6 py-5 font-semibold text-right">Operations</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {loading ? (
                  <tr><td colSpan="7" className="text-center py-12 text-slate-500 animate-pulse">Synchronizing telemetry...</td></tr>
                ) : filteredServers.length === 0 ? (
                  <tr><td colSpan="7" className="text-center py-12 text-slate-500">No nodes match your criteria.</td></tr>
                ) : (
                  filteredServers.map(server => {
                    const riskScore = ((server.cpu_usage * 1.5 + server.memory_usage * 1.2) / 2.7).toFixed(1);
                    return (
                      <tr key={server.id} className="hover:bg-slate-800/40 transition-colors duration-200 group">
                        <td className="px-6 py-4">
                          <div className="font-semibold text-white flex items-center">
                            <div className="w-2 h-2 rounded-full bg-indigo-500 mr-2 shadow-[0_0_8px_rgba(99,102,241,0.8)]"></div>
                            {server.server_name}
                          </div>
                          <div className="text-xs text-slate-500 font-mono mt-1 pl-4">{server.ip_address}</div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold capitalize border ${
                            server.status === 'healthy' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                            server.status === 'warning' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                            'bg-rose-500/10 text-rose-400 border-rose-500/20 animate-pulse'
                          }`}>
                            {server.status === 'healthy' && <CheckCircle size={12} className="mr-1" />}
                            {server.status === 'warning' && <AlertCircle size={12} className="mr-1" />}
                            {server.status === 'critical' && <Activity size={12} className="mr-1" />}
                            {server.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <span className="text-sm text-slate-300 w-10">{server.cpu_usage.toFixed(0)}%</span>
                            <div className="w-20 bg-slate-800 rounded-full h-1.5 ml-2 overflow-hidden">
                              <div className={`h-full rounded-full transition-all duration-1000 ${server.cpu_usage > 85 ? 'bg-rose-500' : 'bg-cyan-400'}`} style={{width: `${server.cpu_usage}%`}}></div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                           <div className="flex items-center">
                            <span className="text-sm text-slate-300 w-10">{server.memory_usage.toFixed(0)}%</span>
                            <div className="w-20 bg-slate-800 rounded-full h-1.5 ml-2 overflow-hidden">
                              <div className={`h-full rounded-full transition-all duration-1000 ${server.memory_usage > 85 ? 'bg-rose-500' : 'bg-fuchsia-400'}`} style={{width: `${server.memory_usage}%`}}></div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-400 font-mono">{server.storage_usage.toFixed(0)}%</td>
                        <td className="px-6 py-4">
                          <span className={`text-sm font-bold ${riskScore > 75 ? 'text-rose-500 drop-shadow-[0_0_5px_rgba(244,63,94,0.5)]' : riskScore > 50 ? 'text-amber-400' : 'text-emerald-400'}`}>
                            {riskScore}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right space-x-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                          <button onClick={() => handleMockMetric(server.id)} className="text-xs px-3 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20 hover:text-indigo-300 transition-colors">Inject Load</button>
                          <button onClick={() => openModal(server)} className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors border border-slate-700">Analyze</button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Modal */}
        {modalOpen && selectedServer && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity" onClick={() => setModalOpen(false)}></div>
            <div className="relative bg-slate-900 border border-white/10 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] w-full max-w-4xl overflow-hidden animate-[scale-in_0.2s_ease-out]">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>
              <div className="p-6 border-b border-white/5 flex justify-between items-center bg-slate-900/50">
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center">
                    <Server size={24} className="mr-3 text-indigo-400" />
                    {selectedServer.server_name}
                  </h2>
                  <p className="text-slate-400 text-sm mt-1 font-mono">{selectedServer.hostname} • {selectedServer.ip_address}</p>
                </div>
                <button onClick={() => setModalOpen(false)} className="p-2 rounded-xl bg-slate-800/50 text-slate-400 hover:text-white hover:bg-rose-500/20 hover:border-rose-500/30 border border-transparent transition-all">
                  <X size={20} />
                </button>
              </div>
              
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="font-semibold text-slate-200 flex items-center tracking-wide">
                    <Activity size={18} className="mr-2 text-indigo-400" /> TELEMETRY STREAM
                  </h3>
                  <button onClick={() => handleMockMetric(selectedServer.id)} className="text-sm bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 px-4 py-2 rounded-lg hover:bg-indigo-600/40 transition-all flex items-center">
                    <Activity size={14} className="mr-2" />
                    Trigger Stress Test
                  </button>
                </div>
                
                <div className="h-80 w-full bg-slate-950/50 rounded-xl p-4 border border-white/5 relative overflow-hidden">
                  <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20 mix-blend-overlay"></div>
                  {metrics.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={metrics}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                        <XAxis dataKey="time" tick={{fontSize: 12, fill: '#94a3b8'}} stroke="#475569" />
                        <YAxis tick={{fontSize: 12, fill: '#94a3b8'}} stroke="#475569" domain={[0, 100]} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', color: '#f1f5f9' }}
                          itemStyle={{ color: '#e2e8f0' }}
                        />
                        <Line type="monotone" dataKey="cpu" stroke="#22d3ee" strokeWidth={3} dot={{r: 4, fill: '#0f172a', strokeWidth: 2}} activeDot={{r: 6, fill: '#22d3ee'}} name="CPU %" />
                        <Line type="monotone" dataKey="ram" stroke="#e879f9" strokeWidth={3} dot={{r: 4, fill: '#0f172a', strokeWidth: 2}} activeDot={{r: 6, fill: '#e879f9'}} name="RAM %" />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-500 relative z-10">
                      <Activity size={48} className="mb-4 text-slate-700 animate-pulse" />
                      <p>Awaiting telemetry data stream...</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
      </main>
    </div>
  );
};

export default Infrastructure;
