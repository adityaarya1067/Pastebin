import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime,timezone
import logging

# --- Configurations ---
ARCHIVE_URL = "https://pastebin.com/archive"
RAW_PASTE_URL = "https://pastebin.com/raw/"
KEYWORDS = ["crypto", "bitcoin", "ethereum", "blockchain", "t.me"]
OUTPUT_FILE = "keyword_matches.jsonl"
LOG_FILE = "crawler.log"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# --- Setup logging ---
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

# --- Step 1: Scrape Pastebin Archive for Paste IDs ---
def get_latest_paste_ids():
    response = requests.get(ARCHIVE_URL, headers=HEADERS)
    if response.status_code != 200:
        logging.error("Failed to fetch archive page.")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    paste_links = soup.select("table.maintable tr td a")
    paste_ids = [link['href'].strip("/") for link in paste_links if link['href'].startswith("/")][:30]
    logging.info(f"Fetched {len(paste_ids)} paste IDs from archive.")
    return paste_ids

# --- Step 2 & 3: Fetch Paste and Check for Keywords ---
def check_paste_for_keywords(paste_id):
    url = RAW_PASTE_URL + paste_id
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            logging.warning(f"Failed to fetch paste {paste_id}. Status: {response.status_code}")
            return None
        content = response.text.lower()
        found = [kw for kw in KEYWORDS if kw in content]
        if found:
            return {
                "source": "pastebin",
                "context": f"Found crypto-related content in Pastebin paste ID {paste_id}",
                "paste_id": paste_id,
                "url": url,
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "keywords_found": found,
                "status": "pending"
            }
        else:
            logging.info(f"No keywords found in paste {paste_id}.")
            return None
    except Exception as e:
        logging.error(f"Exception while processing paste {paste_id}: {e}")
        return None

# --- Step 4: Main Routine ---
def main():
    paste_ids = get_latest_paste_ids()
    matches = []

    with open(OUTPUT_FILE, "w") as f:
        for paste_id in paste_ids:
            result = check_paste_for_keywords(paste_id)
            if result:
                json.dump(result, f)
                f.write("\n")
                logging.info(f"Matched keywords in paste {paste_id}.")
            time.sleep(2)  # Basic rate limiting

    logging.info("Finished crawling Pastebin.")

if __name__ == "__main__":
    main()
