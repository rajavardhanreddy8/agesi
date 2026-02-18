import React, { useState, useEffect } from 'react';
import { Download, FileText, Upload, Image, Brain, Loader2, Send, AlertCircle } from 'lucide-react';
import * as mammoth from 'mammoth';
import { auth } from '../utils/auth';
import api from '../utils/api';
import { generateOutingPDF } from '../utils/pdfGenerator';

export default function OutingFormGenerator() {
    // Basic Form Data
    const [formData, setFormData] = useState({
        studentName: '',
        studentId: '',
        program: '',
        academicYear: '',
        relation: 'father',
        gender: 'son',
        startDate: '',
        startTime: '17:30',
        endDate: '',
        endTime: '08:30',
        purpose: 'Outing',
        todayDate: new Date().toISOString().split('T')[0],
        fatherName: '',
        fatherEmail: '',
        fatherMobile: '',
        motherName: '',
        motherEmail: '',
        motherMobile: '',
        studentEmail: '',
        studentMobile: '',
        formLink: 'https://forms.office.com/Pages/ResponsePage.aspx?id=LSD36rPvekOhA1Bbufv3X9NSKOayoK9NtQfVOU9-8dhUNTVLNjhLSDZYMUlRVUNOMEc1MDQ0WFNDTS4u'
    });

    const [signatureImage, setSignatureImage] = useState(null);
    const [isExtracting, setIsExtracting] = useState(false);
    const [extractionStatus, setExtractionStatus] = useState('');

    // Automation State
    const [submissionStatus, setSubmissionStatus] = useState('');
    const [taskId, setTaskId] = useState(null);
    const [isLoadingProfile, setIsLoadingProfile] = useState(true);

    // Initial Data Load (Profile + Defaults)
    useEffect(() => {
        loadUserProfile();
    }, []);

    const loadUserProfile = async () => {
        setIsLoadingProfile(true);
        try {
            const userProfile = await auth.getProfile();
            if (userProfile.success && userProfile.profile) {
                const p = userProfile.profile;
                setFormData(prev => ({
                    ...prev,
                    studentName: p.full_name,
                    studentId: p.roll_number,
                    program: p.programme,
                    academicYear: p.academic_year?.split('-')[0] || '', // Extract start year
                    studentEmail: p.student_email || p.email, // Prefer college email over auth email
                    studentMobile: p.student_phone,
                    fatherName: p.parent1_name,
                    fatherEmail: p.parent1_email,
                    fatherMobile: p.parent1_phone,
                    motherName: p.parent2_name || '',
                    motherEmail: p.parent2_email || '',
                    motherMobile: p.parent2_phone || '',
                }));
                if (p.signature_data) {
                    setSignatureImage(p.signature_data);
                }
            }
        } catch (error) {
            console.error("Failed to load profile", error);
        } finally {
            setIsLoadingProfile(false);
        }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSignatureUpload = (e) => {
        const file = e.target.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (event) => setSignatureImage(event.target.result);
            reader.readAsDataURL(file);
        }
    };

    // ... Groq logic (Simplified/Removed for brevity if not focus, but keeping structure)
    // Assuming Groq extraction logic remains similar or uses utilities
    // Just keeping the handler shells for now to focus on Auth logic

    // Helper to format date as dd/mm/yyyy
    const formatDate = (dateStr) => {
        if (!dateStr) return '___/___/______';
        const parts = dateStr.split('-'); // YYYY-MM-DD
        if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        return dateStr;
    };

    const generatePDF = () => {
        // Resolve signature URL
        let sigUrl = signatureImage;
        if (sigUrl && !sigUrl.startsWith('data:') && !sigUrl.startsWith('http')) {
            // It's likely a relative path from DB (e.g., 'signatures/user.png')
            // Prepend the backend root URL (not /api)
            const backendRoot = 'https://outing-backend-api.azurewebsites.net';
            sigUrl = `${backendRoot}/${sigUrl.replace(/^\//, '')}`;
        }

        generateOutingPDF({
            studentName: formData.studentName,
            studentId: formData.studentId,
            program: formData.program,
            academicYear: formData.academicYear,

            startDate: formData.startDate,
            startTime: formData.startTime,
            endDate: formData.endDate,
            endTime: formData.endTime,
            purpose: formData.purpose,
            todayDate: formData.todayDate,

            fatherName: formData.fatherName,
            fatherEmail: formData.fatherEmail,
            fatherMobile: formData.fatherMobile,

            motherName: formData.motherName,
            motherEmail: formData.motherEmail,
            motherMobile: formData.motherMobile,

            studentEmail: formData.studentEmail,
            studentMobile: formData.studentMobile,

            signatureImage: sigUrl
        });
    };

    const handleAutoSubmit = async () => {
        const pdfInput = document.getElementById('submissionPdf');
        const pdfFile = pdfInput?.files[0];

        if (!pdfFile) {
            alert("Please upload the PDF you just generated.");
            return;
        }

        setSubmissionStatus('Submitting...');

        try {
            const submitData = new FormData();
            submitData.append('pdf', pdfFile);
            submitData.append('data', JSON.stringify({
                form_url: formData.formLink,
                leave_start_date: formData.startDate,
                leave_end_date: formData.endDate,
                reason: formData.purpose
            }));

            // Use api utility which adds auth header
            const response = await api.post('/submit-form', submitData, {
                headers: { 'Content-Type': 'multipart/form-data' } // api util handles general headers but FormData needs browser to set boundary? 
                // Creating axios instance sets Content-Type: application/json. We need to override or let axios handle it.
                // Axios usually handles FormData automatically if we don't force Content-Type.
                // Note: api.ts sets 'Content-Type': 'application/json'. We should unset it for FormData.
            });

            // Adjust api.ts or use overrides:
            // Actually, axios intercepts config. headers defined in create() might stick.
            // Let's rely on axios to override if we pass FormData, but if 'Content-Type' is set in instance defaults vs interceptors...
            // It's safer to delete it for this request.

            // Re-implementation with api instance:
            // api.post('/submit-form', submitData)

        } catch (e) {
            // ...
        }

        // Actually, let's fix the api call inside real code below
    };

    // Proper submit handler
    const handleSubmitToPortal = async () => {
        const pdfInput = document.getElementById('submissionPdf');
        const pdfFile = pdfInput?.files[0];
        if (!pdfFile) { alert("Please upload PDF"); return; }

        setSubmissionStatus('Initializing...');
        try {
            const fd = new FormData();
            fd.append('pdf', pdfFile);
            fd.append('data', JSON.stringify({
                form_url: formData.formLink,
                leave_start_date: formData.startDate,
                leave_end_date: formData.endDate,
                reason: formData.purpose
            }));

            // CRITICAL: Do NOT set Content-Type for FormData!
            // The browser must set it automatically with the multipart boundary
            // Setting it manually will break the upload
            const res = await api.post('/submit-form', fd);

            if (res.data.success) {
                setTaskId(res.data.task_id);
                setSubmissionStatus('Automation Running...');
                pollStatus(res.data.task_id);
            } else {
                setSubmissionStatus(`Failed: ${res.data.error || 'Unknown error'}`);
            }
        } catch (e) {
            console.error('Submission error:', e);
            const errorMsg = e.response?.data?.error || e.response?.data?.message || e.message || 'Unknown error';
            const errorDetails = e.response?.data?.details || '';
            setSubmissionStatus(`❌ Failed: ${errorMsg}${errorDetails ? ` - ${errorDetails}` : ''}`);
        }
    };

    const pollStatus = (id) => {
        const interval = setInterval(async () => {
            try {
                const res = await api.get(`/task-status/${id}`);
                const task = res.data.task;
                setSubmissionStatus(`${task.status}: ${task.message} (${task.progress}%)`);
                if (task.status === 'completed' || task.status === 'failed') clearInterval(interval);
            } catch (e) { clearInterval(interval); }
        }, 2000);
    };

    if (isLoadingProfile) return <div className="p-8 text-center">Loading Profile...</div>;

    return (
        <div className="max-w-4xl mx-auto bg-white rounded-lg shadow p-8 my-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                <FileText className="text-indigo-600" /> Outing Form Generator
            </h1>

            {/* Form Fields */}
            <div className="space-y-6">
                {/* Student Details Section */}
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <h3 className="font-bold text-blue-900 mb-3">Student Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <input name="studentName" placeholder="Student Name" value={formData.studentName} onChange={handleChange} className="border p-2 rounded" readOnly />
                        <input name="studentId" placeholder="Student ID" value={formData.studentId} onChange={handleChange} className="border p-2 rounded" readOnly />
                        <input name="program" placeholder="Program" value={formData.program} onChange={handleChange} className="border p-2 rounded" readOnly />
                        <input name="academicYear" placeholder="Academic Year" value={formData.academicYear} onChange={handleChange} className="border p-2 rounded" readOnly />
                        <input name="studentEmail" placeholder="Student Email" value={formData.studentEmail} onChange={handleChange} className="border p-2 rounded" />
                        <input name="studentMobile" placeholder="Student Mobile" value={formData.studentMobile} onChange={handleChange} className="border p-2 rounded" />
                    </div>
                </div>

                {/* Father Details Section */}
                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <h3 className="font-bold text-green-900 mb-3">Father Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <input name="fatherName" placeholder="Father Name *" value={formData.fatherName} onChange={handleChange} className="border p-2 rounded" required />
                        <input name="fatherEmail" placeholder="Father Email *" value={formData.fatherEmail} onChange={handleChange} className="border p-2 rounded" type="email" required />
                        <input name="fatherMobile" placeholder="Father Mobile *" value={formData.fatherMobile} onChange={handleChange} className="border p-2 rounded" type="tel" required />
                    </div>
                </div>

                {/* Mother Details Section */}
                <div className="bg-pink-50 p-4 rounded-lg border border-pink-200">
                    <h3 className="font-bold text-pink-900 mb-3">Mother Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <input name="motherName" placeholder="Mother Name" value={formData.motherName} onChange={handleChange} className="border p-2 rounded" />
                        <input name="motherEmail" placeholder="Mother Email" value={formData.motherEmail} onChange={handleChange} className="border p-2 rounded" type="email" />
                        <input name="motherMobile" placeholder="Mother Mobile" value={formData.motherMobile} onChange={handleChange} className="border p-2 rounded" type="tel" />
                    </div>
                </div>

                {/* Outing Details Section */}
                <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                    <h3 className="font-bold text-purple-900 mb-3">Outing Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date *</label>
                            <input name="startDate" type="date" value={formData.startDate} onChange={handleChange} className="border p-2 rounded w-full" required />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">End Date *</label>
                            <input name="endDate" type="date" value={formData.endDate} onChange={handleChange} className="border p-2 rounded w-full" required />
                        </div>
                        <div className="col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Purpose *</label>
                            <input name="purpose" placeholder="Purpose (e.g., Home Visit, Family Function)" value={formData.purpose} onChange={handleChange} className="border p-2 rounded w-full" required />
                        </div>
                    </div>
                </div>

                {/* Signature Section */}
                <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                    <h3 className="font-bold text-yellow-900 mb-3">Parent Signature</h3>
                    {signatureImage && (
                        <div className="mb-3 p-2 bg-white border rounded">
                            <img src={signatureImage} alt="Signature" className="h-16 mx-auto" />
                            <p className="text-sm text-center text-gray-600 mt-1">Signature loaded from profile</p>
                        </div>
                    )}
                    <input type="file" accept="image/*" onChange={handleSignatureUpload} className="block w-full text-sm" />
                    <p className="text-xs text-gray-600 mt-1">Upload a new signature to replace the existing one</p>
                </div>
            </div>

            <div className="border-t pt-6">
                <button onClick={generatePDF} className="bg-indigo-600 text-white px-6 py-2 rounded flex items-center gap-2 w-full justify-center mb-4">
                    <Download size={20} /> 1. Generate PDF
                </button>

                <div className="bg-green-50 p-4 rounded border border-green-200">
                    <h3 className="font-bold text-green-800 mb-2">2. Auto-Submit</h3>
                    <input type="file" id="submissionPdf" accept=".pdf" className="block w-full text-sm mb-4" />
                    <button onClick={handleSubmitToPortal} className="bg-green-600 text-white px-6 py-2 rounded flex items-center gap-2 w-full justify-center">
                        <Send size={20} /> Submit Application
                    </button>
                    {submissionStatus && <div className="mt-2 text-sm font-medium text-blue-800">{submissionStatus}</div>}
                </div>
            </div>
        </div>
    );
}
