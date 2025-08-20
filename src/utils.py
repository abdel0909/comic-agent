from PIL import Image, ImageDraw, ImageFont
import textwrap, os

# Stil: "outline" (nur Schrift mit schwarzer Kontur) oder "glass" (halbtransparente Blase)
BUBBLE_STYLE = os.environ.get("BUBBLE_STYLE", "outline").lower()  # "outline" | "glass"

def _fit_font(W):
    # dynamische Schriftgröße je nach Bildbreite
    size = max(20, W // 36)
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

def _wrap(draw, font, text, max_w):
    # bricht Text so um, dass er in max_w passt
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if draw.textlength(test, font=font) <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur: lines.append(" ".join(cur))
    return "\n".join(lines)

def add_bubbles(img, dialogue):
    """
    Zeichnet Sprechtexte lesbar, ohne das Bild zu verdecken:
    - default: Outline-Text (keine Boxen)
    - optional: halbtransparente "Glas"-Bubbles (BUBBLE_STYLE=glass)
    """
    if not dialogue:
        return img

    W, H = img.size
    font = _fit_font(W)

    # wir schreiben auf eine RGBA-Overlay-Ebene und compositen sie am Ende
    base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    pad = int(W * 0.035)
    col_w = int(W * 0.42)
    line_h = int(font.size * 1.35)

    # Positionen: oben rechts start, dann oben links; wenn voll, an den unteren Rand
    slots = [
        (W - col_w - pad, pad),     # oben rechts
        (pad, pad),                 # oben links
        (pad, H - pad - line_h*4),  # unten links
        (W - col_w - pad, H - pad - line_h*4)  # unten rechts
    ]
    idx = 0

    for turn in dialogue:
        raw = (f"{turn.get('speaker', '')}: " if 'speaker' in turn else '') + turn['text']
        wrapped = _wrap(draw, font, raw, col_w)

        x, y = slots[idx % len(slots)]
        idx += 1

        if BUBBLE_STYLE == "glass":
            # halbtransparente Blase
            text_box = draw.multiline_textbbox((x, y), wrapped, font=font, spacing=6)
            x1, y1, x2, y2 = text_box
            x1 -= 18; y1 -= 12; x2 += 18; y2 += 12
            draw.rounded_rectangle([x1, y1, x2, y2], radius=18,
                                   fill=(255,255,255,170), outline=(0,0,0,200), width=2)
            draw.multiline_text((x+2, y), wrapped, font=font, fill=(0,0,0,255), spacing=6)
        else:
            # Outline-Text: sehr gute Lesbarkeit, verdeckt nichts
            draw.multiline_text((x, y), wrapped, font=font,
                                fill=(255,255,255,255), spacing=6,
                                stroke_width=2, stroke_fill=(0,0,0,255))

    # Overlay zurück auf das Original
    out = Image.alpha_composite(base, overlay).convert("RGB")
    return out
