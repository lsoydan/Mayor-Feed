import os
import json
import requests
from openai import OpenAI

# Initialize OpenAI Client (Pulls seamlessly from your GitHub Secrets)
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

    # Extract top 35 records for high-fidelity evaluation
    target_items = feed_data["items"][:35]
    simplified_list = []
    
    for index, item in enumerate(target_items):
        source = item["authors"][0]["name"] if item.get("authors") else "City Update"
        simplified_list.append({
            "index": index,
            "source": source,
            "title": item.get("title", ""),
            "summary": item.get("content_text", "")[:300] # Provide rich summary context
        })

    # --- TASK 1: RUN GLOBAL RELEVANCE HIGHLIGHT SORTING ---
    print("Executing strategic relevance filter via OpenAI...")
    classifier_prompt = """You are a senior executive intelligence officer advising the Mayor of Chattanooga. 
Review this archive of 35 recent city updates across various platforms (including municipal feeds and social media profiles).
Your objective is to evaluate these items globally and isolate entries of clear executive relevance to a city Mayor.

CRITICAL POLICY FILTERS:
- HIGH IMPORTANCE: Capital/infrastructure project milestones, significant budget allocations, City Council voting outcomes, policy or ordinance overhauls, major economic development announcements, or key public program rollouts.
- ADMINISTRATIVE FILLER (IGNORE): Public relations photo-ops, routine safety reminders (e.g., weather awareness), daily park/pool operational updates, neighborhood garbage/cleanup collection alerts, and low-priority flyers.

EVALUATION RULES: Evaluate entirely on content substance. If an item comes from social media but announces a major city project win, select it. If an official city feed post is just a reminder about routine safety rules, ignore it. Do not just pick items from the top of the list. Aim to isolate the top 4 to 8 best available entries.

RESPONSE FORMAT: You must respond with a JSON object containing a key named "highlights" mapped to an array of matching integer indexes.
Example layout: { "highlights": [1, 14, 22] }"""

    # FIXED: Added quotation marks around "content" keys
    classification_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": classifier_prompt},
            {"role": "user", "content": json.dumps(simplified_list)}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    # Parse out indices safely
    try:
        raw_output = classification_response.choices[0].message.content
        parsed_json = json.loads(raw_output)
        highlight_indices = [int(i) for i in parsed_json.get("highlights", [])]
    except Exception as e:
        print(f"Failed parsing indices, using default fallback. Error: {e}")
        highlight_indices = [0, 1, 2, 3, 4]

    # Assign flags back to the master object array
    for index, item in enumerate(feed_data["items"]):
        item["is_highlight"] = 1 if index in highlight_indices else 0


    # --- TASK 2: GENERATE THE EXECUTIVE SUMMARY BRIEFING ---
    print("Generating executive intelligence brief...")
    briefing_prompt = """You are an elite, concise Chief of Staff drafting a high-level briefing for the Mayor of Chattanooga. 
Review the provided stream of city data and generate an ultra-short executive summary.

CRITICAL FORMATTING RULES:
1. DO NOT use markdown asterisks (like **text**). The system cannot render them.
2. Use raw, basic HTML formatting tags to structure your response. Use <strong>text</strong> for emphasis, and <ul> with <li> for bullet lists.
3. Keep the entire brief restricted to a maximum of 3 highly focused bullet points.
4. Focus only on high-level operational impacts, programmatic milestones, or strategic policy notes. Cut out administrative filler."""

    # Compile the top 10 updates for text summary extraction
    summary_corpus = ""
    for item in feed_data["items"][:10]:
        src = item["authors"][0]["name"] if item.get("authors") else "City News"
        summary_corpus += f"Source: {src}\nTitle: {item.get('title')}\nDetails: {item.get('content_text', '')[:200]}\n\n"

    # FIXED: Added quotation marks around "content" keys here as well
    briefing_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": briefing_prompt},
            {"role": "user", "content": summary_corpus}
        ],
        temperature=0.2
    )
    
    generated_briefing = briefing_response.choices[0].message.content


    # --- TASK 3: SAVE UNIFIED WORKSPACE PACKAGE ---
    output_payload = {
        "summary": generated_briefing,
        "items": feed_data["items"]
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)
        
    print(f"Success! Enriched data written locally to {OUTPUT_FILE}")

if __name__ == "__main__":
    compile_mayor_dashboard()
