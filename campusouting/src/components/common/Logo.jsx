import React from 'react';
import { Link } from 'react-router-dom';

const Logo = ({ className = "" }) => {
    return (
        <Link to="/" className={`flex items-center gap-2 group decoration-transparent ${className}`}>
            <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-fuchsia-500 shadow-lg shadow-indigo-500/30 group-hover:shadow-fuchsia-500/40 transition-all duration-300">
                <span className="text-white font-bold text-lg tracking-tighter mix-blend-overlay">CO</span>
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-fuchsia-600 dark:from-indigo-400 dark:to-fuchsia-400 tracking-tight transition-all duration-300 group-hover:opacity-80">
                CampusOuting
            </span>
        </Link>
    );
};

export default Logo;
