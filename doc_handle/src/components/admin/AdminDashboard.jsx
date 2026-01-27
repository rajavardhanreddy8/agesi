import React, { useState, useEffect } from 'react';
import api from '../../utils/api';

const AdminDashboard = () => {
    const [stats, setStats] = useState(null);
    const [recentActivity, setRecentActivity] = useState([]);
    const [users, setUsers] = useState([]);
    const [view, setView] = useState('dashboard'); // dashboard, users

    useEffect(() => {
        fetchDashboard();
    }, []);

    const fetchDashboard = async () => {
        try {
            const res = await api.get('/admin/dashboard');
            setStats(res.data.stats);
            setRecentActivity(res.data.recent_activity);
        } catch (error) {
            console.error(error);
            if (error.response?.status === 401 || error.response?.status === 403) {
                window.location.href = '/admin/login';
            }
        }
    };

    const fetchUsers = async () => {
        try {
            const res = await api.get('/admin/users');
            setUsers(res.data.users);
        } catch (error) {
            console.error(error);
        }
    };

    if (!stats) return <div className="text-white p-8">Loading Admin Panel...</div>;

    return (
        <div className="min-h-screen bg-slate-900 text-white flex">
            {/* Sidebar */}
            <div className="w-64 bg-slate-800 p-6 border-r border-slate-700">
                <h2 className="text-xl font-bold mb-8 text-indigo-400">🛡️ Admin Panel</h2>
                <nav className="space-y-4">
                    <button
                        onClick={() => setView('dashboard')}
                        className={`w-full text-left p-3 rounded-lg ${view === 'dashboard' ? 'bg-indigo-600' : 'hover:bg-slate-700'}`}
                    >
                        Dashboard
                    </button>
                    <button
                        onClick={() => { setView('users'); fetchUsers(); }}
                        className={`w-full text-left p-3 rounded-lg ${view === 'users' ? 'bg-indigo-600' : 'hover:bg-slate-700'}`}
                    >
                        User Management
                    </button>
                    <button
                        onClick={() => { localStorage.clear(); window.location.href = '/login'; }}
                        className="w-full text-left p-3 rounded-lg hover:bg-red-900/50 text-red-400 mt-8"
                    >
                        Logout
                    </button>
                </nav>
            </div>

            {/* Content */}
            <div className="flex-1 p-8 overflow-y-auto">
                {view === 'dashboard' ? (
                    <>
                        <h1 className="text-3xl font-bold mb-8">System Overview</h1>

                        {/* Stats Grid */}
                        <div className="grid grid-cols-3 gap-6 mb-8">
                            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                                <div className="text-gray-400 mb-2">Total Users</div>
                                <div className="text-3xl font-bold">{stats.total_users}</div>
                            </div>
                            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                                <div className="text-gray-400 mb-2">Revenue</div>
                                <div className="text-3xl font-bold text-green-400">₹{stats.total_revenue}</div>
                            </div>
                            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                                <div className="text-gray-400 mb-2">Total Submissions</div>
                                <div className="text-3xl font-bold text-indigo-400">{stats.total_submissions}</div>
                            </div>
                        </div>

                        {/* Recent Activity */}
                        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                            <div className="p-6 border-b border-slate-700">
                                <h3 className="text-xl font-bold">Recent Activity</h3>
                            </div>
                            <table className="w-full text-left">
                                <thead className="bg-slate-900/50 text-gray-400">
                                    <tr>
                                        <th className="p-4">User</th>
                                        <th className="p-4">Action</th>
                                        <th className="p-4">Description</th>
                                        <th className="p-4">Date</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {recentActivity.map((act, i) => (
                                        <tr key={i} className="hover:bg-slate-700/50">
                                            <td className="p-4">{act.email}</td>
                                            <td className="p-4">
                                                <span className="px-2 py-1 rounded-full bg-indigo-900/50 text-indigo-300 text-xs">
                                                    {act.action}
                                                </span>
                                            </td>
                                            <td className="p-4 text-gray-300">{act.description}</td>
                                            <td className="p-4 text-gray-500 text-sm">{new Date(act.created_at).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                ) : (
                    <>
                        <h1 className="text-3xl font-bold mb-8">User Management</h1>
                        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                            <table className="w-full text-left">
                                <thead className="bg-slate-900/50 text-gray-400">
                                    <tr>
                                        <th className="p-4">Name</th>
                                        <th className="p-4">Email</th>
                                        <th className="p-4">Roll Number</th>
                                        <th className="p-4">Plan</th>
                                        <th className="p-4">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {users.map((user) => (
                                        <tr key={user.id} className="hover:bg-slate-700/50">
                                            <td className="p-4 font-bold">{user.full_name || 'N/A'}</td>
                                            <td className="p-4">{user.email}</td>
                                            <td className="p-4">{user.roll_number || 'N/A'}</td>
                                            <td className="p-4">
                                                <span className={`px-2 py-1 rounded-full text-xs font-bold ${user.plan_type === 'premium' ? 'bg-purple-900 text-purple-300' :
                                                    user.plan_type === 'basic' ? 'bg-blue-900 text-blue-300' :
                                                        'bg-gray-700 text-gray-300'
                                                    }`}>
                                                    {user.plan_type?.toUpperCase() || 'FREE'}
                                                </span>
                                            </td>
                                            <td className="p-4">
                                                <span className={`text-xs ${user.is_active ? 'text-green-400' : 'text-red-400'}`}>
                                                    {user.is_active ? 'Active' : 'Deactivated'}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default AdminDashboard;
