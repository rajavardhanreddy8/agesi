
import React, { useState, useEffect } from 'react';
import api from '../../utils/api';

export const ProfileSettings = () => {
    const [formData, setFormData] = useState({
        // Authentication (readonly mostly, except Outlook PWD)
        email: '',
        outlookPassword: '', // Only for updating

        // Personal Info
        fullName: '',
        rollNumber: '',
        school: 'School of Technology',
        academicYear: '2024-2028',
        programme: 'B.Tech',
        specialization: '',
        studentPhone: '',
        studentEmail: '',

        // Mother Details
        motherName: '',
        motherEmail: '',
        motherPhone: '',

        // Father Details
        fatherName: '',
        fatherEmail: '',
        fatherPhone: '',

        // Email Prefs
        sendParentEmail: false,

        // Signature
        signatureData: '',
        signaturePreview: null
    });

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loadingProfile, setLoadingProfile] = useState(true);

    // Initial Load
    useEffect(() => {
        loadProfile();
    }, []);

    const loadProfile = async () => {
        try {
            const res = await api.get('/profile');
            if (res.data.success) {
                const p = res.data.profile;
                setFormData(prev => ({
                    ...prev,
                    email: p.email || '',
                    fullName: p.full_name || '',
                    rollNumber: p.roll_number || '',
                    school: p.school || 'School of Technology',
                    academicYear: p.academic_year || '2024-2028',
                    programme: p.programme || 'B.Tech',
                    specialization: p.specialization || '',
                    studentPhone: p.student_phone || '',
                    studentEmail: p.student_email || p.email || '', // fallback to main email

                    fatherName: p.parent1_name || '',
                    fatherEmail: p.parent1_email || '',
                    fatherPhone: p.parent1_phone || '',

                    motherName: p.parent2_name || '',
                    motherEmail: p.parent2_email || '',
                    motherPhone: p.parent2_phone || '',

                    sendParentEmail: p.send_parent_email === true,

                    signatureData: p.signature_data || '',
                    signaturePreview: p.signature_data || null
                }));
            }
        } catch (e) {
            setError('Failed to load profile data.');
        } finally {
            setLoadingProfile(false);
        }
    };

    const handleSignatureUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onloadend = () => {
            setFormData(prev => ({
                ...prev,
                signatureData: reader.result,
                signaturePreview: reader.result
            }));
        };
        reader.readAsDataURL(file);
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setIsLoading(true);

        try {
            // Map frontend state to API expected fields
            const payload = {
                full_name: formData.fullName,
                roll_number: formData.rollNumber,
                school: formData.school,
                academic_year: formData.academicYear,
                programme: formData.programme,
                specialization: formData.specialization,
                student_phone: formData.studentPhone,
                student_email: formData.studentEmail,

                parent1_name: formData.fatherName,
                parent1_email: formData.fatherEmail,
                parent1_phone: formData.fatherPhone,

                parent2_name: formData.motherName,
                parent2_email: formData.motherEmail,
                parent2_phone: formData.motherPhone,

                send_parent_email: formData.sendParentEmail,

                signature_data: formData.signatureData,
                outlook_password: formData.outlookPassword // Will only update if not empty
            };

            const res = await api.put('/profile', payload);
            if (res.data.success) {
                setSuccess('Profile updated successfully!');
                setFormData(prev => ({ ...prev, outlookPassword: '' })); // Clear password field for security
                // Optionally reload or just stay put
                window.scrollTo(0, 0);
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to update profile.');
            window.scrollTo(0, 0);
        } finally {
            setIsLoading(false);
        }
    };

    if (loadingProfile) return <div className="text-center p-8 text-white">Loading profile...</div>;

    return (
        <div className="register-container" style={{ minHeight: 'auto', borderRadius: '16px' }}>
            <h2>Edit Profile</h2>

            <form onSubmit={handleSubmit}>
                {/* Document Upload Section */}
                <div className="mb-8 p-6 bg-indigo-50 rounded-lg border-2 border-dashed border-indigo-300">
                    <div className="flex items-center gap-2 mb-3">
                        <span className="text-xl">📄</span>
                        <h3 className="text-lg font-semibold text-gray-800">Auto-Update from Document</h3>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                        Upload a new ID card or form to auto-update your details.
                    </p>

                    <input
                        type="file"
                        accept=".docx"
                        onChange={async (e) => {
                            const file = e.target.files[0];
                            if (!file) return;

                            setIsLoading(true);
                            setSuccess('Extracting data from document...');
                            try {
                                const { extractRegistrationData } = await import('../../utils/docExtractor');
                                const data = await extractRegistrationData(file);

                                setFormData(prev => ({
                                    ...prev,
                                    fullName: data.fullName || prev.fullName,
                                    rollNumber: data.rollNumber || prev.rollNumber,
                                    school: data.school || prev.school,
                                    academicYear: data.academicYear || prev.academicYear,
                                    programme: data.programme || prev.programme,
                                    specialization: data.specialization || prev.specialization,
                                    studentPhone: data.studentPhone || prev.studentPhone,
                                    studentEmail: data.studentEmail || prev.studentEmail,
                                    fatherName: data.fatherName || prev.fatherName,
                                    fatherEmail: data.fatherEmail || prev.fatherEmail,
                                    fatherPhone: data.fatherPhone || prev.fatherPhone,
                                    motherName: data.motherName || prev.motherName,
                                    motherEmail: data.motherEmail || prev.motherEmail,
                                    motherPhone: data.motherPhone || prev.motherPhone,
                                    signatureData: data.signatureData || prev.signatureData,
                                    signaturePreview: data.signatureData || prev.signaturePreview,
                                }));
                                const signatureMsg = data.signatureData ? ' Signature also found!' : '';
                                setSuccess('Data extracted! Review changes below.' + signatureMsg);
                            } catch (err) {
                                setError('Extraction failed: ' + err.message);
                            } finally {
                                setIsLoading(false);
                            }
                        }}
                        className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 cursor-pointer"
                    />
                </div>

                {/* Login Credentials (Update Only) */}
                <section>
                    <h3>Account Credentials</h3>

                    <div className="form-group">
                        <label>College Email (Read-Only)</label>
                        <input
                            type="email"
                            value={formData.email}
                            disabled
                            style={{ opacity: 0.7, cursor: 'not-allowed' }}
                        />
                    </div>

                    <div className="form-group">
                        <label>Update Outlook Password</label>
                        <input
                            type="password"
                            name="outlookPassword"
                            value={formData.outlookPassword}
                            onChange={handleChange}
                            placeholder="Leave empty to keep current password"
                        />
                        <small className="form-text" style={{ display: 'block', color: '#666' }}>
                            Update this ONLY if you changed your actual Outlook password.
                        </small>
                    </div>
                </section>

                {/* Personal Information */}
                <section>
                    <h3>Personal Information</h3>

                    <div className="form-group">
                        <label>Full Name</label>
                        <input type="text" name="fullName" value={formData.fullName} onChange={handleChange} required />
                    </div>

                    <div className="form-group">
                        <label>Roll Number</label>
                        <input type="text" name="rollNumber" value={formData.rollNumber} onChange={handleChange} required />
                    </div>

                    <div className="form-group">
                        <label>School</label>
                        <select name="school" value={formData.school} onChange={handleChange} required>
                            <option value="School of Technology">School of Technology</option>
                            <option value="School of Business">School of Business</option>
                            <option value="School of Law">School of Law</option>
                            <option value="School of Arts and Design">School of Arts and Design</option>
                            <option value="School of Liberal Arts and Humanities">School of Liberal Arts and Humanities</option>
                            <option value="School of Architecture and Planning">School of Architecture and Planning</option>
                            <option value="School of Sciences">School of Sciences</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Programme</label>
                        <select name="programme" value={formData.programme} onChange={handleChange} required>
                            <option value="B.Tech">B.Tech</option>
                            <option value="BBA">BBA</option>
                            <option value="B.Com">B.Com</option>
                            <option value="BA LLB">BA LLB</option>
                            <option value="BBA LLB">BBA LLB</option>
                            <option value="B.Sc">B.Sc</option>
                            <option value="BCA">BCA</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Specialization</label>
                        <input type="text" name="specialization" value={formData.specialization} onChange={handleChange} required />
                    </div>

                    <div className="form-group">
                        <label>Academic Year</label>
                        <input type="text" name="academicYear" value={formData.academicYear} onChange={handleChange} required />
                    </div>

                    <div className="form-group">
                        <label>Phone Number</label>
                        <input type="tel" name="studentPhone" value={formData.studentPhone} onChange={handleChange} required pattern="[0-9]{10}" />
                    </div>
                </section>

                {/* Mother Details */}
                <section>
                    <h3>Mother's Details</h3>
                    <div className="form-group">
                        <label>Name</label>
                        <input type="text" name="motherName" value={formData.motherName} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Email</label>
                        <input type="email" name="motherEmail" value={formData.motherEmail} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Phone</label>
                        <input type="tel" name="motherPhone" value={formData.motherPhone} onChange={handleChange} required pattern="[0-9]{10}" />
                    </div>
                </section>

                {/* Father Details */}
                <section>
                    <h3>Father's Details</h3>
                    <div className="form-group">
                        <label>Name</label>
                        <input type="text" name="fatherName" value={formData.fatherName} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Email</label>
                        <input type="email" name="fatherEmail" value={formData.fatherEmail} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Phone</label>
                        <input type="tel" name="fatherPhone" value={formData.fatherPhone} onChange={handleChange} required pattern="[0-9]{10}" />
                    </div>
                </section>

                {/* Signature Upload */}
                <section>
                    <h3>Your Signature</h3>
                    <p className="text-sm text-gray-600 mb-3">Upload a new signature (PNG/JPG) to update.</p>

                    <div className="form-group">
                        <input
                            type="file"
                            accept="image/png, image/jpeg"
                            onChange={handleSignatureUpload}
                            className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 cursor-pointer"
                        />
                    </div>

                    {formData.signaturePreview && (
                        <div className="mt-3 p-3 border rounded bg-gray-50">
                            <p className="text-sm font-medium mb-2">Current Signature:</p>
                            <img
                                src={formData.signaturePreview?.startsWith('signatures/') ? `https://outing-backend-api.azurewebsites.net/${formData.signaturePreview}` : formData.signaturePreview}
                                alt="Signature preview"
                                style={{ maxHeight: '80px', border: '1px solid #ccc', background: '#fff', padding: '5px' }}
                            />
                        </div>
                    )}
                </section>

                {/* Email Preferences */}
                <section>
                    <h3>Email Preferences</h3>
                    <div
                        onClick={() => setFormData({ ...formData, sendParentEmail: !formData.sendParentEmail })}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            gap: '16px',
                            marginTop: '12px',
                            padding: '16px 20px',
                            borderRadius: '12px',
                            background: formData.sendParentEmail
                                ? 'linear-gradient(135deg, rgba(79,70,229,0.15) 0%, rgba(139,92,246,0.1) 100%)'
                                : 'rgba(255,255,255,0.04)',
                            border: formData.sendParentEmail
                                ? '1.5px solid rgba(139,92,246,0.6)'
                                : '1.5px solid rgba(255,255,255,0.1)',
                            cursor: 'pointer',
                            transition: 'all 0.25s ease',
                            userSelect: 'none',
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                            <span style={{ fontSize: '22px', marginTop: '2px' }}>
                                {formData.sendParentEmail ? '📧' : '🔕'}
                            </span>
                            <div>
                                <div style={{ fontWeight: '600', fontSize: '15px', color: formData.sendParentEmail ? '#a78bfa' : '#e2e8f0', marginBottom: '3px' }}>
                                    Send Outing Pass to Parent
                                </div>
                                <div style={{ fontSize: '13px', color: '#94a3b8', lineHeight: '1.4' }}>
                                    {formData.sendParentEmail
                                        ? `A copy will be emailed to your parent when submission is complete.`
                                        : 'Your parent will not receive an email. Only you will be notified.'}
                                </div>
                            </div>
                        </div>
                        {/* Toggle Switch */}
                        <div style={{ flexShrink: 0 }}>
                            <div style={{
                                width: '48px',
                                height: '26px',
                                borderRadius: '13px',
                                background: formData.sendParentEmail ? '#4f46e5' : '#374151',
                                position: 'relative',
                                transition: 'background 0.25s ease',
                                boxShadow: formData.sendParentEmail ? '0 0 12px rgba(99,102,241,0.5)' : 'none',
                            }}>
                                <div style={{
                                    position: 'absolute',
                                    top: '3px',
                                    left: formData.sendParentEmail ? '25px' : '3px',
                                    width: '20px',
                                    height: '20px',
                                    borderRadius: '50%',
                                    background: '#fff',
                                    transition: 'left 0.25s ease',
                                    boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
                                }} />
                            </div>
                        </div>
                    </div>
                    {/* Status pill */}
                    <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            fontSize: '12px',
                            fontWeight: '600',
                            padding: '3px 10px',
                            borderRadius: '20px',
                            background: formData.sendParentEmail ? 'rgba(79,70,229,0.2)' : 'rgba(239,68,68,0.15)',
                            color: formData.sendParentEmail ? '#a5b4fc' : '#fca5a5',
                            border: formData.sendParentEmail ? '1px solid rgba(99,102,241,0.4)' : '1px solid rgba(239,68,68,0.3)',
                        }}>
                            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: formData.sendParentEmail ? '#818cf8' : '#f87171', display: 'inline-block' }} />
                            {formData.sendParentEmail ? 'Parent email ON' : 'Parent email OFF'}
                        </span>
                    </div>
                </section>

                <button
                    type="submit"
                    className="btn-primary" // Reuse class from Register
                    disabled={isLoading}
                    style={{ marginTop: '20px', width: '100%', padding: '15px' }}
                >
                    {isLoading ? 'Updating...' : 'Update Profile'}
                </button>

                {error && <div className="alert alert-error" style={{ color: 'red', marginTop: '15px', padding: '10px', background: '#ffe6e6', borderRadius: '5px' }}>{error}</div>}
                {success && <div className="alert alert-success" style={{ color: 'green', marginTop: '15px', padding: '10px', background: '#e6ffe6', borderRadius: '5px' }}>{success}</div>}
            </form>
        </div>
    );
};
