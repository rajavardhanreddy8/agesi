
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import textwrap
from datetime import datetime

# optional: register a TTF if you want a nicer font (uncomment & provide file)
# pdfmetrics.registerFont(TTFont('DejaVu', '/path/to/DejaVuSans.ttf'))

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 0.6 * inch
RIGHT_MARGIN = 0.6 * inch
USE_FONT = "Helvetica"          # or 'DejaVu'
USE_BOLD = "Helvetica-Bold"


def wrap_paragraph(c, text, x, y, max_width, font_name=USE_FONT, font_size=10, leading=None):
    """
    Draw wrapped paragraph on canvas 'c' starting at (x, y).
    Returns new y position after drawing the paragraph (y decreases).
    """
    if leading is None:
        leading = font_size * 1.2

    # simple word-wrapping using textwrap but measure width for safety
    words = text.replace("\r", "").split()
    line = ""
    lines = []
    for w in words:
        test = (line + " " + w).strip()
        width = pdfmetrics.stringWidth(test, font_name, font_size)
        if width <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)

    c.setFont(font_name, font_size)
    for ln in lines:
        c.drawString(x, y, ln)
        y -= leading

    return y


def generate_parent_consent_pdf(path_or_buffer, data):
    """
    Create the consent/outgoing form PDF.
    `data` is a dict with keys: student_name, student_id, programme, specialization,
     parent_name, parent_phone, parent_email, reason, leave_start_date, leave_end_date,
     signature_path, father_name, mother_name, student_contact (etc).
    """
    
    # Check if path_or_buffer is a string (path) or a buffer
    if isinstance(path_or_buffer, str):
        # ensure output directory exists
        os.makedirs(os.path.dirname(path_or_buffer), exist_ok=True)
    
    c = canvas.Canvas(path_or_buffer, pagesize=A4)
    width, height = PAGE_WIDTH, PAGE_HEIGHT

    # Header: Title centered
    c.setFont(USE_BOLD, 16)
    c.drawCentredString(width / 2.0, height - 0.8 * inch, "Undertaking by Parents")

    # small subtitle / spacer
    y = height - 1.4 * inch

    # First paragraph with placeholders
    c.setFont(USE_BOLD, 11)
    c.drawString(LEFT_MARGIN, y, "I hereby confirm that my ward Mr./Ms.")
    # draw a long underline area for manual handwriting (if needed)
    underline_x = LEFT_MARGIN + 210
    underline_y = y - 3
    c.line(underline_x, underline_y, width - RIGHT_MARGIN, underline_y)
    
    # Overlay student name
    student_name = data.get('student_name', '') or ''
    if student_name:
        c.setFont(USE_FONT, 11)
        c.drawString(underline_x + 5, y, student_name)

    y -= 0.35 * inch

    # 2nd line: student ID and program
    c.setFont(USE_FONT, 10)
    # Mapping for roll number = student_id
    student_id = data.get('student_id') or data.get('roll_number', '__________')
    prog = data.get('programme', '__________')
    acad_year = data.get('academic_year', '_________')
    
    p1 = f"bearing the student ID {student_id} of {prog} program registered for the A. Y {acad_year}."
    y = wrap_paragraph(c, p1, LEFT_MARGIN, y, width - LEFT_MARGIN - RIGHT_MARGIN, font_size=10)

    y -= 0.15 * inch

    # Letter of Consent heading
    c.setFont(USE_BOLD, 13)
    c.drawString(LEFT_MARGIN, y, "Letter of Consent:")
    y -= 0.25 * inch

    # Main consent paragraph (wrapped)
    c.setFont(USE_FONT, 10)
    
    # Fallback to general 'parent_name' if specific parent_relation is missing
    parent_rel = data.get('parent_relation', f"{data.get('parent_name', 'Parent/Guardian')}")
    
    leave_date = data.get('leave_date_text') or data.get('leave_start_date', 'date')
    return_date = data.get('return_date_text') or data.get('leave_end_date', 'date and time')
    purpose = data.get('purpose') or data.get('reason', 'xxxxxxxxxxxxxx')
    
    consent_text = (
        f"I, {parent_rel}, of the student, batch, section, "
        f"request you to permit my child/ ward/ son/ daughter to leave the campus on {leave_date} "
        f"for the purpose of {purpose}. "
        f"My child/ward/son/ daughter shall return on the {return_date}. (Signature below)"
    )
    y = wrap_paragraph(c, consent_text, LEFT_MARGIN, y, width - LEFT_MARGIN - RIGHT_MARGIN, font_size=10)
    y -= 0.15 * inch

    # Outing rules paragraph
    rules = "Outing & leave are permitted only during university leave declared for festivals, national holidays, and weekends."
    y = wrap_paragraph(c, rules, LEFT_MARGIN, y, width - LEFT_MARGIN - RIGHT_MARGIN, font_size=9)
    y -= 0.25 * inch

    # Confirmation bullet points
    c.setFont(USE_BOLD, 11)
    c.drawString(LEFT_MARGIN, y, "The Parents/Guardian confirms the following,")
    y -= 0.18 * inch

    c.setFont(USE_FONT, 10)
    bullets = [
        "I assure you that it is my responsibility for my ward during the outgoings and have been informed of the same by the university officials.",
        "I firmly insist my ward not to deviate from the campus policy and adhere to the rules and regulations meticulously."
    ]
    for i, b in enumerate(bullets, start=1):
        # Number & text
        c.drawString(LEFT_MARGIN + 6, y, f"{i}.")
        y = wrap_paragraph(c, b, LEFT_MARGIN + 22, y, width - LEFT_MARGIN - RIGHT_MARGIN - 22, font_size=10)
        y -= 0.05 * inch

    y -= 0.2 * inch

    # Date and Parents Signature label on the same line
    c.setFont(USE_BOLD, 11)
    date_val = data.get('date', datetime.now().strftime('%d-%m-%Y'))
    c.drawString(LEFT_MARGIN, y, f"Date: {date_val}")
    c.drawString(width - RIGHT_MARGIN - 2.5 * inch, y, "Parents Signature")
    y -= 0.5 * inch

    # Parent signature image (if provided)
    # Try signature_path first, then signature_data
    sig_path = data.get('signature_path')
    sig_data = data.get('signature_data')
    signature_drawn = False
    
    if sig_path and os.path.exists(sig_path):
        try:
            sig_w = 2.2 * inch
            sig_h = 0.6 * inch
            # drawImage expects bottom-left coordinate
            c.drawImage(sig_path, width - RIGHT_MARGIN - 2.5 * inch, y - sig_h + 0.4*inch, width=sig_w, height=sig_h, mask='auto', preserveAspectRatio=True)
            c.setFont(USE_FONT, 8)
            c.drawString(width - RIGHT_MARGIN - 2.5 * inch, y - sig_h + 0.4*inch - 10, "(Digitally Signed)")
            signature_drawn = True
        except Exception as ex:
            c.setFont(USE_FONT, 9)
            c.drawString(width - RIGHT_MARGIN - 2.5 * inch, y - 10, f"[Signature Error: {ex}]")
    elif sig_data:
        # Handle signature_data (Azure URL or base64)
        try:
            from reportlab.lib.utils import ImageReader
            import io
            import base64
            
            sig_w = 2.2 * inch
            sig_h = 0.6 * inch
            
            if sig_data.startswith('http://') or sig_data.startswith('https://'):
                # Azure Blob Storage URL — download and embed
                import urllib.request
                sig_response = urllib.request.urlopen(sig_data)
                sig_image = ImageReader(io.BytesIO(sig_response.read()))
                c.drawImage(sig_image, width - RIGHT_MARGIN - 2.5 * inch, y - sig_h + 0.4*inch, width=sig_w, height=sig_h, preserveAspectRatio=True, mask='auto')
                c.setFont(USE_FONT, 8)
                c.drawString(width - RIGHT_MARGIN - 2.5 * inch, y - sig_h + 0.4*inch - 10, "(Digitally Signed)")
                signature_drawn = True
            elif sig_data.startswith('data:image'):
                # Base64 encoded image
                header, encoded = sig_data.split(',', 1)
                sig_bytes = base64.b64decode(encoded)
                sig_image = ImageReader(io.BytesIO(sig_bytes))
                c.drawImage(sig_image, width - RIGHT_MARGIN - 2.5 * inch, y - sig_h + 0.4*inch, width=sig_w, height=sig_h, preserveAspectRatio=True, mask='auto')
                c.setFont(USE_FONT, 8)
                c.drawString(width - RIGHT_MARGIN - 2.5 * inch, y - sig_h + 0.4*inch - 10, "(Digitally Signed)")
                signature_drawn = True
            elif os.path.exists(sig_data):
                # File path
                c.drawImage(sig_data, width - RIGHT_MARGIN - 2.5 * inch, y - sig_h + 0.4*inch, width=sig_w, height=sig_h, preserveAspectRatio=True, mask='auto')
                c.setFont(USE_FONT, 8)
                c.drawString(width - RIGHT_MARGIN - 2.5 * inch, y - sig_h + 0.4*inch - 10, "(Digitally Signed)")
                signature_drawn = True
        except Exception as ex:
            c.setFont(USE_FONT, 9)
            c.drawString(width - RIGHT_MARGIN - 2.5 * inch, y - 10, f"[Signature Error: {ex}]")
    
    if not signature_drawn:
        c.setFont(USE_FONT, 9)
        c.drawString(LEFT_MARGIN, y - 10, "") # No signature

    # Draw bottom table for Father, Mother, Student Name, Email & Mobile Number
    # Table position and size
    table_top_y = y - 1.0 * inch
    table_left_x = LEFT_MARGIN
    table_width = width - LEFT_MARGIN - RIGHT_MARGIN
    label_col_width = 2.4 * inch
    remaining = table_width - label_col_width
    col_width = remaining / 3.0  # three small columns for entries

    # rows & heights
    
    # Construct contact strings with proper formatting
    # Father details: Name, Email, Phone
    father_name = data.get('father_name', '') or data.get('parent1_name', '') or data.get('parent_name', '')
    father_email = data.get('father_email', '') or data.get('parent1_email', '') or data.get('parent_email', '')
    father_phone = data.get('father_phone', '') or data.get('parent1_phone', '') or data.get('parent_phone', '')
    
    if father_name or father_email or father_phone:
        father_contact = f"{father_name}, {father_email}, {father_phone}"
    else:
        father_contact = ""
    
    # Mother details: Name, Email, Phone
    mother_name = data.get('mother_name', '') or data.get('parent2_name', '')
    mother_email = data.get('mother_email', '') or data.get('parent2_email', '')
    mother_phone = data.get('mother_phone', '') or data.get('parent2_phone', '')
    
    if mother_name or mother_email or mother_phone:
        mother_contact = f"{mother_name}, {mother_email}, {mother_phone}"
    else:
        mother_contact = ""
        
    # Student contact
    stu_contact = data.get('student_contact')
    if not stu_contact:
        stu_contact = f"{data.get('student_name', '')}, {data.get('student_email', '')}, {data.get('student_phone', '')}"

    rows = [
        ("Father Name, Email & Mobile Number", father_contact),
        ("Mother Name, Email & Mobile Number", mother_contact),
        ("Student Name, Email & Mobile Number", stu_contact),
    ]
    row_height = 0.7 * inch

    # Draw table grid
    c.setLineWidth(0.8)
    # outer border
    c.rect(table_left_x, table_top_y - row_height * len(rows), table_width, row_height * len(rows))

    # vertical separators
    x = table_left_x
    # label column vertical line
    c.line(table_left_x + label_col_width, table_top_y, table_left_x + label_col_width, table_top_y - row_height * len(rows))
    # other verticals
    # The original script drew 3 columns to fill out. I'll just draw one big cell for the value if populated, 
    # but keep the structure similar to the request.
    # Actually request says "3 small columns", likely for Name | Email | Mobile
    # But we are passing a single 'val'. Let's just put the val in the first cell or across.
    # The original script drew vertical lines for empty boxes. I will retain that visual.
    for i in range(1, 4):
        c.line(table_left_x + label_col_width + i * col_width, table_top_y, table_left_x + label_col_width + i * col_width, table_top_y - row_height * len(rows))

    # horizontal separators and content
    for idx, (label, val) in enumerate(rows):
        top = table_top_y - idx * row_height
        # horizontal line
        c.line(table_left_x, top - row_height, table_left_x + table_width, top - row_height)
        # label text left aligned in label cell with small margin
        c.setFont(USE_BOLD, 9)
        # wrap label if too long
        lbl_y = wrap_paragraph(c, label, table_left_x + 6, top - 0.2*inch, label_col_width - 10, font_size=9)
        
        # draw entry
        c.setFont(USE_FONT, 9)
        if val:
            # place as a single-line text in first small column
            # wrap it access the columns? No just put it in.
            # If value is long, wrap it across the cells?
            c.drawString(table_left_x + label_col_width + 6, top - 0.4 * inch, str(val))

    # small footer (optional)
    c.setFont(USE_FONT, 7)
    c.drawCentredString(width / 2.0, 0.5 * inch, "Generated by Campus Outing System")

    c.showPage()
    c.save()
    if isinstance(path_or_buffer, str):
        print(f"PDF Generated at: {path_or_buffer}")


if __name__ == "__main__":
    # Example usage and test data (adjust paths & values as needed)
    out_path = "temp_uploads/parent_consent_generated.pdf"
    sample_data = {
        "student_id": "STU-123456",
        "programme": "B.Tech",
        "specialization": "Computer Science",
        "academic_year": "2024-25",
        "parent_relation": "Mr. Parent Name",
        "leave_date_text": "12-Apr-2026, 09:00 AM",
        "purpose": "family function",
        "return_date_text": "12-Apr-2026, 08:00 PM",
        "date": "12-04-2026",
        # signature image (optional)
        "signature_path": "signatures/test_sig.png",
        # bottom table prefill (optional)
        "father_name": "Father Name",
        "mother_name": "",
        "student_contact": "Test Student, test@example.com, +91-9999999999",
        "student_name": "Test Student Name"
    }

    generate_parent_consent_pdf(out_path, sample_data)
