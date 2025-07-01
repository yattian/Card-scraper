import requests
from io import BytesIO
from PIL import Image
import pillow_avif
import json5 as json
import easyocr
import numpy as np
import cv2

JSON_DUMP_FILE = "scraped_cards_ogs.json5"

# Simple Card class
class Card:
    def __init__(self, card_num: int):
        self.id = f"OGS-{card_num:03d}"
        self.card_num = card_num
    
    def download_image(self) -> Image.Image | None:
        """Download card image from the website"""
        url = f"https://cdn.rgpub.io/public/live/map/riftbound/latest/OGS/cards/{self.id}/full-desktop-2x.avif"
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
    
    def detect_rarity(self, image: Image.Image) -> str:
        """Detect rarity by analyzing the bottom section of the card"""
        # Much smaller, more focused crop
        width, height = image.size
        left_crop = int(width * 0.49)     # More centered
        right_crop = int(width * 0.51)    # Smaller width  
        top_crop = int(height * 0.935)     # Lower down
        bottom_crop = int(height * 0.95) # Very thin slice
        
        rarity_crop = image.crop((left_crop, top_crop, right_crop, bottom_crop))

        rgb_array = np.array(rarity_crop)
        # Get average RGB values
        avg_rgb = np.mean(rgb_array, axis=(0,1))  # Average across height and width
        
        if avg_rgb[2] < 85:
            detected_rarity = "epic"
        elif avg_rgb[1] < 115:
            detected_rarity = "rare"
        elif avg_rgb[0] < 135:
            detected_rarity = "uncommon"
        else:
            detected_rarity = "common"

        return detected_rarity
    
    def extract_text(self, image: Image.Image) -> str:
        """Extract text from card image using OCR on multiple sections"""
        reader = easyocr.Reader(['en'], gpu=True)
        tap_template_white = cv2.imread('assets/white_on_black_auto.png', cv2.IMREAD_GRAYSCALE)
        tap_template_black = cv2.imread('assets/black_on_white_auto.png', cv2.IMREAD_GRAYSCALE)
        if tap_template_white is None:
            raise FileNotFoundError("WHERE IS TAPPING ICONS")
        
        try:
            width, height = image.size

            top_pct = 0.64
            bottom_pct = 0.69
            top = int(height * top_pct)
            bottom = int(height * bottom_pct)
            width_legend_token = int(width * 0.5)
            legend_section = image.crop((0, top, width_legend_token, bottom))
            
            legend_array = np.array(legend_section)
            results = reader.readtext(legend_array)

            section_text = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Only confident detections
                    section_text.append(text)

            section_text = [word.lower() for word in section_text]

            if "legend" in section_text or "recruit" in section_text or "rune" in section_text:
                # Define sections to process
                sections = [
                    (0.64, 0.69),    # 30-50% from top
                    (0.78, 0.93),    # 50-80% from top
                ]
            else:
                # Define sections to process
                sections = [
                    (0.5, 0.56),    # 30-50% from top
                    (0.67, 0.86),    # 50-80% from top
                ]

            section_texts = []
            
            for i, (top_pct, bottom_pct) in enumerate(sections):
                # Crop the section
                top = int(height * top_pct)
                bottom = int(height * bottom_pct)
                section = image.crop((0, top, width, bottom))
                
                # Save the cropped section
                # section.save(f"section_{self.id}_{i}.png")
                # print(f"  Saved section {i}: section_{self.id}_{i}.png")
                
                # Run OCR on this section
                image_array = np.array(section)
                results = reader.readtext(image_array)
                
                section_text = []
                for (bbox, text, confidence) in results:
                    if confidence > 0.5:  # Only confident detections
                        section_text.append(text)
                # print(i)
                if i == 1:
                    # Convert section to grayscale for template matching
                    section_gray = cv2.cvtColor(np.array(section), cv2.COLOR_RGB2GRAY)
                    
                    # Perform template matching
                    result = cv2.matchTemplate(section_gray, tap_template_white, cv2.TM_CCOEFF_NORMED)
                    result2 = cv2.matchTemplate(section_gray, tap_template_black, cv2.TM_CCOEFF_NORMED)
                    
                    # Set threshold for match confidence
                    threshold = 0.8
                    # print(result.max())
                    # print(result2.max())
                    locations = np.where(result >= threshold)
                    locations2 = np.where(result2 >= threshold)
                    
                    if len(locations[0]) > 0 or len(locations2[0]) > 0:  # If we found matches
                        section_text.append("tap")

                # Add to results (empty string if no text found)
                if section_text:
                    section_texts.append(' '.join(section_text))
                    
                else:
                    section_texts.append("")
            # print(section_texts)
            return section_texts  # Always returns exactly 2 strings
            
        except Exception as e:
            print(f"OCR Error: {e}")
            return ["", ""]
        
    def extract_keywords(self, text: str) -> list:
        """Extract keywords from the card text"""
        keywords = []
        text_type = text[0].lower()
        text_keywords = text[1].lower()

        text_type_map = {
            "unit": "unit",
            "spell": "spell", 
            "gear": "gear",
            "rune": "rune",
            "signature": "sigspell",
            "legend": "legend",
            "champion": "champunit",
            "token": "token",
        }
        
        text_keywords_map = {
            "accelerate": "accelerate",
            "draw": "draw",
            "hidden": "hidden",
            "discard": "discard", 
            "tap": "tap"
        }
        
        for search_term, keyword in text_type_map.items():
            if search_term in text_type:
                keywords.append(keyword)

        if "champunit" in keywords and "unit" in keywords:
            # print(keywords)
            keywords.remove("unit")

        if "token" in keywords and "unit" in keywords:
            keywords.remove("unit")

        if "spell" in keywords and "sigspell" in keywords:
            keywords.remove("spell")

        for search_term, keyword in text_keywords_map.items():
            if search_term in text_keywords:
                if search_term == "hidden":
                    keywords.append(keyword)
                else:
                    if "may" in text_keywords:
                        keywords.append(keyword)

        if "unit" in keywords:
            if "spell" in keywords or "sigspell" in keywords:
                print("############# WARNING UNIT AND SPELL??? #############")
        
        return list(set(keywords))  # Remove duplicates

# Main scraping function
def scrape_cards():
    """Scrape cards and extract text"""
    results = []
    results_data = []
    lst_cards = [1, 2, 40, 44, 53, 273, 4, 66, 78, 77, 89, 247, 248, 275]
    lst_cards = [248]
    lst_cards.sort()

    # for i in lst_cards:
    for i in range(1, 25):
        card = Card(i)
        
        # Download image
        image = card.download_image()
        if image is None:
            continue

        if i >= 275 and i <= 298:
            result = {
                "id": card.id,
                "keywords": ["location"],
                "rarity": "uncommon"
            }
            results.append(result)
            continue
        
        # Extract text
        text = card.extract_text(image)

        # Extract keywords from text
        keywords = card.extract_keywords(text)

        result = {
            "id": card.id,
            "text": text,
        }
        results_data.append(result)
        
        # Detect rarity
        rarity = card.detect_rarity(image)
        
        # Store result
        result = {
            "id": card.id,
            "keywords": keywords,
            "rarity": rarity
        }
        results.append(result)
        
        # print(f"Card {card.id} [{rarity}]: {text[:100]}...")  # Show first 100 chars
    # with open("scraped_cards_data.json5", "w") as f:
    #     json.dump(results_data, f, indent=4)
    # Save results
    # Load existing data if file exists
    try:
        with open(JSON_DUMP_FILE, "r") as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    # Convert to dict for easier lookup by ID
    existing_dict = {item["id"]: item for item in existing_data}

    # Update with new results
    for result in results:
        existing_dict[result["id"]] = result  # This will add new or overwrite existing

    # Convert back to list and save
    updated_data = list(existing_dict.values())

    # Sort the data
    def sort_config(config):
        def card_sort_key(entry):
            # Extract numeric part from "OGN-001" -> 1
            return int(entry["id"].split("-")[1])
        
        return sorted(config, key=card_sort_key)

    sorted_data = sort_config(updated_data)

    with open(JSON_DUMP_FILE, "w") as f:
        json.dump(sorted_data, f, indent=4)

    print(f"Updated {JSON_DUMP_FILE} with {len(results)} cards")

if __name__ == "__main__":
    scrape_cards()