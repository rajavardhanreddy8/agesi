import * as mammoth from 'mammoth';

export const extractRegistrationData = async (file) => {
    try {
        // 1. Convert DOCX to Raw Text
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        const text = result.value;

        if (!text || text.trim().length === 0) {
            throw new Error("Document appears to be empty or unreadable.");
        }

        if (text.length < 50) {
            console.warn("Extracted text is very short. Document might be a scanned image.");
            // We continue anyway, but it's likely searching will fail.
        }

        // 2. Call Groq API (optional - falls back to basic extraction if key missing)
        const apiKey = import.meta.env.VITE_GROQ_API_KEY;

        let extractedData = {};

        if (!apiKey) {
            console.warn('VITE_GROQ_API_KEY not found, using basic regex extraction instead of AI');

            // Basic regex extraction as fallback
            extractedData = {
                fullName: text.match(/Name[:\s]+([A-Za-z\s]+)/i)?.[1]?.trim() || '',
                rollNumber: text.match(/Roll\s*No\.?[:\s]+([A-Z0-9]+)/i)?.[1]?.trim() || '',
                school: text.match(/School[:\s]+([A-Za-z\s]+)/i)?.[1]?.trim() || '',
                programme: text.match(/Programme[:\s]+([A-Za-z.\s]+)/i)?.[1]?.trim() || '',
                academicYear: text.match(/Academic\s*Year[:\s]+(\d{4}-\d{4})/i)?.[1]?.trim() || '',
                specialization: text.match(/Specialization[:\s]+([A-Za-z\s&]+)/i)?.[1]?.trim() || '',
                studentPhone: text.match(/Student.*Phone[:\s]+(\d{10})/i)?.[1]?.trim() || '',
                studentEmail: text.match(/Student.*Email[:\s]+([^\s@]+@[^\s@]+\.[^\s@]+)/i)?.[1]?.trim() || '',
                fatherName: text.match(/(?:Father|Parent 1).*Name[:\s]+([A-Za-z\s]+)/i)?.[1]?.trim() || '',
                fatherEmail: text.match(/(?:Father|Parent 1).*Email[:\s]+([^\s@]+@[^\s@]+\.[^\s@]+)/i)?.[1]?.trim() || '',
                fatherPhone: text.match(/(?:Father|Parent 1).*Phone[:\s]+(\d{10})/i)?.[1]?.trim() || '',
                motherName: text.match(/(?:Mother|Parent 2).*Name[:\s]+([A-Za-z\s]+)/i)?.[1]?.trim() || '',
                motherEmail: text.match(/(?:Mother|Parent 2).*Email[:\s]+([^\s@]+@[^\s@]+\.[^\s@]+)/i)?.[1]?.trim() || '',
                motherPhone: text.match(/(?:Mother|Parent 2).*Phone[:\s]+(\d{10})/i)?.[1]?.trim() || ''
            };
        } else {
            // Use AI extraction if API key is available
            const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: 'llama-3.3-70b-versatile',
                    response_format: { type: "json_object" }, // FORCE VALID JSON
                    messages: [
                        {
                            role: "system",
                            content: "You are a data extraction assistant. Extract student registration details from the document text. Output must be valid JSON."
                        },
                        {
                            role: "user",
                            content: `Extract the following details from the text below and return ONLY valid JSON.
            
            Fields to extract:
            - fullName (Student's full name)
            - rollNumber (Student ID/Roll No)
            - school (School Name)
            - programme (Degree program e.g. B.Tech, BBA)
            - academicYear (e.g. 2024-2028)
            - specialization (Branch/Stream e.g. CSE)
            - studentPhone (10-digit mobile)
            - studentEmail (Email address)
            
            PARENT DETAILS:
            - fatherName (Father/Guardian Name)
            - fatherEmail (Father/Guardian Email)
            - fatherPhone (Father/Guardian Phone)
            - motherName (Mother/Guardian Name)
            - motherEmail (Mother/Guardian Email)
            - motherPhone (Mother/Guardian Phone)
            
            INSTRUCTIONS:
            1. If table format is broken, look for proximity. e.g. "Name: John" near "Father" implies Father Name.
            2. Infer relationships: "Mr. X" is likely Father, "Mrs. Y" is likely Mother.
            3. "Parent 1" = Father, "Parent 2" = Mother.
            4. If a field is missing, use empty string "".
            
            Text Content:
            ${text.substring(0, 15000)} 
            
            JSON:`
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

            const data = await response.json();
            const content = data.choices[0].message.content;
            console.log("AI Raw Response:", content); // Debug log (check console)

            extractedData = JSON.parse(content);
        }

        // 3. Extract signature image from document
        try {
            const htmlResult = await mammoth.convertToHtml({ arrayBuffer });
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlResult.value, 'text/html');
            const images = doc.querySelectorAll('img');

            // Find the last image (usually the signature at the bottom)
            if (images.length > 0) {
                const lastImage = images[images.length - 1];
                const signatureSrc = lastImage.getAttribute('src');
                if (signatureSrc && signatureSrc.startsWith('data:image')) {
                    extractedData.signatureData = signatureSrc;
                    console.log('Signature extracted from document');
                }
            }
        } catch (imgErr) {
            console.warn('Could not extract signature image:', imgErr);
        }

        return extractedData;

    } catch (error) {
        console.error("Extraction error:", error);
        throw error;
    }
};
