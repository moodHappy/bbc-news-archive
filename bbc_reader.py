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
    # --- 新增：保留之前的置顶数据 ---
    pinned_paths = set()
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()
                start_marker = "/*DATA_START*/"
                end_marker = "/*DATA_END*/"
                start = content.find(start_marker)
                end = content.find(end_marker)
                if start != -1 and end != -1:
                    old_json_str = content[start+len(start_marker):end]
                    old_data = json.loads(old_json_str)
                    for y_data in old_data.values():
                        for m_data in y_data.values():
                            for d_data in m_data.values():
                                for item in d_data:
                                    if item.get("pinned"):
                                        pinned_paths.add(item["path"])
        except Exception as e:
            print(f"读取历史置顶状态失败: {e}")

    archive_data = {}

    if os.path.exists(BASE_DIR):
        years = [d for d in os.listdir(BASE_DIR) if d.isdigit()]
        for year in years:
            y_key = str(int(year)) 
            if y_key not in archive_data:
                archive_data[y_key] = {}

            months = [d for d in os.listdir(os.path.join(BASE_DIR, year)) if d.isdigit()]
            for month in months:
                m_key = str(int(month)) 
                if m_key not in archive_data[y_key]:
                    archive_data[y_key][m_key] = {}

                files = sorted([f for f in os.listdir(os.path.join(BASE_DIR, year, month)) if f.endswith('.html')], reverse=True)
                for file in files:
                    try:
                        parts = file.replace(".html", "").split('_')
                        if len(parts) >= 4:
                            day = parts[2]
                            d_key = str(int(day)) 
                            time_str = f"{parts[3][:2]}:{parts[3][2:4]}"
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

                            if d_key not in archive_data[y_key][m_key]:
                                archive_data[y_key][m_key][d_key] = []

                            # --- 新增：恢复置顶标记 ---
                            item_data = {
                                "time": time_str,
                                "path": file_path,
                                "title": page_title
                            }
                            if file_path in pinned_paths:
                                item_data["pinned"] = True

                            archive_data[y_key][m_key][d_key].append(item_data)
                    except Exception:
                        pass

    json_data = json.dumps(archive_data)

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
        
        .manual-fetch-bar { background: var(--card); padding: 12px 15px; display: flex; justify-content: flex-end; align-items: center; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 20; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .settings-btn { background: none; border: none; font-size: 20px; cursor: pointer; padding: 5px; }
        
        .modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 100; justify-content: center; align-items: center; padding: 20px; }
        .modal-content { background: var(--card); border-radius: 16px; padding: 20px; width: 100%; max-width: 400px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .modal-title { margin: 0 0 15px 0; font-size: 18px; font-weight: bold; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; font-size: 13px; color: var(--muted); margin-bottom: 5px; font-weight: bold; }
        .form-group input { width: 100%; box-sizing: border-box; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; outline: none; }
        .modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
        .btn { padding: 8px 16px; border-radius: 8px; border: none; font-size: 14px; font-weight: bold; cursor: pointer; }
        .btn-cancel { background: #eee; color: #333; }
        .btn-save { background: var(--primary); color: #fff; }

        #loadingBar { height: 3px; background: var(--primary); width: 0%; transition: width 0.3s; position: absolute; top: 0; left: 0; z-index: 30; }

        .controls { background: var(--card); padding: 15px 20px; display: flex; justify-content: center; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); box-shadow: 0 2px 10px rgba(0,0,0,0.03); }
        .control-btn { background: var(--primary); color: #fff; border: none; border-radius: 4px; padding: 8px 12px; font-size: 14px; cursor: pointer; }
        .control-btn:active { opacity: 0.8; }
        .select-box { padding: 6px 10px; border: 1px solid var(--border); border-radius: 4px; font-size: 15px; background: #fff; outline: none; }
        
        .calendar-wrapper { background: var(--card); padding: 10px 15px 20px 15px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
        .weekdays { display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
        .days-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; }
        
        .day-cell { aspect-ratio: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; font-size: 16px; font-weight: 500; border-radius: 8px; cursor: pointer; position: relative; transition: all 0.2s; }
        .day-cell.empty { visibility: hidden; }
        .day-cell.has-news { color: var(--text); }
        .day-cell.no-news { color: #ccc; }
        
        .day-cell.selected { background: #fff0db; border: 1px solid #f5a623; color: #d0021b; font-weight: bold; }
        .day-cell.today { background: #eef5ff; color: var(--primary); }
        .dot { width: 4px; height: 4px; background-color: var(--primary); border-radius: 50%; position: absolute; bottom: 8px; display: none; }
        .day-cell.has-news .dot { display: block; }
        .day-cell.selected .dot { background-color: #d0021b; }
        
        .news-section { flex: 1; padding: 0 15px 30px 15px; }
        
        .news-item-wrapper { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
        .news-item { flex: 1; background: var(--card); border-radius: 12px; padding: 16px; margin-bottom: 0; display: flex; justify-content: space-between; align-items: center; text-decoration: none; color: var(--text); box-shadow: 0 1px 4px rgba(0,0,0,0.04); overflow: hidden; transition: all 0.2s; }
        .news-item:active { transform: scale(0.98); }
        .news-item.pinned-item { border-left: 4px solid #f5a623; } /* 置顶UI标记 */
        .news-time { font-size: 16px; font-weight: 600; flex-shrink: 0; }
        .news-title { font-size: 14px; color: var(--muted); margin-left: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: right; flex: 1; }
        
        .delete-btn { background: #ff3b30; color: white; border: none; border-radius: 10px; padding: 0 15px; height: 50px; font-size: 16px; cursor: pointer; display: none; transition: all 0.2s; flex-shrink: 0; }
        .pin-btn { background: #f5a623; color: white; border: none; border-radius: 10px; padding: 0 15px; height: 50px; font-size: 16px; cursor: pointer; display: none; transition: all 0.2s; flex-shrink: 0; }

        .empty-state { text-align: center; padding: 40px 20px; color: var(--muted); }

        .toast-msg { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%) translateY(20px); background: rgba(0,0,0,0.8); color: #fff; padding: 12px 24px; border-radius: 24px; font-size: 14px; z-index: 1000; opacity: 0; pointer-events: none; transition: opacity 0.3s, transform 0.3s; white-space: nowrap; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .toast-msg.show { opacity: 1; transform: translateX(-50%) translateY(0); }
    </style>
</head>
<body>
    <div id="loadingBar"></div>
    <div id="toastMsg" class="toast-msg"></div>

    <div class="manual-fetch-bar">
        <button class="settings-btn" onclick="openSettings()">⚙️</button>
    </div>

    <div class="modal-overlay" id="settingsModal">
        <div class="modal-content">
            <h3 class="modal-title">本地配置中心</h3>
            <p style="font-size:12px; color:#888; margin-top:-10px; margin-bottom:15px;">密钥仅保存在您的浏览器本地，不会上传到任何第三方服务器。</p>
            <div class="form-group">
                <label>GitHub Personal Access Token</label>
                <input type="password" id="cfgGhToken" placeholder="ghp_...">
            </div>
            <div class="form-group">
                <label>GitHub 用户名</label>
                <input type="text" id="cfgGhOwner" value="moodHappy" placeholder="例如: moodHappy">
            </div>
            <div class="form-group">
                <label>GitHub 仓库名</label>
                <input type="text" id="cfgGhRepo" placeholder="例如: bbc-news-archive">
            </div>
            <div class="modal-actions">
                <button class="btn btn-cancel" onclick="closeSettings()">取消</button>
                <button class="btn btn-save" onclick="saveSettings()">保存配置</button>
            </div>
        </div>
    </div>

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
            <div id="newsList"></div>
        </div>
    </div>

    <script>
        function showToast(msg, duration = 3000) {
            const toast = document.getElementById('toastMsg');
            toast.textContent = msg;
            toast.classList.add('show');
            setTimeout(() => { toast.classList.remove('show'); }, duration);
        }

        const archiveData = /*DATA_START*/REPLACEME_JSON_DATA/*DATA_END*/;
        
        const today = new Date();
        let currentYear = today.getFullYear();
        let currentMonth = today.getMonth() + 1;
        let selectedDay = today.getDate();
        let selectedYear = currentYear;
        let selectedMonth = currentMonth;
        
        window.deleteMode = false;

        const yearSelect = document.getElementById('yearSelect');
        const monthSelect = document.getElementById('monthSelect');
        const daysGrid = document.getElementById('daysGrid');
        const newsList = document.getElementById('newsList');

        function initSelects() {
            yearSelect.innerHTML = '';
            let dataYears = Object.keys(archiveData).map(Number);
            let generatedYears = [];
            for (let i = -10; i <= 40; i++) generatedYears.push(currentYear + i);
            let allYears = Array.from(new Set([...dataYears, ...generatedYears])).sort((a, b) => b - a);
            
            allYears.forEach(y => {
                const opt = document.createElement('option');
                opt.value = y; opt.textContent = y + ' 年';
                yearSelect.appendChild(opt);
            });
            
            let hasSelectedYear = Array.from(yearSelect.options).some(opt => parseInt(opt.value) === selectedYear);
            if (!hasSelectedYear) {
                const opt = document.createElement('option');
                opt.value = selectedYear; opt.textContent = selectedYear + ' 年';
                yearSelect.insertBefore(opt, yearSelect.firstChild);
            }
            yearSelect.value = selectedYear;
            monthSelect.value = selectedMonth;
        }

        function renderCalendar(year, month) {
            daysGrid.innerHTML = '';
            const firstDay = new Date(year, month - 1, 1).getDay();
            const startDay = firstDay === 0 ? 7 : firstDay;
            const daysInMonth = new Date(year, month, 0).getDate();
            
            for (let i = 1; i < startDay; i++) {
                const emptyCell = document.createElement('div');
                emptyCell.className = 'day-cell empty';
                daysGrid.appendChild(emptyCell);
            }
            
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : {};
            
            for (let day = 1; day <= daysInMonth; day++) {
                const cell = document.createElement('div');
                cell.className = 'day-cell';
                cell.textContent = day;
                
                const dot = document.createElement('div');
                dot.className = 'dot';
                cell.appendChild(dot);
                
                if (monthData[day] && monthData[day].length > 0) cell.classList.add('has-news');
                else cell.classList.add('no-news');
                
                if (year === today.getFullYear() && month === today.getMonth() + 1 && day === today.getDate()) cell.classList.add('today');
                if (year === selectedYear && month === selectedMonth && day === selectedDay) cell.classList.add('selected');
                
                cell.addEventListener('click', () => {
                    selectedYear = year; selectedMonth = month; selectedDay = day;
                    renderCalendar(year, month);
                    renderNews(year, month, day);
                });
                
                daysGrid.appendChild(cell);
            }
        }

        // 获取所有被置顶的文章
        function getAllPinnedNews() {
            let pinned = [];
            for (let y in archiveData) {
                for (let m in archiveData[y]) {
                    for (let d in archiveData[y][m]) {
                        archiveData[y][m][d].forEach(news => {
                            if (news.pinned) pinned.push(news);
                        });
                    }
                }
            }
            return pinned;
        }

        function renderNews(year, month, day) {
            newsList.innerHTML = '';
            
            const allPinned = getAllPinnedNews();
            const monthData = (archiveData[year] && archiveData[year][month]) ? archiveData[year][month] : null;
            const dayData = monthData ? monthData[day] : [];
            
            // 过滤掉当前选中日期里已经被置顶的文章，避免重复渲染
            const currentDayUnpinned = (dayData || []).filter(n => !n.pinned);
            
            // 合并渲染数组：置顶文章永远在最上方
            const itemsToRender = [...allPinned, ...currentDayUnpinned];
            
            if (itemsToRender.length > 0) {
                itemsToRender.forEach((news, index) => {
                    const wrapper = document.createElement('div');
                    wrapper.className = 'news-item-wrapper';

                    const a = document.createElement('a');
                    a.href = news.path;
                    a.className = 'news-item' + (news.pinned ? ' pinned-item' : '');
                    
                    const pinEmoji = news.pinned ? '📌 ' : '';
                    a.innerHTML = `<span class="news-time">${news.time}</span><span class="news-title">${pinEmoji}${news.title}</span>`;
                    wrapper.appendChild(a);

                    // 置顶/取消按钮
                    const pinBtn = document.createElement('button');
                    pinBtn.className = 'pin-btn';
                    pinBtn.innerHTML = news.pinned ? '❌' : '📌';
                    if (window.deleteMode) pinBtn.style.display = 'block';
                    
                    pinBtn.onclick = async (e) => {
                        e.preventDefault();
                        news.pinned = !news.pinned;
                        renderNews(selectedYear, selectedMonth, selectedDay);
                        await syncIndexToGithub(); // 同步置顶状态
                        showToast(news.pinned ? '📌 已置顶' : '❌ 已取消置顶');
                    };
                    wrapper.appendChild(pinBtn);

                    // 删除按钮
                    const delBtn = document.createElement('button');
                    delBtn.className = 'delete-btn';
                    delBtn.innerHTML = '🗑️';
                    if (window.deleteMode) delBtn.style.display = 'block';
                    
                    delBtn.onclick = async (e) => {
                        e.preventDefault();
                        if(confirm('确认删除此条目并同步删除云端文件吗？')) {
                            const pathToDelete = news.path;
                            // 全局查找并删除此文章
                            let found = false;
                            for (let y in archiveData) {
                                for (let m in archiveData[y]) {
                                    for (let d in archiveData[y][m]) {
                                        const arr = archiveData[y][m][d];
                                        const idx = arr.findIndex(item => item.path === pathToDelete);
                                        if (idx !== -1) {
                                            arr.splice(idx, 1);
                                            if (arr.length === 0) delete archiveData[y][m][d];
                                            found = true; break;
                                        }
                                    }
                                    if(found) break;
                                }
                                if(found) break;
                            }
                            
                            renderCalendar(year, month);
                            renderNews(selectedYear, selectedMonth, selectedDay);
                            await syncDeleteToGithub(pathToDelete);
                            showToast('🗑️ 已删除该文章');
                        }
                    };
                    wrapper.appendChild(delBtn);
                    newsList.appendChild(wrapper);
                });
            } else {
                newsList.innerHTML = '<div class="empty-state">当日暂无新闻归档</div>';
            }
        }

        const modal = document.getElementById('settingsModal');
        const loadingBar = document.getElementById('loadingBar');

        function openSettings() {
            document.getElementById('cfgGhToken').value = localStorage.getItem('GH_TOKEN_BBC') || '';
            document.getElementById('cfgGhOwner').value = localStorage.getItem('GH_OWNER_BBC') || 'moodHappy';
            document.getElementById('cfgGhRepo').value = localStorage.getItem('GH_REPO_BBC') || '';
            modal.style.display = 'flex';
        }
        function closeSettings() { modal.style.display = 'none'; }
        function saveSettings() {
            localStorage.setItem('GH_TOKEN_BBC', document.getElementById('cfgGhToken').value.trim());
            localStorage.setItem('GH_OWNER_BBC', document.getElementById('cfgGhOwner').value.trim());
            localStorage.setItem('GH_REPO_BBC', document.getElementById('cfgGhRepo').value.trim());
            closeSettings();
            showToast('✅ 配置已保存');
        }

        let lastTap = 0;
        const calWrapper = document.querySelector('.calendar-wrapper');
        calWrapper.addEventListener('click', function(e) {
            const currentTime = new Date().getTime();
            const tapLength = currentTime - lastTap;
            if (tapLength < 500 && tapLength > 0) {
                window.deleteMode = !window.deleteMode;
                const btns = document.querySelectorAll('.delete-btn, .pin-btn');
                btns.forEach(btn => btn.style.display = window.deleteMode ? 'block' : 'none');
                e.preventDefault();
            }
            lastTap = currentTime;
        });

        // 纯更新 Index 状态（用于置顶功能）
        async function syncIndexToGithub() {
            const ghToken = localStorage.getItem('GH_TOKEN_BBC');
            const ghOwner = localStorage.getItem('GH_OWNER_BBC');
            const ghRepo = localStorage.getItem('GH_REPO_BBC');
            if (!ghToken || !ghOwner || !ghRepo) return;

            try {
                loadingBar.style.width = '30%';
                const idxRes = await fetch(`https://api.github.com/repos/${ghOwner}/${ghRepo}/contents/docs/index.html`, {
                    headers: { 'Authorization': `token ${ghToken}` }
                });
                const idxData = await idxRes.json();
                const idxContent = decodeURIComponent(escape(atob(idxData.content)));

                const dataStart = idxContent.indexOf('/*DATA_START*/') + 14;
                const dataEnd = idxContent.indexOf('/*DATA_END*/');
                const newJsonStr = JSON.stringify(archiveData);
                const newIdxContent = idxContent.substring(0, dataStart) + newJsonStr + idxContent.substring(dataEnd);

                loadingBar.style.width = '70%';
                await fetch(`https://api.github.com/repos/${ghOwner}/${ghRepo}/contents/docs/index.html`, {
                    method: 'PUT',
                    headers: { 'Authorization': `token ${ghToken}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: `Update index.html pinned status`,
                        content: btoa(unescape(encodeURIComponent(newIdxContent))),
                        sha: idxData.sha
                    })
                });
                loadingBar.style.width = '100%';
                setTimeout(() => { loadingBar.style.width = '0%'; }, 1000);
            } catch(e) {
                console.error("Sync pin status failed", e);
                loadingBar.style.width = '0%';
                showToast('❌ 云端同步置顶状态失败');
            }
        }

        async function syncDeleteToGithub(fileRelPath) {
            const ghToken = localStorage.getItem('GH_TOKEN_BBC');
            const ghOwner = localStorage.getItem('GH_OWNER_BBC');
            const ghRepo = localStorage.getItem('GH_REPO_BBC');
            if (!ghToken || !ghOwner || !ghRepo) return;

            try {
                loadingBar.style.width = '10%';
                const targetFilePath = `docs/${fileRelPath}`;
                const fileRes = await fetch(`https://api.github.com/repos/${ghOwner}/${ghRepo}/contents/${targetFilePath}`, {
                    headers: { 'Authorization': `token ${ghToken}` }
                });
                
                if (fileRes.ok) {
                    const fileData = await fileRes.json();
                    await fetch(`https://api.github.com/repos/${ghOwner}/${ghRepo}/contents/${targetFilePath}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `token ${ghToken}`, 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            message: `Delete archived html file: ${fileRelPath}`,
                            sha: fileData.sha
                        })
                    });
                }
                
                loadingBar.style.width = '50%';
                const idxRes = await fetch(`https://api.github.com/repos/${ghOwner}/${ghRepo}/contents/docs/index.html`, {
                    headers: { 'Authorization': `token ${ghToken}` }
                });
                const idxData = await idxRes.json();
                const idxContent = decodeURIComponent(escape(atob(idxData.content)));

                const dataStart = idxContent.indexOf('/*DATA_START*/') + 14;
                const dataEnd = idxContent.indexOf('/*DATA_END*/');
                const newJsonStr = JSON.stringify(archiveData);
                const newIdxContent = idxContent.substring(0, dataStart) + newJsonStr + idxContent.substring(dataEnd);

                loadingBar.style.width = '80%';
                await fetch(`https://api.github.com/repos/${ghOwner}/${ghRepo}/contents/docs/index.html`, {
                    method: 'PUT',
                    headers: { 'Authorization': `token ${ghToken}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: `Update index.html after deleting file`,
                        content: btoa(unescape(encodeURIComponent(newIdxContent))),
                        sha: idxData.sha
                    })
                });
                
                loadingBar.style.width = '100%';
                setTimeout(() => { loadingBar.style.width = '0%'; }, 1000);
            } catch(e) {
                console.error("Sync delete failed", e);
                loadingBar.style.width = '0%';
                showToast('❌ 云端同步删除失败');
            }
        }

        yearSelect.addEventListener('change', (e) => {
            selectedYear = parseInt(e.target.value);
            selectedMonth = parseInt(monthSelect.value);
            let maxDays = new Date(selectedYear, selectedMonth, 0).getDate();
            if (selectedDay > maxDays) selectedDay = maxDays;
            renderCalendar(selectedYear, selectedMonth);
            renderNews(selectedYear, selectedMonth, selectedDay);
        });

        monthSelect.addEventListener('change', (e) => {
            selectedYear = parseInt(yearSelect.value);
            selectedMonth = parseInt(e.target.value);
            let maxDays = new Date(selectedYear, selectedMonth, 0).getDate();
            if (selectedDay > maxDays) selectedDay = maxDays;
            renderCalendar(selectedYear, selectedMonth);
            renderNews(selectedYear, selectedMonth, selectedDay);
        });

        document.getElementById('prevBtn').addEventListener('click', () => {
            let m = parseInt(monthSelect.value) - 1; 
            let y = parseInt(yearSelect.value);
            if (m < 1) { m = 12; y--; }
            monthSelect.value = m; yearSelect.value = y;
            selectedYear = y; selectedMonth = m;
            let maxDays = new Date(selectedYear, selectedMonth, 0).getDate();
            if (selectedDay > maxDays) selectedDay = maxDays;
            renderCalendar(selectedYear, selectedMonth);
            renderNews(selectedYear, selectedMonth, selectedDay);
        });

        document.getElementById('nextBtn').addEventListener('click', () => {
            let m = parseInt(monthSelect.value) + 1; 
            let y = parseInt(yearSelect.value);
            if (m > 12) { m = 1; y++; }
            monthSelect.value = m; yearSelect.value = y;
            selectedYear = y; selectedMonth = m;
            let maxDays = new Date(selectedYear, selectedMonth, 0).getDate();
            if (selectedDay > maxDays) selectedDay = maxDays;
            renderCalendar(selectedYear, selectedMonth);
            renderNews(selectedYear, selectedMonth, selectedDay);
        });

        document.getElementById('todayBtn').addEventListener('click', () => {
            selectedYear = today.getFullYear(); 
            selectedMonth = today.getMonth() + 1; 
            selectedDay = today.getDate();
            let hasSelectedYear = Array.from(yearSelect.options).some(opt => parseInt(opt.value) === selectedYear);
            if(!hasSelectedYear) initSelects();
            yearSelect.value = selectedYear; monthSelect.value = selectedMonth;
            renderCalendar(selectedYear, selectedMonth); 
            renderNews(selectedYear, selectedMonth, selectedDay);
        });

        initSelects();
        renderCalendar(currentYear, currentMonth);
        renderNews(currentYear, currentMonth, selectedDay);
    </script>
</body>
</html>"""

    final_html = html_template.replace(
        "/*DATA_START*/REPLACEME_JSON_DATA/*DATA_END*/", 
        f"/*DATA_START*/{json_data}/*DATA_END*/"
    )

    with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(final_html)
    print("首页 index.html 已更新，置顶功能已加入。")

if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    fetch_bbc_news()
    generate_index()