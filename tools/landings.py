"""Собирает отдельные страницы под поисковые запросы из landings.js.

Вызывается из tools/build.py: тот открывает сайт в браузере и передаёт сюда
window.LANDINGS и window.SITE. Каждая страница пишется в <slug>/index.html —
готовый HTML без JavaScript, чтобы поисковики сразу видели весь текст.
"""
import html, json, re, shutil, urllib.parse

MARK = '<meta name="generator" content="tools/build.py из landings.js">'
CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; "
       "object-src 'none'; base-uri 'self'; form-action 'none'; upgrade-insecure-requests")

# Иконки берутся из index.html (кнопки в правом нижнем углу), чтобы не переписывать SVG руками
ICONS = {}


def icons(root):
    page = (root / "index.html").read_text(encoding="utf-8")
    ICONS["tg"] = re.search(r'<svg class="fab__tg".*?</svg>', page).group(0)
    ICONS["wa"] = re.search(r'<a class="fab fab--mini".*?(<svg class="fab__wa".*?</svg>)', page, re.S).group(1)


def esc(s):
    return html.escape(str(s), quote=True)


def rich(s):
    """*слово* → золотой акцент, как в content.js."""
    return re.sub(r"\*(.+?)\*", r'<span class="accent">\1</span>', esc(s))


def plain(s):
    return str(s).replace("*", "")


def links(site, ask):
    c = site["contacts"]
    tg = f"https://t.me/{c['manager']}?text={urllib.parse.quote(ask)}" if c.get("manager") else ""
    wa = f"https://wa.me/{c['whatsapp']}?text={urllib.parse.quote(ask)}" if c.get("whatsapp") else ""
    return tg or wa, wa if tg else ""


def section_html(sec, alt):
    out = [f'<section class="section{" section--alt" if alt else ""}"><div class="container">',
           f'<div class="section__head"><h2 class="section__title">{rich(sec["title"])}</h2>']
    if sec.get("lead"):
        out.append(f'<p class="section__lead">{esc(sec["lead"])}</p>')
    out.append("</div>")
    for p in sec.get("paras", []):
        out.append(f'<p class="lp-text">{esc(p)}</p>')
    if sec.get("items"):
        out.append('<ul class="lp-cards">' + "".join(
            f'<li><h3>{esc(i["title"])}</h3><p>{esc(i["text"])}</p></li>' for i in sec["items"]) + "</ul>")
    if sec.get("image"):
        im = sec["image"]
        cap = f'<figcaption>{esc(im["caption"])}</figcaption>' if im.get("caption") else ""
        out.append(f'<figure class="lp-figure"><img src="/{esc(im["src"])}" alt="{esc(im["alt"])}" loading="lazy">{cap}</figure>')
    out.append("</div></section>")
    return "".join(out)


def render(lp, all_lps, site, version):
    s, c, b = site["seo"], site["contacts"], site["brand"]
    url = s["url"] + lp["slug"] + "/"
    lead_url, wa_url = links(site, lp["ask"])
    ext = 'target="_blank" rel="noopener"'

    chips = "".join(f"<li>{esc(x)}</li>" for x in lp.get("chips", []))
    wa_btn = f'<a class="btn btn--ghost btn--lg" href="{esc(wa_url)}" {ext}>Написать в WhatsApp</a>' if wa_url else ""
    hero = f'''<section class="lp-hero"><div class="container">
<nav class="crumbs" aria-label="Навигация"><a href="/">Главная</a><span aria-hidden="true">/</span><span>{esc(lp["menu"])}</span></nav>
<h1 class="lp-hero__title">{rich(lp["h1"])}</h1>
<p class="lp-hero__lead">{esc(lp["lead"])}</p>
<ul class="lp-chips">{chips}</ul>
<div class="hero__actions"><a class="btn btn--primary btn--lg" href="{esc(lead_url)}" {ext}>Рассчитать за 1 час</a>{wa_btn}</div>
</div></section>'''

    pr = lp["price"]
    rows = "".join(f"<tr><th scope=\"row\">{esc(r[0])}</th><td>{esc(r[1])}</td><td>{esc(r[2])}</td></tr>" for r in pr["rows"])
    price = f'''<section class="section"><div class="container">
<div class="section__head"><h2 class="section__title">{rich(pr["title"])}</h2>{f'<p class="section__lead">{esc(pr["lead"])}</p>' if pr.get("lead") else ""}</div>
<div class="lp-table-wrap"><table class="lp-table"><thead><tr><th scope="col">Способ</th><th scope="col">Цена</th><th scope="col">Срок</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="lp-note">{esc(pr["note"])}</p>
</div></section>'''

    steps_src = lp.get("steps") or site["process"]["steps"]
    steps = "".join(f'<li class="step"><span class="step__num">{n:02d}</span><h3>{esc(st["title"])}</h3><p>{esc(st["text"])}</p></li>'
                    for n, st in enumerate(steps_src, 1))
    steps = f'''<section class="section section--dark"><div class="container">
<div class="section__head"><h2 class="section__title">Как мы <span class="accent">работаем</span></h2></div>
<ol class="steps">{steps}</ol>
</div></section>'''

    sections = "".join(section_html(sec, i % 2 == 1) for i, sec in enumerate(lp.get("sections", [])))

    adv = "".join(f'<li><h3>{esc(a["title"])}</h3><p>{esc(a["text"])}</p></li>' for a in site["advantages"]["items"])
    perks = f'''<section class="section section--alt"><div class="container">
<div class="section__head"><h2 class="section__title">Почему <span class="accent">AAA168</span></h2></div>
<ul class="lp-cards">{adv}</ul>
</div></section>'''

    faq_items = "".join(f'<details><summary>{esc(f["q"])}</summary><div class="faq__body"><p>{esc(f["a"])}</p></div></details>' for f in lp["faq"])
    faq = f'''<section class="section"><div class="container">
<div class="section__head"><h2 class="section__title">Вопросы и ответы</h2></div>
<div class="faq">{faq_items}</div>
</div></section>'''

    others = "".join(f'<li><a href="/{esc(o["slug"])}/">{esc(o["menu"])}</a></li>' for o in all_lps if o["slug"] != lp["slug"])
    cta = f'''<section class="section section--dark lp-cta"><div class="container">
<div class="section__head"><h2 class="section__title">Рассчитаем доставку <span class="accent">за 1 час</span></h2>
<p class="section__lead">Напишите, что везёте, вес, объём и город получения — менеджер подберёт способ доставки и назовёт цену. {esc(c.get("hours", ""))}.</p></div>
<div class="hero__actions"><a class="btn btn--primary btn--lg" href="{esc(lead_url)}" {ext}>Написать менеджеру</a>{wa_btn}</div>
<nav class="lp-more" aria-label="Другие направления"><p>Ещё направления</p><ul><li><a href="/">Главная</a></li>{others}</ul></nav>
</div></section>'''

    tg_links = "".join(f'<a class="footer__link" href="https://t.me/{esc(h)}" {ext}>{t}</a>' for h, t in
                       [(c.get("telegram"), "Telegram-канал"), (c.get("telegramChat"), "Telegram-чат"), (c.get("knowledgeBase"), "База знаний")] if h)
    footer = f'''<footer class="footer"><div class="container">
<div class="footer__grid">
<div class="footer__brand">
<a class="logo" href="/"><img class="logo__img" src="/{esc(b["logo"])}" alt="" width="42" height="42"><span class="logo__text"><span class="logo__name">{esc(b["name"])}</span><span class="logo__tag">{esc(b["tagline"])}</span></span></a>
<p class="footer__about">{esc(site["footer"]["about"])}</p>
<a class="footer__phone" href="tel:{esc(c["phoneRaw"])}">{esc(c["phone"])}</a>
{tg_links}
<a class="footer__link" href="mailto:{esc(c["email"])}">{esc(c["email"])}</a>
</div>
<div><p class="footer__title">Направления</p><ul>{"".join(f'<li><a href="/{esc(o["slug"])}/">{esc(o["menu"])}</a></li>' for o in all_lps)}</ul></div>
<div><p class="footer__title">Разделы</p><ul>{"".join(f'<li><a href="/{esc(n["href"])}">{esc(n["label"])}</a></li>' for n in site["nav"])}</ul></div>
</div>
<div class="footer__bottom">
<p>{esc(site["footer"]["cities"])}</p>
<p>© {esc(b["company"])} · <a href="/privacy.html">Политика конфиденциальности</a></p>
<p class="footer__legal">{esc(b["legalName"])} · Рег. номер в КНР (USCC): {esc(b["regCode"])}<br>Адрес: {esc(b["address"])}</p>
<p class="footer__disclaimer">{esc(site["footer"]["disclaimer"])}</p>
</div>
</div></footer>'''

    fab = f'<a class="fab{" fab--tg" if c.get("manager") else ""}" href="{esc(lead_url)}" {ext} aria-label="Написать менеджеру">{ICONS["tg"] if c.get("manager") else ICONS["wa"]}</a>'
    if wa_url:
        fab += f'\n<a class="fab fab--mini" href="{esc(wa_url)}" {ext} aria-label="Написать в WhatsApp">{ICONS["wa"]}</a>'

    org = {"@type": "Organization", "@id": s["url"] + "#org", "name": b["name"], "legalName": b.get("legalName"),
           "url": s["url"], "logo": s["url"] + b["logo"], "telephone": c["phoneRaw"], "email": c["email"]}
    ld = {"@context": "https://schema.org", "@graph": [
        org,
        {"@type": "Service", "name": plain(lp["h1"]), "description": lp["description"], "url": url,
         "provider": {"@id": s["url"] + "#org"}, "serviceType": "Доставка грузов из Китая",
         "areaServed": site["process"]["countries"]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": s["url"]},
            {"@type": "ListItem", "position": 2, "name": lp["menu"], "item": url}]},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": f["q"],
            "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in lp["faq"]]},
    ]}
    ld_json = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")

    return f'''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="{CSP}">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {MARK}
  <title>{esc(lp["title"])}</title>
  <meta name="description" content="{esc(lp["description"])}">
  <meta name="theme-color" content="#0e1a33">
  <link rel="canonical" href="{esc(url)}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="ru_RU">
  <meta property="og:site_name" content="{esc(b["name"])}">
  <meta property="og:title" content="{esc(lp["title"])}">
  <meta property="og:description" content="{esc(lp["description"])}">
  <meta property="og:url" content="{esc(url)}">
  <meta property="og:image" content="{esc(s["url"] + s["image"])}">
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" type="image/png" sizes="120x120" href="/assets/icon-120.png">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="preload" href="/assets/fonts/onest-cyrillic.woff2" as="font" type="font/woff2" crossorigin="">
  <link rel="stylesheet" href="/css/style.css?v={version}">
  <script type="application/ld+json">{ld_json}</script>
</head>
<body class="lp">
<header class="header is-scrolled">
  <div class="container header__inner">
    <a class="logo" href="/" aria-label="На главную"><img class="logo__img" src="/{esc(b["logo"])}" alt="" width="42" height="42"><span class="logo__text"><span class="logo__name">{esc(b["name"])}</span><span class="logo__tag">{esc(b["tagline"])}</span></span></a>
    <a class="header__phone" href="tel:{esc(c["phoneRaw"])}">{esc(c["phone"])}</a>
    <a class="btn btn--primary btn--sm lp__cta" href="{esc(lead_url)}" {ext}>Рассчитать</a>
  </div>
</header>
<main>
{hero}
{price}
{steps}
{sections}
{perks}
{faq}
{cta}
</main>
{footer}
{fab}
</body>
</html>
'''


def build(root, lps, site, version):
    """Пишет страницы, удаляет страницы, которых больше нет в landings.js. Возвращает список slug."""
    icons(root)
    slugs = []
    for lp in lps:
        slug = lp["slug"]
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
            raise SystemExit(f"landings.js: slug «{slug}» — только латиница, цифры и дефисы")
        page = render(lp, lps, site, version)
        if 'style="' in page:
            raise SystemExit(f"landings.js: в странице {slug} есть style=\"...\" — его заблокирует CSP")
        (root / slug).mkdir(exist_ok=True)
        (root / slug / "index.html").write_text(page, encoding="utf-8", newline="\n")
        slugs.append(slug)
    for f in root.glob("*/index.html"):
        if f.parent.name not in slugs and MARK in f.read_text(encoding="utf-8", errors="ignore"):
            shutil.rmtree(f.parent)
    return slugs


def footer_links(lps):
    return "".join(f'<li><a href="{esc(lp["slug"])}/">{esc(lp["menu"])}</a></li>' for lp in lps)
