# ======================================================
# Google News RSS → 본문 500자 + 대표이미지 + Screenshot + HTML Report
# Yahoo 스타일 헤더 포함
# ======================================================

import os
import time
import feedparser
import requests
from urllib.parse import urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# =========================
# 설정
# =========================
MAX_ARTICLES = 10
RSS_URL = (
    "https://news.google.com/rss/topics/"
    "CAAqKggKIiRDQkFTRlFvSUwyMHZNRGRqTVhZU0JXVnVMVWRDR2dKSlRpZ0FQAQ"
    "?hl=ko&gl=KR&ceid=KR:ko"
)

BASE_DIR = os.getcwd()
ASSET_DIR = os.path.join(BASE_DIR, "assets")
os.makedirs(ASSET_DIR, exist_ok=True)

# =========================
# 유틸 함수
# =========================
def extract_press_name(url):
    return urlparse(url).netloc.replace("www.", "").split(".")[0]


def extract_article_date(entry):
    try:
        return datetime(*entry.published_parsed[:6]).strftime("%Y%m%d")
    except:
        return datetime.today().strftime("%Y%m%d")


def auto_scroll(page):
    page.evaluate("""
        async () => {
            await new Promise(resolve => {
                let total = 0;
                const step = 600;
                const timer = setInterval(() => {
                    window.scrollBy(0, step);
                    total += step;
                    if (total >= document.body.scrollHeight) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 200);
            });
        }
    """)


def download_image(url, path):
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and len(r.content) > 5000:
            with open(path, "wb") as f:
                f.write(r.content)
            return path
    except:
        pass
    return ""


def extract_article_text(page, limit=500):
    soup = BeautifulSoup(page.content(), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n", strip=True)
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 40]
    joined = " ".join(lines)
    return joined[:limit]


def find_article_image(page, idx, date, press):
    og = page.locator("meta[property='og:image']").get_attribute("content")
    if og:
        path = os.path.join(ASSET_DIR, f"{date}_{press}_{idx:02d}_og.jpg")
        img = download_image(og, path)
        if img:
            return img

    imgs = page.locator("img")
    for i in range(min(imgs.count(), 10)):
        src = imgs.nth(i).get_attribute("src")
        if src and src.startswith("http"):
            path = os.path.join(ASSET_DIR, f"{date}_{press}_{idx:02d}_alt.jpg")
            img = download_image(src, path)
            if img:
                return img
    return ""

# =========================
# RSS 수집
# =========================
def fetch_google_news():
    feed = feedparser.parse(RSS_URL)
    articles = []

    for e in feed.entries[:MAX_ARTICLES]:
        articles.append({
            "title": e.title,
            "link": e.link,
            "date": extract_article_date(e),
            "press": extract_press_name(e.link),
            "content": "",
            "image": "",
            "screenshot": ""
        })

    print(f"✅ RSS 수집 완료: {len(articles)}건")
    return articles

# =========================
# 기사 크롤링
# =========================
def crawl_articles(articles):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for idx, art in enumerate(articles, start=1):
            print(f"\n[{idx}] {art['title']}")
            try:
                page.goto(art["link"], timeout=60000)
                time.sleep(3)

                art["content"] = extract_article_text(page)
                art["image"] = find_article_image(
                    page, idx, art["date"], art["press"]
                )

                auto_scroll(page)
                time.sleep(2)

                shot = os.path.join(
                    ASSET_DIR,
                    f"{art['date']}_{art['press']}_{idx:02d}_full.png"
                )
                page.screenshot(path=shot, full_page=True)
                art["screenshot"] = shot

                print("  ✔ 본문 / 이미지 완료")

            except Exception as e:
                print("  ❌ 오류:", e)

        browser.close()

    return articles

# =========================
# HTML 리포트 생성
# =========================
def generate_html_report(articles):
    today = datetime.today().strftime("%Y.%m.%d")
    #filename = f"report_{today.replace('.', '')}.html"
    filename = f"index.html"

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>News Report {today}</title>
<style>
body {{
  background:#f5f5f5; font-family:Arial; margin:0;
}}
/* ===== Header ===== */
.report-header {{
  background:#fff; padding:18px 24px 10px;
}}
.header-top {{
  display:grid;
  grid-template-columns:220px 1fr 260px;
  align-items:center;
}}
.logo {{
  font-size:28px; font-weight:800; color:#5f01d1;
}}
.logo span {{ color:#111; }}
.header-title h1 {{
  margin:0; font-size:22px;
}}
.header-title p {{
  margin:4px 0 0; font-size:13px; color:#666;
}}
.nav {{
  display:flex; justify-content:flex-end; gap:18px;
  font-weight:600;
}}
.nav .active {{ color:#5f01d1; }}
.header-divider {{
  margin-top:14px; border-bottom:2px solid #e5e5e5;
}}
/* ===== Cards ===== */
.card {{
  background:#fff;
  max-width:1000px;
  margin:20px auto;
  display:grid;
  grid-template-columns:300px 1fr;
  gap:20px;
  padding:20px;
  border-radius:8px;
  box-shadow:0 2px 8px rgba(0,0,0,0.1);
  min-height:220px;
}}
.card img {{
  width:100%; height:200px; object-fit:cover;
  border-radius:6px;
}}
.meta {{ color:#666; font-size:13px; }}
</style>
</head>
<body>

<div class="report-header">
  <div class="header-top">
    <div class="logo">NEWS<span>Report</span></div>
    <div class="header-title">
      <h1>Daily News Report</h1>
      <p>Google News 자동 수집 · {today}</p>
    </div>
    <div class="nav">
      <span class="active">News</span>
      <span>Finance</span>
      <span>Tech</span>
      <span>World</span>
    </div>
  </div>
  <div class="header-divider"></div>
</div>
"""

    for a in articles:
        img = f"<img src='{a['image']}'>" if a["image"] else ""
        html += f"""
<div class="card">
  <div>{img}</div>
  <div>
    <h2>{a['title']}</h2>
    <div class="meta">{a['date']} | {a['press']}</div>
    <p>{a['content']}</p>
    <p><a href="{a['link']}" target="_blank">기사 원문 보기 →</a></p>
  </div>
</div>
"""

    html += "</body></html>"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ HTML 리포트 생성 완료: {filename}")

# =========================
# 실행
# =========================
if __name__ == "__main__":
    articles = fetch_google_news()
    articles = crawl_articles(articles)
    generate_html_report(articles)
