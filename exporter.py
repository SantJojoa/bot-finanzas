from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from textwrap import wrap

def generate_pdf(ingresos, egresos, saldo, registros, filename="reporte.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    titulo = "📊 Resumen Financiero"
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, titulo)
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 120, f"Ingresos: ${int(ingresos):,} COP".replace(",", "."))
    c.drawString(50, height - 140, f"Egresos: ${int(egresos):,} COP".replace(",", "."))
    c.drawString(50, height - 160, f"Saldo: ${int(saldo):,} COP".replace(",", "."))
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 200, "🧾 Movimientos:")

    y = height - 220
    c.setFont("Helvetica", 11)

    for registro in registros:
        fecha, cantidad, tipo, descripcion = registro
        texto = f"- [{fecha}] {tipo}: {cantidad} - {descripcion}"

        for linea in wrap(texto, width=90):
            c.drawString(50, y, linea)
            y -= 15

            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y, "🧾 Movimientos:")
                y -= 20
                c.setFont("Helvetica", 11)

    c.save()
