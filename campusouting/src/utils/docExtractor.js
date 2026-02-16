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

        // 2. Call Groq API (optional - falls back to basic extraction if key missing)
        const apiKey = import.meta.env.VITE_GROQ_API_KEY;

        let extractedData = {};

        if (!apiKey) {
            console.warn('VITE_GROQ_API_KEY not found, using basic regex extraction instead of AI');
            console.log('📄 Document text preview:', text.substring(0, 500)); // Debug

            // Improved regex extraction with multiple pattern attempts
            extractedData = {
                fullName: (
                    text.match(/(?:Student\s*)?Name[:\s-]*([A-Za-z\s.]+?)(?:\n|Roll|Student)/i)?.[1]?.trim() ||
                    text.match(/Name[:\s]+([A-Za-z\s.]+)/i)?.[1]?.trim() ||
                    ''
                ),
                rollNumber: (
                    text.match(/(?:Roll\s*(?:Number|No\.?|ID)|Student\s*ID)[:\s-]*([A-Z0-9]+)/i)?.[1]?.trim() ||
                    text.match(/\b(\d{2}WU\d{7})\b/i)?.[1]?.trim() ||
                    ''
                ),
                school: (
                    text.match(/School[:\s-]*([A-Za-z\s&,]+?)(?:\n|Programme|Academic)/i)?.[1]?.trim() ||
                    ''
                ),
                programme: (
                    text.match(/Programme[:\s-]*([A-Za-z.\s]+?)(?:\n|Specialization|Year)/i)?.[1]?.trim() ||
                    text.match(/\b(B\.Tech|BBA|BCom|B\.\s?Arch|B\.Des|BA\s?LLB|BBA\s?LLB|B\.A\.|B\.Sc\.|BCA|MBBA)\b/i)?.[1]?.trim() ||
                    ''
                ),
                academicYear: (
                    text.match(/(?:Academic\s*Year|Session|Year)[:\s-]*(\d{4}\s*-\s*\d{4})/i)?.[1]?.replace(/\s/g, '') ||
                    ''
                ),
                specialization: (
                    text.match(/(?:Specialization|Branch|Stream|Department)[:\s-]*([A-Za-z\s&,]+?)(?:\n|Phone|Email|Parent|Father|Mother)/i)?.[1]?.trim() ||
                    ''
                ),
                studentPhone: (
                    text.match(/(?:Student\s*)?(?:Phone|Mobile|Contact)[:\s-]*(\d{10})/i)?.[1]?.trim() ||
                    text.match(/\b(\d{10})\b/)?.[1]?.trim() ||
                    ''
                ),
                studentEmail: (
                    text.match(/(?:Student\s*)?Email[:\s-]*([^\s@]+@[^\s@]+\.[^\s@]+)/i)?.[1]?.trim() ||
                    text.match(/([^\s@]+@woxsen\.edu\.in)/i)?.[1]?.trim() ||
                    ''
                ),
                fatherName: (
                    text.match(/Father['`']?s?\s*Name[:\s-]*([A-Za-z\s.]+?)(?:\n|Email|Phone|Mother)/i)?.[1]?.trim() ||
                    ''
                ),
                fatherEmail: (
                    text.match(/Father['`']?s?\s*Email[:\s-]*([^\s@]+@[^\s@]+\.[^\s@]+)/i)?.[1]?.trim() ||
                    ''
                ),
                fatherPhone: (
                    text.match(/Father['`']?s?\s*(?:Phone|Mobile|Contact)[:\s-]*(\d{10})/i)?.[1]?.trim() ||
                    ''
                ),
                motherName: (
                    text.match(/Mother['`']?s?\s*Name[:\s-]*([A-Za-z\s.]+?)(?:\n|Email|Phone|Father|Signature)/i)?.[1]?.trim() ||
                    ''
                ),
                motherEmail: (
                    text.match(/Mother['`']?s?\s*Email[:\s-]*([^\s@]+@[^\s@]+\.[^\s@]+)/i)?.[1]?.trim() ||
                    ''
                ),
                motherPhone: (
                    text.match(/Mother['`']?s?\s*(?:Phone|Mobile|Contact)[:\s-]*(\d{10})/i)?.[1]?.trim() ||
                    ''
                )
            };

            console.log('✅ Extracted data:', extractedData); // Debug
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

            extractedData = JSON.parse(jsonMatch[0]);
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
