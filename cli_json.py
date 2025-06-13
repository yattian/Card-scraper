import json5 as json
import os

CONFIG_FILE = "card_config.json5"
MAX_CARD_ID = 298

KEYWORD_MENU = {
    "1": "unit",
    "2": "spell",
    "3": "accelerate",
    "4": "gear",
    "5": "tap",
    "6": "draw",
    "7": "hidden",
    "8": "rune",
    "9": "discard",
    "10": "sigspell",
    "11": "leader",
    "12": "champunit",
    "v": "next",
    "q": "quit"
}


RARITY_MAP = {
    "1": "common",
    "2": "uncommon",
    "3": "rare",
    "4": "epic",
    "5": "legendary",
    "6": ""
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return []


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    print(f"💾 Config saved to {CONFIG_FILE}")


def tag_single(card_id, config):
    print(f"\n📝 Tagging card: {card_id}")
    keywords = []

    while True:
        print("\nSelect a keyword to add:")
        for key, val in KEYWORD_MENU.items():
            print(f"{key}: {val}")

        choice = input("Choice: ").strip()
        if choice == "v":
            break
        elif choice == "q":
            save_config(config)
            print("👋 Exiting early.")
            exit()
        elif choice in KEYWORD_MENU:
            kw = KEYWORD_MENU[choice]
            if kw not in keywords:
                keywords.append(kw)
                print(f"✅ Added: {kw}")
                print("Keywords: ", keywords)
            else:
                print("⚠️ Already added.")
        else:
            print("❌ Invalid choice.")

    # Select rarity
    rarity = None
    while rarity is None:
        print("\nSelect rarity:")
        for key, val in RARITY_MAP.items():
            print(f"{key}: {val}")
        r_choice = input("Rarity (1–6): ").strip()
        if r_choice in RARITY_MAP:
            rarity = RARITY_MAP[r_choice]
            print(f"🎖️ Rarity set: {rarity}")
        else:
            print("❌ Invalid rarity, enter 1–5.")

    # Update config
    new_entry = {"id": card_id, "keywords": keywords, "rarity": rarity}
    for i, entry in enumerate(config):
        if entry["id"] == card_id:
            config[i] = new_entry
            break
    else:
        config.append(new_entry)

    return config


def tag_range(config, start, end):
    for i in range(start, end + 1):
        card_id = f"OGN-{i:03}"
        config = tag_single(card_id, config)
    return config


def tag_all_prompt(config):
    print(f"📋 Tagging range of cards (1–{MAX_CARD_ID})")
    while True:
        try:
            start = int(input("Start card number: "))
            end = int(input("End card number: "))
            if 1 <= start <= end <= MAX_CARD_ID:
                return tag_range(config, start, end)
            else:
                print("❌ Range must be within 1–298.")
        except ValueError:
            print("❌ Please enter valid integers.")


def tag_one(config):
    while True:
        raw = input("Enter card number (1–298): ").strip()
        if raw.isdigit():
            i = int(raw)
            if 1 <= i <= MAX_CARD_ID:
                card_id = f"OGN-{i:03}"
                return tag_single(card_id, config)
            else:
                print("❌ Number out of range. Try again.")
        else:
            print("❌ Invalid input. Enter a number.")


def sort_config(config):
    def card_sort_key(entry):
        # Extract numeric part from "OGN-001" -> 1
        return int(entry["id"].split("-")[1])
    
    return sorted(config, key=card_sort_key)


def sort_only():
    config = load_config()
    sorted_config = sort_config(config)
    save_config(sorted_config)


def main():
    config = load_config()

    print("==== Card Tagging Tool ====")
    print("1. Tag range of cards")
    print("2. Tag single card")
    print("3. Sort")
    choice = input("Choose option: ").strip()

    if choice == "1":
        config = tag_all_prompt(config)
    elif choice == "2":
        config = tag_one(config)
    elif choice == "3":
        config = load_config()
        config = sort_config(config)
    else:
        print("❌ Invalid menu choice.")
        return

    save_config(config)


if __name__ == "__main__":
    main()
