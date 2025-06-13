import os
import json5 as json
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import pillow_avif

# === Config ===
FINAL_DIR = "ImagesFinal"
PNG_DIR = "ImagesPNG"
CONFIG_PATH = "card_config.json5"
os.makedirs(FINAL_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)

# === Card Class ===
class Card:
    def __init__(self, id: str, keywords: list[str], rarity: str = "common"):
        self.id = id
        self.keywords = keywords
        self.rarity = rarity
        self.set_key, self.card_num = self.id.split("-")
        self.pixelborn_internal_numb = 0  # currently hardcoded as 00

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            keywords=data.get("keywords", []),
            rarity=data.get("rarity", "common")
        )

    def pixelborn_id(self, first_letter):
        set_config = {"OGN": 1}
        set_num = set_config.get(self.set_key, 1)
        return first_letter + f"{set_num:03d}" + f"{self.pixelborn_internal_numb:02d}" + self.card_num

    def download_image(self) -> Image.Image | None:
        url = f"https://cdn.rgpub.io/public/live/map/riftbound/latest/{self.set_key}/cards/{self.id}/full-desktop-2x.avif"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✔ Downloaded: {self.id}")
                return Image.open(BytesIO(response.content)).convert("RGB")
            else:
                print(f"✘ Not found: {self.id} (HTTP {response.status_code})")
        except Exception as e:
            print(f"✘ Error downloading {self.id}: {e}")
        return None

    def resize_and_pad(self, img: Image.Image) -> Image.Image:
        orig_w, orig_h = img.size
        scale = 1024 / orig_h
        new_w = int(orig_w * scale)
        resized = img.resize((new_w, 1024), Image.LANCZOS)

        canvas = Image.new("RGB", (1024, 1024), (0, 0, 0))
        offset = (1024 - new_w) // 2
        canvas.paste(resized, (offset, 0))
        return canvas

    def apply_modifications(self, img: Image.Image) -> Image.Image:
        draw = ImageDraw.Draw(img)

        if "unit" in self.keywords or "champunit" in self.keywords or "spell" in self.keywords:
            self.draw_white_circle(draw)

        if "unit" in self.keywords or "champunit" in self.keywords:
            x1, y1 = 1024 - 206, 59
            square_size = 57
            draw.rectangle((x1 - square_size, y1, x1, y1 + square_size), fill="black")
        
        if "gear" in self.keywords:
            # Black diamond (top-right)
            cx, cy = 228.5, 90  # center of the diamond
            half = 45

            points = [
                (cx, cy - half),  # top
                (cx + half, cy),  # right
                (cx, cy + half),  # bottom
                (cx - half, cy),  # left
            ]
            draw.polygon(points, fill="white")

        return img
    
    def apply_extra_modifications(self, img: Image.Image) -> Image.Image:
        width, height = img.size
        cx, cy = width // 2, height // 3  # 1/3 down the image
        base_half = 160
        height_triangle = 240
        darken_ratio = 0.6

        # Define reusable triangle drawing function
        def draw_triangle(base_img: Image.Image, offset_x: int = 0) -> Image.Image:
            points = [
                (cx - base_half + offset_x, cy - height_triangle // 2),
                (cx - base_half + offset_x, cy + height_triangle // 2),
                (cx + base_half + offset_x, cy),
            ]

            # Shadow mask
            triangle_mask = Image.new("L", base_img.size, 0)
            mask_draw = ImageDraw.Draw(triangle_mask)
            mask_draw.polygon(points, fill=255)
            blurred = triangle_mask.filter(ImageFilter.GaussianBlur(6))

            # Apply shadow
            shadow = Image.new("RGBA", base_img.size, (0, 0, 0, 100))
            base_img = Image.composite(shadow, base_img.convert("RGBA"), blurred)

            # Draw white triangle
            overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.polygon(points, fill=(255, 255, 255, 230))
            return Image.alpha_composite(base_img, overlay)

        # Only do this if the card has "accelerate"
        if "accelerate" in self.keywords:
            # Darken image
            img_accel = img.copy()
            img_accel = ImageEnhance.Brightness(img_accel).enhance(darken_ratio)

            # Save version with two triangles
            two_triangle = draw_triangle(img_accel.copy(), offset_x=-100)
            two_triangle = draw_triangle(two_triangle, offset_x=+100)
            pixel_id_two = self.pixelborn_id("a")
            self.pixelborn_internal_numb += 1
            two_triangle.save(os.path.join(FINAL_DIR, f"{pixel_id_two}.png"))
        
        if "discard" in self.keywords:
            img_discard = img.copy()
            img_discard = ImageEnhance.Brightness(img_discard).enhance(darken_ratio)

            width, height = img_discard.size
            rect_width = 200
            rect_height = 300
            cx, cy = width // 2, height // 3

            x0 = cx - rect_width // 2
            y0 = cy - rect_height // 2
            x1 = cx + rect_width // 2
            y1 = cy + rect_height // 2

            # Create shadow mask
            shadow_mask = Image.new("L", img_discard.size, 0)
            mask_draw = ImageDraw.Draw(shadow_mask)
            mask_draw.rectangle([x0, y0, x1, y1], fill=255)

            blurred = shadow_mask.filter(ImageFilter.GaussianBlur(12))
            shadow = Image.new("RGBA", img_discard.size, (0, 0, 0, 100))
            img_discard = Image.composite(shadow, img_discard.convert("RGBA"), blurred)

            # Draw white rectangle
            overlay = Image.new("RGBA", img_discard.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([x0, y0, x1, y1], fill=(255, 255, 255, 255))
            
            # Draw "X" with black border
            x_pad = 10
            y_pad = 10
            x_thickness = 20

            # Lines of the "X"
            line1 = [(x0 + x_pad, y0 + y_pad), (x1 - x_pad, y1 - y_pad)]
            line2 = [(x0 + x_pad, y1 - y_pad), (x1 - x_pad, y0 + y_pad)]

            # First draw thicker black lines for border
            overlay_draw.line(line1, fill="black", width=x_thickness + 6)
            overlay_draw.line(line2, fill="black", width=x_thickness + 6)

            # Then draw thinner white lines on top
            overlay_draw.line(line1, fill="white", width=x_thickness)
            overlay_draw.line(line2, fill="white", width=x_thickness)

            img_discard = Image.alpha_composite(img_discard, overlay)

            # Save discard version
            pixel_id = self.pixelborn_id("a")
            self.pixelborn_internal_numb += 1
            img_discard.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))


        # Save version with one triangle
        img_play = img.copy()
        img_play = ImageEnhance.Brightness(img_play).enhance(darken_ratio)
        one_triangle = draw_triangle(img_play.copy())
        pixel_id_one = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        one_triangle.save(os.path.join(FINAL_DIR, f"{pixel_id_one}.png"))

        return img

    def draw_white_circle(self, draw: ImageDraw.ImageDraw):
        if self.rarity in ["common", "uncommon"]:
            cx = 190
            cy = 51
            r = 78
            
            draw.ellipse((cx, cy, cx + r, cy + r), fill="white")
        
        if self.rarity in ["rare", "epic", "legendary"]:
            cx = 193
            cy = 51
            r = 79

            draw.ellipse((cx, cy, cx + r, cy + r), fill="white")

    def process(self):
        img = self.download_image()
        if img is None:
            return

        pixel_id = self.pixelborn_id("c")

        img = self.resize_and_pad(img)
        img.save(os.path.join(PNG_DIR, f"{pixel_id}.png"))

        modified = self.apply_modifications(img.copy())
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

        self.apply_extra_modifications(modified.copy())

        print(f"✅ Saved: {pixel_id}.png")

# === Load config and process cards ===
with open(CONFIG_PATH, "r") as f:
    entries = json.load(f)
    cards = [Card.from_dict(entry) for entry in entries]

for card in cards:
    card.process()
