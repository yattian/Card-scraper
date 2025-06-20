## Quick Start

**Note 1:** If you're just here for the ZIP file of the images, here you go (paste in Pixelborn settings) - https://archive.org/download/images-final/pixelbornaltart.zip

**Note 2:** I've found out that you don't even need to restart the client after uploading images, just go into cards and scroll to the bottom and back up quickly. 

**Note 3:** Again, this is mostly automated so there may be some problems with the images and Pixelborn.

# Card Scraper for Pixelborn

A Python-based tool for scraping and processing card images from Riftbound, generating custom variants for use with Pixelborn (not affiliated). This tool is designed for personal use only.

![image](https://github.com/user-attachments/assets/c7515757-e682-402a-8bd2-6254356dbdec)

## Features

- **Automated card scraping** with OCR-based keyword detection
- **Rarity detection** using colour analysis
- **Manual configuration** options for fine tuning card metadata
- **Multiple card variants** including accelerate, discard, tap, draw, and hidden versions
- **Alternative artwork** support
- **Pixelborn compatible** output format

**Note:** You can skip to step 4 if you just want to generate the images since I have already uploaded the json files. There will be MORE cards than required. This is because the image to text reader reads keywords like "Discard" and generates a discard variant for Pixelborn. However, some cards do not require that image so it's not needed. This is fine, because Pixelborn won't call on those cards anyway.

1. **Install dependencies:**
   ```bash
   pip install requests pillow pillow-avif json5 easyocr opencv-python numpy cairosvg
   ```

2. **Run the automated scraper:**
   ```bash
   python auto_config.py
   ```
   This will download card images, detect keywords using OCR, and generate initial configuration.

3. **Fine-tune configuration (optional):**
   ```bash
   python manual_config.py
   ```
   Use this to manually correct any incorrect keyword or rarity assignments.

4. **Generate final images:**
   ```bash
   python main.py
   ```
   Choose between normal or alternative artwork when prompted.

5. **Import to Pixelborn:**
   Move the generated images from the `ImagesFinal` folder to your Pixelborn directory - %YOUR USERNAME %\AppData\LocalLow\Rebellious Software\Pixelborn\Cards\Key

## File Structure

```
├── auto_config.py      # Automated scraping and OCR processing
├── manual_config.py    # Manual configuration editor
├── main.py            # Final image generation
├── scraped_cards.json5 # Generated card metadata
├── ImagesFinal/       # Final processed images
├── ImagesPNG/         # Intermediate PNG files
└── assets/            # Template images for OCR
```

## How It Works

### Automated Processing (`auto_config.py`)
- Downloads card images from the Riftbound CDN
- Uses OCR to extract card text and detect keywords
- Analyses bottom section colour to determine rarity
- Detects special symbols (tap icons) using template matching
- Generates initial configuration file

### Manual Configuration (`manual_config.py`)
- Interactive menu system for editing card metadata
- Supports tagging individual cards or ranges
- Keyword management with predefined options
- Rarity assignment with validation
- You can also edit the json5 file directly if required

### Image Generation (`main.py`)
- Resizes and crops images to 1024x1024 format
- Applies keyword specific visual modifications
- Generates multiple variants for cards with special abilities
- Creates darkened overlay versions with appropriate icons
- Outputs Pixelborn compatible naming convention

## Generated Variants

For cards with special abilities, the tool automatically generates multiple versions:
- **Base variant:** Standard card image with visual modifications
- **Ability variants:** Darkened overlays with appropriate icons (e.g., chevron for accelerate, eye-off for hidden)
- **Play variant:** General action variant for cards with multiple abilities

## Requirements

- Python 3.8+
- Required packages: `requests`, `pillow`, `pillow-avif`, `json5`, `easyocr`, `opencv-python`, `numpy`, `cairosvg`
- GPU support recommended for faster OCR processing

## Limitations

- Designed for Riftbound card format only
- OCR accuracy may vary depending on card design
- Manual verification recommended for complex cards

## Made with vibe coding woohoo!

P.S. Thank you community for using my image link! Means a lot to me.

![image](https://github.com/user-attachments/assets/4525f9e5-10c8-4ffa-9a3d-5e7dcf1001a0)

![image](https://github.com/user-attachments/assets/8da96228-c5e2-4af5-a2fa-c5b746b181e6)



---

**Disclaimer:** This tool is for personal use only and is not affiliated with Pixelborn, Riftbound, or any related companies.
