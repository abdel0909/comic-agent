from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Image
import os, glob

def export_pdf(out_path="out/comic.pdf", panels_dir="out/panels", pages_dir="out/pages"):
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4

    # --- Zuerst alle Seitenbilder einfügen ---
    page_imgs = sorted(glob.glob(os.path.join(pages_dir, "*.png")))
    for p in page_imgs:
        c.drawImage(p, 0, 0, width, height, preserveAspectRatio=True, anchor='c')
        c.showPage()

    # --- Dann alle Panels einzeln (als Bonus) ---
    panel_imgs = sorted(glob.glob(os.path.join(panels_dir, "*.png")))
    for p in panel_imgs:
        c.drawImage(p, 0, 0, width, height, preserveAspectRatio=True, anchor='c')
        c.showPage()

    c.save()
    print(f"[ok] PDF gespeichert: {out_path}")

if __name__ == "__main__":
    export_pdf()
