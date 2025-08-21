from reportlab.platypus import SimpleDocTemplate, Image, PageBreak, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import os, glob

def export_pdf():
    doc = SimpleDocTemplate("out/comic.pdf", pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    text_style = styles["Normal"]
    text_style.fontSize = 14
    text_style.leading = 18
    
    panels = sorted(glob.glob("out/pages/page_*.png"))

    for i, img_path in enumerate(panels):
        # --- Bildseite ---
        story.append(Image(img_path, width=400, height=500))  # passt Bild ein
        story.append(PageBreak())

        # --- Textseite ---
        txt_file = img_path.replace(".png", ".txt")  # zu jedem Bild ein .txt?
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            text = f"Text zu Szene {i+1}"
        
        # Stil: Pergament-artiger Hintergrund
        story.append(Paragraph(
            f"<para align=center><b><font color='brown'>{text}</font></b></para>",
            text_style
        ))
        story.append(PageBreak())
    
    doc.build(story)
    print("✅ Comic mit getrennten Textseiten gespeichert: out/comic.pdf")
