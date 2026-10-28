"""Автотесты сайта: открывают его в Edge как на ПК и на телефоне и прощёлкивают всё интерактивное.

Запуск:
    python -m pip install --user playwright
    python tests/qa.py                          # живой сайт на GitHub Pages
    python tests/qa.py http://localhost:8080/   # локальная копия (python -m http.server 8080)
"""
import json, sys, urllib.parse, urllib.request
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

URL = sys.argv[1] if len(sys.argv) > 1 else "https://egorguluyta030501.github.io/aaa168-site/"
WA = "8615604281718"
results = []


def check(name, ok, detail=""):
    results.append((bool(ok), name, detail))


def wa_text(url):
    return urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("text", [""])[0]


def noise(text):
    # скрипт антивируса Kaspersky встраивается в страницы на компьютере разработчика — это не сайт
    return "kaspersky" in text.lower()


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)

    for label, vp in [("ПК", {"width": 1366, "height": 800}), ("Телефон", {"width": 390, "height": 844})]:
        mobile = label == "Телефон"
        ctx = browser.new_context(viewport=vp, is_mobile=mobile, has_touch=mobile)
        page = ctx.new_page()
        errors, failed, popups = [], [], []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: m.type == "error" and not noise(m.text) and errors.append(m.text))
        page.on("requestfailed", lambda r: not noise(r.url) and failed.append(r.url))
        page.on("response", lambda r: r.status >= 400 and failed.append(f"{r.status} {r.url}"))
        # сайт не должен ничего грузить со сторонних серверов (Google Fonts и т. п.)
        host = urllib.parse.urlparse(URL).netloc
        external = []
        page.on("request", lambda r: not noise(r.url) and r.url.startswith("http")
                and urllib.parse.urlparse(r.url).netloc != host and external.append(r.url))
        ctx.on("page", lambda pg: popups.append(pg.url))
        # WhatsApp не открываем по-настоящему — запоминаем адрес
        page.add_init_script("window.__opened=[]; window.open=(u)=>{window.__opened.push(u); return null;};")
        page.add_init_script("window.__csp=[]; document.addEventListener('securitypolicyviolation', e => {"
                             " if (!/kaspersky/i.test(e.blockedURI + e.sourceFile)) window.__csp.push(e.violatedDirective + ' ' + e.blockedURI); });")

        page.goto(URL, wait_until="load", timeout=60000)
        page.wait_for_timeout(1500)
        P = f"[{label}] "

        # --- загрузка и безопасность ---
        check(P + "нет JS-ошибок", not errors, "; ".join(errors[:3]))
        check(P + "все файлы загрузились", not failed, "; ".join(failed[:5]))
        check(P + "CSP включена", page.query_selector("meta[http-equiv='Content-Security-Policy']"))
        check(P + "нет запросов к сторонним серверам", not external, str(external[:5]))
        check(P + "шрифт Onest загружен с сайта",
              page.evaluate("[...document.fonts].some(f => f.family.includes('Onest') && f.status === 'loaded')"))
        check(P + "CSP ничего не блокирует на сайте", not page.evaluate("window.__csp"), str(page.evaluate("window.__csp")[:5]))
        check(P + "нет горизонтальной прокрутки",
              page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"),
              str(page.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")))

        # --- тексты ---
        empties = page.evaluate("""[...document.querySelectorAll('[data-text],[data-rich]')]
            .filter(e => !e.textContent.trim() && !e.closest('[hidden]')).map(e => e.dataset.text || e.dataset.rich)""")
        check(P + "все тексты подставились", not empties, str(empties))
        body = page.evaluate("document.body.innerText")
        check(P + "нет китайских символов", not page.evaluate(r"/[一-鿿]/.test(document.body.innerText)"))
        bad = [w for w in ["отслеживан", "онлайн", "серая", "белая", "белое", "белой", "тамож", "оформлен",
                           "документ", "деклар", "сертиф", "официальн", "undefined", "null", "NaN"] if w in body.lower()]
        check(P + "нет запрещённых и мусорных слов", not bad, str(bad))
        check(P + "заголовок вкладки и описание актуальные",
              "СНГ" in page.title() and "Выкуп" not in page.get_attribute("meta[name=description]", "content"))

        # --- картинки и ссылки ---
        broken = page.evaluate("""(async () => {
            const imgs = [...document.images]; imgs.forEach(i => i.loading = 'eager');
            await Promise.all(imgs.map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; })));
            return imgs.filter(i => !i.naturalWidth).map(i => i.getAttribute('src'));
        })()""")
        check(P + "все картинки открываются", not broken, str(broken))
        links = page.evaluate("""[...document.querySelectorAll('a')].filter(a => !a.closest('[hidden]') && !a.hidden)
            .map(a => [a.textContent.trim().slice(0, 30), a.getAttribute('href'), a.target, a.rel])""")
        check(P + "у всех видимых ссылок есть адрес", all(l[1] for l in links), str([l for l in links if not l[1]][:5]))
        check(P + "ссылки в новое окно защищены noopener",
              all("noopener" in l[3] for l in links if l[2] == "_blank"), str([l for l in links if l[2] == "_blank" and "noopener" not in l[3]]))
        anchors = {l[1] for l in links if l[1] and l[1].startswith("#") and len(l[1]) > 1}
        check(P + "пункты меню ведут на существующие блоки", all(page.query_selector(h) for h in anchors),
              str([h for h in anchors if not page.query_selector(h)]))
        wa = {l[1] for l in links if l[1] and "wa.me" in l[1]}
        check(P + "WhatsApp-ссылки на правильный номер", wa and all(WA in h for h in wa), str(wa))
        tg = sorted({l[1] for l in links if l[1] and "t.me" in l[1]})
        check(P + "Telegram-ссылки", tg == ["https://t.me/CARGO_AAA168", "https://t.me/cargo_aaa168cargo"], str(tg))
        order = page.evaluate("[...document.querySelectorAll('main > section[id]')].map(s => s.id)")
        check(P + "«О компании» сразу после главного экрана", order[:1] == ["about"], str(order))

        # --- меню на телефоне ---
        if mobile:
            page.click("#burger"); page.wait_for_timeout(400)
            check(P + "бургер открывает меню", page.evaluate("getComputedStyle(document.querySelector('#nav')).visibility") == "visible")
            page.click("#nav-links a[href='#faq']"); page.wait_for_timeout(900)
            check(P + "меню закрывается после выбора пункта", not page.evaluate("document.body.classList.contains('nav-open')"))
            page.evaluate("window.scrollTo(0,0)")

        # --- персональные данные: сайт их не спрашивает ---
        check(P + "в формах нет полей имени и телефона",
              not page.query_selector("form input[type=tel], form input[name=name], form input[name=phone]"))
        check(P + "есть ссылка на политику конфиденциальности", page.query_selector("footer a[href='privacy.html']"))
        check(P + "пока нет Telegram менеджера — вторая кнопка скрыта", not page.is_visible(".alt-send"))

        # --- быстрая заявка ---
        page.evaluate("window.__opened=[]")
        page.select_option("#quick-country", "Казахстан")
        page.click("#quick-mode button[data-v='Ж/Д']")
        page.fill("#quick-weight", "300")
        page.click("#quick-form button[type=submit]")
        opened = page.evaluate("window.__opened")
        txt = wa_text(opened[0]) if opened else ""
        check(P + "быстрая заявка уходит в WhatsApp с данными",
              opened and WA in opened[0] and all(x in txt for x in ["Казахстан", "Ж/Д", "300 кг"]),
              txt.replace("\n", " | "))

        # --- анимации ---
        page.wait_for_timeout(1500)
        stats = page.evaluate("[...document.querySelectorAll('.stat__value')].map(e => e.textContent)")
        check(P + "цифры досчитались до конца", stats[:3] == ["от 12 дней", "от 16 дней", "5–8 дней"], str(stats))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)"); page.wait_for_timeout(500)
        sc = page.evaluate("new DOMMatrix(getComputedStyle(document.querySelector('#progress')).transform).a")
        check(P + "полоса прокрутки растёт", 0.3 < sc < 0.7, str(sc))
        check(P + "кнопка «Наверх» видна после прокрутки", page.is_visible("#totop"))
        page.click("#totop"); page.wait_for_timeout(1500)
        check(P + "«Наверх» возвращает в начало", page.evaluate("window.scrollY") < 5, str(page.evaluate("window.scrollY")))
        check(P + "наверху кнопка «Наверх» скрыта", not page.is_visible("#totop"))

        # --- листалки ---
        n_rev = page.evaluate("document.querySelectorAll('#reviews-list .shot').length")
        n_vid = page.evaluate("document.querySelectorAll('#warehouse-list .vcard').length")
        check(P + "7 отзывов и 6 видео склада", n_rev == 7 and n_vid == 6, f"{n_rev} отзывов, {n_vid} видео")
        hv = page.evaluate("(() => { const v = document.querySelector('#hero-video'); return [v.currentSrc.split('/').pop(), v.paused, v.readyState] })()")
        check(P + "фоновое видео главного экрана играет",
              hv[0] == ("hero-mobile.mp4" if mobile else "hero.mp4") and hv[2] >= 2, str(hv))
        n_blocks = page.evaluate("['#advantages-list .perk', '#transport-list .mode', '#cargo-list .good', '#steps-list .step', '#team-list .person']"
                                 ".map(s => document.querySelectorAll(s).length)")
        team_n = page.evaluate("window.SITE.team.items.length")
        check(P + "преимущества, доставка, что возим, этапы и команда на месте", n_blocks == [4, 3, 8, 5, team_n], str(n_blocks))
        check(P + "пустая команда — блок скрыт", team_n > 0 or not page.is_visible("#team"))
        # маршрут по этапам: вверху страницы ещё не пройден, у блока — пройден
        p0 = page.evaluate("getComputedStyle(document.querySelector('#route')).getPropertyValue('--p')")
        page.evaluate("document.querySelector('#route').scrollIntoView({block: 'start', behavior: 'instant'})")
        page.wait_for_timeout(400)
        p1 = page.evaluate("getComputedStyle(document.querySelector('#route')).getPropertyValue('--p')")
        check(P + "линия маршрута растёт при прокрутке", float(p0) < float(p1), f"{p0} → {p1}")
        # строка едет, только когда видна на экране
        page.evaluate("document.querySelector('#countries-list').scrollIntoView({block: 'center', behavior: 'instant'})")
        page.wait_for_timeout(300)
        x0 = page.evaluate("new DOMMatrix(getComputedStyle(document.querySelector('#countries-list')).transform).m41")
        page.wait_for_timeout(600)
        x1 = page.evaluate("new DOMMatrix(getComputedStyle(document.querySelector('#countries-list')).transform).m41")
        check(P + "бегущая строка стран едет", x0 != x1, f"{x0} → {x1}")
        page.evaluate("window.scrollTo(0, 0)"); page.wait_for_timeout(300)
        for sid in ["#warehouse-list", "#reviews-list"]:
            page.evaluate(f"document.querySelector('{sid}').scrollIntoView({{block: 'center', behavior: 'instant'}})")
            page.wait_for_timeout(1300)
            before = page.evaluate(f"document.querySelector('{sid}').scrollLeft")
            page.click(f"{sid} >> xpath=.. >> .slider__btn[data-dir='1']")
            page.wait_for_timeout(1000)
            after = page.evaluate(f"document.querySelector('{sid}').scrollLeft")
            check(P + f"листалка {sid} листается вперёд", after > before, f"{before} → {after}")
            page.click(f"{sid} >> xpath=.. >> .slider__btn[data-dir='-1']")
            page.wait_for_timeout(1000)
            check(P + f"листалка {sid} листается назад", page.evaluate(f"document.querySelector('{sid}').scrollLeft") < after)

        # --- видео ---
        page.click("#warehouse-list .vcard__play >> nth=0")
        page.wait_for_timeout(2500)
        v = page.evaluate("""(() => { const v = document.querySelector('#warehouse-list video');
            return v ? {ready: v.readyState, err: v.error && v.error.code, w: v.videoWidth} : null })()""")
        check(P + "видео склада запускается", v and not v["err"] and v["ready"] >= 2 and v["w"] > 0, str(v))
        page.evaluate("document.querySelector('#about').scrollIntoView({behavior: 'instant'})"); page.wait_for_timeout(1300)
        page.click("#about-video .vcard__play"); page.wait_for_timeout(2500)
        v = page.evaluate("""(() => { const v = document.querySelector('#about-video video');
            return v ? {ready: v.readyState, err: v.error && v.error.code, w: v.videoWidth} : null })()""")
        check(P + "видео «О компании» запускается", v and not v["err"] and v["ready"] >= 2 and v["w"] > 0, str(v))

        # --- отзыв во весь экран ---
        page.evaluate("document.querySelector('#reviews').scrollIntoView({behavior: 'instant'})"); page.wait_for_timeout(1300)
        page.click("#reviews-list .shot >> nth=0"); page.wait_for_timeout(400)
        check(P + "скриншот отзыва открывается", page.evaluate("document.querySelector('#lightbox').open"))
        page.mouse.click(5, 5); page.wait_for_timeout(300)
        check(P + "и закрывается кликом мимо", not page.evaluate("document.querySelector('#lightbox').open"))

        # --- основная форма ---
        page.evaluate("window.__opened=[]")
        page.select_option("#form-country", "Беларусь")
        page.select_option("#form-mode", "Авиа")
        page.select_option("#form-budget", index=2)
        page.fill("#form-message", "мебель, 300 кг")
        page.click("#lead-form button.btn[type=submit]")
        opened = page.evaluate("window.__opened")
        txt = wa_text(opened[0]) if opened else ""
        check(P + "основная форма уходит в WhatsApp со всеми полями",
              all(x in txt for x in ["Беларусь", "Авиа", "Бюджет", "мебель, 300 кг"]),
              txt.replace("\n", " | "))
        # попытка внедрить HTML через форму не должна попасть в страницу
        page.fill("#form-message", "<img src=x onerror=alert(1)>")
        page.click("#lead-form button.btn[type=submit]")
        check(P + "введённый текст не превращается в HTML на странице",
              not page.query_selector("img[src='x']"))

        page.click("#faq-list details:nth-child(2) summary")
        check(P + "вопрос раскрывается", page.evaluate("document.querySelector('#faq-list details:nth-child(2)').open"))

        check(P + "не открылось лишних вкладок", not popups, str(popups))
        check(P + "за всё время нет JS-ошибок", not errors, "; ".join(errors[:3]))
        ctx.close()

    # --- если в content.js указать Telegram менеджера, заявки уходят туда ---
    ctx = browser.new_context(viewport={"width": 1366, "height": 800})
    page = ctx.new_page()

    def with_manager(route):
        body = route.fetch().text().replace('manager: ""', 'manager: "test_manager"')
        route.fulfill(body=body, content_type="application/javascript; charset=utf-8")
    page.route("**/content.js*", with_manager)
    page.add_init_script("window.__opened=[]; window.open=(u)=>{window.__opened.push(u); return null;};")
    page.goto(URL, wait_until="load", timeout=60000)
    page.wait_for_timeout(800)
    check("[Telegram] кнопка «Написать менеджеру» ведёт в Telegram",
          page.get_attribute(".hero__actions [data-lead]", "href") == "https://t.me/test_manager"
          and page.evaluate("document.querySelector('.fab').classList.contains('fab--tg')"))
    page.fill("#quick-weight", "50")
    page.click("#quick-form button.quick__btn")
    page.click("#quick-form .alt-send")
    opened = page.evaluate("window.__opened")
    check("[Telegram] заявка уходит в Telegram менеджера, вторая кнопка — в WhatsApp",
          len(opened) == 2 and opened[0].startswith("https://t.me/test_manager?text=") and "50 кг" in wa_text(opened[0])
          and WA in opened[1], str(opened))
    ctx.close()

    # --- что видит поисковый робот без JavaScript ---
    ctx = browser.new_context(java_script_enabled=False)
    page = ctx.new_page()
    page.goto(URL, wait_until="load", timeout=60000)
    raw = page.evaluate("document.body.innerText")
    check("[Без JS] текст страницы виден поисковику",
          all(x in raw for x in ["Доставка грузов из Китая", "Виды доставки", "Вопросы и ответы", "Сколько идёт доставка?",
                                 "Что можно привезти из Китая", "Как работает карго"]))
    check("[Без JS] один заголовок h1", page.evaluate("document.querySelectorAll('h1').length") == 1)
    check("[Без JS] canonical и превью для соцсетей",
          page.get_attribute("link[rel=canonical]", "href") and page.get_attribute("meta[property='og:image']", "content"))
    ld = page.evaluate("document.querySelector('script[type=\"application/ld+json\"]')?.textContent")
    try:
        ok = json.loads(ld)["@graph"][0]["@type"] == "Organization"
    except Exception:
        ok = False
    check("[Без JS] разметка schema.org корректна", ok)
    for path in ["robots.txt", "sitemap.xml", "privacy.html", "favicon.ico", "assets/og-image.jpg"]:
        try:
            code = urllib.request.urlopen(URL + path, timeout=30).status
        except Exception as e:
            code = str(e)
        check(f"[Файлы] {path} открывается", code == 200, str(code))
    page.goto(URL + "privacy.html", wait_until="load")
    check("[Политика] страница с текстом и ссылкой на главную",
          "Политика конфиденциальности" in page.title() and page.query_selector("a[href='./']"))
    ctx.close()
    browser.close()

fails = [r for r in results if not r[0]]
for ok, name, detail in results:
    print(("OK   " if ok else "FAIL ") + name + ("" if ok or not detail else "  →  " + detail))
print(f"\nИтого: {len(results) - len(fails)}/{len(results)} проверок прошли")
sys.exit(1 if fails else 0)
