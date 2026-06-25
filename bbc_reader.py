import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 我们把所有生成的网页统一放到 docs 文件夹里，方便 GitHub Pages 读取
BASE_DIR = "docs"

def fetch_bbc_news():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("正在解析 BBC News 首页...")
    try:
        response = requests.get("https://www.bbc.com/news", headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        article_url = None
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if '/news/articles/' in href:
                article_url = "https://www.bbc.com" + href if href.startswith('/') else href
                break
                
        if not article_url:
            print("未找到文章链接。")
            return
            
        # 记录最新一条新闻的链接，避免重复抓取
        record_file = "last_bbc_url.txt"
        last_url = ""
        if os.path.exists(record_file):
            with open(record_file, "r") as f:
                last_url = f.read().strip()
                
        if article_url == last_url:
            print("头条未更新，停止抓取。")
            return
            
        print(f"发现新突发头条: {article_url}")
        with open(record_file, "w") as f:
            f.write(article_url)

        art_res = requests.get(article_url, headers=headers, timeout=10)
        art_soup = BeautifulSoup(art_res.text, 'html.parser')
        
        title_tag = art_soup.find('h1')
        title = title_tag.text.strip() if title_tag else "BBC News"
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        paragraphs = art_soup.find_all('p')
        content_paragraphs = []
        
        for p in paragraphs:
            text = p.text.strip()
            if len(text.split()) <= 8: continue
            if "Copyright" in text and "BBC" in text: continue
            if "The BBC is not responsible" in text: continue
            if "Read about our approach" in text: continue
            content_paragraphs.append(text)
        
        if content_paragraphs:
            save_article(title, content_paragraphs, current_time, article_url)
            generate_index() # 每次抓取完，重新生成一次导航页
            
    except Exception as e:
        print(f"抓取错误: {e}")

def save_article(title, paragraphs, pub_date, article_url):
    now = datetime.now()
    year_str, month_str = str(now.year), str(now.month)
    
    target_dir = os.path.join(BASE_DIR, year_str, month_str)
    os.makedirs(target_dir, exist_ok=True)
    
    filename = f"{now.year}_{now.month}_{now.day}_{now.strftime('%H%M')}.html"
    html_path = os.path.join(target_dir, filename)
    
    p_tags = "\n".join([f"<p>{p}</p>" for p in paragraphs])
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; font-size: 1.2rem; line-height: 1.6; color: #333; padding: 20px; max-width: 800px; margin: 0 auto; }}
        h1 {{ font-size: 1.5rem; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        .meta {{ font-size: 0.9rem; color: #888; margin-bottom: 20px; }}
        a {{ color: #0066cc; text-decoration: none; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="meta">📅 {pub_date} | 🔗 <a href="{article_url}" target="_blank">阅读原文</a> | 🔙 <a href="../../index.html">返回首页</a></div>
    {p_tags}
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"文章已保存: {html_path}")

def generate_index():
    # 自动扫描 docs 文件夹，生成包含所有新闻的 index.html
    links_html = ""
    
    # 倒序遍历年份和月份，让最新的新闻排在最前面
    years = sorted([d for d in os.listdir(BASE_DIR) if d.isdigit()], reverse=True)
    for year in years:
        months = sorted([d for d in os.listdir(os.path.join(BASE_DIR, year)) if d.isdigit()], reverse=True)
        for month in months:
            links_html += f"<h2>{year}年 {month}月</h2><ul>"
            month_path = os.path.join(BASE_DIR, year, month)
            files = sorted([f for f in os.listdir(month_path) if f.endswith('.html')], reverse=True)
            for file in files:
                file_path = f"{year}/{month}/{file}"
                # 简单地用文件名作为显示的文字
                display_name = file.replace(".html", "")
                links_html += f"<li><a href='{file_path}'>{display_name}</a></li>"
            links_html += "</ul>"

    index_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的 BBC 新闻库</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; line-height: 1.6; }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        a {{ color: #0066cc; text-decoration: none; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin-bottom: 10px; padding-bottom: 5px; border-bottom: 1px dashed #eee; }}
    </style>
</head>
<body>
    <h1>📰 我的 BBC 新闻库</h1>
    <p>全自动定时抓取归档</p>
    {links_html}
</body>
</html>"""
    
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_content)
    print("首页 index.html 已更新。")

if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    fetch_bbc_news()
