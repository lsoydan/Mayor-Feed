import os
import json
import requests
from openai import OpenAI
from datetime import datetime

client = OpenAI()

MAIN_FEED_ID = "_fSzIxvtfekt0QkYy"
RSS_APP_URL = f"https://rss.app/feeds/v1.1/{MAIN_FEED_ID}.json"
OUTPUT_FILE = "mayor_news.json"

def compile_mayor_dashboard():
    print("Fetching live data from RSS.app...")
    response = requests.get(RSS_APP_URL)
    feed_data = response.json()

    if not feed_data.get("items"):
        print("No news entries discovered. Exiting.")
        return

    # 1. LOAD EXISTING DATA
    existing_items = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_items = existing_data.get("items", [])
        except Exception as e:
            print(f"Could not load existing data: {e}")

    # 2. FIND ONLY THE NEW ITEMS (Deduplicate by URL)
    existing_urls = {item.get("url") for item in existing_items}
    new_items = [item for item in feed_data["items"] if item.get("url") not in existing_urls]

    if not new_items:
        print("No new items to process. Exiting.")
        return

    print(f"Found {len(new_items)} new items. Preparing for AI evaluation...")

    # 3. PREPARE NEW ITEMS FOR AI
    simplified_list = []
    for index, item in enumerate(new_items[:35]): # Still capping at 35 to save tokens
        source = item["authors"][0]["name"] if item.get("authors") else "City Update"
        simplified_list.append({
            "index": index,
            "source": source,
            "title": item.get("title", ""),
            "summary": item.get("content_text", "")[:300]
        })

    # 4. RUN AI EVALUATION (Your existing prompt logic goes here)
    classifier_prompt = """... [Your existing prompt] ..."""
    
    classification_response = client.chat.completions.create(
        model="gpt-4o-mini", # Consider upgrading this (see below)
        messages=[
            {"role": "system", "content": classifier_prompt},
            {"role": "user", "content": json.dumps(simplified_list)}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    try:
        raw_output = classification_response.choices[0].message.content
        parsed_json = json.loads(raw_output)
        highlight_indices = [int(i) for i in parsed_json.get("highlights", [])]
    except Exception as e:
        print(f"Failed parsing indices. Error: {e}")
        highlight_indices = []

    # Assign flags to the new items
    for index, item in enumerate(new_items):
        item["is_highlight"] = 1 if index in highlight_indices else 0

    # 5. MERGE AND SORT
    all_items = new_items + existing_items
    
    # Sort chronologically by date_published (newest first)
    all_items.sort(
        key=lambda x: x.get("date_published", "1970-01-01T00:00:00Z"), 
        reverse=True
    )

    # Keep a rolling buffer of the last 150 items so the file doesn't grow infinitely,
    # ensuring you retain enough history to naturally display ~20 highlights.
    all_items = all_items[:150]

    # ... [Run your Task 2 Executive Briefing generation here] ...
    # For the briefing, you might want to only summarize `new_items` or the top 10 of `all_items`.
    generated_briefing = "Your generated brief..."

    # 6. SAVE UPDATED WORKSPACE
    output_payload = {
        "summary": generated_briefing,
        "items": all_items
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)
        
    print(f"Success! Enriched data written locally to {OUTPUT_FILE}")

if __name__ == "__main__":
    compile_mayor_dashboard()
