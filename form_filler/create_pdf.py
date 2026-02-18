
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
    Create the consent/outgoing form PDF matching the "Undertaking by Parents" template.
    """
    
    # Check if path_or_buffer is a string (path) or a buffer
    if isinstance(path_or_buffer, str):
        # ensure output directory exists
        os.makedirs(os.path.dirname(path_or_buffer), exist_ok=True)
    
    c = canvas.Canvas(path_or_buffer, pagesize=A4)
    width, height = PAGE_WIDTH, PAGE_HEIGHT

    # --- Header: Title ---
    c.setFont(USE_BOLD, 14)
    # Underlined title
    title = "Undertaking by Parents"
    title_w = pdfmetrics.stringWidth(title, USE_BOLD, 14)
    c.drawCentredString(width / 2.0, height - 1.0 * inch, title)
    c.line((width - title_w) / 2.0, height - 1.0 * inch - 2, (width + title_w) / 2.0, height - 1.0 * inch - 2)

    y = height - 1.5 * inch

    # --- Ward Details Paragraph ---
    c.setFont(USE_FONT, 11)
    
    # Construct the sentence with filled data
    # "I hereby confirm that my ward Mr./Ms. _______ bearing the student ID _______ of ______ program registered for the A. Y ______"
    
    student_name = data.get('student_name', '')
    student_id = data.get('student_id') or data.get('roll_number', '')
    prog = data.get('programme', '')
    acad_year = data.get('academic_year', '')
    
    text_obj = c.beginText(LEFT_MARGIN, y)
    text_obj.setFont(USE_FONT, 11)
    
    # We'll use a helper to draw text and lines for the blanks
    def draw_filled_field(canvas_obj, x_cursor, y_cursor, label_pre, value, label_post, min_width=50):
        # Draw pre-label
        canvas_obj.setFont(USE_FONT, 11)
        canvas_obj.drawString(x_cursor, y_cursor, label_pre)
        x_cursor += pdfmetrics.stringWidth(label_pre, USE_FONT, 11)
        
        # Draw value (bold? or just normal)
        # Template implies just handwriting style, so we underline the space
        if value:
            # Draw value centered in the line
            val_width = pdfmetrics.stringWidth(value, USE_FONT, 11)
            line_width = max(min_width, val_width + 10)
            
            # Draw empty line
            canvas_obj.line(x_cursor, y_cursor - 1, x_cursor + line_width, y_cursor - 1)
            
            # Draw text centered above line
            text_x = x_cursor + (line_width - val_width) / 2
            canvas_obj.drawString(text_x, y_cursor + 1, value)
            
            x_cursor += line_width
        else:
            # Draw empty line
            line_width = min_width
            canvas_obj.line(x_cursor, y_cursor - 1, x_cursor + line_width, y_cursor - 1)
            x_cursor += line_width
            
        # Draw post-label
        canvas_obj.drawString(x_cursor, y_cursor, label_post)
        x_cursor += pdfmetrics.stringWidth(label_post, USE_FONT, 11)
        return x_cursor

    # Line 1
    cursor_x = LEFT_MARGIN
    cursor_x = draw_filled_field(c, cursor_x, y, "I hereby confirm that my ward Mr./Ms. ", student_name, "", min_width=180)
    
    y -= 0.35 * inch
    # Line 2
    cursor_x = LEFT_MARGIN
    cursor_x = draw_filled_field(c, cursor_x, y, "bearing the student ID ", student_id, " of ", min_width=100)
    cursor_x = draw_filled_field(c, cursor_x, y, "", prog, " program registered for", min_width=100)
    
    y -= 0.35 * inch
    # Line 3
    cursor_x = LEFT_MARGIN
    cursor_x = draw_filled_field(c, cursor_x, y, "the A. Y ", acad_year, "", min_width=80)

    y -= 0.6 * inch

    # --- Letter of Consent Title ---
    c.setFont(USE_BOLD, 12)
    title2 = "Letter of Consent:"
    title2_w = pdfmetrics.stringWidth(title2, USE_BOLD, 12)
    c.drawCentredString(width / 2.0, y, title2)
    c.line((width - title2_w) / 2.0, y - 2, (width + title2_w) / 2.0, y - 2)
    
    y -= 0.4 * inch

    # --- Consent Body ---
    # "I, father/ mother/ guardian, of the student, batch, section, request you to permit my child/ ward/ son/ daughter to leave the campus on date and time for the purpose of xxxxxxxxxxxxxxx. My child/ward/son/ daughter shall return on the date and time. (Signature below)"
    
    c.setFont(USE_FONT, 11)
    
    leave_date = data.get('leave_date_text') or data.get('leave_start_date', '')
    return_date = data.get('return_date_text') or data.get('leave_end_date', '')
    purpose = data.get('purpose') or data.get('reason', '')
    
    # We construct the paragraph text with explicit bolding where needed logic is hard in standard reportlab without Platypus.
    # We basically need to bold specific parts: "my child/ ward/ son/ daughter", date, time, purpose, "child/ward/son/ daughter", return date, time, "(Signature below)".
    # To keep it simple and robust, we will write it as a continuous heavy paragraph for now using standard font, 
    # OR we use the trick of drawing bold words separately? Too complex for this simple agent tool.
    # Best approach: Use Bold font for the variable data to highlight it effectively.

    # Start text object
    text = c.beginText(LEFT_MARGIN, y)
    text.setFont(USE_FONT, 11)
    
    # We'll use simple string composition with "bolding" by changing font manually if we used paragraph flow. 
    # But doing line-by-line is safer.
    
    lines = [
        f"I, father/ mother/ guardian, of the student, batch, section, request you to permit my",
        f"child/ ward/ son/ daughter to leave the campus on {leave_date}",
        f"for the purpose of {purpose}. My child/ward/son/ daughter shall",
        f"return on the {return_date}. (Signature below)"
    ]
    
    # Let's try to wrap it dynamically but highlighting is key.
    # The user template highlights: "my child/ ward/ son/ daughter", date, purpose, date.
    # We will simulate bolding for the *entire* filled value for emphasis.
    
    # Let's just use a standard paragraph for now but clean.
    full_text = f"I, father/ mother/ guardian, of the student, batch, section, request you to permit my child/ ward/ son/ daughter to leave the campus on  {leave_date}  for the purpose of  {purpose} . My child/ward/son/ daughter shall return on the  {return_date} . (Signature below)"
    
    y = wrap_paragraph(c, full_text, LEFT_MARGIN, y, width - LEFT_MARGIN - RIGHT_MARGIN, font_size=11, leading=18)
    
    y -= 0.3 * inch

    # --- Rules ---
    rules = "Outing & leave are permitted only during university leave declared for festivals, national holidays, and weekends."
    y = wrap_paragraph(c, rules, LEFT_MARGIN, y, width - LEFT_MARGIN - RIGHT_MARGIN, font_size=10)

    y -= 0.4 * inch

    # --- Confirmation Title ---
    c.setFont(USE_BOLD, 12)
    title3 = "The Parents/Guardian confirms the following,"
    title3_w = pdfmetrics.stringWidth(title3, USE_BOLD, 12)
    c.drawCentredString(width / 2.0, y, title3)
    c.line((width - title3_w) / 2.0, y - 2, (width + title3_w) / 2.0, y - 2)

    y -= 0.3 * inch

    # --- Bullets ---
    bullets = [
        "I assure you that it is my responsibility for my ward during the outgoings and have been informed of the same by the university officials.",
        "I firmly insist my ward not to deviate from the campus policy and adhere to the rules and regulations meticulously."
    ]
    
    for i, b in enumerate(bullets, start=1):
        c.setFont(USE_FONT, 11)
        c.drawString(LEFT_MARGIN + 10, y, f"{i}.")
        y = wrap_paragraph(c, b, LEFT_MARGIN + 30, y, width - LEFT_MARGIN - RIGHT_MARGIN - 30, font_size=11)
        y -= 0.1 * inch

    y -= 0.6 * inch

    # --- Date and Signature Line ---
    date_val = data.get('date', datetime.now().strftime('%d-%m-%Y'))
    
    c.setFont(USE_BOLD, 12)
    c.drawString(LEFT_MARGIN, y, "Date:")
    c.setFont(USE_FONT, 12)
    c.drawString(LEFT_MARGIN + 40, y, date_val)
    c.line(LEFT_MARGIN + 40, y - 2, LEFT_MARGIN + 150, y - 2)

    c.setFont(USE_BOLD, 12)
    c.drawString(width - RIGHT_MARGIN - 150, y, "Parents Signature")
    
    # Signature placement
    sig_y_pos = y + 10 # slightly above label
    
    # Insert Signature Image logic
    sig_path = data.get('signature_path')
    sig_data = data.get('signature_data')
    
    if sig_path and os.path.exists(sig_path):
        try:
            c.drawImage(sig_path, width - RIGHT_MARGIN - 150, sig_y_pos, width=120, height=50, mask='auto', preserveAspectRatio=True)
        except: pass
    elif sig_data:
        try:
            from reportlab.lib.utils import ImageReader
            import base64, io
            if sig_data.startswith('data:image'):
                 header, encoded = sig_data.split(',', 1)
                 sig_bytes = base64.b64decode(encoded)
                 sig_image = ImageReader(io.BytesIO(sig_bytes))
                 c.drawImage(sig_image, width - RIGHT_MARGIN - 150, sig_y_pos, width=120, height=50, mask='auto', preserveAspectRatio=True)
        except: pass

    y -= 1.0 * inch

    # --- Bottom Table ---
    # 3 rows, 2 columns (Label | Value)
    # Actually screenshot shows: Label Column | Empty Box | Empty Box | Empty Box?
    # User screenshot has 4 columns: [Label] [Empty] [Empty] [Empty]
    # Labels: "Father Name, Email & Mobile Number", "Mother Name, Email & Mobile Number", "Student Name, Email & Mobile Number"
    
    # We will construct a simple table with ReportLab primitive lines
    
    table_top = y
    row_h = 40
    col1_w = 200
    col2_w = (width - LEFT_MARGIN - RIGHT_MARGIN - col1_w) # One big column for value, or split?
    # Screenshot shows 3 empty columns for filling. Since we are digital, we should fill the value.
    # Where does the value go? In the first available slot? 
    # Let's make it 2 columns: Label | Value content
    
    # Data prep
    father_str = f"{data.get('father_name', '')}\n{data.get('father_email', '')}\n{data.get('father_phone', '')}".strip()
    mother_str = f"{data.get('mother_name', '')}\n{data.get('mother_email', '')}\n{data.get('mother_phone', '')}".strip()
    
    stu_contact = data.get('student_contact', '')
    if not stu_contact:
        stu_contact = f"{data.get('student_name', '')}\n{data.get('student_email', '')}\n{data.get('student_phone', '')}".strip()
        
    table_data = [
        ("Father Name, Email &\nMobile Number", father_str),
        ("Mother Name, Email &\nMobile Number", mother_str),
        ("Student Name, Email &\nMobile Number", stu_contact)
    ]
    
    c.setLineWidth(1)
    c.setFont(USE_FONT, 10)
    
    curr_y = table_top
    
    for label, value in table_data:
        # Draw row rects
        # Col 1 (Label)
        c.rect(LEFT_MARGIN, curr_y - row_h, col1_w, row_h)
        # Col 2 (Value)
        c.rect(LEFT_MARGIN + col1_w, curr_y - row_h, col2_w, row_h)
        
        # Text
        # draw label centered vertically?
        # reportlab draws from bottom up.
        # simple multi-line text draw
        text_obj = c.beginText(LEFT_MARGIN + 5, curr_y - 12)
        text_obj.setFont(USE_FONT, 10)
        for line in label.split('\n'):
            text_obj.textLine(line)
        c.drawText(text_obj)
        
        # draw value
        val_obj = c.beginText(LEFT_MARGIN + col1_w + 5, curr_y - 12)
        val_obj.setFont(USE_FONT, 10)
        for line in value.split('\n'):
            val_obj.textLine(line)
        c.drawText(val_obj)
        
        curr_y -= row_h

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
