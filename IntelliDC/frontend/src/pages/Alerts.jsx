import React, { useState, useEffect } from 'react';
import { alertService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle, Search, Filter, ShieldAlert, Shield, Activity, Server, Clock } from 'lucide-react';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('NEW'); // NEW, ACKNOWLEDGED, RESOLVED, DISMISSED
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/signin');
  };

  const fetchAlerts = async () => {
    try {
      const response = await alertService.getAlerts();
      setAlerts(response.data.alerts || response.data || []);
    } catch (error) {
      console.error('Failed to fetch alerts', error);
      if (error.response && error.response.status === 401) {
        logout();
        navigate('/signin');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const intervalId = setInterval(fetchAlerts, 30000);
    return () => clearInterval(intervalId);
  }, []);

  const handleAcknowledge = async (id) => {
    try {
      await alertService.acknowledgeAlert(id);
      fetchAlerts();
    } catch (error) {
      console.error('Failed to acknowledge alert', error);
    }
  };

  const handleResolve = async (id) => {
    try {
      await alertService.resolveAlert(id);
      fetchAlerts();
    } catch (error) {
      console.error('Failed to resolve alert', error);
    }
  };

  const handleDismiss = async (id) => {
    try {
      await alertService.dismissAlert(id);
      fetchAlerts();
    } catch (error) {
      console.error('Failed to dismiss alert', error);
    }
  };

  const filteredAlerts = alerts.filter(a => {
    const statusMatch = filterStatus === 'ALL' || a.status === filterStatus;
    const severityMatch = filterSeverity === 'ALL' || a.severity === filterSeverity;
    return statusMatch && severityMatch;
  });

  const getSeverityStyles = (severity) => {
    switch(severity) {
      case 'CRITICAL': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'HIGH': return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
      case 'MEDIUM': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      default: return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
    }
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
              <Link to="/alerts" className="text-sm text-white font-medium relative after:absolute after:bottom-[-20px] after:left-0 after:w-full after:h-0.5 after:bg-indigo-400">Alerts</Link>
              <Link to="/reports" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">Reports</Link>
              
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
      
      <main className="flex-grow py-8 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white tracking-tight flex items-center">
                  <ShieldAlert className="text-rose-500 mr-3" size={32} />
                  Alert Engine
              </h1>
              <p className="text-slate-400 mt-2">Deduplicated, AI-prioritized incident notifications.</p>
            </div>
            <button onClick={fetchAlerts} className="px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 rounded-lg text-sm font-medium transition-colors shadow-sm">
                Sync Alerts
            </button>
          </div>

          <div className="bg-slate-900/60 backdrop-blur-lg p-4 rounded-t-2xl border border-white/5 flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0 shadow-xl border-b-0">
            <div className="flex space-x-2 bg-slate-950/50 p-1 rounded-xl border border-slate-800">
               {['NEW', 'ACKNOWLEDGED', 'RESOLVED', 'DISMISSED', 'ALL'].map(s => (
                <button
                    key={s}
                    onClick={() => setFilterStatus(s)}
                    className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-all duration-200 capitalize ${
                    filterStatus === s 
                        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/20' 
                        : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                    }`}
                >
                    {s.toLowerCase()}
                </button>
               ))}
            </div>
            <div className="flex space-x-2 items-center bg-slate-950/50 p-1 rounded-xl border border-slate-800">
              <Filter size={16} className="text-slate-400 mx-2" />
              {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].map(p => (
                <button
                  key={p}
                  onClick={() => setFilterSeverity(p)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                    filterSeverity === p 
                      ? 'bg-slate-700 text-white' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-slate-900/60 backdrop-blur-lg rounded-b-2xl border border-white/5 shadow-2xl p-6 min-h-[500px]">
             {loading ? (
                <div className="flex justify-center items-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
                </div>
              ) : filteredAlerts.length === 0 ? (
                <div className="text-center py-24 text-slate-500">
                  <Shield size={64} className="mx-auto text-emerald-500/30 mb-6" />
                  <h3 className="text-xl font-bold text-slate-300 mb-2">No {filterStatus !== 'ALL' ? filterStatus.toLowerCase() : ''} alerts found</h3>
                  <p>System operating normally.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredAlerts.map(alert => (
                    <div key={alert.id} className={`border rounded-xl p-5 flex flex-col md:flex-row gap-5 hover:bg-slate-800/40 transition-colors shadow-lg ${getSeverityStyles(alert.severity)}`}>
                      <div className="flex-shrink-0 mt-1 bg-slate-950/50 p-3 rounded-xl border border-inherit">
                        <AlertCircle size={28} className="drop-shadow-lg" />
                      </div>
                      <div className="flex-grow">
                        <div className="flex items-center justify-between mb-1">
                          <h3 className="text-xl font-bold text-slate-100">{alert.title}</h3>
                          <span className="text-xs font-mono opacity-60">
                            {new Date(alert.updated_at || alert.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm mt-1 opacity-90 font-medium">{alert.description}</p>
                        
                        <div className="mt-4 flex flex-wrap gap-3 text-xs font-medium opacity-80">
                          <div className="flex items-center gap-1.5 bg-slate-950/40 px-3 py-1.5 rounded-lg border border-inherit">
                            <Server size={14} /> Affected Node: <span className="font-mono ml-1">{alert.server_id}</span>
                          </div>
                          {alert.observed_values && Object.keys(alert.observed_values).length > 0 && (
                            <div className="flex items-center gap-1.5 bg-slate-950/40 px-3 py-1.5 rounded-lg border border-inherit">
                                <Activity size={14} /> Values: {JSON.stringify(alert.observed_values)}
                            </div>
                          )}
                          <div className="flex items-center gap-1.5 bg-slate-950/40 px-3 py-1.5 rounded-lg border border-inherit">
                            Priority Score: {alert.priority}
                          </div>
                        </div>
                      </div>
                      <div className="flex-shrink-0 flex flex-row md:flex-col justify-end md:justify-center gap-2 mt-4 md:mt-0">
                         {alert.status === 'NEW' && (
                           <button onClick={() => handleAcknowledge(alert.id)} className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 text-xs font-semibold py-2.5 px-4 rounded-lg transition-colors">
                             Acknowledge
                           </button>
                         )}
                         {(alert.status === 'NEW' || alert.status === 'ACKNOWLEDGED') && (
                           <button onClick={() => handleResolve(alert.id)} className="bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400 border border-emerald-500/30 text-xs font-semibold py-2.5 px-4 rounded-lg transition-colors shadow-sm">
                             Resolve
                           </button>
                         )}
                         {(alert.status === 'NEW' || alert.status === 'ACKNOWLEDGED') && (
                           <button onClick={() => handleDismiss(alert.id)} className="bg-slate-800/50 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-transparent hover:border-rose-500/30 text-xs font-semibold py-2.5 px-4 rounded-lg transition-colors">
                             Dismiss
                           </button>
                         )}
                         {alert.status === 'RESOLVED' && (
                           <span className="flex items-center text-sm font-bold text-emerald-500 bg-emerald-500/10 px-4 py-2 rounded-lg border border-emerald-500/20">
                             <CheckCircle size={16} className="mr-2" /> Resolved
                           </span>
                         )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Alerts;
