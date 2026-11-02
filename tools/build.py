"""Готовит сайт для поисковиков.

1. Открывает index.html в браузере, даёт main.js подставить тексты из content.js
   и сохраняет готовую страницу обратно в index.html. Так Яндекс видит весь текст
   сразу, без выполнения JavaScript. Посетителям ничего не меняется: main.js
   при загрузке всё равно заново подставляет тексты из content.js.
2. Пишет sitemap.xml и robots.txt с адресом сайта из content.js (seo.url),
   а для своего домена — файл CNAME для GitHub Pages.

Запускается сам при коммите (.git/hooks/pre-commit). Вручную:
    python tools/build.py
"""
import datetime, mimetypes, pathlib, re, sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
BASE = "https://site.local/"
PAGES = ["", "privacy.html"]  # страницы для sitemap.xml

# Файлы отдаются прямо с диска, без сети — так в страницу ничего не встроит
# антивирус или прокси, и не грузятся видео.
def serve(route):
    path = route.request.url[len(BASE):].split("?")[0].split("#")[0] or "index.html"
    file = (ROOT / path).resolve()
    if ROOT not in file.parents or not file.is_file() or file.suffix == ".mp4":
        return route.fulfill(status=404, body="")
    route.fulfill(status=200, body=file.read_bytes(),
                  content_type=mimetypes.guess_type(file.name)[0] or "application/octet-stream")


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1366, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.route("**/*", lambda r: serve(r) if r.request.url.startswith(BASE) else r.abort())
    page.add_init_script("window.PRERENDER = true;")
    page.goto(BASE, wait_until="load")
    page.wait_for_timeout(300)
    if errors:
        sys.exit("Ошибка JavaScript, index.html не изменён: " + "; ".join(errors))

    html = page.evaluate("""() => {
        const root = document.documentElement.cloneNode(true);
        root.classList.remove('js');
        if (!root.classList.length) root.removeAttribute('class');
        // перевод строки после </html> браузер переносит в <body> — без этого он копится с каждой сборкой
        const body = root.querySelector('body');
        while (body.lastChild && body.lastChild.nodeType === 3 && !body.lastChild.textContent.trim()) body.lastChild.remove();
        body.append('\\n');
        return '<!doctype html>\\n' + root.outerHTML + '\\n';
    }""")
    seo = page.evaluate("window.SITE.seo")
    browser.close()

# Проверки, чтобы не сохранить сломанную страницу
problems = []
if 'style="' in html:
    problems.append("в разметке остались style=\"...\" — их заблокирует CSP")
if re.search(r"kaspersky", html, re.I):
    problems.append("в разметку попал скрипт антивируса")
if "<h1" not in html or html.count('data-text="hero.text"></p>') or len(html) < 20000:
    problems.append("тексты не подставились")
if problems:
    sys.exit("index.html не изменён: " + "; ".join(problems))

INDEX.write_text(html, encoding="utf-8", newline="\n")

url = seo["url"]
today = datetime.date.today().isoformat()
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{url}{pg}</loc><lastmod>{today}</lastmod></url>\n" for pg in PAGES)
    + "</urlset>\n", encoding="utf-8", newline="\n")
(ROOT / "robots.txt").write_text(
    "User-agent: *\n"
    "Disallow: /tests/\n"
    "Disallow: /tools/\n"
    f"\nSitemap: {url}sitemap.xml\n", encoding="utf-8", newline="\n")
# Свой домен для GitHub Pages: файл CNAME с адресом. На *.github.io он не нужен.
host = re.match(r"https?://([^/]+)", url).group(1)
cname = ROOT / "CNAME"
if host.endswith(".github.io"):
    cname.unlink(missing_ok=True)
else:
    cname.write_text(host + "\n", encoding="utf-8", newline="\n")

print(f"Готово: index.html ({len(html) // 1024} КБ), sitemap.xml, robots.txt → {url}")
