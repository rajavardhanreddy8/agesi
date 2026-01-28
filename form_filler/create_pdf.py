
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import os

def generate_outing_pdf(path, data):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 1*inch, "Woxsen University - Outing Request")
    
    c.setFont("Helvetica", 12)
    y = height - 2*inch
    
    fields = [
        ("Student Name:", data.get('student_name', '')),
        ("Roll Number:", data.get('roll_number', '')),
        ("School:", data.get('school', '')),
        ("Program/Spec:", f"{data.get('programme', '')} - {data.get('specialization', '')}"),
        ("Email:", data.get('student_email', '')),
        ("Phone:", data.get('student_phone', '')),
        ("Parent Name:", data.get('parent_name', '')),
        ("Parent Phone:", data.get('parent_phone', '')),
        ("Parent Email:", data.get('parent_email', '')),
        ("------------------------------------------------", ""),
        ("Reason:", data.get('reason', '')),
        ("Start Date:", data.get('leave_start_date', '')),
        ("End Date:", data.get('leave_end_date', ''))
    ]
    
    for label, value in fields:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1*inch, y, label)
        c.setFont("Helvetica", 10)
        # Handle None in value
        val_str = str(value) if value else "N/A"
        c.drawString(3*inch, y, val_str)
        y -= 0.3*inch
        
    y -= 0.5*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*inch, y, "Student Declaration:")
    y -= 0.2*inch
    c.setFont("Helvetica", 9)
    c.drawString(1*inch, y, "I hereby declare that the details furnished above are true to the best of my knowledge.")
    
    y -= 1*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*inch, y, "Parent Signature:")
    
    # Signature Image
    sig_path = data.get('signature_path')
    if sig_path and os.path.exists(sig_path):
        try:
            # Draw image (preserve aspect ratio roughly or fixed box)
            # x, y, width, height. y is bottom left.
            c.drawImage(sig_path, 1*inch, y - 0.8*inch, width=2*inch, height=0.6*inch, mask='auto', preserveAspectRatio=True)
            c.drawString(1*inch, y - 1*inch, "(Digitally Signed)")
        except Exception as e:
            c.drawString(1*inch, y - 0.5*inch, f"[Signature Error: {str(e)}]")
    else:
        c.drawString(1*inch, y - 0.5*inch, "[No Signature Found]")
        
    c.save()
    print(f"PDF Generated at: {path}")

if __name__ == "__main__":
    # Test
    test_data = {
        'student_name': 'Test Student',
        'signature_path': 'signatures/test_sig.png'
    }
    generate_outing_pdf("temp_uploads/test_gen.pdf", test_data)

