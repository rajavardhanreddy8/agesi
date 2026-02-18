
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
    sig_label_x = width - RIGHT_MARGIN - 150
    c.drawString(sig_label_x, y, "Parents Signature")
    
    # --- Signature Image (drawn ABOVE the label) ---
    sig_path = data.get('signature_path')
    sig_data = data.get('signature_data')
    sig_w = 130
    sig_h = 50
    sig_x = sig_label_x
    sig_y = y + 12  # above the label text
    
    def _try_draw_signature(canvas_obj, image_source, sx, sy, sw, sh):
        """Try to draw a signature from various sources."""
        from reportlab.lib.utils import ImageReader
        import base64 as b64mod
        import io as iomod
        import urllib.request
        
        try:
            if isinstance(image_source, str):
                if os.path.exists(image_source):
                    # Local file path
                    canvas_obj.drawImage(image_source, sx, sy, width=sw, height=sh, mask='auto', preserveAspectRatio=True)
                    return True
                elif image_source.startswith(('http://', 'https://')):
                    # URL (e.g., Azure Blob)
                    resp = urllib.request.urlopen(image_source)
                    img = ImageReader(iomod.BytesIO(resp.read()))
                    canvas_obj.drawImage(img, sx, sy, width=sw, height=sh, mask='auto', preserveAspectRatio=True)
                    return True
                elif image_source.startswith('data:image'):
                    # Base64 data URI
                    _, encoded = image_source.split(',', 1)
                    img_bytes = b64mod.b64decode(encoded)
                    img = ImageReader(iomod.BytesIO(img_bytes))
                    canvas_obj.drawImage(img, sx, sy, width=sw, height=sh, mask='auto', preserveAspectRatio=True)
                    return True
        except Exception as e:
            print(f"Signature draw error: {e}")
        return False
    
    sig_drawn = False
    if sig_path:
        sig_drawn = _try_draw_signature(c, sig_path, sig_x, sig_y, sig_w, sig_h)
    if not sig_drawn and sig_data:
        sig_drawn = _try_draw_signature(c, sig_data, sig_x, sig_y, sig_w, sig_h)

    y -= 0.8 * inch

    # ============================================================
    # BOTTOM TABLE: 4 columns — Label | Name | Email | Phone
    # Matches the Word template exactly
    # ============================================================
    
    table_x = LEFT_MARGIN
    table_w = width - LEFT_MARGIN - RIGHT_MARGIN
    
    # Column widths (4 columns)
    label_w = 150          # "Father Name, Email & Mobile Number"
    name_w = 120           # Name value
    email_w = 140          # Email value
    phone_w = table_w - label_w - name_w - email_w  # Phone value (remainder)
    
    row_h = 45  # height per row
    
    # Prepare row data: (label, name, email, phone)
    father_name = data.get('father_name', '') or data.get('parent1_name', '') or data.get('parent_name', '') or ''
    father_email = data.get('father_email', '') or data.get('parent1_email', '') or data.get('parent_email', '') or ''
    father_phone = data.get('father_phone', '') or data.get('parent1_phone', '') or data.get('parent_phone', '') or ''
    
    mother_name = data.get('mother_name', '') or data.get('parent2_name', '') or ''
    mother_email = data.get('mother_email', '') or data.get('parent2_email', '') or ''
    mother_phone = data.get('mother_phone', '') or data.get('parent2_phone', '') or ''
    
    stu_name = data.get('student_name', '') or ''
    stu_email = data.get('student_email', '') or ''
    stu_phone = data.get('student_phone', '') or ''
    
    rows = [
        ("Father Name, Email &\nMobile Number", father_name, father_email, father_phone),
        ("Mother Name, Email &\nMobile Number", mother_name, mother_email, mother_phone),
        ("Student Name, Email &\nMobile Number", stu_name, stu_email, stu_phone),
    ]
    
    col_widths = [label_w, name_w, email_w, phone_w]
    
    c.setLineWidth(0.8)
    
    curr_y = y
    
    for (label, name_val, email_val, phone_val) in rows:
        cell_values = [label, name_val, email_val, phone_val]
        
        # Draw each cell rectangle
        cx = table_x
        for i, cw in enumerate(col_widths):
            c.rect(cx, curr_y - row_h, cw, row_h)
            cx += cw
        
        # Fill text into each cell
        cx = table_x
        for i, (cw, val) in enumerate(zip(col_widths, cell_values)):
            if val:
                # Use bold for the label column, normal for data
                font = USE_BOLD if i == 0 else USE_FONT
                font_size = 8 if i == 0 else 9
                
                # Wrap text within the cell
                padding = 4
                max_text_w = cw - 2 * padding
                
                # Split into lines that fit
                words = val.replace('\n', ' ').split()
                lines = []
                line = ""
                for w in words:
                    test = (line + " " + w).strip()
                    tw = pdfmetrics.stringWidth(test, font, font_size)
                    if tw <= max_text_w:
                        line = test
                    else:
                        if line:
                            lines.append(line)
                        line = w
                if line:
                    lines.append(line)
                
                # Draw lines vertically centered in cell
                line_h = font_size + 3
                total_text_h = len(lines) * line_h
                start_text_y = curr_y - (row_h - total_text_h) / 2 - font_size
                
                c.setFont(font, font_size)
                for li, ln in enumerate(lines):
                    c.drawString(cx + padding, start_text_y - li * line_h, ln)
            
            cx += cw
        
        curr_y -= row_h

    c.showPage()
    c.save()
    if isinstance(path_or_buffer, str):
        print(f"PDF Generated at: {path_or_buffer}")


if __name__ == "__main__":
    # Example usage and test data (adjust paths & values as needed)
    out_path = "temp_uploads/parent_consent_generated.pdf"
    sample_data = {
        "student_name": "GUNTAKA RAJAVARDHAN REDDY",
        "student_id": "23WUBOT048",
        "programme": "B.Tech",
        "specialization": "Computer Science",
        "academic_year": "2024-25",
        "leave_date_text": "12-Apr-2026, 09:00 AM",
        "purpose": "family function",
        "return_date_text": "12-Apr-2026, 08:00 PM",
        "date": "18-02-2026",
        # signature image (optional)
        "signature_path": "",
        # Table data — each detail in its own cell
        "father_name": "Raghunadha reddy",
        "father_email": "rrtradersind@gmail.com",
        "father_phone": "8919455860",
        "mother_name": "Pranitha",
        "mother_email": "pranithaguntaka@gmail.com",
        "mother_phone": "9010787739",
        "student_email": "guntaka.reddy_2028@woxsen.edu.in",
        "student_phone": "8639929405",
    }

    generate_parent_consent_pdf(out_path, sample_data)
