# src/export_pdf.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os, glob, sys

def export_pdf(out_path="out/comic.pdf", panels_dir="out/panels", pages_dir="out/pages"):
    os.makedirs("out", exist_ok=True)
    os.makedirs(panels_dir, exist_ok=True)
    os.makedirs(pages_dir, exist_ok=True)

    page_imgs  = sorted(glob.glob(os.path.join(pages_dir, "*.png")))
    panel_imgs = sorted(glob.glob(os.path.join(panels_dir, "*.png")))
    if not page_imgs and not panel_imgs:
        raise SystemExit("❌ Keine Bilder gefunden. Erst rendern (src.agent), dann PDF exportieren.")

    c = canvas.Canvas(out_path, pagesize=A4)
    W, H = A4

    for p in page_imgs:
        c.drawImage(p, 0, 0, W, H, preserveAspectRatio=True, anchor='c'); c.showPage()

    for p in panel_imgs:
        c.drawImage(p, 0, 0, W, H, preserveAspectRatio=True, anchor='c'); c.showPage()

    c.save()
    print(f"✅ PDF gespeichert: {out_path} (Seitenbilder: {len(page_imgs)}, Panels: {len(panel_imgs)})")

if __name__ == "__main__":
    export_pdf()
