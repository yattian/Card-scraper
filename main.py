import os
import json5 as json
import requests
from io import BytesIO
from PIL import Image, ImageDraw
import pillow_avif


# === Config ===
FINAL_DIR = "ImagesFinal"
PNG_DIR = "ImagesPNG"
CONFIG_PATH = "card_config.json5"
os.makedirs(FINAL_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)

# === Load config ===
with open(CONFIG_PATH, "r") as f:
    card_config = {entry["id"]: entry for entry in json.load(f)}


# === Functions ===
def download_avif_as_png(set_key: str, card_id: str) -> Image.Image | None:
    url = f"https://cdn.rgpub.io/public/live/map/riftbound/latest/{set_key}/cards/{card_id}/full-desktop-2x.avif"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✔ Downloaded: {card_id}")
            return Image.open(BytesIO(response.content)).convert("RGB")
        else:
            print(f"✘ Not found: {card_id} (HTTP {response.status_code})")
    except Exception as e:
        print(f"✘ Error downloading {card_id}: {e}")
    return None

def resize_and_pad(img: Image.Image) -> Image.Image:
    orig_w, orig_h = img.size
    scale = 1024 / orig_h
    new_w = int(orig_w * scale)
    resized = img.resize((new_w, 1024), Image.LANCZOS)

    canvas = Image.new("RGB", (1024, 1024), (0, 0, 0))
    offset = (1024 - new_w) // 2
    canvas.paste(resized, (offset, 0))

    return canvas

def draw_white_circle(draw: ImageDraw.ImageDraw, cx: int = 190, cy: int = 49, r: int = 78):
    """
    Draw a white circle at (cx, cy) with radius r.
    """
    draw.ellipse((cx, cy, cx + r, cy + r), fill="white")


def apply_main_mods(img: Image.Image, keywords: list[str], rarity: str) -> Image.Image:
    draw = ImageDraw.Draw(img)

    if "unit" in keywords:
        draw_white_circle(draw)

        # Cover might value (top right)
        x1, y1 = 1024 - 208, 58
        square_size = 55
        draw.rectangle((x1 - square_size, y1, x1, y1 + square_size), fill="black")

    if "champunit" in keywords:
        draw_white_circle(draw)

        # Cover might value (top right)
        x1, y1 = 1024 - 208, 58
        square_size = 55
        draw.rectangle((x1 - square_size, y1, x1, y1 + square_size), fill="black")

    if "gear" in keywords:
        pass

    if "spell" in keywords:
        draw_white_circle(draw)

    return img

# def apply_hidden_mods(img: Image.Image) -> Image.Image:
#     # Dim image and overlay an icon in the center
#     img = ImageEnhance.Brightness(img).enhance(0.5)
#     draw = ImageDraw.Draw(img)
#     draw.text((512, 512), "👁", fill="white", anchor="mm")
#     return img

def process_card(card_id: str, keywords: list[str], rarity: str):

    pixelborn_internal_numb = 0
    set_key, card_num = card_id.split("-")  # '001'
    set_config = {"OGN": 1}
    set_num = set_config.get(set_key, 1)
    pixelborn_id = "c" + f"{set_num:03d}" + f"{pixelborn_internal_numb:02d}" + card_num

    img = download_avif_as_png(set_key, card_id)

    if img is None:
        return

    img = resize_and_pad(img)
    img.save(os.path.join(PNG_DIR, f"{pixelborn_id}.png"))
    base = apply_main_mods(img.copy(), keywords, rarity)
    
    # Always save normal version
    base.save(os.path.join(FINAL_DIR, f"{pixelborn_id}.png"))
    print(f"✅ Saved: {pixelborn_id}.png")

    # if "hidden" in keywords:
    #     hidden = apply_hidden_mods(base.copy())
    #     hidden.save(os.path.join(FINAL_DIR, f"{card_id}_hidden.png"))
    #     print(f"✅ Saved: {card_id}_hidden.png")

# === Run ===
# Loop
for card_id, entry in card_config.items():
    keywords = entry.get("keywords", [])
    rarity = entry.get("rarity", "common")  # default if missing
    process_card(card_id, keywords, rarity)
