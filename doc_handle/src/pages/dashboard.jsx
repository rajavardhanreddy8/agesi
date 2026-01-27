import React from 'react';
import OutingFormGenerator from '../components/OutingFormGenerator';
import Navigation from '../components/Navigation';

const Dashboard = () => (
    <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="container mx-auto px-4">
            <OutingFormGenerator />
        </div>
    </div>
);

export default Dashboard;
