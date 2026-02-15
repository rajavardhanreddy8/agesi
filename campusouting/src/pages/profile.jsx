import React from 'react';
import { ProfileSettings } from '../components/auth/ProfileSettings';
import Navigation from '../components/Navigation';

const Profile = () => (
    <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="py-12 container mx-auto px-4">
            <ProfileSettings />
        </div>
    </div>
);

export default Profile;
