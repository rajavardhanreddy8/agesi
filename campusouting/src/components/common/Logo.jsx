import React from 'react';
import { Link } from 'react-router-dom';
import logoImg from '../../assets/logo.jpg';

const Logo = ({ className = "" }) => {
    return (
        <Link to="/" className={`flex items-center gap-2 group decoration-transparent ${className}`}>
            <img src={logoImg} alt="campusouting logo" className="w-8 h-8 rounded-lg" />
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-fuchsia-600 dark:from-indigo-400 dark:to-fuchsia-400 tracking-tight transition-all duration-300 group-hover:opacity-80">
                campusouting
            </span>
        </Link>
    );
};

export default Logo;
