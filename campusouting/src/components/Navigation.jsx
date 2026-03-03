import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { auth } from '../utils/auth';
import Logo from './common/Logo';

const Navigation = () => {
    const user = auth.getUser();

    const handleLogout = () => {
        auth.logout();
    };

    return (
        <nav className="nav-style">
            <div className="nav-container">
                <Logo />

                <div className="nav-links">
                    {auth.isAuthenticated() ? (
                        <>
                            <Link to="/dashboard" className="nav-link">Dashboard</Link>
                            <Link to="/profile" className="nav-link">Profile</Link>
                            <Link to="/plans" className="nav-link nav-link-premium">💎 Plans</Link>
                            <span className="nav-user">Hi, {user?.full_name?.split(' ')[0] || 'User'}</span>
                            <button onClick={handleLogout} className="btn-sm-primary bg-red-600 hover:bg-red-700">
                                Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="nav-link">Login</Link>
                            <Link to="/register" className="btn-sm-primary">Get Started</Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
};

export default Navigation;
