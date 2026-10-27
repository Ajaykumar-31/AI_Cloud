import React, { useState, useEffect } from 'react';
import { workloadService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { Search, Plus, Edit2, Trash2, X, FileText, Server, Activity, Database, Cloud } from 'lucide-react';

const Workloads = () => {
  const [workloads, setWorkloads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterPriority, setFilterPriority] = useState('ALL');
  const [modalOpen, setModalOpen] = useState(false);
  const [currentWorkload, setCurrentWorkload] = useState(null);
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/signin');
  };

  const emptyForm = {
    workload_name: '',
    application_type: '',
    department: '',
    priority: 'LOW',
    criticality: 'LOW',
    sensitivity: 'INTERNAL',
    status: 'pending'
  };

  const [formData, setFormData] = useState(emptyForm);

  const fetchWorkloads = async () => {
    try {
      const response = await workloadService.getWorkloads();
      setWorkloads(response.data.workloads || response.data || []);
    } catch (error) {
      console.error('Failed to fetch workloads', error);
      if (error.response && error.response.status === 401) {
        logout();
        navigate('/signin');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkloads();
  }, []);

  const handleOpenModal = (workload = null) => {
    if (workload) {
      setCurrentWorkload(workload);
      setFormData(workload);
    } else {
      setCurrentWorkload(null);
      setFormData(emptyForm);
    }
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setCurrentWorkload(null);
    setFormData(emptyForm);
  };

  const handleFormChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (currentWorkload) {
        await workloadService.updateWorkload(currentWorkload.id, formData);
      } else {
        await workloadService.createWorkload(formData);
      }
      fetchWorkloads();
      handleCloseModal();
    } catch (error) {
      console.error('Failed to save workload', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this workload?')) {
      try {
        await workloadService.deleteWorkload(id);
        fetchWorkloads();
      } catch (error) {
        console.error('Failed to delete workload', error);
      }
    }
  };

  const filteredWorkloads = workloads.filter(w => {
    const matchesSearch = w.workload_name.toLowerCase().includes(search.toLowerCase()) || 
                          w.department.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filterPriority === 'ALL' || w.priority === filterPriority;
    return matchesSearch && matchesFilter;
  });

  const getPriorityColor = (priority) => {
    switch(priority) {
      case 'CRITICAL': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'HIGH': return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
      case 'MEDIUM': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'LOW': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      default: return 'bg-slate-800 text-slate-400 border-slate-700';
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
              <Link to="/workloads" className="text-sm text-white font-medium relative after:absolute after:bottom-[-20px] after:left-0 after:w-full after:h-0.5 after:bg-indigo-400">Workloads</Link>
              <Link to="/alerts" className="text-sm text-slate-400 hover:text-white transition-colors duration-200">Alerts</Link>
              
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
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
            <div>
              <h1 className="text-3xl font-bold text-white tracking-tight flex items-center">
                  <Database className="text-indigo-500 mr-3" size={32} />
                  Workload Management
              </h1>
              <p className="text-slate-400 mt-2">Manage application deployments and metadata context.</p>
            </div>
            <button 
              onClick={() => handleOpenModal()}
              className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl shadow-lg shadow-indigo-900/20 flex items-center transition-colors font-medium border border-indigo-500/30"
            >
              <Plus size={18} className="mr-2" />
              Add Workload
            </button>
          </div>

          <div className="bg-slate-900/60 backdrop-blur-lg p-4 rounded-t-2xl border border-white/5 flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0 shadow-xl">
            <div className="relative w-full sm:w-80">
              <Search className="absolute left-3 top-2.5 text-slate-500" size={18} />
              <input 
                type="text" 
                placeholder="Search workloads by name or department..." 
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="pl-10 pr-4 py-2 w-full bg-slate-950/50 border border-slate-700/50 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-slate-200 placeholder-slate-500 transition-all"
              />
            </div>
            <div className="flex space-x-2 bg-slate-950/50 p-1 rounded-xl border border-slate-800">
              {['ALL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(p => (
                <button
                  key={p}
                  onClick={() => setFilterPriority(p)}
                  className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                    filterPriority === p 
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/20' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-slate-900/60 backdrop-blur-lg rounded-b-2xl border border-white/5 border-t-0 overflow-hidden shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-950/50 text-slate-400 text-xs uppercase tracking-widest border-b border-white/5">
                    <th className="px-6 py-5 font-semibold">Workload Identity</th>
                    <th className="px-6 py-5 font-semibold">Department</th>
                    <th className="px-6 py-5 font-semibold">Architecture</th>
                    <th className="px-6 py-5 font-semibold">Priority</th>
                    <th className="px-6 py-5 font-semibold">Sensitivity</th>
                    <th className="px-6 py-5 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {loading ? (
                    <tr><td colSpan="6" className="text-center py-12 text-slate-500 animate-pulse">Loading workloads...</td></tr>
                  ) : filteredWorkloads.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="text-center py-16 text-slate-500">
                        <FileText size={48} className="mx-auto text-slate-700 mb-4" />
                        <p>No workloads found matching criteria.</p>
                      </td>
                    </tr>
                  ) : (
                    filteredWorkloads.map(workload => (
                      <tr key={workload.id} className="hover:bg-slate-800/40 transition-colors duration-200 group">
                        <td className="px-6 py-4">
                          <div className="font-semibold text-white flex items-center">
                            <Cloud size={14} className="mr-2 text-indigo-400" />
                            {workload.workload_name}
                          </div>
                          <div className="text-xs text-slate-500 font-mono mt-1 pl-6">ID: {workload.id}</div>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-300">{workload.department}</td>
                        <td className="px-6 py-4 text-sm text-slate-300 font-medium">{workload.application_type}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold capitalize border ${getPriorityColor(workload.priority)}`}>
                            {workload.priority}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs font-mono text-slate-400">{workload.sensitivity}</td>
                        <td className="px-6 py-4 text-right space-x-3 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => handleOpenModal(workload)} className="text-slate-400 hover:text-indigo-400 transition-colors p-2 bg-slate-800 rounded-lg">
                            <Edit2 size={16} />
                          </button>
                          <button onClick={() => handleDelete(workload.id)} className="text-slate-400 hover:text-rose-400 transition-colors p-2 bg-slate-800 rounded-lg">
                            <Trash2 size={16} />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Modal */}
          {modalOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity" onClick={handleCloseModal}></div>
              <div className="relative bg-slate-900 border border-white/10 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] w-full max-w-2xl overflow-hidden animate-[scale-in_0.2s_ease-out]">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>
                <div className="p-6 border-b border-white/5 flex justify-between items-center bg-slate-900/50">
                  <h2 className="text-xl font-bold text-white flex items-center">
                    <Database className="mr-3 text-indigo-400" size={20} />
                    {currentWorkload ? 'Edit Workload' : 'Provision Workload'}
                  </h2>
                  <button onClick={handleCloseModal} className="text-slate-500 hover:text-white transition-colors">
                    <X size={20} />
                  </button>
                </div>
                
                <form onSubmit={handleSubmit} className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Workload Name</label>
                      <input type="text" name="workload_name" value={formData.workload_name} onChange={handleFormChange} required className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-white placeholder-slate-600" />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Architecture</label>
                      <input type="text" name="application_type" value={formData.application_type} onChange={handleFormChange} required className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-white placeholder-slate-600" placeholder="e.g. Web Server, DB" />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Department</label>
                      <input type="text" name="department" value={formData.department} onChange={handleFormChange} required className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-white placeholder-slate-600" />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Status</label>
                      <input type="text" name="status" value={formData.status} onChange={handleFormChange} required className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-white placeholder-slate-600" />
                    </div>
                    
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Priority</label>
                      <select name="priority" value={formData.priority} onChange={handleFormChange} className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-white">
                        <option value="LOW">LOW</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="HIGH">HIGH</option>
                        <option value="CRITICAL">CRITICAL</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Criticality</label>
                      <select name="criticality" value={formData.criticality} onChange={handleFormChange} className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-white">
                        <option value="LOW">LOW</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="HIGH">HIGH</option>
                        <option value="CRITICAL">CRITICAL</option>
                      </select>
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Sensitivity</label>
                      <select name="sensitivity" value={formData.sensitivity} onChange={handleFormChange} className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-white">
                        <option value="PUBLIC">PUBLIC</option>
                        <option value="INTERNAL">INTERNAL</option>
                        <option value="CONFIDENTIAL">CONFIDENTIAL</option>
                        <option value="RESTRICTED">RESTRICTED</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="flex justify-end space-x-3 pt-4 border-t border-white/5">
                    <button type="button" onClick={handleCloseModal} className="px-5 py-2.5 border border-slate-700 hover:bg-slate-800 rounded-xl text-slate-300 font-medium transition-colors">
                      Cancel
                    </button>
                    <button type="submit" className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-500 font-medium transition-colors shadow-lg shadow-indigo-900/20">
                      Save Workload
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
};

export default Workloads;
