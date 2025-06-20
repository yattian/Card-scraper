import json5 as json

def compare_card_files():
    """Compare scraped_cards.json5 and scraped_cards_tester.json5 for differences"""
    try:
        # Load both files
        with open("scraped_cards.json5", "r") as f:
            main_data = json.load(f)
        
        with open("scraped_cards_tester.json5", "r") as f:
            tester_data = json.load(f)
        
        # Convert to dictionaries for easier comparison
        main_dict = {item["id"]: item for item in main_data}
        tester_dict = {item["id"]: item for item in tester_data}
        
        # Find common IDs
        main_ids = set(main_dict.keys())
        tester_ids = set(tester_dict.keys())
        common_ids = main_ids & tester_ids
        
        print(f"Comparing {len(main_data)} cards in main file vs {len(tester_data)} cards in tester file")
        print(f"Found {len(common_ids)} common card IDs")
        
        # Cards only in main file
        only_in_main = main_ids - tester_ids
        if only_in_main:
            print(f"\nCards only in main file ({len(only_in_main)}): {sorted(only_in_main)}")
        
        # Cards only in tester file
        only_in_tester = tester_ids - main_ids
        if only_in_tester:
            print(f"\nCards only in tester file ({len(only_in_tester)}): {sorted(only_in_tester)}")
        
        # Compare common cards
        differences = []
        
        for card_id in sorted(common_ids):
            main_card = main_dict[card_id]
            tester_card = tester_dict[card_id]
            
            # Compare keywords
            main_keywords = set(main_card.get("keywords", []))
            tester_keywords = set(tester_card.get("keywords", []))
            
            # Compare rarity
            main_rarity = main_card.get("rarity", "unknown")
            tester_rarity = tester_card.get("rarity", "unknown")
            
            # Check for differences
            keyword_diff = main_keywords != tester_keywords
            rarity_diff = main_rarity != tester_rarity
            
            if keyword_diff or rarity_diff:
                diff_info = {
                    "id": card_id,
                    "keyword_diff": keyword_diff,
                    "rarity_diff": rarity_diff
                }
                
                if keyword_diff:
                    diff_info["keywords_main"] = sorted(main_keywords)
                    diff_info["keywords_tester"] = sorted(tester_keywords)
                    diff_info["keywords_added"] = sorted(tester_keywords - main_keywords)
                    diff_info["keywords_removed"] = sorted(main_keywords - tester_keywords)
                
                if rarity_diff:
                    diff_info["rarity_main"] = main_rarity
                    diff_info["rarity_tester"] = tester_rarity
                
                differences.append(diff_info)
        
        # Display results
        if differences:
            print(f"\n=== FOUND {len(differences)} DIFFERENCES ===")
            for diff in differences:
                print(f"\n{diff['id']}:")
                
                if diff["keyword_diff"]:
                    print(f"  Keywords:")
                    print(f"    Main:   {diff['keywords_main']}")
                    print(f"    Tester: {diff['keywords_tester']}")
                    if diff["keywords_added"]:
                        print(f"    Added:  {diff['keywords_added']}")
                    if diff["keywords_removed"]:
                        print(f"    Removed: {diff['keywords_removed']}")
                
                if diff["rarity_diff"]:
                    print(f"  Rarity:")
                    print(f"    Main:   {diff['rarity_main']}")
                    print(f"    Tester: {diff['rarity_tester']}")
        else:
            print(f"\n✅ No differences found in common cards!")
        
        return differences
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return []
    except Exception as e:
        print(f"❌ Error comparing files: {e}")
        return []

if __name__ == "__main__":
    compare_card_files()