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
        """Apply keyword-specific modifications and save variants"""
        base_img = img.copy()
        
        # Apply each keyword modification that generates variants
        if "accelerate" in self.keywords:
            self._create_accelerate_variant(base_img)
        
        if "discard" in self.keywords:
            self._create_discard_variant(base_img)
        
        if "accelerate" in self.keywords or "discard" in self.keywords:
            # Always create the base "play" variant (single triangle)
            self._create_play_variant(base_img)
        
        return img

    def _create_accelerate_variant(self, base_img: Image.Image):
        """Create accelerate variant with two triangles"""
        darkened = self._darken_image(base_img)
        
        # Add two triangles
        modified = self._add_triangle(darkened, offset_x=-100)
        modified = self._add_triangle(modified, offset_x=100)
        
        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_discard_variant(self, base_img: Image.Image):
        """Create discard variant with X overlay"""
        darkened = self._darken_image(base_img)
        modified = self._add_discard_overlay(darkened)
        
        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_play_variant(self, base_img: Image.Image):
        """Create standard play variant with single triangle"""
        darkened = self._darken_image(base_img)
        modified = self._add_triangle(darkened)
        
        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _darken_image(self, img: Image.Image, ratio: float = 0.6) -> Image.Image:
        """Apply darkening effect to image"""
        return ImageEnhance.Brightness(img.copy()).enhance(ratio)

    def _add_triangle(self, img: Image.Image, offset_x: int = 0) -> Image.Image:
        """Add a white triangle with shadow to the image"""
        width, height = img.size
        cx, cy = width // 2, height // 3
        base_half = 160
        height_triangle = 240
        
        points = [
            (cx - base_half + offset_x, cy - height_triangle // 2),
            (cx - base_half + offset_x, cy + height_triangle // 2),
            (cx + base_half + offset_x, cy),
        ]
        
        # Create shadow
        img_with_shadow = self._add_shadow(img, points, blur_radius=6)
        
        # Add white triangle
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.polygon(points, fill=(255, 255, 255, 230))
        
        return Image.alpha_composite(img_with_shadow, overlay)

    def _add_discard_overlay(self, img: Image.Image) -> Image.Image:
        """Add white rectangle with X for discard variant"""
        width, height = img.size
        cx, cy = width // 2, height // 3
        rect_width, rect_height = 200, 300
        
        x0 = cx - rect_width // 2
        y0 = cy - rect_height // 2
        x1 = cx + rect_width // 2
        y1 = cy + rect_height // 2
        
        # Create shadow
        img_with_shadow = self._add_shadow(img, [x0, y0, x1, y1], blur_radius=12, is_rectangle=True)
        
        # Add white rectangle
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle([x0, y0, x1, y1], fill=(255, 255, 255, 255))
        
        # Add X with border
        self._draw_x_with_border(overlay_draw, x0, y0, x1, y1)
        
        return Image.alpha_composite(img_with_shadow, overlay)

    def _add_shadow(self, img: Image.Image, shape_coords, blur_radius: int, is_rectangle: bool = False) -> Image.Image:
        """Add shadow effect to a shape"""
        shadow_mask = Image.new("L", img.size, 0)
        mask_draw = ImageDraw.Draw(shadow_mask)
        
        if is_rectangle:
            mask_draw.rectangle(shape_coords, fill=255)
        else:
            mask_draw.polygon(shape_coords, fill=255)
        
        blurred = shadow_mask.filter(ImageFilter.GaussianBlur(blur_radius))
        shadow = Image.new("RGBA", img.size, (0, 0, 0, 100))
        return Image.composite(shadow, img.convert("RGBA"), blurred)

    def _draw_x_with_border(self, draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int):
        """Draw an X with black border inside a rectangle"""
        x_pad, y_pad = 10, 10
        x_thickness = 20
        
        line1 = [(x0 + x_pad, y0 + y_pad), (x1 - x_pad, y1 - y_pad)]
        line2 = [(x0 + x_pad, y1 - y_pad), (x1 - x_pad, y0 + y_pad)]
        
        # Black border
        draw.line(line1, fill="black", width=x_thickness + 6)
        draw.line(line2, fill="black", width=x_thickness + 6)
        
        # White lines
        draw.line(line1, fill="white", width=x_thickness)
        draw.line(line2, fill="white", width=x_thickness)

    def draw_white_circle(self, draw: ImageDraw.ImageDraw):
        if self.rarity in ["common", "uncommon"]:
            cx = 190
            cy = 51
            r = 78
            
            draw.ellipse((cx, cy, cx + r, cy + r), fill="white")
        
        if self.rarity in ["rare", "epic", "legendary"]:
            cx = 192.6
            cy = 49
            r = 82

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
