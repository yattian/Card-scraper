import os
import json5 as json
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import pillow_avif
from cairosvg import svg2png

# === Config ===
FINAL_DIR = "ImagesFinal"
PNG_DIR = "ImagesPNG"
CONFIG_PATH = "scraped_cards.json5"
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
        if ALT_ART:
            url = f"https://cdn.rgpub.io/public/live/map/riftbound/latest/{self.set_key}/cards/{self.id}a/full-desktop-2x.avif"
        else:
            url = f"https://cdn.rgpub.io/public/live/map/riftbound/latest/{self.set_key}/cards/{self.id}/full-desktop-2x.avif"
        
        if ALT_ART:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"✔ Downloaded ALT: {self.id}")
                    return Image.open(BytesIO(response.content)).convert("RGB")
                else:
                    url = f"https://cdn.rgpub.io/public/live/map/riftbound/latest/{self.set_key}/cards/{self.id}/full-desktop-2x.avif"
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        print(f"✔ Downloaded: {self.id}")
                        return Image.open(BytesIO(response.content)).convert("RGB")
                    else:
                        print(f"✘ Not found: {self.id} (HTTP {response.status_code})")
            except Exception as e:
                print(f"✘ Error downloading {self.id}: {e}")
            return None
        else:
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

        if "unit" in self.keywords or "champunit" in self.keywords or "spell" in self.keywords or "sigspell" in self.keywords:
            self.draw_white_circle(draw)

        if "unit" in self.keywords or "champunit" in self.keywords or "token" in self.keywords:
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
        extra_applied = False
        
        # Apply each keyword modification that generates variants
        if "accelerate" in self.keywords:
            self._create_accelerate_variant(base_img)
            extra_applied = True
        
        if "discard" in self.keywords:
            self._create_discard_variant(base_img)
            extra_applied = True

        if "tap" in self.keywords:
            self._create_tap_variant(base_img)

        if "draw" in self.keywords:
            self._create_draw_variant(base_img)
            extra_applied = True

        if "hidden" in self.keywords:
            self._create_hidden_variant(base_img)
            extra_applied = True
        
        if "kill" in self.keywords:
            self._create_kill_variant(base_img)

        if "spend" in self.keywords:
            self._create_spend_variant(base_img)

        if "qiyana_victorious" in self.keywords:
            self._create_draw_variant(base_img)
            self._create_channel_variant(base_img)

        if "udyr_wildman" in self.keywords:
            self._create_damage_variant(base_img)
            self._create_stun_variant(base_img)
            self._create_ready_variant(base_img)
            self._create_ganking_variant(base_img)

        if "teemo_legend" in self.keywords:
            self._create_tap_variant(base_img)
            self._create_hidden_variant(base_img, only_hidden=True)

        if "the_dreaming_tree" in self.keywords:
            self._create_draw_variant(base_img)

        if "ava_achiever" in self.keywords:
            self._create_hidden_variant(base_img, only_hidden=True)
            
        if extra_applied and "location" not in self.keywords:
            # Always create the base "play" variant (single triangle)
            self._create_play_variant(base_img)
    
    def _add_svg_overlay(self, img: Image.Image, svg_string: str) -> Image.Image:
        """Generic method to add any SVG icon overlay"""
        
        img_width, img_height = img.size
        if "legend" in self.keywords:
            img_height = int(img_height * 0.4)
        else:
            img_height = int(img_height * 0.3)
        cx, cy = img_width // 2, img_height
        
        # Convert SVG to PNG
        png_data = svg2png(bytestring=svg_string.encode('utf-8'))
        icon_img = Image.open(BytesIO(png_data)).convert("RGBA")
        
        # Position the icon at the center
        icon_x = cx - icon_img.width // 2
        icon_y = cy - icon_img.height // 2
        
        # Create a copy of the base image and paste the icon
        result = img.convert("RGBA")
        result.paste(icon_img, (icon_x, icon_y), icon_img)
        
        return result
    
    def _add_two_svg_overlay(self, img: Image.Image, svg_string: str) -> Image.Image:
        """Add two SVG overlays: one on the left and one on the right of the card"""

        img_width, img_height = img.size
        if "legend" in self.keywords:
            img_height = int(img_height * 0.4)
        else:
            img_height = int(img_height * 0.3)
        cy = img_height

        # Convert both SVGs to PNG
        png_left = svg2png(bytestring=svg_string.encode('utf-8'))
        png_right = svg2png(bytestring=svg_string.encode('utf-8'))

        icon_left = Image.open(BytesIO(png_left)).convert("RGBA")
        icon_right = Image.open(BytesIO(png_right)).convert("RGBA")

        # Compute horizontal positions (25% and 75% of width)
        left_x = int(img_width * 0.35) - icon_left.width // 2
        right_x = int(img_width * 0.65) - icon_right.width // 2
        icon_y = cy - icon_left.height // 2  # Same vertical for both

        # Paste icons onto a copy of the image
        result = img.convert("RGBA")
        result.paste(icon_left, (left_x, icon_y), icon_left)
        result.paste(icon_right, (right_x, icon_y), icon_right)

        return result

    
    def _darken_image(self, img: Image.Image, ratio: float = 0.6) -> Image.Image:
        return ImageEnhance.Brightness(img.copy()).enhance(ratio)
    
    def _darken_half_image(self, img: Image.Image, ratio: float = 0.6) -> Image.Image:
        """Darken image but leave bottom rectangular area untouched"""
        
        # Easy to modify dimensions
        bottom_rect_width = 670      # Width of the untouched rectangle
        bottom_rect_height = 320     # Height of the untouched rectangle  
        bottom_margin = 60           # Distance from bottom edge
        fade_distance = 20
        
        # Calculate rectangle position
        img_width, img_height = img.size
        rect_x = (img_width - bottom_rect_width) // 2  # Center horizontally
        rect_y = img_height - bottom_rect_height - bottom_margin  # Position from bottom
        
        # Create darkened version of the whole image
        darkened = ImageEnhance.Brightness(img.copy()).enhance(ratio)
        
        # Create mask for the rectangle area with fade
        mask = Image.new("L", img.size, 0)  # Start with all black (darkened)
        mask_draw = ImageDraw.Draw(mask)
        
        # Draw the main white rectangle (full brightness area)
        inner_rect = [rect_x + fade_distance, rect_y + fade_distance, 
                    rect_x + bottom_rect_width - fade_distance, 
                    rect_y + bottom_rect_height - fade_distance]
        mask_draw.rectangle(inner_rect, fill=255)
        
        # Create gradient fade around the edges
        for i in range(fade_distance):
            # Calculate fade intensity (255 at center, 0 at edge)
            fade_intensity = int(255 * (i + 1) / fade_distance)
            
            # Draw expanding rectangles with decreasing intensity
            fade_rect = [rect_x + fade_distance - i, rect_y + fade_distance - i,
                        rect_x + bottom_rect_width - fade_distance + i,
                        rect_y + bottom_rect_height - fade_distance + i]
            mask_draw.rectangle(fade_rect, outline=fade_intensity, width=1)
        
        # Apply gaussian blur to smooth the fade
        mask = mask.filter(ImageFilter.GaussianBlur(radius=fade_distance // 4))
        
        # Composite: where mask is white (255), use original; where black (0), use darkened
        result = Image.composite(img, darkened, mask)
        
        return result

    def _create_accelerate_variant(self, base_img: Image.Image):
        darkened = self._darken_image(base_img)
        modified = self._add_svg_overlay(darkened, '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="480" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevrons-right-icon lucide-chevrons-right"><path d="m6 17 5-5-5-5"/><path d="m13 17 5-5-5-5"/></svg>')
        
        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_discard_variant(self, base_img: Image.Image):
        darkened = self._darken_image(base_img)
        modified = self._add_svg_overlay(darkened, '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="480" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-down-icon lucide-chevron-down"><path d="m6 9 6 6 6-6"/></svg>')
        
        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_play_variant(self, base_img: Image.Image):
        darkened = self._darken_image(base_img)
        modified = self._add_svg_overlay(darkened, '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="480" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-right-icon lucide-chevron-right"><path d="m9 18 6-6-6-6"/></svg>')
        
        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_tap_variant(self, base_img: Image.Image):
        darkened = self._darken_half_image(base_img)
        modified = self._add_svg_overlay(darkened, '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-corner-right-down-icon lucide-corner-right-down"><path d="m10 15 5 5 5-5"/><path d="M4 4h7a4 4 0 0 1 4 4v12"/></svg>')
        
        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_draw_variant(self, base_img: Image.Image):
        darkened = self._darken_image(base_img)
        modified = self._add_svg_overlay(darkened, '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 48" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                                        <rect width="24" height="36" x="0" y="6" rx="2"/>
                                                        <path d="M8 24h8"/>
                                                        <path d="M12 20v8"/>
                                                        </svg>''')

        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_hidden_variant(self, base_img: Image.Image, only_hidden=False):
        darkened = self._darken_image(base_img)
        modified = self._add_svg_overlay(darkened, '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-eye-off-icon lucide-eye-off"><path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/><path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/><path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"/><path d="m2 2 20 20"/></svg>')
        
        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

        if only_hidden:
            return
        # Modified hidden requires another hidden play (eye-off + chevron-right)
        combined_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 48 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <!-- Eye-off icon (left side) -->
        <g transform="translate(0,0)">
        <path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/>
        <path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/>
        <path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"/>
        <path d="m2 2 20 20"/>
        </g>
        <!-- Chevron-right icon (right side) -->
        <g transform="translate(0,-24) scale(3)">
        <path d="m9 18 6-6-6-6"/>
        </g>
        </svg>'''

        modified = self._add_svg_overlay(darkened, combined_svg)
        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_channel_variant(self, base_img: Image.Image):
        darkened = self._darken_image(base_img)
        modified = self._add_svg_overlay(darkened, '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-import-icon lucide-import"><path d="M12 3v12"/><path d="m8 11 4 4 4-4"/><path d="M8 5H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-4"/></svg>''')

        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_damage_variant(self, base_img: Image.Image):
        darkened = self._darken_image(base_img)
        modified = self._add_two_svg_overlay(darkened, '''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-flame-icon lucide-flame"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>''')

        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_stun_variant(self, base_img: Image.Image):
        darkened = self._darken_image(base_img)
        modified = self._add_svg_overlay(darkened, '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shell-icon lucide-shell"><path d="M14 11a2 2 0 1 1-4 0 4 4 0 0 1 8 0 6 6 0 0 1-12 0 8 8 0 0 1 16 0 10 10 0 1 1-20 0 11.93 11.93 0 0 1 2.42-7.22 2 2 0 1 1 3.16 2.44"/></svg>''')

        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_ready_variant(self, base_img: Image.Image):
        darkened = self._darken_image(base_img)
        modified = self._add_svg_overlay(darkened, '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-corner-up-left-icon lucide-corner-up-left"><path d="M20 20v-7a4 4 0 0 0-4-4H4"/><path d="M9 14 4 9l5-5"/></svg>''')

        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_ganking_variant(self, base_img: Image.Image):
        darkened = self._darken_image(base_img)
        modified = self._add_svg_overlay(darkened, '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-arrow-left-right-icon lucide-arrow-left-right"><path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/></svg>''')

        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_kill_variant(self, base_img: Image.Image):
        darkened = self._darken_image(base_img)
        modified = self._add_svg_overlay(darkened, '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-x-icon lucide-x"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>''')

        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def _create_spend_variant(self, base_img: Image.Image):
        darkened = self._darken_image(base_img)
        modified = self._add_svg_overlay(darkened, '''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-arrow-down-icon lucide-arrow-down"><path d="M12 5v14"/><path d="m19 12-7 7-7-7"/></svg>''')

        pixel_id = self.pixelborn_id("a")
        self.pixelborn_internal_numb += 1
        modified.save(os.path.join(FINAL_DIR, f"{pixel_id}.png"))

    def draw_white_circle(self, draw: ImageDraw.ImageDraw): 
        if 'sigspell' in self.keywords:
            cx = 185
            cy = 48
            r = 86
            
            draw.ellipse((cx, cy, cx + r, cy + r), fill="white")
        elif 'spell' in self.keywords and self.rarity == "epic":
            cx = 185
            cy = 48
            r = 86
            
            draw.ellipse((cx, cy, cx + r, cy + r), fill="white")
        elif self.rarity in ["common", "uncommon"]:
            cx = 190
            cy = 52
            r = 79
            
            draw.ellipse((cx, cy, cx + r, cy + r), fill="white")
        elif self.rarity in ["rare", "epic", "legendary"]:
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

print("==== Card Tagging Tool ====")
print("1. Normal art")
print("2. Alt art")
print("3. Sort JSON file")
choice = input("Choose option: ").strip()

if choice == "1":
    ALT_ART = False
elif choice == "2":
    ALT_ART = True
elif choice == "3":
    # Sort the JSON file
    with open(CONFIG_PATH, "r") as f:
        entries = json.load(f)
    
    # Check for duplicates
    seen_ids = {}
    duplicates = []
    for entry in entries:
        card_id = entry["id"]
        if card_id in seen_ids:
            duplicates.append(card_id)
        else:
            seen_ids[card_id] = True
    
    if duplicates:
        print(f"⚠️  Found {len(duplicates)} duplicate cards: {duplicates}")
    
    def sort_config(config):
        def card_sort_key(entry):
            # Extract numeric part from "OGN-001" -> 1
            return int(entry["id"].split("-")[1])
        return sorted(config, key=card_sort_key)
    
    sorted_entries = sort_config(entries)
    
    with open(CONFIG_PATH, "w") as f:
        json.dump(sorted_entries, f, indent=4)
    
    print(f"✅ Sorted {len(sorted_entries)} cards in {CONFIG_PATH}")
    exit()
else:
    ALT_ART = False


SPECIFIC_CARDS = [164, 79, 61] 

# === Load config and process cards ===
with open(CONFIG_PATH, "r") as f:
    entries = json.load(f)
    
    # Filter entries to only include specific card numbers
    if len(SPECIFIC_CARDS) >= 1:
        filtered_entries = []
        for entry in entries:
            # Extract card number from ID (e.g., "OGN-001" -> 1)
            card_num = int(entry["id"].split("-")[1])
            if card_num in SPECIFIC_CARDS:
                filtered_entries.append(entry)
        entries = filtered_entries
        print(f"Processing {len(entries)} specific cards: {SPECIFIC_CARDS}")
    else:
        print(f"Processing all {len(entries)} cards")
    
    cards = [Card.from_dict(entry) for entry in entries]

for card in cards:
    card.process()

# https://lucide.dev/icons/