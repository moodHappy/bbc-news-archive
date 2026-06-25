import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timezone, timedelta

BASE_DIR = "docs"
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
        
        now = datetime.now(tz_utc_8)
        current_time = now.strftime("%Y-%m-%d %H:%M")
        
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
    years_data = {}
    
    # 构建数据字典
    years = sorted([d for d in os.listdir(BASE_DIR) if d.isdigit()], key=int, reverse=True)
    for year in years:
        months = sorted([d for d in os.listdir(os.path.join(BASE_DIR, year)) if d.isdigit()], key=int, reverse=True)
        years_data[year] = {}
        for month in months:
            files = sorted([f for f in os.listdir(os.path.join(BASE_DIR, year, month)) if f.endswith('.html')], reverse=True)
            years_data[year][month] = files

    # 生成 HTML 代码片段
    year_buttons_html = ""
    month_grids_html = ""
    articles_html = ""
    
    is_first_year = True
    
    for year, months_dict in years_data.items():
        year_active = "active" if is_first_year else ""
        year_buttons_html += f'<button class="tab-btn {year_active}" data-year="{year}">{year} 年</button>'
        
        month_grid_display = "grid" if is_first_year else "none"
        month_grids_html += f'<div class="month-grid" id="grid-{year}" style="display: {month_grid_display};">'
        
        is_first_month = True
        for month, files in months_dict.items():
            month_active = "active" if is_first_year and is_first_month else ""
            month_grids_html += f'<button class="month-btn {month_active}" data-target-year="{year}" data-target-month="{month}">{month}月</button>'
            
            for file in files:
                file_path = f"{year}/{month}/{file}"
                try:
                    parts = file.replace(".html", "").split('_')
                    time_str = f"{parts[2]}日 {parts[3][:2]}:{parts[3][2:]}"
                except:
                    time_str = file.replace(".html", "")
                    
                article_display = "flex" if is_first_year and is_first_month else "none"
                articles_html += f"""
                    <a href="{file_path}" class="news-item" data-item-year="{year}" data-item-month="{month}" style="display: {article_display};">
                        <span class="news-time">{time_str}</span>
                        <span class="news-title">BBC 突发新闻存档 ➔</span>
                    </a>
                """
            is_first_month = False
        month_grids_html += '</div>'
        is_first_year = False

    index_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>我的 BBC 新闻库</title>
    <style>
        :root {{ --bg: #f5f5f7; --text: #1d1d1f; --muted: #86868b; --accent: #0066cc; --card: #ffffff; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; -webkit-font-smoothing: antialiased; background: var(--bg); color: var(--text); margin: 0; padding: 0; text-align: left; }}
        
        /* 顶部导航区 */
        .header {{ background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); padding: 20px; position: sticky; top: 0; z-index: 100; box-shadow: 0 1px 0 rgba(0,0,0,0.05); }}
        .header h1 {{ margin: 0; font-size: 1.5rem; font-weight: 700; }}
        
        /* 年份横向滚动栏 (隐藏滚动条) */
        .year-tabs {{ display: flex; overflow-x: auto; gap: 12px; margin-top: 15px; padding-bottom: 5px; -webkit-overflow-scrolling: touch; scrollbar-width: none; }}
        .year-tabs::-webkit-scrollbar {{ display: none; }}
        .tab-btn {{ flex-shrink: 0; background: #e5e5ea; color: var(--text); border: none; padding: 8px 18px; border-radius: 20px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: 0.2s; }}
        .tab-btn.active {{ background: var(--text); color: #fff; }}
        
        .container {{ max-width: 600px; margin: 15px auto; padding: 0 15px; padding-bottom: 50px; }}
        
        /* 月份九宫格 */
        .month-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 25px; }}
        .month-btn {{ background: var(--card); border: 1px solid #e5e5ea; color: var(--text); padding: 12px 0; border-radius: 12px; font-size: 1rem; font-weight: 500; cursor: pointer; transition: 0.2s; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
        .month-btn.active {{ background: #f0f7ff; border-color: var(--accent); color: var(--accent); font-weight: 600; }}
        
        /* 新闻列表 */
        .news-list {{ display: flex; flex-direction: column; gap: 10px; }}
        .news-item {{ display: flex; justify-content: space-between; align-items: center; padding: 16px; background: var(--card); border: 1px solid #e5e5ea; border-radius: 14px; text-decoration: none; transition: 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
        .news-item:active {{ transform: scale(0.98); }}
        .news-time {{ font-size: 1rem; font-weight: 600; color: var(--text); }}
        .news-title {{ font-size: 0.9rem; color: var(--muted); }}
        
        /* 列表为空时的提示 */
        #empty-state {{ display: none; text-align: center; padding: 40px 20px; color: var(--muted); font-size: 1rem; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📰 我的 BBC 新闻库</h1>
        <div class="year-tabs">
            {year_buttons_html}
        </div>
    </div>
    
    <div class="container">
        {month_grids_html}
        
        <div class="news-list" id="news-container">
            {articles_html}
            <div id="empty-state">该月份暂无新闻存档</div>
        </div>
    </div>

    <script>
        const yearBtns = document.querySelectorAll('.tab-btn');
        const monthGrids = document.querySelectorAll('.month-grid');
        const monthBtns = document.querySelectorAll('.month-btn');
        const newsItems = document.querySelectorAll('.news-item');
        const emptyState = document.getElementById('empty-state');

        // 切换年份逻辑
        yearBtns.forEach(btn => {{
            btn.addEventListener('click', () => {{
                yearBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const targetYear = btn.getAttribute('data-year');
                
                // 显示对应的月份面板
                monthGrids.forEach(grid => grid.style.display = 'none');
                const targetGrid = document.getElementById('grid-' + targetYear);
                targetGrid.style.display = 'grid';
                
                // 自动选中该年份下的第一个可用月份
                const firstMonthBtn = targetGrid.querySelector('.month-btn');
                if (firstMonthBtn) {{
                    firstMonthBtn.click();
                }} else {{
                    filterNews(targetYear, 'none'); // 清空列表
                }}
            }});
        }});

        // 切换月份逻辑
        monthBtns.forEach(btn => {{
            btn.addEventListener('click', () => {{
                // 移除当前面板下所有月份的激活状态
                const parentGrid = btn.closest('.month-grid');
                parentGrid.querySelectorAll('.month-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const targetYear = btn.getAttribute('data-target-year');
                const targetMonth = btn.getAttribute('data-target-month');
                filterNews(targetYear, targetMonth);
            }});
        }});

        // 过滤新闻列表
        function filterNews(year, month) {{
            let hasVisible = false;
            newsItems.forEach(item => {{
                if (item.getAttribute('data-item-year') === year && item.getAttribute('data-item-month') === month) {{
                    item.style.display = 'flex';
                    hasVisible = true;
                }} else {{
                    item.style.display = 'none';
                }}
            }});
            
            emptyState.style.display = hasVisible ? 'none' : 'block';
        }}
    </script>
</body>
</html>"""
    
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_content)
    print("首页 index.html 强制更新完毕。")

if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    fetch_bbc_news()
    generate_index()
