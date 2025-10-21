import time
import json
import requests
from bs4 import BeautifulSoup
from telegram import Bot, InputMediaPhoto, InputMediaVideo
import os

# ====== Налаштування через Environment Variables ======
TELEGRAM_BOT_TOKEN = os.getenv("8230816153:AAES92dghbu2n2s5yOefp872kmKugAC6CHU")
CHANNEL_ID = os.getenv("@kwlxessprod")
CHECK_INTERVAL = 300  # 5 хвилин
PROFILE_URL = "https://x.com/fortnite?s=21"
STORAGE_FILE = "posted_ids.json"
GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ru&dt=t&q="
# ========================================================

bot = Bot(token=8230816153:AAES92dghbu2n2s5yOefp872kmKugAC6CHU)

def load_posted():
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_posted(s):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(s), f, ensure_ascii=False, indent=2)

def translate_google(text):
    url = GOOGLE_TRANSLATE_URL + requests.utils.quote(text)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    try:
        return "".join([item[0] for item in resp.json()[0]])
    except Exception:
        return text

def fetch_latest_posts(profile_url):
    r = requests.get(profile_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    posts = []

    for post in soup.find_all("div", attrs={"data-testid":"tweet"}):
        text_blocks = post.find_all("div", {"lang": True})
        if not text_blocks:
            continue
        text = " ".join(tb.get_text(separator="\n") for tb in text_blocks).strip()
        tweet_id = post.get("data-tweet-id") or hash(text)
        link = f"https://x.com/fortnite/status/{tweet_id}"

        images = []
        videos = []

        for img in post.find_all("img", {"alt": "Image"}):
            img_url = img.get("src")
            if img_url:
                images.append(img_url)

        for video_tag in post.find_all("video"):
            video_src = video_tag.get("src")
            if video_src:
                videos.append(video_src)

        posts.append({
            "id": str(tweet_id),
            "text": text,
            "link": link,
            "images": images,
            "videos": videos
        })
    return posts

def post_to_telegram(post):
    translated_text = translate_google(post["text"][:4000])
    caption = f"{translated_text}\n\n🔗 Источник: {post['link']}"

    media_group = []

    for img in post["images"]:
        media_group.append(InputMediaPhoto(media=img))
    for vid in post["videos"]:
        media_group.append(InputMediaVideo(media=vid))

    if media_group:
        media_group[0].caption = caption
        bot.send_media_group(chat_id=CHANNEL_ID, media=media_group)
    else:
        bot.send_message(chat_id=CHANNEL_ID, text=caption, parse_mode="HTML", disable_web_page_preview=False)

def main_loop():
    posted = load_posted()
    while True:
        try:
            posts = fetch_latest_posts(PROFILE_URL)
            for post in reversed(posts):
                if post["id"] in posted:
                    continue
                post_to_telegram(post)
                posted.add(post["id"])
                save_posted(posted)
                time.sleep(2)
        except Exception as e:
            print("Error:", e)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
