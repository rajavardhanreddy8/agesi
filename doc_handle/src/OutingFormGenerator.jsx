import React, { useState, useEffect } from 'react';
import { Calendar, Download, FileText, Upload, Image, Brain, Loader2, Send, CheckCircle, AlertCircle } from 'lucide-react';
import * as mammoth from 'mammoth';

export default function OutingFormGenerator(props) {
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
        formLink: '' // Store form link from mail agent
    });
    const [signatureImage, setSignatureImage] = useState(null);
    const [uploadedDoc, setUploadedDoc] = useState(null);
    const [isExtracting, setIsExtracting] = useState(false);
    const [extractionStatus, setExtractionStatus] = useState('');

    // Automation State
    const [portalPassword, setPortalPassword] = useState('');
    const [submissionStatus, setSubmissionStatus] = useState('');
    const [taskId, setTaskId] = useState(null);
    const [formUrlInput, setFormUrlInput] = useState('');

    // Fetch data from Mail Agent
    useEffect(() => {
        fetch('/outing_data.json')
            .then(res => res.json())
            .then(data => {
                if (data) {
                    console.log("Loaded outing data:", data);
                    setFormData(prev => ({
                        ...prev,
                        startDate: data.start_date ? convertToInputDate(data.start_date) : prev.startDate,
                        endDate: data.end_date ? convertToInputDate(data.end_date) : prev.endDate,
                        formLink: data.form_link || ''
                    }));
                    if (data.form_link) setFormUrlInput(data.form_link);
                }
            })
            .catch(err => console.log("No auto-fill data found (outing_data.json missing or invalid).", err));
    }, []);

    const convertToInputDate = (dateStr) => {
        // Converts DD.MM.YYYY to YYYY-MM-DD
        if (!dateStr) return '';
        const parts = dateStr.split('.');
        if (parts.length === 3) {
            return `${parts[2]}-${parts[1]}-${parts[0]}`;
        }
        return dateStr;
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSignatureUpload = (e) => {
        const file = e.target.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (event) => {
                setSignatureImage(event.target.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const extractWithGroq = async (documentText) => {
        setIsExtracting(true);
        setExtractionStatus('Connecting to Groq API...');

        // In a real app, use an env variable or backend proxy. 
        const apiKey = import.meta.env.VITE_GROQ_API_KEY;

        if (!apiKey) {
            setExtractionStatus("Error: VITE_GROQ_API_KEY not set in .env");
            setIsExtracting(false);
            return;
        }

        try {
            const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: 'llama-3.3-70b-versatile',
                    messages: [
                        {
                            role: "system",
                            content: "You are a helpful assistant that extracts JSON data from documents."
                        },
                        {
                            role: "user",
                            content: `Extract the following information from this outing form document. Return ONLY a valid JSON object with these exact fields, no additional text:

{
  "studentName": "full student name",
  "studentId": "student ID number",
  "program": "program/course name (e.g., Btech CSE)",
  "academicYear": "academic year (e.g., 2025)",
  "fatherName": "father's full name",
  "fatherEmail": "father's email",
  "fatherMobile": "father's mobile number (10 digits)",
  "motherName": "mother's full name", 
  "motherEmail": "mother's email",
  "motherMobile": "mother's mobile number (10 digits)",
  "studentEmail": "student's email",
  "studentMobile": "student's mobile number (10 digits)",
  "purpose": "purpose of outing (e.g., home)"
}

If any field is not found, use empty string "".

Document text:
${documentText}

Return only the JSON object:`
                        }
                    ],
                    temperature: 0.1
                })
            });

            if (!response.ok) {
                throw new Error(`Groq API Error: ${response.statusText}`);
            }

            setExtractionStatus('Processing with AI...');
            const data = await response.json();
            const extractedText = data.choices[0].message.content;

            // Parse JSON from LLM response
            const jsonMatch = extractedText.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                const extractedData = JSON.parse(jsonMatch[0]);

                setFormData(prev => ({
                    ...prev,
                    studentName: extractedData.studentName || prev.studentName,
                    studentId: extractedData.studentId || prev.studentId,
                    program: extractedData.program || prev.program,
                    academicYear: extractedData.academicYear || prev.academicYear,
                    fatherName: extractedData.fatherName || prev.fatherName,
                    fatherEmail: extractedData.fatherEmail || prev.fatherEmail,
                    fatherMobile: extractedData.fatherMobile || prev.fatherMobile,
                    motherName: extractedData.motherName || prev.motherName,
                    motherEmail: extractedData.motherEmail || prev.motherEmail,
                    motherMobile: extractedData.motherMobile || prev.motherMobile,
                    studentEmail: extractedData.studentEmail || prev.studentEmail,
                    studentMobile: extractedData.studentMobile || prev.studentMobile,
                    purpose: extractedData.purpose || prev.purpose,
                }));

                setExtractionStatus('✓ Successfully extracted information!');
            } else {
                throw new Error('Could not parse LLM response');
            }
        } catch (error) {
            console.error('LLM extraction error:', error);
            setExtractionStatus(`Error: ${error.message}`);
        } finally {
            setIsExtracting(false);
        }
    };

    // Refactored to separate logic from event handler
    const processDocumentObj = async (arrayBuffer) => {
        setExtractionStatus('Reading document...');
        try {
            // Extract signature image
            const htmlResult = await mammoth.convertToHtml({ arrayBuffer: arrayBuffer });
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlResult.value, 'text/html');
            const images = doc.querySelectorAll('img');

            if (images.length > 0) {
                const signatureImg = images[images.length - 1]; // Assuming last image is signature
                if (signatureImg && signatureImg.src) {
                    setSignatureImage(signatureImg.src);
                }
            }

            // Extract text and use LLM
            const result = await mammoth.extractRawText({ arrayBuffer });
            const text = result.value;

            // Use AI to extract information
            await extractWithGroq(text);

        } catch (error) {
            console.error('Error parsing document:', error);
            setExtractionStatus('Error reading document');
        }
    };

    const handleDocUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploadedDoc(file.name);
        const arrayBuffer = await file.arrayBuffer();
        await processDocumentObj(arrayBuffer);
    };



    const generatePDF = () => {
        const printWindow = window.open('', '', 'height=900,width=800');

        // ... (HTML content same as before, simplified for brevity in this rewrite context)
        // IMPORTANT: In overwrite, I must preserve this.

        const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Outing Form</title>
        <style>
          @media print { body { margin: 0; } .no-print { display: none; } }
          body { font-family: 'Times New Roman', serif; padding: 40px 60px; max-width: 800px; margin: 0 auto; line-height: 1.6; }
          h1 { text-align: center; font-size: 18px; margin: 20px 0; text-decoration: underline; }
          .content { margin: 20px 0; text-align: justify; }
          .indent { margin-left: 40px; margin-bottom: 15px; }
          .underline { text-decoration: underline; font-weight: bold; }
          ol { margin-left: 20px; }
          li { margin: 10px 0; }
          .signature-section { margin-top: 30px; display: flex; justify-content: space-between; align-items: flex-end; }
          .signature-img { max-width: 150px; max-height: 50px; margin-bottom: 5px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          td { border: 1px solid #000; padding: 8px; font-size: 14px; }
          .bold { font-weight: bold; }
          button { background: #4CAF50; color: white; border: none; padding: 12px 24px; font-size: 16px; cursor: pointer; border-radius: 5px; margin: 20px auto; display: block; }
          button:hover { background: #45a049; }
        </style>
      </head>
      <body>
        <h1>Undertaking by Parents</h1>
        <div class="content indent">
          I hereby confirm that my ward Mr./Ms. <span class="underline">${formData.studentName}</span>
          bearing the student ID <span class="underline">${formData.studentId}</span> of 
          <span class="underline">${formData.program}</span> program registered for
          the A. Y <span class="underline">${formData.academicYear}</span>
        </div>
        <h1>Letter of Consent:</h1>
        <div class="content indent">
          I, <span class="underline">${formData.relation}</span>, of the student, request you to permit 
          <span class="bold">my ${formData.gender}</span> to leave the campus 
          <span class="bold">on date ${formData.startDate ? formData.startDate.split('-').reverse().join('.') : ''}</span> 
          <span class="bold">and time ${formData.startTime}</span> for the purpose of 
          <span class="underline">${formData.purpose}</span>. My <span class="bold">${formData.gender}</span> 
          shall return on the <span class="bold">date ${formData.endDate ? formData.endDate.split('-').reverse().join('.') : ''}</span> 
          <span class="bold">and time ${formData.endTime}</span>. (Signature below)
        </div>
        <div class="content indent" style="font-style: italic; font-size: 14px;">
          Outing & leave are permitted only during university leave declared for festivals, national holidays, and weekends.
        </div>
        <h1>The Parents/Guardian confirms the following,</h1>
        <ol>
          <li>I assure you that it is my responsibility for my ward during the outgoings and have been informed of the same by the university officials.</li>
          <li>I firmly insist my ward not to deviate from the campus policy and adhere to the rules and regulations meticulously.</li>
        </ol>
        <div class="signature-section">
          <div><span class="bold">Date:</span> ${formData.todayDate ? formData.todayDate.split('-').reverse().join('.') : ''}</div>
          <div style="text-align: center;">
            ${signatureImage ? `<img src="${signatureImage}" class="signature-img" alt="Signature" />` : '<div style="height: 50px;"></div>'}
            <div class="bold">Parents Signature</div>
          </div>
        </div>
        <table>
          <tr><td class="bold">Father Name, Email & Mobile Number</td><td>${formData.fatherName}</td><td>${formData.fatherEmail}</td><td>${formData.fatherMobile}</td></tr>
          <tr><td class="bold">Mother Name, Email & Mobile Number</td><td>${formData.motherName}</td><td>${formData.motherEmail}</td><td>${formData.motherMobile}</td></tr>
          <tr><td class="bold">Student Name, Email & Mobile Number</td><td>${formData.studentName}</td><td>${formData.studentEmail}</td><td>${formData.studentMobile}</td></tr>
        </table>
        <button class="no-print" onclick="window.print()">Print / Save as PDF</button>
      </body>
      </html>
    `;
        printWindow.document.write(htmlContent);
        printWindow.document.close();
    };

    const isFormValid = () => {
        return formData.studentName && formData.startDate && formData.endDate;
    };

    // --- AUTOMATION SUBMISSION LOGIC ---
    const handleSubmitToPortal = async () => {
        if (!portalPassword) {
            alert("Please enter your Microsoft Portal Password to automate the submission.");
            return;
        }

        const pdfInput = document.getElementById('submissionPdf');
        const pdfFile = pdfInput?.files[0];
        if (!pdfFile) {
            alert("Please upload the PDF you just generated (to verify and submit).");
            return;
        }

        setSubmissionStatus('Preparing submission...');

        try {
            const formDataToSend = new FormData();
            formDataToSend.append('pdf', pdfFile);

            const automationData = {
                form_url: formUrlInput || "https://forms.office.com/Pages/ResponsePage.aspx?id=LSD36rPvekOhA1Bbufv3X9NSKOayoK9NtQfVOU9-8dhUNTVLNjhLSDZYMUlRVUNOMEc1MDQ0WFNDTS4u",
                email: formData.studentEmail,
                password: portalPassword,
                form_data: {
                    student_name: formData.studentName,
                    roll_number: formData.studentId,
                    school: 'School of Technology', // TODO: Add to UI or extract
                    academic_session: formData.academicYear ? `${formData.academicYear}-${parseInt(formData.academicYear) + 4}` : '2024-2028',
                    programme: formData.program,
                    specialization: 'CSE', // TODO: Add to UI
                    reason: formData.purpose,
                    leave_start_date: formData.startDate ? new Date(formData.startDate).toLocaleDateString('en-US') : '',
                    leave_end_date: formData.endDate ? new Date(formData.endDate).toLocaleDateString('en-US') : '',
                    student_email: formData.studentEmail,
                    student_phone: formData.studentMobile,
                    parent_email: formData.fatherEmail,
                    parent_phone: formData.fatherMobile
                }
            };

            formDataToSend.append('data', JSON.stringify(automationData));

            setSubmissionStatus('Sending to Automation Agent...');

            // Use the centralized API utility or env var
            // const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://outing-backend-api.azurewebsites.net';

            const response = await fetch('https://outing-backend-api.azurewebsites.net/api/submit-form', {
                method: 'POST',
                body: formDataToSend
            });

            const result = await response.json();

            if (result.success) {
                setTaskId(result.task_id);
                setSubmissionStatus(`Automation started! Task ID: ${result.task_id}. Please wait...`);
                pollStatus(result.task_id);
            } else {
                setSubmissionStatus(`Error: ${result.error}`);
            }

        } catch (e) {
            console.error(e);
            setSubmissionStatus(`Request failed: ${e.message}. Is Flask API running?`);
        }
    };

    const pollStatus = (id) => {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`https://outing-backend-api.azurewebsites.net/api/task-status/${id}`);
                const data = await res.json();
                if (data.success) {
                    const task = data.task;
                    setSubmissionStatus(`Status: ${task.status} - ${task.message} (${task.progress}%)`);

                    if (task.status === 'completed' || task.status === 'failed') {
                        clearInterval(interval);
                        if (task.status === 'completed') alert("Form Submitted Successfully!");
                    }
                }
            } catch (e) {
                console.error("Polling error", e);
            }
        }, 2000);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
            <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-xl p-8">
                <div className="flex items-center gap-3 mb-6">
                    <FileText className="w-8 h-8 text-indigo-600" />
                    <h1 className="text-3xl font-bold text-gray-800">AI-Powered Outing Form Generator</h1>
                </div>

                {/* ... Groq status ... */}
                <div className="mb-6 p-4 bg-orange-50 border-l-4 border-orange-500 rounded">
                    <div className="flex items-start gap-2">
                        <Brain className="w-5 h-5 text-orange-600 mt-0.5" />
                        <div>
                            <p className="text-sm font-semibold text-orange-900">Groq AI Extraction Enabled</p>
                        </div>
                    </div>
                </div>

                {/* Upload Section ... */}
                <div className="mb-8 p-6 bg-indigo-50 rounded-lg border-2 border-dashed border-indigo-300">
                    <div className="flex items-center gap-2 mb-3">
                        <Upload className="w-5 h-5 text-indigo-600" />
                        <h2 className="text-lg font-semibold text-gray-800">Upload Previous Outing Form</h2>
                    </div>
                    <input type="file" accept=".docx" onChange={handleDocUpload} disabled={isExtracting} className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 cursor-pointer disabled:opacity-50" />
                    {/* ... */}
                </div>

                {/* Signature Upload ... */}
                <div className="mb-8 p-6 bg-purple-50 rounded-lg border-2 border-dashed border-purple-300">
                    <div className="flex items-center gap-2 mb-3">
                        <Image className="w-5 h-5 text-purple-600" />
                        <h2 className="text-lg font-semibold text-gray-800">Signature Image</h2>
                    </div>
                    <input type="file" accept="image/*" onChange={handleSignatureUpload} className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700 cursor-pointer" />
                    {/* ... */}
                </div>

                {/* Forms ... */}
                <div className="space-y-6">
                    <div className="border-b pb-4">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">Student Information</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Inputs */}
                            <input type="text" name="studentName" value={formData.studentName} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Student Name" />
                            <input type="text" name="studentId" value={formData.studentId} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Student ID" />
                            <input type="text" name="program" value={formData.program} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Program" />
                            <input type="text" name="academicYear" value={formData.academicYear} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Academic Year" />
                            <input type="email" name="studentEmail" value={formData.studentEmail} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Student Email" />
                            <input type="tel" name="studentMobile" value={formData.studentMobile} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Student Mobile" />
                        </div>
                    </div>

                    {/* Outing Details */}
                    <div className="border-b pb-4">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">Outing Details</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <select name="relation" value={formData.relation} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg"><option value="father">Father</option><option value="mother">Mother</option><option value="guardian">Guardian</option></select>
                            <select name="gender" value={formData.gender} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg"><option value="son">Son</option><option value="daughter">Daughter</option></select>
                            <input type="date" name="startDate" value={formData.startDate} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" />
                            <input type="time" name="startTime" value={formData.startTime} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" />
                            <input type="date" name="endDate" value={formData.endDate} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" />
                            <input type="time" name="endTime" value={formData.endTime} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" />
                            <div className="md:col-span-2"><input type="text" name="purpose" value={formData.purpose} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Purpose" /></div>
                            <input type="date" name="todayDate" value={formData.todayDate} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" />
                        </div>
                    </div>
                    {/* Parent Info */}
                    <div>
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">Parent Information</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <input type="text" name="fatherName" value={formData.fatherName} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Father Name" />
                            <input type="email" name="fatherEmail" value={formData.fatherEmail} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Father Email" />
                            <input type="tel" name="fatherMobile" value={formData.fatherMobile} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Father Mobile" />
                            <input type="text" name="motherName" value={formData.motherName} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Mother Name" />
                            <input type="email" name="motherEmail" value={formData.motherEmail} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Mother Email" />
                            <input type="tel" name="motherMobile" value={formData.motherMobile} onChange={handleChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Mother Mobile" />
                        </div>
                    </div>

                    {/* ACTIONS */}
                    <div className="flex flex-col gap-4 mt-8 border-t pt-6">
                        {/* 1. Generate PDF */}
                        <button
                            onClick={generatePDF}
                            disabled={!isFormValid()}
                            className={`w-full flex items-center justify-center gap-2 py-3 px-6 rounded-lg font-semibold text-white transition-all ${isFormValid() ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-gray-400 cursor-not-allowed'
                                }`}
                        >
                            <Download className="w-5 h-5" />
                            1. Generate & Save PDF
                        </button>

                        {/* Automation Section */}
                        <div className="bg-green-50 p-6 rounded-lg border border-green-200 mt-4">
                            <h3 className="text-xl font-bold text-green-800 mb-4 flex items-center gap-2">
                                <Send className="w-6 h-6" />
                                2. Submit to Portal (Automation)
                            </h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-1">Microsoft Portal Password</label>
                                    <input
                                        type="password"
                                        value={portalPassword}
                                        onChange={(e) => setPortalPassword(e.target.value)}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-white"
                                        placeholder="Enter password"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-1">Target Form URL</label>
                                    <input
                                        type="text"
                                        value={formUrlInput}
                                        onChange={(e) => setFormUrlInput(e.target.value)}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-white text-xs text-gray-500"
                                        placeholder="Form URL"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-1">Upload Generated PDF</label>
                                    <input
                                        type="file"
                                        id="submissionPdf"
                                        accept=".pdf"
                                        className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-green-600 file:text-white hover:file:bg-green-700 cursor-pointer"
                                    />
                                    <p className="text-xs text-gray-500 mt-1">Please select the PDF you just saved in step 1.</p>
                                </div>

                                <div className="bg-white p-3 rounded border border-gray-200 text-sm">
                                    <p className="font-semibold text-gray-700 mb-1">Verifying Data to Submit:</p>
                                    <ul className="text-gray-600 space-y-1 text-xs">
                                        <li>• Name: {formData.studentName || "(Empty)"}</li>
                                        <li>• Roll: {formData.studentId || "(Empty)"}</li>
                                        <li>• School: {formData.school}</li>
                                        <li>• Dates: {formData.startDate} to {formData.endDate}</li>
                                    </ul>
                                </div>

                                <button
                                    onClick={handleSubmitToPortal}
                                    disabled={!portalPassword}
                                    className={`w-full flex items-center justify-center gap-2 py-3 px-6 rounded-lg font-semibold text-white transition-all ${portalPassword ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-400 cursor-not-allowed'
                                        }`}
                                >
                                    <Send className="w-5 h-5" />
                                    Auto-Fill Form & Upload PDF
                                </button>

                                {submissionStatus && (
                                    <div className={`p-3 rounded text-sm font-medium flex items-center gap-2 ${submissionStatus.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>
                                        {submissionStatus.includes('Error') ? <AlertCircle className="w-4 h-4" /> : <Loader2 className="w-4 h-4 animate-spin" />}
                                        {submissionStatus}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
