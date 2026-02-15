import React, { useState } from 'react';
import api from '../../utils/api';

const AdminLogin = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const response = await api.post('/admin/login', { email, password });
            if (response.data.success) {
                localStorage.setItem('token', response.data.token);
                localStorage.setItem('isAdmin', 'true');
                window.location.href = '/admin/dashboard';
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Login failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-900">
            <div className="w-full max-w-md bg-slate-800 p-8 rounded-2xl shadow-2xl border border-gray-700">
                <h2 className="text-3xl font-bold text-center text-white mb-2">Admin Portal</h2>
                <p className="text-center text-gray-400 mb-8">Restricted Access Only</p>

                {error && <div className="bg-red-500/10 text-red-500 p-3 rounded-lg mb-4 text-center">{error}</div>}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-gray-300 text-sm font-bold mb-2">Admin Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full bg-slate-900 border border-gray-600 rounded-lg p-3 text-white focus:border-indigo-500 focus:outline-none"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-gray-300 text-sm font-bold mb-2">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-slate-900 border border-gray-600 rounded-lg p-3 text-white focus:border-indigo-500 focus:outline-none"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-gradient-to-r from-red-600 to-red-700 text-white font-bold py-3 rounded-lg hover:from-red-500 hover:to-red-600 transition-all"
                    >
                        {isLoading ? 'Verifying...' : 'Access Dashboard'}
                    </button>

                    <div className="text-center">
                        <a href="/login" className="text-gray-500 text-sm hover:text-gray-400">Back to Student Login</a>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AdminLogin;
