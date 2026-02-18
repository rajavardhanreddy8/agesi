import * as mammoth from 'mammoth';

// Standardized list of programmes to match the dropdown in RegisterForm
const STANDARD_PROGRAMMES = [
    "B.Tech", "BBA", "BCom", "B.Sc", "B.Des", "B.Arch", "Integrated MBA", "Integrated BBA-MBA", "MBA", "MBA (BA/AI/ML)", "MBA (Financial Services)"
];

const normalizeProgramme = (extractedProgramme) => {
    if (!extractedProgramme) return '';

    const normalized = extractedProgramme.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();

    // Specific check for B.Tech variations first to avoid BBA confusion
    if (normalized.includes('btech') || normalized.includes('technology') || normalized.includes('engineering')) {
        return "B.Tech";
    }

    // Check for BBA but ensure it's not part of MBBA or BBA-LLB if they exist as separate options
    if (normalized === 'bba' || normalized === 'bachelorsinbusinessadministration') {
        // Double check against standard list logic below
    }

    // Exact or fuzzy matching logic
    const match = STANDARD_PROGRAMMES.find(prog => {
        const progNormalized = prog.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
        // Strict equality for short acronyms to avoid partial matching (e.g. BBA inside MBBA)
        if (progNormalized.length < 4) {
            return normalized === progNormalized;
        }
        return normalized.includes(progNormalized) || progNormalized.includes(normalized);
    });

    return match || extractedProgramme; // Return match if found, else original (user can fix)
};

export const extractRegistrationData = async (file) => {
    try {
        // 1. Convert DOCX to Raw Text
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        const text = result.value;

        if (!text || text.trim().length === 0) {
            throw new Error("Document appears to be empty or unreadable.");
        }

        console.log("Raw Extracted Text (First 200 chars):", text.substring(0, 200));

        let extractedData = {};
        const apiKey = import.meta.env.VITE_GROQ_API_KEY;

        // 2. AI Extraction (Preferred)
        if (apiKey) {
            console.log('Using AI Model for Extraction...');

            try {
                const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${apiKey}`
                    },
                    body: JSON.stringify({
                        model: 'llama-3.3-70b-versatile',
                        response_format: { type: "json_object" },
                        messages: [
                            {
                                role: "system",
                                content: `You are an expert data extraction assistant. Your ONLY job is to extract student registration details from messy document text.
                                
                                CRITICAL: You must extract the following fields. If a field is not explicitly labeled, infer it from the context.
                                
                                Return a valid JSON object with these exact keys:
                                - fullName (Student Name)
                                - rollNumber (Roll No / ID No / Registration No)
                                - email (Student's College Email - prefer .woxsen.edu.in if available, otherwise personal)
                                - phone (Student's Contact Number)
                                - school (School Name e.g., School of Technology, School of Business)
                                - programme (Course Name e.g., B.Tech, BBA, MBA, B.Des, B.Arch, B.Sc)
                                - specialization (Branch / Specialization e.g., CSE, AI&DS, Marketing)
                                - academicYear (Year of Study e.g., 2023-2024)
                                
                                PARENT DETAILS (Crucial):
                                - fatherName (Father's Name)
                                - fatherPhone (Father's Phone Number)
                                - fatherEmail (Father's Email ID)
                                - motherName (Mother's Name)
                                - motherPhone (Mother's Phone Number)
                                - motherEmail (Mother's Email ID)

                                If a specific parent field (like email) is missing, return an empty string "". Do not make up data.
                                `
                            },
                            {
                                role: "user",
                                content: `Extract data from the following text:\n\n${text}\n\nReturn JSON only:`
                            }
                        ],
                        temperature: 0.1
                    })
                });

                if (!response.ok) {
                    const errData = await response.json().catch(() => ({}));
                    console.error("Groq API Error:", errData);
                    throw new Error(`AI Extraction failed: ${response.statusText}`);
                }

                const jsonResponse = await response.json();
                const aiContent = jsonResponse.choices[0]?.message?.content;

                console.log("AI Raw Response:", aiContent);

                if (aiContent) {
                    const parsedData = JSON.parse(aiContent);
                    extractedData = {
                        fullName: parsedData.fullName || '',
                        rollNumber: parsedData.rollNumber || '',
                        studentEmail: parsedData.email || '', // Mapped to studentEmail
                        studentPhone: parsedData.phone || '', // Mapped to studentPhone
                        school: parsedData.school || '',
                        programme: normalizeProgramme(parsedData.programme),
                        specialization: parsedData.specialization || '',
                        academicYear: parsedData.academicYear || '',
                        fatherName: parsedData.fatherName || '',
                        fatherPhone: parsedData.fatherPhone || '',
                        fatherEmail: parsedData.fatherEmail || '',
                        motherName: parsedData.motherName || '',
                        motherPhone: parsedData.motherPhone || '',
                        motherEmail: parsedData.motherEmail || ''
                    };
                }
            } catch (aiError) {
                console.warn("AI extraction failed, falling back to regex...", aiError);
                // Fallback continues below
            }
        } else {
            console.warn("VITE_GROQ_API_KEY is missing. Using Regex fallback.");
        }

        // 3. Regex Fallback (If AI failed or key missing)
        // Only run if extractedData is empty (meaning AI path wasn't taken or failed)
        if (Object.keys(extractedData).length === 0) {
            console.log("Running Regex Extraction...");
            // More robust regex patterns
            const findMatch = (patterns) => {
                for (const pattern of patterns) {
                    const match = text.match(pattern);
                    if (match && match[1]) return match[1].trim();
                }
                return '';
            };

            extractedData = {
                fullName: findMatch([/Name\s*[:\-]?\s*([^\n\r]+)/i, /Student Name\s*[:\-]?\s*([^\n\r]+)/i]),
                rollNumber: findMatch([/Roll\s*No\.?\s*[:\-]?\s*([A-Z0-9]+)/i, /ID\s*No\.?\s*[:\-]?\s*([A-Z0-9]+)/i]),
                // Prioritize woxsen.edu.in email
                studentEmail: findMatch([/Email\s*ID\s*[:\-]?\s*([a-zA-Z0-9._%+-]+@woxsen\.edu\.in)/i, /Email\s*ID\s*[:\-]?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i]),
                studentPhone: findMatch([/Phone\s*(?:No\.?)?\s*[:\-]?\s*([0-9+\-\s]{10,})/i, /Contact\s*(?:No\.?)?\s*([0-9+\-\s]{10,})/i]),
                programme: normalizeProgramme(findMatch([/Programme\s*[:\-]?\s*([^\n\r]+)/i, /Course\s*[:\-]?\s*([^\n\r]+)/i])),

                specialization: findMatch([/Specialization\s*[:\-]?\s*([^\n\r]+)/i, /Branch\s*[:\-]?\s*([^\n\r]+)/i]),
                academicYear: findMatch([/Academic\s*Year\s*[:\-]?\s*([0-9\-]+)/i]),
                // Basic Parent extraction via Regex is hard due to multiple parents, but we try
                fatherName: findMatch([/Father(?:'s)?\s*Name\s*[:\-]?\s*([^\n\r]+)/i]),
                motherName: findMatch([/Mother(?:'s)?\s*Name\s*[:\-]?\s*([^\n\r]+)/i])
            };
        }

        // 4. Image/Signature Extraction (Original Logic Preserved)
        try {
            const htmlResult = await mammoth.convertToHtml({ arrayBuffer });
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlResult.value, 'text/html');
            const images = doc.querySelectorAll('img');

            if (images.length > 0) {
                // Heuristic: The signature is often the LAST image in the document
                const lastImage = images[images.length - 1];
                const signatureSrc = lastImage.getAttribute('src');

                if (signatureSrc && signatureSrc.startsWith('data:image')) {
                    extractedData.signatureData = signatureSrc;
                    console.log('Signature extracted from document');
                }
            }
        } catch (imgError) {
            console.warn("Signature extraction failed:", imgError);
        }

        return extractedData;

    } catch (error) {
        console.error("Extraction error:", error);
        throw error;
    }
};
