import React, { useState, useEffect } from 'react';
import { aiService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle, BrainCircuit, Activity, CheckCircle, Shield, ArrowRight, Server } from 'lucide-react';

const AIRecommendations = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchRecommendations();
    const intervalId = setInterval(fetchRecommendations, 60000); // 1 minute refresh
    return () => clearInterval(intervalId);
  }, []);

  const fetchRecommendations = async () => {
    try {
      const response = await aiService.getRecommendations();
      setRecommendations(response.data.recommendations || response.data || []);
    } catch (error) {
      console.error('Failed to fetch recommendations', error);
      if (error.response && error.response.status === 401) {
        logout();
        navigate('/signin');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (id, status) => {
    try {
      await aiService.updateRecommendationStatus(id, status);
      fetchRecommendations();
    } catch (error) {
      console.error('Failed to update recommendation status', error);
    }
  };

  const activeRecs = recommendations.filter(r => ['NEW', 'REVIEWED'].includes(r.status));
  const otherRecs = recommendations.filter(r => !['NEW', 'REVIEWED'].includes(r.status));

  const getPriorityColor = (severity) => {
    if (severity === 'CRITICAL') return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
    if (severity === 'HIGH') return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
    if (severity === 'MEDIUM') return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20';
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
              <Link to="/ai-recommendations" className="text-sm text-white font-medium relative after:absolute after:bottom-[-20px] after:left-0 after:w-full after:h-0.5 after:bg-indigo-400">AI Recommendations</Link>
              <Link to="/alerts" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">Alerts</Link>
              
              <div className="border-l border-slate-700 h-6 mx-2"></div>
              
              <span className="text-xs font-semibold bg-indigo-500/20 text-indigo-300 px-3 py-1 rounded-full border border-indigo-500/30 shadow-[0_0_10px_rgba(99,102,241,0.2)]">{user?.role || 'Admin'}</span>
              <button 
                onClick={() => {logout(); navigate('/signin')}}
                className="bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 px-4 py-2 rounded-lg text-sm transition-all duration-200"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-grow relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight flex items-center">
                <BrainCircuit className="text-indigo-500 mr-3" size={32} />
                Explainable AI Engine
            </h1>
            <p className="text-slate-400 mt-2">Transparent, evidence-based mitigation strategies.</p>
          </div>
          <button onClick={fetchRecommendations} className="px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 rounded-lg text-sm font-medium transition-colors shadow-sm">
            Refresh Engine
          </button>
        </div>
        
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
          </div>
        ) : recommendations.length === 0 ? (
          <div className="bg-slate-900/60 backdrop-blur-lg p-12 rounded-2xl border border-white/5 text-center shadow-xl">
            <Shield size={48} className="mx-auto text-emerald-500/50 mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">No Active Recommendations</h3>
            <p className="text-slate-400">The AI Engine indicates your cluster is operating optimally.</p>
          </div>
        ) : (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-white mb-4 border-b border-white/10 pb-2">Active Recommendations ({activeRecs.length})</h2>
            {activeRecs.length === 0 && <p className="text-slate-500 italic">No pending recommendations.</p>}
            
            {activeRecs.map(rec => (
              <div key={rec.id} className="bg-slate-900/60 backdrop-blur-lg rounded-2xl border border-white/5 shadow-xl overflow-hidden group">
                <div className="p-6">
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold border uppercase ${getPriorityColor(rec.severity)}`}>
                          {rec.severity}
                        </span>
                        <span className="text-slate-400 text-sm font-mono flex items-center">
                            <Server size={14} className="mr-1" /> {rec.server_name}
                        </span>
                        {rec.topsis_rank && (
                           <span className="text-xs text-fuchsia-400 bg-fuchsia-500/10 px-2 py-1 rounded border border-fuchsia-500/20 font-bold">
                             TOPSIS Rank #{rec.topsis_rank}
                           </span>
                        )}
                      </div>
                      <h3 className="text-2xl font-bold text-white">{rec.summary}</h3>
                      <p className="text-slate-400 mt-2 text-sm">{rec.explanation}</p>
                    </div>
                    <div className="flex items-center gap-2 bg-slate-950/50 p-3 rounded-xl border border-slate-800">
                      <div className="text-right mr-3">
                        <p className="text-xs text-slate-500 uppercase tracking-widest font-semibold">Risk Score</p>
                        <p className="text-2xl font-black text-white">{rec.risk_score?.toFixed(1) || '0.0'}</p>
                      </div>
                      <Activity className={rec.risk_score > 75 ? "text-rose-500" : "text-amber-500"} size={32} />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                    <div className="bg-indigo-950/30 p-4 rounded-xl border border-indigo-500/20 border-l-4 border-l-indigo-500">
                      <h4 className="text-xs uppercase tracking-widest text-indigo-400 font-semibold mb-2 flex items-center">
                        <ArrowRight size={14} className="mr-1" /> Suggested Action
                      </h4>
                      <p className="text-sm text-indigo-100 leading-relaxed font-medium">{rec.suggested_action}</p>
                    </div>
                    <div className="bg-emerald-950/30 p-4 rounded-xl border border-emerald-500/20 border-l-4 border-l-emerald-500">
                      <h4 className="text-xs uppercase tracking-widest text-emerald-400 font-semibold mb-2 flex items-center">
                         <CheckCircle size={14} className="mr-1" /> Expected Outcome
                      </h4>
                      <p className="text-sm text-emerald-100 leading-relaxed font-medium">{rec.expected_outcome}</p>
                    </div>
                  </div>

                  <div className="mt-6 flex flex-col md:flex-row justify-between items-center border-t border-white/5 pt-4">
                     <div className="text-xs text-slate-500">
                        Generated {new Date(rec.created_at).toLocaleString()} • Confidence: {(rec.confidence * 100).toFixed(0)}% • Data: {rec.data_freshness}
                     </div>
                     <div className="flex space-x-3 mt-4 md:mt-0">
                        {rec.status === 'NEW' && (
                            <button onClick={() => handleStatusChange(rec.id, 'REVIEWED')} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-lg transition-colors border border-slate-600">
                                Mark Reviewed
                            </button>
                        )}
                        <button onClick={() => handleStatusChange(rec.id, 'DISMISSED')} className="px-4 py-2 bg-slate-800 hover:bg-rose-500/20 text-slate-200 hover:text-rose-400 text-sm font-semibold rounded-lg transition-colors border border-slate-600 hover:border-rose-500/30">
                            Dismiss
                        </button>
                        <button onClick={() => handleStatusChange(rec.id, 'ACCEPTED')} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg transition-colors shadow-lg shadow-indigo-900/20">
                            Accept & Proceed
                        </button>
                     </div>
                  </div>
                </div>
              </div>
            ))}

            {otherRecs.length > 0 && (
                <>
                <h2 className="text-lg font-semibold text-slate-500 mt-12 mb-4 border-b border-slate-800 pb-2">History & Processed ({otherRecs.length})</h2>
                <div className="space-y-4">
                    {otherRecs.slice(0, 5).map(rec => (
                        <div key={rec.id} className="bg-slate-900/30 rounded-xl border border-white/5 p-4 flex justify-between items-center opacity-70 hover:opacity-100 transition-opacity">
                            <div>
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase mr-3 ${getPriorityColor(rec.severity)}`}>{rec.status}</span>
                                <span className="font-semibold text-slate-300">{rec.summary}</span>
                                <span className="text-slate-500 text-xs ml-3">{rec.server_name}</span>
                            </div>
                            {rec.status === 'ACCEPTED' && (
                                <button onClick={() => handleStatusChange(rec.id, 'RESOLVED')} className="text-xs bg-emerald-500/20 text-emerald-400 px-3 py-1.5 rounded hover:bg-emerald-500/30 transition-colors border border-emerald-500/30">
                                    Mark Resolved
                                </button>
                            )}
                        </div>
                    ))}
                </div>
                </>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default AIRecommendations;
