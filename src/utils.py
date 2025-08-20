from PIL import Image, ImageDraw, ImageFont

def add_bubbles(img, dialogue):
    if not dialogue: 
        return img
    img = img.copy()
    draw = ImageDraw.Draw(img)
    W, H = img.size
    pad = 24
    y = pad
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 28)
    except:
        font = ImageFont.load_default()

    for turn in dialogue:
        text = (turn.get("speaker", "") + ": " if "speaker" in turn else "") + turn["text"]
        w = min(W - 2*pad, 520)
        h = 120
        box = [pad, y, pad+w, y+h]
        draw.rounded_rectangle(box, radius=18, fill=(255,255,255), outline=(0,0,0), width=3)
        draw.text((pad+18, y+16), text, fill=(0,0,0), font=font)
        y += h + 12
        if y > H - 140:
            pad = W - w - 24
            y = 24
    return img

def compose_page(images, page_size=(1536, 1024)):
    page = Image.new("RGB", page_size, (250, 250, 250))
    slots = [
        (0, 0, page_size[0]//2 - 2, page_size[1]),
        (page_size[0]//2 + 2, 0, page_size[0]-2, page_size[1]//2 - 2),
        (page_size[0]//2 + 2, page_size[1]//2 + 2, page_size[0]-2, page_size[1]-2)
    ]
    for img, (x1,y1,x2,y2) in zip(images, slots):
        slot = img.resize((x2-x1, y2-y1))
        page.paste(slot, (x1, y1))
    return page
