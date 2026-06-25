import requests
from bs4 import BeautifulSoup
import os
import json
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
            <a href="../../index.html">🔙 返回日历</a>
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
    archive_data = {}
    
    # 扫描目录，构建 JSON 数据结构: { year: { month: { day: [ {time, path} ] } } }
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
                        # 文件名格式: YYYY_M_D_HHMM.html
                        parts = file.replace(".html", "").split('_')
                        if len(parts) == 4:
                            day = parts[2]
                            time_str = f"{parts[3][:2]}:{parts[3][2:]}"
                            file_path = f"{year}/{month}/{file}"
                            
                            if day not in archive_data[year][month]:
                                archive_data[year][month][day] = []
                                
                            archive_data[year][month][day].append({
                                "time": time_str,
                                "path": file_path
                            })
                    except Exception:
                        pass

    # 将 Python 字典转为 JSON 字符串注入到前端
    json_data = json.dumps(archive_data)

    # 前端 HTML 模板 (使用占位符避免转义花括号的麻烦)
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>我的 BBC 新闻库</title>
    <style>
        :root { --bg: #f5f5f7; --text: #333; --muted: #888; --primary: #4a88f7; --border: #e0e0e0; --card: #fff; }
        body { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; -webkit-font-smoothing: antialiased; background: var(--bg); margin: 0; padding: 0; color: var(--text); }
        
        .container { max-width: 600px; margin: 0 auto; background: var(--bg); min-height: 100vh; display: flex; flex-direction: column; }
        
        /* 顶部控制区 */
        .controls { background: var(--card); padding: 15px 20px; display: flex; justify-content: center; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 10; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }
        .control-btn { background: var(--primary); color: #fff; border: none; border-radius: 4px; padding: 8px 12px; font-size: 14px; cursor: pointer; }
        .control-btn:active { opacity: 0.8; }
        .select-box { padding: 6px 10px; border: 1px solid var(--border); border-radius: 4px; font-size: 15px; background: #fff; outline: none; }
        
        /* 日历区 */
        .calendar-wrapper { background: var(--card); padding: 10px 15px 20px 15px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
        .weekdays { display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
        .days-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; }
        
        .day-cell { aspect-ratio: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; font-size: 16px; font-weight: 500; border-radius: 8px; cursor: pointer; position: relative; transition: all 0.2s; }
        .day-cell.empty { visibility: hidden; }
        .day-cell.has-news { color: var(--text); }
        .day-cell.no-news { color: #ccc; }
        
        /* 选中状态和指示灯 */
        .day-cell.selected { background: #fff0db; border: 1px solid #f5a623; color: #d0021b; font-weight: bold; }
        .day-cell.today { background: #eef5ff; color: var(--primary); }
        .dot { width: 4px; height: 4px; background-color: var(--primary); border-radius: 50%; position: absolute; bottom: 8px; display: none; }
        .day-cell.has-news .dot { display: block; }
        .day-cell.selected .dot { background-color: #d0021b; }
        
        /* 新闻列表区 */
        .news-section { flex: 1; padding: 0 15px 30px 15px; }
        .date-header { font-size: 18px; font-weight: bold; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }
        .news-item { background: var(--card); border-radius: 12px; padding: 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; text-decoration: none; color: var(--text); box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
        .news-item:active { transform: scale(0.98); }
        .news-time { font-size: 16px; font-weight: 600; }
        .news-title { font-size: 14px; color: var(--muted); }
        
        .empty-state { text-align: center; padding: 40px 20px; color: var(--muted); }
    </style>
</head>
<body>
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
            <button class="control-btn" id="todayBtn">回到今天</button>
        </div>

        <div class="calendar-wrapper">
            <div class="weekdays">
                <span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span>
            </div>
            <div class="days-grid" id="daysGrid"></div>
        </div>

        <div class="news-section">
            <div class="date-header" id="selectedDateDisplay">选中日期</div>
            <div id="newsList"></div>
        </div>
    </div>

    <script>
        const archiveData = DATA_PLACEHOLDER;
        
        // 获取当前真实时间作为基准
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
        const selectedDateDisplay = document.getElementById('selectedDateDisplay');

        // 初始化年份下拉框 (从数据中提取有的年份，或者填入当前年)
        function initSelects() {
            const years = Object.keys(archiveData).map(Number).sort((a, b) => b - a);
            if (!years.includes(currentYear)) years.unshift(currentYear);
            
            years.forEach(y => {
                const opt = document.createElement('option');
                opt.value = y; opt.textContent = y + ' 年';
                yearSelect.appendChild(opt);
            });
            yearSelect.value = currentYear;
            monthSelect.value = currentMonth;
        }

        // 渲染日历网格
        function renderCalendar(year, month) {
            daysGrid.innerHTML = '';
            
            // 计算该月第一天是星期几 (0是周日，转为1-7)
            const firstDay = new Date(year, month - 1, 1).getDay();
            const startDay = firstDay === 0 ? 7 : firstDay;
            
            // 计算该月有几天
            const daysInMonth = new Date(year, month, 0).getDate();
            
            // 填充前面的空白
            for (let i = 1; i < startDay; i++) {
                const emptyCell = document.createElement('div');
                emptyCell.className = 'day-cell empty';
                daysGrid.appendChild(emptyCell);
            }
            
            // 填充日期
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : {};
            
            for (let day = 1; day <= daysInMonth; day++) {
                const cell = document.createElement('div');
                cell.className = 'day-cell';
                cell.textContent = day;
                
                const dot = document.createElement('div');
                dot.className = 'dot';
                cell.appendChild(dot);
                
                // 判断状态
                if (monthData[day]) {
                    cell.classList.add('has-news');
                } else {
                    cell.classList.add('no-news');
                }
                
                if (year === today.getFullYear() && month === today.getMonth() + 1 && day === today.getDate()) {
                    cell.classList.add('today');
                }
                
                if (year === selectedYear && month === selectedMonth && day === selectedDay) {
                    cell.classList.add('selected');
                }
                
                // 点击事件
                cell.addEventListener('click', () => {
                    selectedYear = year;
                    selectedMonth = month;
                    selectedDay = day;
                    renderCalendar(year, month); // 重新渲染刷新选中样式
                    renderNews(year, month, day);
                });
                
                daysGrid.appendChild(cell);
            }
        }

        // 渲染新闻列表
        function renderNews(year, month, day) {
            selectedDateDisplay.textContent = `${year}年 ${month}月 ${day}日`;
            newsList.innerHTML = '';
            
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : null;
            const dayData = monthData ? monthData[day] : null;
            
            if (dayData && dayData.length > 0) {
                dayData.forEach(news => {
                    const a = document.createElement('a');
                    a.href = news.path;
                    a.className = 'news-item';
                    a.innerHTML = `<span class="news-time">${day}日 ${news.time}</span><span class="news-title">BBC 突发新闻存档 ➔</span>`;
                    newsList.appendChild(a);
                });
            } else {
                newsList.innerHTML = '<div class="empty-state">当日暂无新闻归档</div>';
            }
        }

        // 事件监听
        yearSelect.addEventListener('change', (e) => {
            renderCalendar(parseInt(e.target.value), parseInt(monthSelect.value));
        });
        
        monthSelect.addEventListener('change', (e) => {
            renderCalendar(parseInt(yearSelect.value), parseInt(e.target.value));
        });

        document.getElementById('prevBtn').addEventListener('click', () => {
            let m = parseInt(monthSelect.value) - 1;
            let y = parseInt(yearSelect.value);
            if (m < 1) { m = 12; y--; yearSelect.value = y; }
            monthSelect.value = m;
            renderCalendar(y, m);
        });

        document.getElementById('nextBtn').addEventListener('click', () => {
            let m = parseInt(monthSelect.value) + 1;
            let y = parseInt(yearSelect.value);
            if (m > 12) { m = 1; y++; yearSelect.value = y; }
            monthSelect.value = m;
            renderCalendar(y, m);
        });

        document.getElementById('todayBtn').addEventListener('click', () => {
            selectedYear = today.getFullYear();
            selectedMonth = today.getMonth() + 1;
            selectedDay = today.getDate();
            yearSelect.value = selectedYear;
            monthSelect.value = selectedMonth;
            renderCalendar(selectedYear, selectedMonth);
            renderNews(selectedYear, selectedMonth, selectedDay);
        });

        // 初始启动
        initSelects();
        renderCalendar(currentYear, currentMonth);
        renderNews(currentYear, currentMonth, selectedDay);
    </script>
</body>
</html>"""

    # 替换占位符生成最终 HTML
    final_html = html_template.replace("DATA_PLACEHOLDER", json_data)
    
    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(final_html)
    print("首页 index.html 已更新为动态日历模式。")

if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    fetch_bbc_news()
    generate_index()
