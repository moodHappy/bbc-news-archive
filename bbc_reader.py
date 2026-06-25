import requests
from bs4 import BeautifulSoup
import os
import json
import re
from collections import Counter
import random
from datetime import datetime, timezone, timedelta

BASE_DIR = "docs"
tz_utc_8 = timezone(timedelta(hours=8))

# 英文停用词表（过滤虚词）
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'of', 'to', 'in', 'for', 'on', 'with', 'at', 'by', 
    'from', 'up', 'about', 'into', 'over', 'after', 'is', 'are', 'was', 'were', 
    'be', 'been', 'has', 'have', 'had', 'it', 'its', 'they', 'their', 'he', 'she', 
    'who', 'whom', 'this', 'that', 'these', 'those', 'as', 'but', 'not', 'or', 'if', 
    'will', 'would', 'can', 'could', 'should', 'says', 'new', 'us', 'uk', 'bbc', 
    'news', 'say', 'more', 'one', 'out', 'first', 'last', 'year', 'two', 'how', 
    'why', 'what', 'i', 'you', 'we', 't', 's', 'can', 'no', 'old', 'day', 'th'
}

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
        .meta {{ font-size: 0.9rem; color: var(--muted); margin-bottom: 30px; display: flex; flex-wrap: nowrap; gap: 10px; align-items: center; white-space: nowrap; overflow-x: auto; scrollbar-width: none; }}
        .meta::-webkit-scrollbar {{ display: none; }}
        .meta span {{ flex-shrink: 0; }}
        .meta a {{ color: var(--accent); text-decoration: none; background: #f0f7ff; padding: 6px 10px; border-radius: 8px; font-weight: 500; transition: background 0.2s; flex-shrink: 0; }}
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
            <a href="../../index.html">🔙 返回应用</a>
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

def get_cloud_tags_html():
    """实时抓取 BBC 首页生成当天的词云 HTML片段"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get("https://www.bbc.com/news", headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = []
        for tag in soup.find_all(['h2', 'h3']):
            t = tag.get_text().strip()
            if t and len(t.split()) > 2:
                headlines.append(t)
                
        all_words = []
        for hl in headlines:
            cleaned = re.sub(r'[^a-zA-Z\s]', '', hl).lower()
            for word in cleaned.split():
                if word not in STOP_WORDS and len(word) > 2:
                    all_words.append(word)
                    
        word_counts = Counter(all_words).most_common(45)
        if not word_counts: return "<p>暂无词频数据</p>", ""
        
        max_count = word_counts[0][1]
        min_count = word_counts[-1][1]
        random.shuffle(word_counts)
        
        tags_html = ""
        colors = ['#1d1d1f', '#0066cc', '#515154', '#bf4800', '#2f5496', '#333333', '#008080']
        for word, count in word_counts:
            if max_count != min_count:
                font_size = 1.0 + (count - min_count) / (max_count - min_count) * 2.2
            else:
                font_size = 2.0
            color = random.choice(colors)
            tags_html += f'<span class="cloud-tag" style="font-size: {font_size:.2f}rem; color: {color};" title="出现 {count} 次">{word}</span>\n'
            
        update_time = datetime.now(tz_utc_8).strftime('%Y-%m-%d %H:%M')
        return tags_html, update_time
    except Exception as e:
        return f"<p>生成词云失败: {e}</p>", ""

def generate_index():
    # ---------- 1. 日历数据构建 ----------
    archive_data = {}
    if os.path.exists(BASE_DIR):
        years = [d for d in os.listdir(BASE_DIR) if d.isdigit()]
        for year in years:
            archive_data[year] = {}
            months = [d for d in os.listdir(os.path.join(BASE_DIR, year)) if d.isdigit()]
            for month in months:
                archive_data[year][month] = {}
                files = sorted([f for f in os.listdir(os.path.join(BASE_DIR, year, month)) if f.endswith('.html')], reverse=True)
                for file in files:
                    try:
                        parts = file.replace(".html", "").split('_')
                        if len(parts) == 4:
                            day = parts[2]
                            time_str = f"{parts[3][:2]}:{parts[3][2:]}"
                            file_path = f"{year}/{month}/{file}"
                            
                            page_title = "BBC 新闻"
                            try:
                                with open(os.path.join(BASE_DIR, year, month, file), 'r', encoding='utf-8') as f_html:
                                    content = f_html.read(2000)
                                    start = content.find('<title>')
                                    end = content.find('</title>')
                                    if start != -1 and end != -1:
                                        page_title = content[start+7:end]
                            except:
                                pass
                            
                            if day not in archive_data[year][month]:
                                archive_data[year][month][day] = []
                                
                            archive_data[year][month][day].append({
                                "time": time_str,
                                "path": file_path,
                                "title": page_title
                            })
                    except Exception:
                        pass
    json_data = json.dumps(archive_data)

    # ---------- 2. 词云数据构建 ----------
    cloud_html, cloud_time = get_cloud_tags_html()

    # ---------- 3. 终极 WebApp 模板 ----------
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>我的 BBC 新闻库</title>
    <style>
        :root {{ --bg: #f5f5f7; --text: #333; --muted: #888; --primary: #0066cc; --border: #e0e0e0; --card: #fff; }}
        body, html {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; -webkit-font-smoothing: antialiased; background: var(--bg); margin: 0; padding: 0; color: var(--text); height: 100%; overflow: hidden; }}
        
        /* 核心 App 骨架 (滑动容器 + 底部导航) */
        .app-viewport {{ display: flex; flex-direction: column; height: 100%; }}
        .views-container {{ flex: 1; display: flex; overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: none; -webkit-overflow-scrolling: touch; }}
        .views-container::-webkit-scrollbar {{ display: none; }}
        .view-page {{ width: 100vw; flex-shrink: 0; scroll-snap-align: start; overflow-y: auto; position: relative; }}
        
        .container {{ max-width: 600px; margin: 0 auto; padding-bottom: 20px; }}
        
        /* ======== 页面 1: 日历样式 ======== */
        .controls {{ background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); padding: 15px 20px; display: flex; justify-content: center; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 10; box-shadow: 0 1px 5px rgba(0,0,0,0.02); }}
        .control-btn {{ background: var(--primary); color: #fff; border: none; border-radius: 6px; padding: 8px 12px; font-size: 14px; cursor: pointer; font-weight: 500; }}
        .control-btn:active {{ opacity: 0.8; transform: scale(0.95); }}
        .select-box {{ padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 15px; background: #fff; outline: none; font-family: inherit; }}
        
        .calendar-wrapper {{ background: var(--card); padding: 15px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
        .weekdays {{ display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; font-weight: 600; font-size: 13px; color: var(--muted); margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #f0f0f0; }}
        .days-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; }}
        
        .day-cell {{ aspect-ratio: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; font-size: 16px; font-weight: 500; border-radius: 10px; cursor: pointer; position: relative; transition: all 0.2s; }}
        .day-cell.empty {{ visibility: hidden; }}
        .day-cell.has-news {{ color: var(--text); }}
        .day-cell.no-news {{ color: #ccc; }}
        
        .day-cell.selected {{ background: #fff0db; border: 1px solid #f5a623; color: #d0021b; font-weight: bold; }}
        .day-cell.today {{ background: #eef5ff; color: var(--primary); font-weight: 600; }}
        .dot {{ width: 5px; height: 5px; background-color: var(--primary); border-radius: 50%; position: absolute; bottom: 6px; display: none; }}
        .day-cell.has-news .dot {{ display: block; }}
        .day-cell.selected .dot {{ background-color: #d0021b; }}
        
        .news-section {{ padding: 0 15px; }}
        .news-item {{ background: var(--card); border-radius: 14px; padding: 18px 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; text-decoration: none; color: var(--text); box-shadow: 0 2px 8px rgba(0,0,0,0.03); overflow: hidden; }}
        .news-item:active {{ transform: scale(0.98); background: #fafafa; }}
        .news-time {{ font-size: 16px; font-weight: 600; flex-shrink: 0; }}
        .news-title {{ font-size: 14px; color: var(--muted); margin-left: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: right; flex: 1; }}
        .empty-state {{ text-align: center; padding: 40px 20px; color: var(--muted); font-size: 14px; }}
        
        /* ======== 页面 2: 词云样式 ======== */
        .cloud-container {{ padding: 25px 20px; }}
        .cloud-header {{ margin-bottom: 25px; padding-top: 10px; }}
        .cloud-header h1 {{ font-size: 1.8rem; font-weight: 700; margin: 0 0 5px 0; }}
        .cloud-header p {{ color: var(--muted); font-size: 0.9rem; margin: 0; }}
        .cloud-card {{ background: var(--card); border-radius: 18px; padding: 30px 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); display: flex; flex-wrap: wrap; gap: 12px 18px; align-items: center; justify-content: flex-start; }}
        .cloud-tag {{ display: inline-block; font-weight: 600; transition: transform 0.2s; cursor: pointer; line-height: 1.2; }}
        .cloud-tag:active {{ transform: scale(1.1); opacity: 0.8; }}
        
        /* ======== 底部导航栏 ======== */
        .bottom-nav {{ height: 60px; background: rgba(255,255,255,0.95); backdrop-filter: blur(15px); border-top: 1px solid #eaeaea; display: flex; justify-content: space-around; align-items: center; padding-bottom: env(safe-area-inset-bottom); flex-shrink: 0; }}
        .nav-item {{ display: flex; flex-direction: column; align-items: center; justify-content: center; width: 50%; height: 100%; color: #999; font-size: 11px; font-weight: 600; cursor: pointer; transition: color 0.2s; }}
        .nav-item.active {{ color: var(--primary); }}
        .nav-icon {{ font-size: 22px; margin-bottom: 3px; }}
    </style>
</head>
<body>
    <div class="app-viewport">
        
        <div class="views-container" id="viewsContainer">
            
            <div class="view-page" id="page-calendar">
                <div class="container">
                    <div class="controls">
                        <button class="control-btn" id="prevBtn">&lt;</button>
                        <select class="select-box" id="yearSelect"></select>
                        <select class="select-box" id="monthSelect">
                            <option value="1">01月</option><option value="2">02月</option><option value="3">03月</option>
                            <option value="4">04月</option><option value="5">05月</option><option value="6">06月</option>
                            <option value="7">07月</option><option value="8">08月</option><option value="9">09月</option>
                            <option value="10">10月</option><option value="11">11月</option><option value="12">12月</option>
                        </select>
                        <button class="control-btn" id="nextBtn">&gt;</button>
                        <button class="control-btn" id="todayBtn">今天</button>
                    </div>

                    <div class="calendar-wrapper">
                        <div class="weekdays">
                            <span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span>
                        </div>
                        <div class="days-grid" id="daysGrid"></div>
                    </div>

                    <div class="news-section">
                        <div id="newsList"></div>
                    </div>
                </div>
            </div>
            
            <div class="view-page" id="page-cloud">
                <div class="container cloud-container">
                    <div class="cloud-header">
                        <h1>☁️ 今日趋势</h1>
                        <p>更新于 {cloud_time} (BBC 首页实时捕捉)</p>
                    </div>
                    <div class="cloud-card">
                        {cloud_html}
                    </div>
                </div>
            </div>
            
        </div>

        <div class="bottom-nav">
            <div class="nav-item active" id="tab-calendar">
                <div class="nav-icon">📅</div>
                <span>归档</span>
            </div>
            <div class="nav-item" id="tab-cloud">
                <div class="nav-icon">📊</div>
                <span>趋势</span>
            </div>
        </div>
        
    </div>

    <script>
        // ================= Tab 切换与滑动同步逻辑 =================
        const container = document.getElementById('viewsContainer');
        const tabs = document.querySelectorAll('.nav-item');
        
        tabs.forEach((tab, index) => {{
            tab.addEventListener('click', () => {{
                const width = window.innerWidth;
                container.scrollTo({{ left: width * index, behavior: 'smooth' }});
            }});
        }});

        container.addEventListener('scroll', () => {{
            const index = Math.round(container.scrollLeft / window.innerWidth);
            tabs.forEach((t, i) => t.classList.toggle('active', i === index));
        }});

        // ================= 日历核心逻辑 =================
        const archiveData = DATA_PLACEHOLDER;
        const today = new Date();
        let currentYear = today.getFullYear();
        let currentMonth = today.getMonth() + 1;
        let selectedDay = today.getDate();
        let selectedYear = currentYear;
        let selectedMonth = currentMonth;

        const yearSelect = document.getElementById('yearSelect');
        const monthSelect = document.getElementById('monthSelect');
        const daysGrid = document.getElementById('daysGrid');
        const newsList = document.getElementById('newsList');

        function initSelects() {{
            const years = Object.keys(archiveData).map(Number).sort((a, b) => b - a);
            if (!years.includes(currentYear)) years.unshift(currentYear);
            
            years.forEach(y => {{
                const opt = document.createElement('option');
                opt.value = y; opt.textContent = y + ' 年';
                yearSelect.appendChild(opt);
            }});
            yearSelect.value = currentYear;
            monthSelect.value = currentMonth;
        }}

        function renderCalendar(year, month) {{
            daysGrid.innerHTML = '';
            const firstDay = new Date(year, month - 1, 1).getDay();
            const startDay = firstDay === 0 ? 7 : firstDay;
            const daysInMonth = new Date(year, month, 0).getDate();
            
            for (let i = 1; i < startDay; i++) {{
                const emptyCell = document.createElement('div');
                emptyCell.className = 'day-cell empty';
                daysGrid.appendChild(emptyCell);
            }}
            
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : {{}};
            
            for (let day = 1; day <= daysInMonth; day++) {{
                const cell = document.createElement('div');
                cell.className = 'day-cell';
                cell.textContent = day;
                
                const dot = document.createElement('div');
                dot.className = 'dot';
                cell.appendChild(dot);
                
                if (monthData[day]) cell.classList.add('has-news');
                else cell.classList.add('no-news');
                
                if (year === today.getFullYear() && month === today.getMonth() + 1 && day === today.getDate()) {{
                    cell.classList.add('today');
                }}
                
                if (year === selectedYear && month === selectedMonth && day === selectedDay) {{
                    cell.classList.add('selected');
                }}
                
                cell.addEventListener('click', () => {{
                    selectedYear = year; selectedMonth = month; selectedDay = day;
                    renderCalendar(year, month);
                    renderNews(year, month, day);
                }});
                
                daysGrid.appendChild(cell);
            }}
        }}

        function renderNews(year, month, day) {{
            newsList.innerHTML = '';
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : null;
            const dayData = monthData ? monthData[day] : null;
            
            if (dayData && dayData.length > 0) {{
                dayData.forEach(news => {{
                    const a = document.createElement('a');
                    a.href = news.path; a.className = 'news-item';
                    a.innerHTML = `<span class="news-time">${{news.time}}</span><span class="news-title">${{news.title}} ➔</span>`;
                    newsList.appendChild(a);
                }});
            }} else {{
                newsList.innerHTML = '<div class="empty-state">当日暂无新闻归档</div>';
            }}
        }}

        yearSelect.addEventListener('change', (e) => renderCalendar(parseInt(e.target.value), parseInt(monthSelect.value)));
        monthSelect.addEventListener('change', (e) => renderCalendar(parseInt(yearSelect.value), parseInt(e.target.value)));

        document.getElementById('prevBtn').addEventListener('click', () => {{
            let m = parseInt(monthSelect.value) - 1; let y = parseInt(yearSelect.value);
            if (m < 1) {{ m = 12; y--; yearSelect.value = y; }}
            monthSelect.value = m; renderCalendar(y, m);
        }});

        document.getElementById('nextBtn').addEventListener('click', () => {{
            let m = parseInt(monthSelect.value) + 1; let y = parseInt(yearSelect.value);
            if (m > 12) {{ m = 1; y++; yearSelect.value = y; }}
            monthSelect.value = m; renderCalendar(y, m);
        }});

        document.getElementById('todayBtn').addEventListener('click', () => {{
            selectedYear = today.getFullYear(); selectedMonth = today.getMonth() + 1; selectedDay = today.getDate();
            yearSelect.value = selectedYear; monthSelect.value = selectedMonth;
            renderCalendar(selectedYear, selectedMonth);
            renderNews(selectedYear, selectedMonth, selectedDay);
        }});

        initSelects();
        renderCalendar(currentYear, currentMonth);
        renderNews(currentYear, currentMonth, selectedDay);
    </script>
</body>
</html>"""

    # 替换占位符并写入文件
    final_html = html_template.replace("DATA_PLACEHOLDER", json_data)
    
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(final_html)
    print("首页 index.html 已更新为 WebApp 形态 (日历 + 词云切换)。")

if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    fetch_bbc_news()
    generate_index()
