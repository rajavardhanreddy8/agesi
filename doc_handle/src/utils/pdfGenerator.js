
export const generateOutingPDF = (data) => {
    const {
        studentName, studentId, program, academicYear,
        startDate, startTime, endDate, endTime, purpose,
        todayDate,
        fatherName, fatherEmail, fatherMobile,
        motherName, motherEmail, motherMobile,
        studentEmail, studentMobile,
        signatureImage
    } = data;

    const formatDate = (dateStr) => {
        if (!dateStr) return '___/___/______';
        const parts = dateStr.split('-'); // YYYY-MM-DD
        if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        return dateStr;
    };

    // Default times if not provided
    const sTime = startTime || '17:30';
    const eTime = endTime || '08:30';

    const printWindow = window.open('', '', 'height=900,width=800');
    if (!printWindow) {
        alert('Please allow popups to generate the PDF');
        return;
    }

    const htmlContent = `
  <!DOCTYPE html><html><head><title>Outing Form - ${studentName || 'Student'}</title>
  <style>
      @media print { 
          body { margin: 0; } 
          .no-print { display: none; } 
          * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
      }
      body { font-family: 'Times New Roman', serif; padding: 40px; max-width: 800px; margin: 0 auto; color: #000; line-height: 1.5; font-size: 14pt; }
      
      /* Utility classes */
      .bold { font-weight: bold; }
      .center { text-align: center; }
      .underline { text-decoration: underline; }
      
      /* Layout Tables */
      table.main-layout { width: 100%; border-collapse: collapse; border: none; }
      table.main-layout td { border: none; padding: 5px 0; vertical-align: top; }
      
      /* Data Table */
      table.data-table { width: 100%; border-collapse: collapse; border: 2px solid #000; margin-top: 20px; }
      table.data-table td { border: 1px solid #000; padding: 8px; vertical-align: middle; }
      
      .field-line { border-bottom: 1px solid #000; display: inline-block; min-width: 50px; text-align: center; font-weight: bold; padding: 0 5px; }

  </style></head><body>
    
    <!-- Header -->
    <div class="center" style="margin-bottom: 30px;">
        <h1 style="font-size: 18pt; text-decoration: underline; margin: 0; text-transform: uppercase;">Undertaking by Parents</h1>
    </div>

    <!-- First Paragraph -->
    <div style="text-align: justify; line-height: 2; margin-bottom: 20px;">
        I hereby confirm that my ward Mr./Ms. <span class="field-line" style="min-width: 200px;">${studentName || ''}</span> 
        bearing the student ID <span class="field-line" style="min-width: 120px;">${studentId || ''}</span> of 
        <span class="field-line" style="min-width: 100px;">${program || ''}</span> program registered for the A.Y 
        <span class="field-line" style="min-width: 80px;">${academicYear || ''}</span>.
    </div>

    <!-- Consent Header -->
    <div class="center" style="margin: 20px 0;">
        <h2 style="font-size: 16pt; text-decoration: underline; margin: 0;">Letter of Consent:</h2>
    </div>

    <!-- Consent Body -->
    <div style="text-align: justify; margin-bottom: 20px;">
        I, father/ mother/ guardian, of the student, batch, section, request you to permit <span class="bold">my child/ ward/ son/ daughter</span> to leave the campus <span class="bold">on date</span> ${formatDate(startDate)} <span class="bold">and time</span> ${sTime} for the purpose of <span class="bold">${purpose || 'Outing'}</span>. My <span class="bold">child/ward/son/ daughter</span> shall return on the <span class="bold">date</span> ${formatDate(endDate)} <span class="bold">and time</span> ${eTime}. (Signature below)
    </div>

    <!-- Footer Note -->
    <div style="text-align: justify; margin-bottom: 20px;">
        Outing & leave are permitted only during university leave declared for festivals, national holidays, and weekends.
    </div>

    <!-- Confirmation Header -->
    <div class="center" style="margin: 20px 0;">
        <h2 style="font-size: 16pt; text-decoration: underline; margin: 0;">The Parents/Guardian confirms the following,</h2>
    </div>

    <!-- List -->
    <table class="main-layout">
        <tr>
            <td style="width: 30px;">1.</td>
            <td>I assure you that it is my responsibility for my ward during the outgoings and have been informed of the same by the university officials.</td>
        </tr>
        <tr>
            <td>2.</td>
            <td>I firmly insist my ward not to deviate from the campus policy and adhere to the rules and regulations meticulously.</td>
        </tr>
    </table>

    <!-- Signature Row (Using Table for alignment) -->
    <table class="main-layout" style="margin-top: 40px; margin-bottom: 20px;">
        <tr>
            <td style="width: 50%; vertical-align: bottom;">
                <span class="bold">Date: ${formatDate(todayDate || new Date().toISOString().split('T')[0])}</span>
            </td>
            <td style="width: 50%; text-align: right; vertical-align: bottom;">
                <div style="display: inline-block; text-align: center;">
                    ${signatureImage ? `<img src="${signatureImage}" onerror="this.style.border='1px solid red'; this.alt='Sign Load Failed'" style="height: 50px; display: block; margin: 0 auto 5px auto;" />` : '<div style="height: 50px;"></div>'}
                    <span class="bold">Parents Signature</span>
                </div>
            </td>
        </tr>
    </table>

    <!-- Details Table -->
    <table class="data-table">
        <tr style="height: 50px;">
            <td style="width: 30%;">Father Name, Email & Mobile Number</td>
            <td style="width: 25%;">${fatherName || ''}</td>
            <td style="width: 25%;">${fatherEmail || ''}</td>
            <td style="width: 20%;">${fatherMobile || ''}</td>
        </tr>
        <tr style="height: 50px;">
            <td>Mother Name, Email & Mobile Number</td>
            <td>${motherName || ''}</td>
            <td>${motherEmail || ''}</td>
            <td>${motherMobile || ''}</td>
        </tr>
        <tr style="height: 50px;">
            <td>Student Name, Email & Mobile Number</td>
            <td>${studentName || ''}</td>
            <td>${studentEmail || ''}</td>
            <td>${studentMobile || ''}</td>
        </tr>
    </table>

    <div class="no-print" style="margin-top: 20px; text-align: center;">
        <button onclick="window.print()" style="background: #4f46e5; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">Print / Save as PDF</button>
        <p style="margin-top: 10px; color: #666; font-size: 12px;">Use "Save as PDF" in the print dialog</p>
    </div>
  </body></html>`;

    printWindow.document.write(htmlContent);
    printWindow.document.close();
};
