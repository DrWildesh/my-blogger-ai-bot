import os
import sys
import datetime
import urllib.request
import xml.etree.ElementTree as ET
import google.generativeai as gemini
from google.oauth2 import service_account
from googleapiclient.discovery import build

# =====================================================================
# CONFIGURATION: Map your 6 Blogs to their respective RSS sources and post times
# =====================================================================
BLOGS_SCHEDULE = {
    # Hour 0, 8, 16 (12:00 AM, 8:00 AM, 4:00 PM) -> Blog 1
    0:  {"blog_id": "2557794244892578706", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"},
    8:  {"blog_id": "2557794244892578706", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"},
    16: {"blog_id": "2557794244892578706", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"},
    
    # Hour 1, 9, 17 (1:00 AM, 9:00 AM, 5:00 PM) -> Blog 2
    1:  {"blog_id": "667277865892510923", "rss": "https://feeds-api.dotdashmeredith.com/v1/rss/google/aa6fe5c4-9f19-4c32-b63e-6e4c19b5a50f"},
    9:  {"blog_id": "667277865892510923", "rss": "https://feeds-api.dotdashmeredith.com/v1/rss/google/aa6fe5c4-9f19-4c32-b63e-6e4c19b5a50f"},
    17: {"blog_id": "667277865892510923", "rss": "https://feeds-api.dotdashmeredith.com/v1/rss/google/aa6fe5c4-9f19-4c32-b63e-6e4c19b5a50f"},

    # Hour 2, 10, 18 (2:00 AM, 10:00 AM, 6:00 PM) -> Blog 3
    2:  {"blog_id": "8694465556513961438", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"},
    10: {"blog_id": "8694465556513961438", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"},
    18: {"blog_id": "8694465556513961438", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"},

    # Hour 3, 11, 19 (3:00 AM, 11:00 AM, 7:00 PM) -> Blog 4
    3:  {"blog_id": "3445866004315418011", "rss": "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRFZ4ZERBU0FtVnVLQUFQAQ?hl=en-US&gl=US&ceid=US:en"},
    11: {"blog_id": "3445866004315418011", "rss": "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRFZ4ZERBU0FtVnVLQUFQAQ?hl=en-US&gl=US&ceid=US:en"},
    19: {"blog_id": "3445866004315418011", "rss": "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRFZ4ZERBU0FtVnVLQUFQAQ?hl=en-US&gl=US&ceid=US:en"},

    # Hour 4, 12, 20 (4:00 AM, 12:00 PM, 8:00 PM) -> Blog 5
    4:  {"blog_id": "4176027887432358295", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en"},
    12: {"blog_id": "4176027887432358295", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en"},
    20: {"blog_id": "4176027887432358295", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en"},

    # Hour 5, 13, 21 (5:00 AM, 1:00 PM, 9:00 PM) -> Blog 6
    5:  {"blog_id": "3478386588551852434", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en"},
    13: {"blog_id": "3478386588551852434", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en"},
    21: {"blog_id": "3478386588551852434", "rss": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN:en"},
}

gemini.configure(api_key=os.environ["GEMINI_API_KEY"])

def fetch_rss_item(rss_url, hour):
    """Selects item index 0, 1, or 2 from RSS based on daily post count."""
    # Maps hour loops to pull unique daily posts (1st, 2nd, or 3rd latest article)
    index_map = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1, 16:2, 17:2, 18:2, 19:2, 20:2, 21:2}
    article_index = index_map.get(hour, 0)

    req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        root = ET.fromstring(response.read())
    
    items = root.findall('.//item')
    if len(items) > article_index:
        target = items[article_index]
        return {
            "title": target.find('title').text,
            "link": target.find('link').text,
            "description": target.find('description').text if target.find('description') is not None else ""
        }
    return None

def generate_post(article):
    """Prompts Gemini to structure a detailed HTML layout."""
    model = gemini.GenerativeModel('gemini-1.5-flash')
    prompt = f"Write an engaging blog post from this news. Title: {article['title']}. Content: {article['description']}. Source: {article['link']}. Output clean HTML markup only, do not wrap in markdown code fence syntax blocks."
    return model.generate_content(prompt).text

def publish_to_blogger(blog_id, title, content):
    """Authenticates using Service Account JSON credentials to post safely."""
    key_data = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    scopes = ['https://googleapis.com']
    creds = service_account.Credentials.from_service_account_info(key_data, scopes=scopes)
    
    service = build('blogger', 'v3', credentials=creds)
    body = {"title": title, "content": content}
    service.posts().insert(blogId=blog_id, body=body).execute()
    print(f"Post successfully created in Blog ID: {blog_id}")

def main():
    current_hour = datetime.datetime.utcnow().hour
    print(f"Current UTC Execution Hour: {current_hour}")
    
    if current_hour not in BLOGS_SCHEDULE:
        print("No blog scheduled for this specific hour. Exiting script.")
        return

    job = BLOGS_SCHEDULE[current_hour]
    print(f"Targeting Blog ID: {job['blog_id']} from RSS source: {job['rss']}")
    
    article = fetch_rss_item(job['rss'], current_hour)
    if not article:
        print("RSS feed structural issue or index empty.")
        return
        
    ai_content = generate_post(article)
    publish_to_blogger(job['blog_id'], article['title'], ai_content)

if __name__ == "__main__":
    main()
