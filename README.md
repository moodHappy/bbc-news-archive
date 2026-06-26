# BBC News Archive

自动抓取 BBC News 头条文章并生成纯静态 WebApp 的自动化工具。该项目通过 GitHub Actions 实现定时任务，提供一个无广告、防干扰的纯净英语阅读环境。

## ✨ 核心特性

* **🤖 全自动运行**：利用 GitHub Actions，每小时自动检测并抓取 BBC News 首页的最新突发头条。
* **📱 响应式 WebApp**：自动生成移动端友好的 HTML 页面（位于 `docs/index.html`），包含底部导航栏，支持滑动切换视图。
* **📅 日历归档系统**：按年、月、日直观地管理和回溯所有抓取到的历史新闻。
* **☁️ 实时词云趋势**：通过抓取首页标题，自动过滤虚词并统计词频，生成当天的热词云，快速掌握国际新闻焦点。
* **📖 纯净阅读体验**：去除页面多余元素与免责声明，自动排版为大字体、宽行距的静态页面，非常适合日常的沉浸式英文阅读和语感培养。
* **⚡ GitHub Pages 完美兼容**：所有静态文件均输出至 `docs` 目录，可直接零成本开启 GitHub Pages 部署。

## 📂 目录结构

```text
bbc-news-archive/
├── .github/
│   └── workflows/
│       └── auto-scrape.yml    # GitHub Actions 定时任务配置
├── docs/                      # WebApp 及文章静态文件目录（供 GitHub Pages 使用）
│   ├── index.html             # WebApp 首页（日历 + 词云界面）
│   └── YYYY/                  # 按年份、月份归档的具体新闻 HTML 页面
├── bbc_reader.py              # 核心 Python 爬虫与静态页面生成脚本
└── last_bbc_url.txt           # 记录上一篇抓取的文章 URL，防止重复生成

```
## 🚀 快速开始
如果你想在自己的 GitHub 账号下运行这套系统：
 1. **Fork 本仓库**
   点击页面右上角的 Fork 按钮，将项目复制到你的账号下。
 2. **开启 GitHub Actions 权限**
   * 进入你 Fork 后的仓库，点击 Settings -> Actions -> General。
   * 在 Workflow permissions 部分，选择 **Read and write permissions** 并保存（这允许机器人将抓取到的 HTML 文件自动 Commit 并推送到仓库）。
   * 点击顶部的 Actions 标签页，同意并启用 Workflows。
 3. **手动触发一次运行 (可选)**
   * 在 Actions 标签页左侧选择 Auto Scrape BBC News。
   * 点击右侧的 Run workflow 按钮，验证脚本是否能成功抓取并生成文件。
 4. **开启 GitHub Pages 部署**
   * 进入 Settings -> Pages。
   * Source 选择 Deploy from a branch。
   * Branch 选择 main，文件夹选择 /docs，然后点击 Save。
   * 几分钟后，你就可以通过专属链接（如 https://<你的用户名>.github.io/bbc-news-archive/）访问你的个人新闻库了。
## 🛠️ 技术栈
 * **Python 3.10**: 核心脚本语言。
 * **Requests & BeautifulSoup4**: 负责网络请求与 HTML DOM 树解析。
 * **Vanilla HTML/CSS/JS**: 构建高性能、无依赖的纯静态 WebApp。
 * **GitHub Actions**: 提供稳定的云端定时运行环境。
## 📝 许可证
本项目仅供学习与个人阅读使用，新闻内容的版权归 BBC 所有。
