import React, { useState } from 'react';
import { auth } from '../../utils/auth';

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
        programme: 'B.Tech',
        specialization: '',
        studentPhone: '',
        studentEmail: '',

        // Parent 1
        parent1Name: '',
        parent1Email: '',
        parent1Phone: '',
        parent1Relation: 'Father',

        // Parent 2 (optional)
        parent2Name: '',
        parent2Email: '',
        parent2Phone: '',
        parent2Relation: 'Mother',

        // Signature
        signatureData: ''
    });

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [verifyingCredentials, setVerifyingCredentials] = useState(false);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (!formData.email.endsWith('@woxsen.edu.in')) {
            setError('Please use your Woxsen college email (@woxsen.edu.in)');
            return;
        }

        setIsLoading(true);
        setVerifyingCredentials(true);

        try {
            const result = await auth.register({
                email: formData.email,
                password: formData.outlookPassword, // Use Outlook password for login too
                outlook_password: formData.outlookPassword,
                full_name: formData.fullName,
                roll_number: formData.rollNumber,
                school: formData.school,
                academic_year: formData.academicYear,
                programme: formData.programme,
                specialization: formData.specialization,
                student_phone: formData.studentPhone,
                student_email: formData.studentEmail || null,
                parent1_name: formData.parent1Name,
                parent1_email: formData.parent1Email,
                parent1_phone: formData.parent1Phone,
                parent1_relation: formData.parent1Relation,
                parent2_name: formData.parent2Name || null,
                parent2_email: formData.parent2Email || null,
                parent2_phone: formData.parent2Phone || null,
                parent2_relation: formData.parent2Relation,
                signature_data: formData.signatureData || null
            });

            if (result.success) {
                setSuccess(result.message);
                setTimeout(() => {
                    window.location.href = '/login';
                }, 3000);
            }

        } catch (err) {
            setError(err.response?.data?.error || 'Registration failed. Please try again.');
        } finally {
            setIsLoading(false);
            setVerifyingCredentials(false);
        }
    };

    return (
        <div className="register-container">
            <h2>Register for Outing Automation</h2>

            {error && <div className="alert alert-error" style={{ color: 'red' }}>{error}</div>}
            {success && <div className="alert alert-success" style={{ color: 'green' }}>{success}</div>}

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
                                    parent1Name: data.parent1Name || prev.parent1Name,
                                    parent1Email: data.parent1Email || prev.parent1Email,
                                    parent1Phone: data.parent1Phone || prev.parent1Phone,
                                    parent2Name: data.parent2Name || prev.parent2Name,
                                    parent2Email: data.parent2Email || prev.parent2Email,
                                    parent2Phone: data.parent2Phone || prev.parent2Phone,
                                }));
                                setSuccess('Data extracted successfully! Please review below.');
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
                        <label>College Email (@woxsen.edu.in) *</label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            required
                            placeholder="your.name@woxsen.edu.in"
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
                            placeholder="24WU0101111"
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

                {/* Parent/Guardian 1 */}
                <section>
                    <h3>Parent/Guardian 1 Details</h3>

                    <div className="form-group">
                        <label>Name *</label>
                        <input
                            type="text"
                            name="parent1Name"
                            value={formData.parent1Name}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Relation *</label>
                        <select name="parent1Relation" value={formData.parent1Relation} onChange={handleChange}>
                            <option value="Father">Father</option>
                            <option value="Mother">Mother</option>
                            <option value="Guardian">Guardian</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Email *</label>
                        <input
                            type="email"
                            name="parent1Email"
                            value={formData.parent1Email}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Phone *</label>
                        <input
                            type="tel"
                            name="parent1Phone"
                            value={formData.parent1Phone}
                            onChange={handleChange}
                            required
                            pattern="[0-9]{10}"
                        />
                    </div>
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

                <p className="text-center">
                    Already have an account? <a href="/login">Login here</a>
                </p>
            </form>
        </div>
    );
};
