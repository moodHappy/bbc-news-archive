import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timezone, timedelta

# GitHub Pages 部署目录
BASE_DIR = "docs"

# 强制设置时区为东八区 (北京时间)，防止 GitHub 服务器使用 UTC 时间
tz_utc_8 = timezone(timedelta(hours=8))

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
            
        record_file = "last_bbc_url.txt"
        last_url = ""
        if os.path.exists(record_file):
            with open(record_file, "r") as f:
                last_url = f.read().strip()
                
        if article_url == last_url:
            print("头条未更新，本次不生成新文章。")
            return
            
        print(f"发现新突发头条: {article_url}")
        with open(record_file, "w") as f:
            f.write(article_url)

        art_res = requests.get(article_url, headers=headers, timeout=10)
        art_soup = BeautifulSoup(art_res.text, 'html.parser')
        
        title_tag = art_soup.find('h1')
        title = title_tag.text.strip() if title_tag else "BBC News"
        
        # 使用北京时间
        now = datetime.now(tz_utc_8)
        current_time = now.strftime("%Y-%m-%d %H:%M")
        
        paragraphs = art_soup.find_all('p')
        content_paragraphs = []
        
        for p in paragraphs:
            text = p.text.strip()
            # 过滤短文本和版权声明
            if len(text.split()) <= 8: continue
            if "Copyright" in text and "BBC" in text: continue
            if "The BBC is not responsible" in text: continue
            if "Read about our approach" in text: continue
            content_paragraphs.append(text)
        
        if content_paragraphs:
            save_article(title, content_paragraphs, current_time, article_url, now)
            
    except Exception as e:
        print(f"抓取错误: {e}")

def save_article(title, paragraphs, pub_date, article_url, now_obj):
    year_str, month_str = str(now_obj.year), str(now_obj.month)
    
    target_dir = os.path.join(BASE_DIR, year_str, month_str)
    os.makedirs(target_dir, exist_ok=True)
    
    filename = f"{now_obj.year}_{now_obj.month}_{now_obj.day}_{now_obj.strftime('%H%M')}.html"
    html_path = os.path.join(target_dir, filename)
    
    p_tags = "\n".join([f"<p>{p}</p>" for p in paragraphs])
    
    # 现代化文章阅读排版，左对齐，Apple 原生字体栈
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{ --bg: #f5f5f7; --card: #ffffff; --text: #1d1d1f; --muted: #86868b; --accent: #0066cc; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; -webkit-font-smoothing: antialiased; text-align: left; font-size: 1.25rem; line-height: 1.7; color: var(--text); background: var(--bg); margin: 0; padding: 0; }}
        .container {{ max-width: 800px; margin: 0 auto; background: var(--card); padding: 40px 25px; min-height: 100vh; box-shadow: 0 4px 24px rgba(0,0,0,0.04); box-sizing: border-box; }}
        h1 {{ font-size: 1.8rem; margin-top: 0; padding-bottom: 15px; border-bottom: 1px solid #e5e5ea; line-height: 1.3; }}
        .meta {{ font-size: 0.95rem; color: var(--muted); margin-bottom: 30px; display: flex; flex-wrap: wrap; gap: 15px; align-items: center; }}
        .meta a {{ color: var(--accent); text-decoration: none; background: #f0f7ff; padding: 6px 12px; border-radius: 8px; font-weight: 500; transition: background 0.2s; }}
        .meta a:hover {{ background: #e1efff; }}
        p {{ margin-bottom: 22px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="meta">
            <span>📅 {pub_date}</span>
            <a href="{article_url}" target="_blank">🔗 阅读原文</a>
            <a href="../../index.html">🔙 返回目录</a>
        </div>
        <div class="content">
            {p_tags}
        </div>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"文章已保存: {html_path}")

def generate_index():
    links_html = ""
    
    # 获取年份并倒序
    years = sorted([d for d in os.listdir(BASE_DIR) if d.isdigit()], key=int, reverse=True)
    is_first_month_overall = True  # 用于标记是否是全站最新的一月
    
    for year in years:
        links_html += f'<div class="year-card"><div class="accordion-header year-header"><span>📚 {year} 年</span><span class="chevron rotate">▶</span></div><div class="accordion-content year-content active" style="display: block;">'
        
        months = sorted([d for d in os.listdir(os.path.join(BASE_DIR, year)) if d.isdigit()], key=int, reverse=True)
        for month in months:
            # 只有全站最新的那一个月份默认展开，其他的收起
            month_active_cls = "active" if is_first_month_overall else ""
            month_chevron = "rotate" if is_first_month_overall else ""
            month_display = "block" if is_first_month_overall else "none"
            
            links_html += f"""
                <div class="month-card">
                    <div class="accordion-header month-header">
                        <span>📅 {month} 月</span>
                        <span class="chevron {month_chevron}">▶</span>
                    </div>
                    <div class="accordion-content month-content {month_active_cls}" style="display: {month_display};">
            """
            
            files = sorted([f for f in os.listdir(os.path.join(BASE_DIR, year, month)) if f.endswith('.html')], reverse=True)
            for file in files:
                file_path = f"{year}/{month}/{file}"
                
                # 解析文件名生成漂亮的时间戳
                try:
                    parts = file.replace(".html", "").split('_')
                    if len(parts) == 4:
                        time_str = f"{parts[2]}日 {parts[3][:2]}:{parts[3][2:]}"
                    else:
                        time_str = file.replace(".html", "")
                except:
                    time_str = file.replace(".html", "")
                    
                links_html += f"""
                        <a href="{file_path}" class="news-item">
                            <span class="news-time">{time_str}</span>
                            <span class="news-title">BBC 突发新闻存档 ➔</span>
                        </a>
                """
            
            links_html += "</div></div>"
            is_first_month_overall = False
        links_html += "</div></div>"

    # 现代化主页排版与交互脚本
    index_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的 BBC 新闻库</title>
    <style>
        :root {{ --bg: #f5f5f7; --text: #1d1d1f; --muted: #86868b; --accent: #0066cc; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; -webkit-font-smoothing: antialiased; background: var(--bg); color: var(--text); margin: 0; padding: 0; text-align: left; }}
        .header {{ background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); padding: 25px 20px; position: sticky; top: 0; z-index: 100; box-shadow: 0 1px 0 rgba(0,0,0,0.05); }}
        .header h1 {{ margin: 0; font-size: 1.6rem; font-weight: 700; }}
        .header p {{ margin: 5px 0 0 0; color: var(--muted); font-size: 0.9rem; }}
        .container {{ max-width: 600px; margin: 20px auto; padding: 0 15px; padding-bottom: 50px; }}
        
        /* 折叠卡片 UI */
        .year-card {{ background: #ffffff; border-radius: 14px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.03); overflow: hidden; }}
        .accordion-header {{ padding: 18px 20px; font-size: 1.15rem; font-weight: 600; cursor: pointer; display: flex; justify-content: space-between; align-items: center; user-select: none; transition: background 0.2s; }}
        .year-header {{ background: #fafafa; border-bottom: 1px solid #f0f0f0; }}
        .accordion-header:hover {{ background: #f0f0f5; }}
        .chevron {{ font-size: 0.8rem; color: var(--muted); transition: transform 0.3s ease; }}
        .chevron.rotate {{ transform: rotate(90deg); }}
        .accordion-content {{ padding: 15px; }}
        
        .month-card {{ border-left: 3px solid var(--accent); margin-bottom: 12px; background: #fdfdfd; border-radius: 0 8px 8px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
        .month-header {{ padding: 14px 16px; font-size: 1.05rem; font-weight: 500; border-bottom: none; }}
        
        /* 新闻列表条目 */
        .news-item {{ display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; margin-bottom: 8px; background: #ffffff; border: 1px solid #e5e5ea; border-radius: 10px; text-decoration: none; transition: all 0.2s ease; }}
        .news-item:hover {{ border-color: var(--accent); box-shadow: 0 2px 10px rgba(0,102,204,0.1); transform: translateY(-1px); }}
        .news-item:last-child {{ margin-bottom: 0; }}
        .news-time {{ font-size: 0.95rem; font-weight: 600; color: var(--text); }}
        .news-title {{ font-size: 0.85rem; color: var(--accent); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📰 我的 BBC 新闻库</h1>
        <p>全自动定时抓取归档</p>
    </div>
    
    <div class="container">
        {links_html}
    </div>

    <script>
        // 处理折叠与展开的交互逻辑
        document.querySelectorAll('.accordion-header').forEach(header => {{
            header.addEventListener('click', () => {{
                const content = header.nextElementSibling;
                const chevron = header.querySelector('.chevron');
                
                if (content.classList.contains('active')) {{
                    content.style.display = 'none';
                    content.classList.remove('active');
                    chevron.classList.remove('rotate');
                }} else {{
                    content.style.display = 'block';
                    content.classList.add('active');
                    chevron.classList.add('rotate');
                }}
            }});
        }});
    </script>
</body>
</html>"""
    
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_content)
    print("首页 index.html 已强制更新！")

if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    fetch_bbc_news()
    # 【核心修复】：无论上一步有没有抓取到新文章，强制无条件重新生成一次精美排版的主页！
    generate_index()
