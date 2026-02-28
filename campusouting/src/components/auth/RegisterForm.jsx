import React, { useState } from 'react';
import { auth } from '../../utils/auth';
import Logo from '../common/Logo';

export const RegisterForm = () => {
    const [formData, setFormData] = useState({
        // Authentication
        email: '',
        password: '',
        outlookPassword: '',

        // Personal Info
        fullName: '',
        rollNumber: '',
        school: 'School of Technology',
        academicYear: '2024-2028',
        programme: '',
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

        // Signature
        signatureData: '',
        signaturePreview: null
    });

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [verifyingCredentials, setVerifyingCredentials] = useState(false);
    const [signatureFile, setSignatureFile] = useState(null);

    // Handle signature file upload
    const handleSignatureUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setSignatureFile(file);

        // Convert to base64 for preview and storage
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
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (isLoading) return;

        // Client-side validation for required fields
        const requiredFields = [
            { key: 'email', label: 'College Email' },
            { key: 'password', label: 'Password' },
            { key: 'outlookPassword', label: 'Outlook Password' },
            { key: 'fullName', label: 'Full Name' },
            { key: 'rollNumber', label: 'Roll Number' },
            { key: 'school', label: 'School' },
            { key: 'programme', label: 'Programme' },
            { key: 'specialization', label: 'Specialization' },
            { key: 'studentPhone', label: 'Phone Number' },
            { key: 'fatherName', label: "Father's Name" },
            { key: 'fatherEmail', label: "Father's Email" },
            { key: 'fatherPhone', label: "Father's Phone" },
            { key: 'motherName', label: "Mother's Name" },
            { key: 'motherEmail', label: "Mother's Email" },
            { key: 'motherPhone', label: "Mother's Phone" },
        ];

        for (const { key, label } of requiredFields) {
            if (!formData[key] || !formData[key].trim()) {
                setError(`${label} is required. Please fill in all fields.`);
                return;
            }
        }

        setIsLoading(true);
        setVerifyingCredentials(true);

        try {
            // First verify Outlook credentials
            try {
                const verifyRes = await import('../../utils/api').then(m => m.default.post('/verify-outlook', {
                    email: formData.email,
                    outlook_password: formData.outlookPassword
                }));

                if (!verifyRes.data.success) {
                    throw new Error(verifyRes.data.error || 'Invalid college email or password');
                }
            } catch (err) {
                // If the error has a response from the server, use that specific message
                const errorMsg = err.response?.data?.error || err.message || 'Verification failed';
                console.error("Verification error details:", err.response?.data || err);
                throw new Error(errorMsg);
            }

            setVerifyingCredentials(false);
            setSuccess('Credentials verified! Creating account...');

            const result = await auth.register({
                email: formData.email,
                password: formData.password,
                outlook_password: formData.outlookPassword,
                full_name: formData.fullName,
                roll_number: formData.rollNumber,
                school: formData.school,
                academic_year: formData.academicYear,
                programme: formData.programme,
                specialization: formData.specialization,
                student_phone: formData.studentPhone,
                student_email: formData.email,
                parent1_name: formData.fatherName,
                parent1_email: formData.fatherEmail,
                parent1_phone: formData.fatherPhone,
                parent1_relation: 'Father',
                parent2_name: formData.motherName,
                parent2_email: formData.motherEmail,
                parent2_phone: formData.motherPhone,
                parent2_relation: 'Mother',
                signature_data: formData.signatureData || null
            });

            if (result.success) {
                setSuccess(result.message);
                setTimeout(() => {
                    window.location.href = '/login';
                }, 3000);
            }

        } catch (err) {
            setError(err.response?.data?.error || err.message || 'Registration failed. Please try again.');
        } finally {
            setIsLoading(false);
            setVerifyingCredentials(false);
        }
    };

    return (
        <div className="register-container">
            <div className="text-center mb-10 flex flex-col items-center">
                <Logo className="scale-125 mb-4" />
                <h2 style={{ marginBottom: 0 }}>Create your account</h2>
                <p className="text-slate-400 mt-2 text-sm">Join campusouting for intelligent outing automation.</p>
            </div>


            <form onSubmit={handleSubmit}>
                {/* Document Upload Section */}
                <div className="mb-8 p-6 bg-indigo-50 rounded-lg border-2 border-dashed border-indigo-300">
                    <div className="flex items-center gap-2 mb-3">
                        <span className="text-xl">📄</span>
                        <h3 className="text-lg font-semibold text-gray-800">Auto-Fill from Document</h3>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                        Upload a previous outing form or id card document to automatically fill your details.
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
                                const signatureMsg = data.signatureData ? ' Signature also extracted!' : '';
                                setSuccess('Data extracted successfully!' + signatureMsg + ' Please review below.');
                            } catch (err) {
                                setError('Failed to extract data: ' + err.message);
                            } finally {
                                setIsLoading(false);
                            }
                        }}
                        className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 cursor-pointer"
                    />
                </div>

                {/* Login Credentials */}
                <section>
                    <h3>Login Credentials</h3>

                    <div className="form-group">
                        <label>College Email (@college.edu.in) *</label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            required
                            placeholder="your.name@college.edu.in"
                        />
                    </div>

                    <div className="form-group">
                        <label>Password *</label>
                        <input
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            required
                            minLength={8}
                            placeholder="Minimum 8 characters"
                        />
                    </div>


                    <div className="form-group">
                        <label>Outlook Password *</label>
                        <input
                            type="password"
                            name="outlookPassword"
                            value={formData.outlookPassword}
                            onChange={handleChange}
                            required
                            placeholder="Your Microsoft account password"
                        />
                        <small className="form-text" style={{ display: 'block', color: '#666' }}>
                            ⚠️ Use your Outlook password. This will be used for <b>logging in</b> to this portal and for <b>automating</b> your form submissions.
                        </small>
                    </div>
                </section>

                {/* Personal Information */}
                <section>
                    <h3>Personal Information</h3>

                    <div className="form-group">
                        <label>Full Name *</label>
                        <input
                            type="text"
                            name="fullName"
                            value={formData.fullName}
                            onChange={handleChange}
                            required
                            placeholder="As per college records"
                        />
                    </div>

                    <div className="form-group">
                        <label>Roll Number *</label>
                        <input
                            type="text"
                            name="rollNumber"
                            value={formData.rollNumber}
                            onChange={handleChange}
                            required
                            placeholder="22WU0000000"
                        />
                    </div>

                    <div className="form-group">
                        <label>School *</label>
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
                        <label>Programme *</label>
                        <select name="programme" value={formData.programme} onChange={handleChange} required>
                            <option value="">-- Select Programme --</option>
                            <option value="BBA">BBA (Bachelor of Business Administration)</option>
                            <option value="MBBA">MBBA (Master of Business Administration)</option>
                            <option value="BCom">BCom (Bachelor of Commerce)</option>
                            <option value="B. Arch">B. Arch (Bachelor of Architecture)</option>
                            <option value="B.Des">B.Des (Bachelor of Design)</option>
                            <option value="BA LLB">BA LLB (Bachelor of Arts + Law)</option>
                            <option value="BBA LLB">BBA LLB (BBA + Law)</option>
                            <option value="B.A.">B.A. (Bachelor of Arts)</option>
                            <option value="B.Tech">B.Tech (Bachelor of Technology)</option>
                            <option value="B.Sc.">B.Sc. (Bachelor of Science)</option>
                            <option value="BCA">BCA (Bachelor of Computer Applications)</option>
                        </select>
                        <small className="form-text" style={{ display: 'block', color: '#666', marginTop: '4px' }}>
                            ⚠️ Select your PROGRAMME (e.g., B.Tech, BBA), NOT your specialization (e.g., CSE, Marketing)
                        </small>
                    </div>

                    <div className="form-group">
                        <label>Specialization *</label>
                        <input
                            type="text"
                            name="specialization"
                            value={formData.specialization}
                            onChange={handleChange}
                            required
                            placeholder="e.g., CSE, ECE, Mechanical"
                        />
                    </div>

                    <div className="form-group">
                        <label>Phone Number *</label>
                        <input
                            type="tel"
                            name="studentPhone"
                            value={formData.studentPhone}
                            onChange={handleChange}
                            required
                            pattern="[0-9]{10}"
                            placeholder="10-digit mobile number"
                        />
                    </div>
                </section>

                {/* Mother Details */}
                <section>
                    <h3>Mother's Details</h3>

                    <div className="form-group">
                        <label>Mother's Name *</label>
                        <input
                            type="text"
                            name="motherName"
                            value={formData.motherName}
                            onChange={handleChange}
                            required
                            placeholder="Mother's full name"
                        />
                    </div>

                    <div className="form-group">
                        <label>Mother's Email *</label>
                        <input
                            type="email"
                            name="motherEmail"
                            value={formData.motherEmail}
                            onChange={handleChange}
                            required
                            placeholder="mother@email.com"
                        />
                    </div>

                    <div className="form-group">
                        <label>Mother's Phone *</label>
                        <input
                            type="tel"
                            name="motherPhone"
                            value={formData.motherPhone}
                            onChange={handleChange}
                            required
                            pattern="[0-9]{10}"
                            placeholder="10-digit mobile number"
                        />
                    </div>
                </section>

                {/* Father Details */}
                <section>
                    <h3>Father's Details</h3>

                    <div className="form-group">
                        <label>Father's Name *</label>
                        <input
                            type="text"
                            name="fatherName"
                            value={formData.fatherName}
                            onChange={handleChange}
                            required
                            placeholder="Father's full name"
                        />
                    </div>

                    <div className="form-group">
                        <label>Father's Email *</label>
                        <input
                            type="email"
                            name="fatherEmail"
                            value={formData.fatherEmail}
                            onChange={handleChange}
                            required
                            placeholder="father@email.com"
                        />
                    </div>

                    <div className="form-group">
                        <label>Father's Phone *</label>
                        <input
                            type="tel"
                            name="fatherPhone"
                            value={formData.fatherPhone}
                            onChange={handleChange}
                            required
                            pattern="[0-9]{10}"
                            placeholder="10-digit mobile number"
                        />
                    </div>
                </section>

                {/* Signature Upload */}
                <section>
                    <h3>Your Signature</h3>
                    <p className="text-sm text-gray-600 mb-3">Upload an image of your signature (PNG or JPG)</p>

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
                            <p className="text-sm font-medium mb-2">Signature Preview:</p>
                            <img
                                src={formData.signaturePreview}
                                alt="Signature preview"
                                style={{ maxHeight: '80px', border: '1px solid #ccc', background: '#fff', padding: '5px' }}
                            />
                        </div>
                    )}
                </section>

                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={isLoading}
                    style={{ marginTop: '20px' }}
                >
                    {verifyingCredentials ? 'Verifying Outlook credentials...' :
                        isLoading ? 'Registering...' :
                            'Register'}
                </button>

                {error && <div className="alert alert-error" style={{ color: 'red', marginTop: '15px', padding: '10px', background: '#ffe6e6', borderRadius: '5px' }}>{error}</div>}
                {success && <div className="alert alert-success" style={{ color: 'green', marginTop: '15px', padding: '10px', background: '#e6ffe6', borderRadius: '5px' }}>{success}</div>}

                <p className="text-center">
                    Already have an account? <a href="/login">Login here</a>
                </p>
            </form>
        </div>
    );
};
