import React, { useState, useEffect } from 'react';
import { auth } from '../../utils/auth';

export const ProfileSettings = () => {
    const [profile, setProfile] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [message, setMessage] = useState('');

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        try {
            const result = await auth.getProfile();
            if (result.success) {
                setProfile(result.profile);
            }
        } catch (err) {
            console.error('Failed to fetch profile:', err);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) return <div>Loading profile...</div>;
    if (!profile) return <div>Profile not found</div>;

    return (
        <div className="profile-settings">
            <h2>Profile Settings</h2>

            {message && <div className="alert">{message}</div>}

            <div className="profile-info">
                <h3>Personal Information</h3>
                <p><strong>Name:</strong> {profile.full_name}</p>
                <p><strong>Roll Number:</strong> {profile.roll_number}</p>
                <p><strong>Email:</strong> {profile.email}</p>
                <p><strong>School:</strong> {profile.school}</p>
                <p><strong>Programme:</strong> {profile.programme}</p>
                <p><strong>Specialization:</strong> {profile.specialization}</p>

                <p><strong>Student Phone:</strong> {profile.student_phone}</p>
                <p><strong>Parent Name:</strong> {profile.parent1_name}</p>
                <p><strong>Parent Email:</strong> {profile.parent1_email}</p>
                <p><strong>Parent Phone:</strong> {profile.parent1_phone}</p>

                <button onClick={() => alert("Edit not implemented yet")}>
                    Edit Profile
                </button>
            </div>
        </div>
    );
};
