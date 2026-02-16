import React, { useState, useEffect } from 'react';
import api from '../../utils/api';
import { RefreshCw, Mail } from 'lucide-react';

const AdminDashboard = () => {
    const [stats, setStats] = useState(null);
    const [recentActivity, setRecentActivity] = useState([]);
    const [users, setUsers] = useState([]);
    const [view, setView] = useState('dashboard'); // dashboard, users, settings, submissions
    const [config, setConfig] = useState({
        form_link: '',
        start_date: '',
        end_date: '',
        default_reason: ''
    });
    const [submissions, setSubmissions] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [showPassword, setShowPassword] = useState(false);
    const [decryptedPassword, setDecryptedPassword] = useState('');
    const [actionLoading, setActionLoading] = useState(false);

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

    const fetchSubmissions = async () => {
        try {
            const res = await api.get('/admin/submissions');
            setSubmissions(res.data.submissions);
        } catch (error) {
            console.error(error);
        }
    };

    const handleToggleAutomation = async (userId, currentStatus) => {
        setActionLoading(true);
        try {
            await api.post(`/admin/user/${userId}/automation`, { enabled: !currentStatus });
            // Refresh users
            const updatedUsers = users.map(u =>
                u.id === userId ? { ...u, automation_enabled: !currentStatus } : u
            );
            setUsers(updatedUsers);
            if (selectedUser?.id === userId) {
                setSelectedUser({ ...selectedUser, automation_enabled: !currentStatus });
            }
        } catch (error) {
            alert('Failed to toggle automation');
        } finally {
            setActionLoading(false);
        }
    };

    const handleUpdatePlan = async (userId, newPlan) => {
        if (!window.confirm(`Are you sure you want to change this user's plan to ${newPlan}?`)) return;

        setActionLoading(true);
        try {
            await api.post(`/admin/user/${userId}/subscription`, { plan_type: newPlan });
            await fetchUsers();
            if (selectedUser?.id === userId) {
                // simple refresh
                const updated = users.find(u => u.id === userId);
                if (updated) setSelectedUser({ ...updated, plan_type: newPlan });
            }
            alert('Plan updated successfully');
        } catch (error) {
            alert('Failed to update plan: ' + (error.response?.data?.error || error.message));
        } finally {
            setActionLoading(false);
        }
    };

    const fetchConfig = async () => {
        try {
            const res = await api.get('/config/active-outing');
            if (res.data.success) {
                setConfig({
                    form_link: res.data.form_link || '',
                    start_date: res.data.start_date || '',
                    end_date: res.data.end_date || '',
                    default_reason: res.data.default_reason || ''
                });
            }
        } catch (error) {
            console.error(error);
        }
    };

    const handleUpdateConfig = async (e) => {
        e.preventDefault();
        setActionLoading(true);
        try {
            await api.post('/admin/update-form-settings', config);
            alert('Settings updated successfully');
        } catch (error) {
            alert('Failed to update settings');
        } finally {
            setActionLoading(false);
        }
    };

    const handleViewPassword = async (userId) => {
        if (!window.confirm("SECURITY WARNING: You are about to view a user's decrypted password. This action is logged. Continue?")) return;

        setActionLoading(true);
        try {
            const res = await api.get(`/admin/user/${userId}/password`);
            setDecryptedPassword(res.data.password);
            setShowPassword(true);
        } catch (error) {
            alert('Failed to retrieve password: ' + (error.response?.data?.error || error.message));
        } finally {
            setActionLoading(false);
        }
    };

    const handleSyncFromMail = async () => {
        if (!window.confirm("This will fetch the latest email from 'student.outing@woxsen.edu.in' (or similar trusted senders) and overwrite the current settings. Continue?")) return;

        setActionLoading(true);
        try {
            const res = await api.post('/admin/sync-config-from-mail');
            if (res.data.success) {
                alert('Sync Complete!\nUpdated: ' + JSON.stringify(res.data.updates, null, 2));
                fetchConfig();
            }
        } catch (error) {
            alert('Sync failed: ' + (error.response?.data?.error || error.message));
        } finally {
            setActionLoading(false);
        }
    };

    if (!stats) return <div className="text-white p-8">Loading Admin Panel...</div>;

    return (
        <div className="min-h-screen bg-slate-900 text-white flex">
            {/* Sidebar */}
            <div className="w-64 bg-slate-800 p-6 border-r border-slate-700 fixed h-full">
                <h2 className="text-xl font-bold mb-8 text-indigo-400">🛡️ Admin Panel</h2>
                <nav className="space-y-4">
                    <button
                        onClick={() => { setView('dashboard'); setSelectedUser(null); }}
                        className={`w-full text-left p-3 rounded-lg ${view === 'dashboard' ? 'bg-indigo-600' : 'hover:bg-slate-700'}`}
                    >
                        Dashboard
                    </button>
                    <button
                        onClick={() => { setView('users'); fetchUsers(); setSelectedUser(null); }}
                        className={`w-full text-left p-3 rounded-lg ${view === 'users' ? 'bg-indigo-600' : 'hover:bg-slate-700'}`}
                    >
                        User Management
                    </button>
                    <button
                        onClick={() => { setView('settings'); fetchConfig(); setSelectedUser(null); }}
                        className={`w-full text-left p-3 rounded-lg ${view === 'settings' ? 'bg-indigo-600' : 'hover:bg-slate-700'}`}
                    >
                        Form Settings
                    </button>
                    <button
                        onClick={() => { setView('submissions'); fetchSubmissions(); setSelectedUser(null); }}
                        className={`w-full text-left p-3 rounded-lg ${view === 'submissions' ? 'bg-indigo-600' : 'hover:bg-slate-700'}`}
                    >
                        Automation Logs
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
            <div className="flex-1 p-8 ml-64 overflow-y-auto">
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
                            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                                <div className="text-gray-400 mb-2">Automation Queue</div>
                                <div className="text-3xl font-bold text-amber-400">{stats.queue_size || 0}</div>
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
                                            <td className="p-4 text-gray-500 text-sm">{new Date(act.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                ) : view === 'settings' ? (
                    <div className="max-w-2xl">
                        <div className="flex justify-between items-center mb-8">
                            <h1 className="text-3xl font-bold">System Configuration</h1>
                            <div className="flex gap-2">
                                <button
                                    onClick={handleSyncFromMail}
                                    disabled={actionLoading}
                                    className="px-3 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/50 rounded-lg text-indigo-300 transition-colors flex items-center gap-2"
                                    title="Sync from Latest Email"
                                >
                                    <Mail size={18} />
                                    <span className="text-sm font-bold">Autofill from Mail</span>
                                </button>
                                <button
                                    onClick={fetchConfig}
                                    className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-indigo-400 transition-colors"
                                    title="Refresh Settings"
                                >
                                    <RefreshCw size={20} />
                                </button>
                            </div>
                        </div>
                        <div className="bg-slate-800 p-8 rounded-xl border border-slate-700">
                            <form onSubmit={handleUpdateConfig} className="space-y-6">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">ACTIVE FORM LINK (MS FORMS)</label>
                                    <input
                                        type="url"
                                        required
                                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white outline-none focus:border-indigo-500"
                                        placeholder="https://forms.office.com/r/..."
                                        value={config.form_link}
                                        onChange={(e) => setConfig({ ...config, form_link: e.target.value })}
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-2">START DATE</label>
                                        <input
                                            type="date"
                                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white outline-none focus:border-indigo-500"
                                            value={config.start_date}
                                            onChange={(e) => setConfig({ ...config, start_date: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-2">END DATE</label>
                                        <input
                                            type="date"
                                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white outline-none focus:border-indigo-500"
                                            value={config.end_date}
                                            onChange={(e) => setConfig({ ...config, end_date: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">DEFAULT REASON</label>
                                    <input
                                        type="text"
                                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white outline-none focus:border-indigo-500"
                                        placeholder="Home Visit"
                                        value={config.default_reason}
                                        onChange={(e) => setConfig({ ...config, default_reason: e.target.value })}
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={actionLoading}
                                    className="w-full bg-indigo-600 hover:bg-indigo-700 py-4 rounded-xl font-bold transition-all shadow-lg shadow-indigo-500/20"
                                >
                                    {actionLoading ? 'Saving...' : 'Update Global Settings'}
                                </button>
                            </form>
                        </div>
                    </div>
                ) : view === 'submissions' ? (
                    <>
                        <div className="flex justify-between items-center mb-8">
                            <h1 className="text-3xl font-bold">Automation Submissions</h1>
                            <button
                                onClick={fetchSubmissions}
                                className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-indigo-400 transition-colors"
                                title="Refresh Submissions"
                            >
                                <RefreshCw size={20} />
                            </button>
                        </div>
                        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                            <table className="w-full text-left">
                                <thead className="bg-slate-900/50 text-gray-400">
                                    <tr>
                                        <th className="p-4">Student</th>
                                        <th className="p-4">Roll</th>
                                        <th className="p-4">Status</th>
                                        <th className="p-4">Details</th>
                                        <th className="p-4">Date</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {submissions.map((sub, i) => (
                                        <tr key={i} className="hover:bg-slate-700/50">
                                            <td className="p-4">
                                                <div className="font-bold">{sub.student_profiles?.full_name || 'N/A'}</div>
                                                <div className="text-xs text-gray-500">{sub.users?.email}</div>
                                            </td>
                                            <td className="p-4 text-sm font-mono">{sub.student_profiles?.roll_number}</td>
                                            <td className="p-4">
                                                <span className={`px-2 py-1 rounded-full text-xs font-bold ${sub.status === 'completed' ? 'bg-green-900 text-green-300' :
                                                    sub.status === 'failed' ? 'bg-red-900 text-red-300' :
                                                        'bg-amber-900 text-amber-300'
                                                    }`}>
                                                    {sub.status.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="p-4 text-sm text-gray-300">
                                                {sub.message || sub.error || 'Processing...'}
                                                {sub.screenshot_path && (
                                                    <div className="mt-1">
                                                        <a href={`/api/admin/screenshot/${sub.task_id}`} target="_blank" className="text-indigo-400 hover:underline text-xs">View Screenshot</a>
                                                    </div>
                                                )}
                                            </td>
                                            <td className="p-4 text-gray-500 text-sm">{new Date(sub.submitted_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="flex justify-between items-center mb-8">
                            <h1 className="text-3xl font-bold">User Management</h1>
                            <button
                                onClick={fetchUsers}
                                className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-indigo-400 transition-colors"
                                title="Refresh Users"
                            >
                                <RefreshCw size={20} />
                            </button>
                        </div>

                        {selectedUser ? (
                            <div className="bg-slate-800 p-8 rounded-xl border border-slate-700">
                                <button
                                    onClick={() => setSelectedUser(null)}
                                    className="mb-6 text-indigo-400 hover:text-indigo-300 flex items-center"
                                >
                                    ← Back to List
                                </button>

                                <div className="flex justify-between items-start mb-8">
                                    <div>
                                        <h2 className="text-2xl font-bold">{selectedUser.full_name || 'Incognito User'}</h2>
                                        <p className="text-gray-400">{selectedUser.email}</p>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm text-gray-400">Roll Number</div>
                                        <div className="font-mono text-lg">{selectedUser.roll_number || 'N/A'}</div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-8 mb-8">
                                    <div className="bg-slate-900/50 p-6 rounded-lg">
                                        <h3 className="text-lg font-bold mb-4 text-indigo-400">Subscription & Automation</h3>
                                        <div className="space-y-4">
                                            <div className="flex justify-between items-center">
                                                <span>Current Plan</span>
                                                <span className={`px-2 py-1 rounded-full text-xs font-bold ${selectedUser.plan_type === 'premium' ? 'bg-purple-900 text-purple-300' : 'bg-blue-900 text-blue-300'}`}>
                                                    {selectedUser.plan_type?.toUpperCase() || 'FREE'}
                                                </span>
                                            </div>
                                            <div className="flex gap-2">
                                                <button onClick={() => handleUpdatePlan(selectedUser.id, 'free')} className="flex-1 bg-slate-700 hover:bg-slate-600 py-2 rounded text-sm text-gray-300">Set Free</button>
                                                <button onClick={() => handleUpdatePlan(selectedUser.id, 'basic')} className="flex-1 bg-blue-900/50 hover:bg-blue-900 py-2 rounded text-sm text-blue-300">Set Basic</button>
                                                <button onClick={() => handleUpdatePlan(selectedUser.id, 'premium')} className="flex-1 bg-purple-900/50 hover:bg-purple-900 py-2 rounded text-sm text-purple-300">Set Premium</button>
                                            </div>

                                            <div className="border-t border-slate-700 my-4 pt-4 flex justify-between items-center">
                                                <span>Automation Status</span>
                                                <button
                                                    onClick={() => handleToggleAutomation(selectedUser.id, selectedUser.automation_enabled)}
                                                    className={`px-4 py-2 rounded-lg font-bold ${selectedUser.automation_enabled ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}
                                                >
                                                    {selectedUser.automation_enabled ? 'ENABLED' : 'DISABLED'}
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="bg-slate-900/50 p-6 rounded-lg border border-red-900/30">
                                        <h3 className="text-lg font-bold mb-4 text-red-400">⚠️ Sensitive Data</h3>
                                        <div className="space-y-4">
                                            <div className="flex justify-between items-center">
                                                <span>Outlook Credentials</span>
                                                {!showPassword ? (
                                                    <button
                                                        onClick={() => handleViewPassword(selectedUser.id)}
                                                        className="px-3 py-1 bg-red-900/30 hover:bg-red-900/50 text-red-300 rounded text-sm border border-red-900/50"
                                                    >
                                                        View Password
                                                    </button>
                                                ) : (
                                                    <div className="flex items-center gap-2">
                                                        <code className="bg-slate-800 px-2 py-1 rounded text-red-200">{decryptedPassword}</code>
                                                        <button onClick={() => { setShowPassword(false); setDecryptedPassword('') }} className="text-gray-400 text-xs hover:text-white">Hide</button>
                                                    </div>
                                                )}
                                            </div>
                                            <p className="text-xs text-gray-500 mt-2">
                                                Accessing user passwords is logged. Only view if absolutely necessary for debugging automation issues.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                                <table className="w-full text-left">
                                    <thead className="bg-slate-900/50 text-gray-400">
                                        <tr>
                                            <th className="p-4">Name</th>
                                            <th className="p-4">Email</th>
                                            <th className="p-4">Plan</th>
                                            <th className="p-4">Auto</th>
                                            <th className="p-4">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-700">
                                        {users.map((user) => (
                                            <tr key={user.id} className="hover:bg-slate-700/50 cursor-pointer" onClick={() => setSelectedUser(user)}>
                                                <td className="p-4 font-bold">{user.full_name || 'N/A'}</td>
                                                <td className="p-4 text-gray-400">{user.email}</td>
                                                <td className="p-4">
                                                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${user.plan_type === 'premium' ? 'bg-purple-900 text-purple-300' :
                                                        user.plan_type === 'basic' ? 'bg-blue-900 text-blue-300' :
                                                            'bg-gray-700 text-gray-300'
                                                        }`}>
                                                        {user.plan_type?.toUpperCase() || 'FREE'}
                                                    </span>
                                                </td>
                                                <td className="p-4">
                                                    <span className={`text-xs px-2 py-1 rounded-full ${user.automation_enabled ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                                                        {user.automation_enabled ? 'Auto ON' : 'Auto OFF'}
                                                    </span>
                                                </td>
                                                <td className="p-4">
                                                    <button className="text-indigo-400 hover:text-indigo-300 text-sm font-medium">Manage →</button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default AdminDashboard;
