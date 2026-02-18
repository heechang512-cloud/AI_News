import os
import time
import feedparser
from urllib.parse import urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# =========================
# 설정
# =========================
MAX_ARTICLES = 50
RSS_URL = "https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGRqTVhZU0JXVnVMVWRDR2dKSlRpZ0FQAQ?hl=ko&gl=KR&ceid=KR:ko"

BASE_DIR = os.getcwd()
ASSET_DIR = os.path.join(BASE_DIR, "assets")
#os.makedirs(ASSET_DIR, exist_ok=True)

# =========================
# 수집 유틸리티
# =========================
def extract_press_name(url):
    return urlparse(url).netloc.replace("www.", "").split(".")[0]

def extract_article_date(entry):
    try: return datetime(*entry.published_parsed[:6]).strftime("%Y%m%d")
    except: return datetime.today().strftime("%Y%m%d")

def extract_article_text(page, limit=200):
    try:
        soup = BeautifulSoup(page.content(), "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]): tag.decompose()
        text = soup.get_text(" ", strip=True)
        lines = [l.strip() for l in text.split("  ") if len(l.strip()) > 30]
        return " ".join(lines)[:limit]
    except: return "본문 추출 실패"

def find_article_image_url(page):
    try:
        og = page.locator("meta[property='og:image']").get_attribute("content")
        if og and og.startswith("http"): return og
    except: pass
    return ""

def fetch_weather(page):
    try:
        page.goto("https://search.naver.com/search.naver?query=날씨", wait_until="networkidle")
        temp = page.locator(".temperature_text strong").first.inner_text().replace("현재 온도", "").strip()
        status = page.locator(".before_slash").first.inner_text().strip()
        return {"temp": temp, "status": status}
    except: return {"temp": "N/A", "status": "확인불가"}

# =========================
# 메인 크롤링 (스크린샷 기능 주석 처리)
# =========================
def run_crawler():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 800})

        weather = fetch_weather(page)
        feed = feedparser.parse(RSS_URL)
        articles = []

        for idx, e in enumerate(feed.entries[:MAX_ARTICLES], start=1):
            print(f"[{idx}/{MAX_ARTICLES}] 처리 중: {e.title[:20]}...")
            try:
                # domcontentloaded로 설정하여 텍스트 위주로 빠르게 접근
                page.goto(e.link, timeout=60000, wait_until="domcontentloaded")
                time.sleep(2)
                # [주석 처리] 추후 사용을 위해 스크린샷 로직은 보존하되 실행은 하지 않음
                # shot_name = f"{extract_article_date(e)}_{extract_press_name(e.link)}_{idx:02d}.png"
                # shot_path = os.path.join(ASSET_DIR, shot_name)
                # page.screenshot(path=shot_path, full_page=True)

                # 이미지 URL 추출
                img_url = find_article_image_url(page)
                
                # [수정된 부분] 이미지 URL이 없거나 비어있으면 해당 기사는 추가하지 않고 패스
                if not img_url or img_url.strip() == "":
                    #print(f"   >> 이미지가 없어 이 기사는 제외합니다.")
                    continue
                articles.append({
                    "title": e.title,
                    "link": e.link,
                    "date": extract_article_date(e),
                    "press": extract_press_name(e.link),
                    "content": extract_article_text(page),
                    "image_url": find_article_image_url(page)
                })
            except: continue

        browser.close()
        return articles, weather

# =========================
# HTML 생성 (실시간 갱신 기능 강화)
# =========================
def make_html(articles, weather):
    today = datetime.today().strftime("%Y.%m.%d")
    now_time = datetime.now().strftime("%H:%M") 
    #filename = f"report_{today.replace('.', '')}.html"
    filename = f"index.html"

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
    body {{ background:#f5f5f5; font-family: 'Malgun Gothic', sans-serif; margin:0; }}
    .header {{ background:#fff; padding:15px; border-bottom:2px solid #5f01d1; }}
    .header-content {{ display: flex; align-items: center; max-width: 1200px; margin: auto; }}
    .top-logo {{ height: 40px; margin-right: 20px; }}
    
    .main-layout {{ display: flex; max-width: 1200px; margin: 20px auto; gap: 20px; padding: 0 20px; }}
    .news-area {{ flex: 1; }}
    
    .sidebar {{ width: 280px; position: sticky; top: 20px; height: fit-content; }}
    .weather-box {{ background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; }}
    
    .card {{ background:#fff; display:grid; grid-template-columns:300px 1fr; gap:20px; padding:20px; margin-bottom:20px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1); }}
    .card img {{ width:100%; height:200px; object-fit:cover; border-radius:6px; }}
    
    .footer {{ background: #fff; border-top: 1px solid #ddd; margin-top: 50px; text-align: center; }}
    .footer-img {{ width: 95%; max-width: 1140px; padding: 20px 0; }}
</style>
</head>
<body>

<div class="header">
    <div class="header-content">
        <img src="top.png" class="top-logo">
        <div style="flex-grow:1; text-align:center;">
            <h1 style="margin:0; font-size:22px;">Daily News Report</h1>
            <p style="margin:5px 0 0; font-size:13px; color:#666;">{today} 뉴스 브리핑</p>
        </div>
    </div>
</div>

<div class="main-layout">
    <div class="news-area">
"""
    for a in articles:
        img = a['image_url'] if a['image_url'] else "https://via.placeholder.com/300x200"
        html += f"""
        <div class="card">
            <img src="{img}">
            <div>
                <div style="color:#666; font-size:13px; margin-bottom:8px;">{a['press']} | {a['date']}</div>
                <h2 style="margin:0 0 12px 0; font-size:20px;">{a['title']}</h2>
                <div style="font-size:14px; color:#444; line-height:1.6;">{a['content']}...</div>
                <a href="{a['link']}" target="_blank" style="display:inline-block; margin-top:10px; color:#5f01d1; text-decoration:none; font-weight:bold; font-size:13px;">원문 보기 →</a>
            </div>
        </div>"""

    html += f"""
    </div>
    <div class="sidebar">
        <div class="weather-box">
            <div style="font-weight:bold; color:#5f01d1; margin-bottom:15px;">● Live Weather</div>
            <div style="display:flex; align-items:center; justify-content:center; gap:10px;">
                <span style="font-size: 30px;">☀️</span>
                <span style="font-size: 38px; font-weight: 800;">{weather['temp']}</span>
            </div>
            <div style="font-size: 14px; color: #444; margin-top: 5px; font-weight: 600;">{weather['status']}</div>
            <div style="margin-top: 15px; font-size: 11px; color: #999; border-top: 1px dashed #eee; padding-top: 10px;">
                서울 지역   {now_time}
            </div>
        </div>
    </div>
</div>

<footer class="footer">
    <img src="buttom.png" class="footer-img">
</footer>

<script>
    // 10분(600,000ms)마다 페이지를 새로고침합니다.
    // 파이썬 프로그램을 계속 실행 중이라면, 새로고침 시 수집된 최신 HTML을 다시 불러오게 됩니다.
    setTimeout(function() {{
        location.reload();
    }}, 600000);
</script>

</body>
</html>
"""
    with open(filename, "w", encoding="utf-8") as f: f.write(html)
    print(f"✅ 리포트 생성 완료: {filename} (최근 업데이트: {now_time})")

if __name__ == "__main__":
     # 현재는 1회 실행 후 생성된 파일 내에서 새로고침되도록 구성되었습니다.
    data, weather = run_crawler()
    make_html(data, weather)