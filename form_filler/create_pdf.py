
from reportlab.pdfgen import canvas

def create_dummy_pdf(path):
    c = canvas.Canvas(path)
    c.drawString(100, 750, "Hello, this is a dummy PDF for testing.")
    c.save()

if __name__ == "__main__":
    create_dummy_pdf("temp_uploads/test_outing.pdf")
