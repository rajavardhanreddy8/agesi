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

        // 2. Call Groq API
        const apiKey = import.meta.env.VITE_GROQ_API_KEY;
        if (!apiKey) {
            throw new Error("VITE_GROQ_API_KEY is missing in environment variables.");
        }

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
                        content: "You are a data extraction assistant. Extract student registration details from the document text."
                    },
                    {
                        role: "user",
                        content: `Extract the following details from the text below and return ONLY valid JSON.
            
            Fields to extract:
            - fullName (Student Name)
            - rollNumber (Student ID/Roll No)
            - school (School Name, e.g. School of Technology)
            - programme (e.g. B.Tech, BBA)
            - academicYear (e.g. 2024-2028)
            - specialization (e.g. CSE)
            - studentPhone
            - studentEmail
            - fatherName (Father's Name)
            - fatherEmail (Father's Email)
            - fatherPhone (Father's Phone)
            - motherName (Mother's Name)
            - motherEmail (Mother's Email)
            - motherPhone (Mother's Phone)

            If a field is not found, use empty string "".
            
            Text:
            ${text}
            
            JSON:`
                    }
                ],
                temperature: 0.1
            })
        });

        if (!response.ok) {
            throw new Error(`AI Extraction failed: ${response.statusText}`);
        }

        const data = await response.json();
        const content = data.choices[0].message.content;

        // Parse JSON
        const jsonMatch = content.match(/\{[\s\S]*\}/);
        if (!jsonMatch) {
            throw new Error("Could not parse AI response.");
        }

        const extractedData = JSON.parse(jsonMatch[0]);

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
