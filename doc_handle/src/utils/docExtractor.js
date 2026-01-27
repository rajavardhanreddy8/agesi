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
            - parent1Name (Father/Guardian Name)
            - parent1Email
            - parent1Phone
            - parent2Name (Mother Name - optional)
            - parent2Email
            - parent2Phone

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

        return JSON.parse(jsonMatch[0]);

    } catch (error) {
        console.error("Extraction error:", error);
        throw error;
    }
};
