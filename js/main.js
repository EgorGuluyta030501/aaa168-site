/* Подставляет контент из content.js в страницу и оживляет интерактив.
   Тексты здесь не хранятся — правьте content.js. */
(function () {
  "use strict";

  const S = window.SITE;
  if (!S) return;

  // tools/build.py открывает страницу с PRERENDER = true и сохраняет готовый текст прямо в index.html,
  // чтобы Яндекс видел его без JavaScript. В этом режиме анимации не запускаются.
  const BUILD = window.PRERENDER === true;
  window.__siteReady = true;
  document.documentElement.classList.add("js");

  // Если скрипт упадёт (например, в content.js чего-то не хватает),
  // блоки страницы всё равно станут видимыми — см. catch в конце файла.
  try {

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const get = (obj, path) => path.split(".").reduce((o, k) => (o == null ? o : o[k]), obj);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const rich = (s) => esc(s).replace(/\*(.+?)\*/g, '<span class="accent">$1</span>');
  const plain = (s) => String(s ?? "").replace(/\*/g, "");

  // Иконки для карточек: в content.js пишется имя иконки, например icon: "truck"
  const svg = (body) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${body}</svg>`;
  const ICONS = {
    truck: svg('<path d="M2 5.5h12v10H2zM14 8.5h4l3.5 3.5v3.5H14"/><circle cx="6" cy="18.5" r="2"/><circle cx="17.5" cy="18.5" r="2"/>'),
    train: svg('<rect x="5" y="3" width="14" height="14" rx="3"/><path d="M5 11h14"/><path d="M9 14h.01M15 14h.01"/><path d="m8 21 2-4M16 21l-2-4"/>'),
    plane: svg('<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>'),
    customs: svg('<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/><path d="m9 15 2 2 4-4"/>'),
    track: svg('<path d="M12 21s-7-6.1-7-11a7 7 0 0 1 14 0c0 4.9-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>'),
    camera: svg('<path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/><circle cx="12" cy="13.5" r="3.5"/>'),
    manager: svg('<path d="M4 15v-3a8 8 0 0 1 16 0v3"/><rect x="3" y="14" width="4" height="6" rx="1.5"/><rect x="17" y="14" width="4" height="6" rx="1.5"/><path d="M19 20c0 1.1-1.3 2-3 2h-3"/>'),
    box: svg('<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5M12 13v8"/>'),
    shield: svg('<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>'),
    gear: svg('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>'),
    sofa: svg('<path d="M5 11V8a3 3 0 0 1 3-3h8a3 3 0 0 1 3 3v3"/><path d="M3 13a2 2 0 0 1 4 0v2h10v-2a2 2 0 0 1 4 0v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M6 19v2M18 19v2"/>'),
    chip: svg('<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>'),
    shirt: svg('<path d="M20.4 6.6 16 3a4 4 0 0 1-8 0L3.6 6.6a1 1 0 0 0-.3 1.2l1.4 2.9a1 1 0 0 0 1.2.5L8 10.5V20a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-9.5l2.1.7a1 1 0 0 0 1.2-.5l1.4-2.9a1 1 0 0 0-.3-1.2z"/>'),
    cart: svg('<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.7 12.4a2 2 0 0 0 2 1.6h7.6a2 2 0 0 0 2-1.5L21 8H6.2"/>'),
    sample: svg('<path d="M9 3h6M10 3v6L4.6 18.2A2 2 0 0 0 6.3 21h11.4a2 2 0 0 0 1.7-2.8L14 9V3"/><path d="M7 15h10"/>'),
    wrench: svg('<path d="M14.7 6.3a4 4 0 0 0 5 5L21 12.6a6 6 0 0 1-7.5 1.7L6 21.8a2.1 2.1 0 0 1-3-3l7.5-7.5a6 6 0 0 1 1.7-7.5z"/>'),
    brick: svg('<rect x="3" y="5" width="18" height="14" rx="1"/><path d="M3 12h18M9 5v7M15 12v7"/>'),
    coin: svg('<circle cx="12" cy="12" r="9"/><path d="M14.8 9.2A3 3 0 0 0 12 8c-1.7 0-3 .9-3 2s1.3 1.7 3 2 3 .9 3 2-1.3 2-3 2a3 3 0 0 1-2.8-1.2M12 6.5v1.5M12 16v1.5"/>'),
    check: svg('<path d="m5 12.5 4.5 4.5L19 7.5"/>'),
  };

  const C = S.contacts;
  const waLink = (text) => `https://wa.me/${C.whatsapp}` + (text ? `?text=${encodeURIComponent(text)}` : "");
  const tgLink = (text) => `https://t.me/${C.manager}` + (text ? `?text=${encodeURIComponent(text)}` : "");
  // Заявки идут в Telegram менеджера, если он указан, иначе в WhatsApp
  const leadLink = (text) => (C.manager ? tgLink(text) : waLink(text));

  /* ---------- Тексты, SEO, бренд, контакты ---------- */
  // находит или создаёт тег в <head>: setHead("meta", "property", "og:title", "content", "...")
  const setHead = (tag, key, name, attr, value) => {
    let el = $(`${tag}[${key}="${name}"]`);
    if (!value) { if (el) el.remove(); return; }
    if (!el) { el = document.createElement(tag); el.setAttribute(key, name); document.head.appendChild(el); }
    el.setAttribute(attr, value);
  };
  if (S.seo) {
    const SEO = S.seo;
    const abs = (path) => (SEO.url && path ? new URL(path, SEO.url).href : "");
    document.title = SEO.title;
    setHead("meta", "name", "description", "content", SEO.description);
    setHead("link", "rel", "canonical", "href", SEO.url);
    setHead("meta", "property", "og:title", "content", SEO.title);
    setHead("meta", "property", "og:description", "content", SEO.description);
    setHead("meta", "property", "og:url", "content", SEO.url);
    setHead("meta", "property", "og:site_name", "content", S.brand.name);
    setHead("meta", "property", "og:image", "content", abs(SEO.image));
    setHead("meta", "name", "yandex-verification", "content", SEO.yandexVerification);
    setHead("meta", "name", "google-site-verification", "content", SEO.googleVerification);

    // Разметка schema.org: поисковик понимает, что это за компания и какие вопросы на странице
    const ld = {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "Organization",
          name: S.brand.name,
          legalName: S.brand.company,
          url: SEO.url,
          logo: abs(S.brand.logo),
          description: SEO.description,
          email: C.email || undefined,
          telephone: C.phoneRaw || undefined,
          areaServed: S.process ? S.process.countries : undefined,
          sameAs: [C.telegram && "https://t.me/" + C.telegram].filter(Boolean),
        },
        {
          "@type": "FAQPage",
          mainEntity: S.faq.items.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })),
        },
      ],
    };
    let ldEl = $("#ld-json");
    if (!ldEl) {
      ldEl = document.createElement("script");
      ldEl.type = "application/ld+json";
      ldEl.id = "ld-json";
      document.head.appendChild(ldEl);
    }
    ldEl.textContent = JSON.stringify(ld);
  }

  $$("[data-text]").forEach((el) => { el.textContent = plain(get(S, el.dataset.text)); });
  $$("[data-rich]").forEach((el) => { el.innerHTML = rich(get(S, el.dataset.rich)); });

  const markHTML = S.brand.logo
    ? `<img class="logo__img" src="${esc(S.brand.logo)}" alt="" width="42" height="42">`
    : `<span class="logo__mark">${esc(S.brand.mark)}</span>`;
  const brandHTML =
    markHTML +
    `<span class="logo__text"><span class="logo__name">${esc(S.brand.name)}<em>${esc(S.brand.suffix)}</em></span>` +
    `<span class="logo__tag">${esc(S.brand.tagline)}</span></span>`;
  $$("[data-brand]").forEach((el) => { el.innerHTML = brandHTML; });

  // пустой контакт в content.js — ссылка на него скрывается
  const bind = (sel, value, apply) => $$(sel).forEach((el) => { el.hidden = !value; if (value) apply(el); });
  bind("[data-lead]", C.manager || C.whatsapp, (el) => { el.href = leadLink(); });
  $$(".fab").forEach((el) => el.classList.toggle("fab--tg", Boolean(C.manager)));
  bind("[data-alt]", C.manager && C.whatsapp, () => {});
  bind("[data-tgmanager]", C.manager, (el) => { el.textContent = "@" + C.manager; el.href = tgLink(); });
  bind("[data-phone]", C.phone, (el) => { el.textContent = C.phone; el.href = "tel:" + C.phoneRaw; });
  bind("[data-phone2]", C.phone2, (el) => { el.textContent = C.phone2; el.href = "tel:" + C.phone2Raw; });
  bind("[data-wa]", C.whatsapp, (el) => { el.href = waLink(); });
  $$("[data-label]").forEach((el) => { el.textContent = C[el.dataset.label] || ""; });
  $$("[data-contact]").forEach((el) => { el.textContent = C[el.dataset.contact] || ""; });
  $$("[data-row]").forEach((el) => { el.hidden = !C[el.dataset.row]; });
  bind("[data-tg]", C.telegram, (el) => { el.href = "https://t.me/" + C.telegram; });
  bind("[data-tgchat]", C.telegramChat, (el) => { el.href = "https://t.me/" + C.telegramChat; });
  bind("[data-email]", C.email, (el) => { el.textContent = C.email; el.href = "mailto:" + C.email; });
  $("#year").textContent = new Date().getFullYear();

  /* ---------- Меню ---------- */
  $("#nav-links").innerHTML = S.nav.map((n) => `<a href="${esc(n.href)}">${esc(n.label)}</a>`).join("");

  const header = $("#header");
  const burger = $("#burger");
  const setMenu = (open) => {
    document.body.classList.toggle("nav-open", open);
    burger.setAttribute("aria-expanded", String(open));
    burger.setAttribute("aria-label", open ? "Закрыть меню" : "Открыть меню");
  };
  burger.addEventListener("click", () => setMenu(!document.body.classList.contains("nav-open")));
  $$("#nav a").forEach((a) => a.addEventListener("click", () => setMenu(false)));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") setMenu(false); });

  const onScroll = () => header.classList.toggle("is-scrolled", window.scrollY > 10);
  // при открытии меню шапка всегда видна
  burger.addEventListener("click", () => header.classList.remove("is-hidden"));
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Главный экран ---------- */
  $("#stats").innerHTML = S.stats
    .map((s) => `<div class="stat"><div class="stat__value">${esc(s.value)}</div><div class="stat__label">${esc(s.label)}</div></div>`)
    .join("");

  /* ---------- Виды доставки: карточки с фото ---------- */
  $("#transport-list").innerHTML = S.transport.items
    .map((it) => `
    <article class="mode reveal">
      <div class="mode__media">
        ${it.photo ? `<img src="${esc(it.photo)}" alt="${esc(it.title)}" loading="lazy" width="800" height="600">` : ""}
        <span class="chip">${esc(it.price)}</span>
      </div>
      <div class="mode__body">
        <h3 class="mode__title"><span class="mode__icon" aria-hidden="true">${ICONS[it.icon] || ""}</span>${esc(it.title)}</h3>
        <p class="mode__text">${esc(it.text)}</p>
        <div class="mode__foot">
          <span class="mode__meta">${esc(it.term || "")}</span>
          <a class="link-arrow" href="#contact" data-topic="${esc(it.title)}">${esc(S.transport.linkText)} <span>→</span></a>
        </div>
      </div>
    </article>`)
    .join("");

  /* ---------- Что возим ---------- */
  if (S.cargo) {
    $("#cargo-list").innerHTML = S.cargo.items
      .map((it) => `
      <article class="good reveal">
        <span class="good__icon" aria-hidden="true">${ICONS[it.icon] || ""}</span>
        <h3 class="good__title">${esc(it.title)}</h3>
        <p class="good__text">${esc(it.text)}</p>
      </article>`)
      .join("");
  }

  /* ---------- Преимущества (в блоке «О компании») ---------- */
  $("#advantages-list").innerHTML = S.advantages.items
    .map((it) => `
      <li class="perk reveal">
        <span class="perk__icon" aria-hidden="true">${ICONS[it.icon] || ""}</span>
        <div><h3 class="perk__title">${esc(it.title)}</h3><p class="perk__text">${esc(it.text)}</p></div>
      </li>`)
    .join("");

  /* ---------- Как работает карго: этапы и страны ---------- */
  const PR = S.process;
  $("#steps-list").innerHTML = PR.steps
    .map((s, i) => `
      <li class="step reveal">
        <span class="step__num">${String(i + 1).padStart(2, "0")}</span>
        <h3>${esc(s.title)}</h3>
        <p>${esc(s.text)}</p>
      </li>`)
    .join("");
  $("#countries-list").innerHTML = PR.countries.map((c) => `<li>${esc(c)}</li>`).join("");

  /* ---------- Видео ---------- */
  // Видео не грузится, пока его не нажмут: на странице только лёгкая картинка-превью
  const videoCard = (v) => `
    <figure class="vcard reveal">
      <button class="vcard__play" type="button" data-src="${esc(v.src)}" aria-label="Смотреть: ${esc(v.title)}">
        <img src="${esc(v.poster)}" alt="" loading="lazy">
        <span class="vcard__icon" aria-hidden="true"></span>
      </button>
      <figcaption>${esc(v.title)}</figcaption>
    </figure>`;

  $("#warehouse-list").innerHTML = S.warehouse.videos.map(videoCard).join("").replace(/vcard reveal/g, "vcard");
  if (S.about.video) $("#about-video").innerHTML = videoCard(S.about.video);

  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".vcard__play");
    if (!btn) return;
    // одновременно играет только одно видео
    $$("video.vcard__video").forEach((v) => v.pause());
    const video = document.createElement("video");
    video.className = "vcard__video";
    video.src = btn.dataset.src;
    video.poster = $("img", btn).src;
    video.controls = true;
    video.playsInline = true;
    video.autoplay = true;
    btn.replaceWith(video);
    video.addEventListener("play", () => $$("video.vcard__video").forEach((v) => v !== video && v.pause()));
  });

  /* ---------- Отзывы ---------- */
  const R = S.reviews;
  $("#reviews-list").innerHTML = [
    ...R.texts.map((r) => `
      <figure class="review panel">
        <div class="review__stars" aria-label="5 из 5">★★★★★</div>
        <blockquote class="review__text">${esc(r.text)}</blockquote>
        <figcaption class="review__author"><strong>${esc(r.author)}</strong><span>${esc(r.role)}</span></figcaption>
      </figure>`),
    ...R.screenshots.map((s) => `
      <button class="shot" type="button" data-full="${esc(s.src)}" aria-label="Открыть отзыв целиком">
        <img src="${esc(s.src)}" alt="${esc(s.alt)}" loading="lazy">
      </button>`),
  ].join("");

  /* ---------- Листалки (отзывы, видео) ---------- */
  $$(".slider").forEach((slider) => {
    const track = $(".slider__track", slider);
    const [prev, next] = $$(".slider__btn", slider);
    const update = () => {
      const max = track.scrollWidth - track.clientWidth - 2;
      prev.disabled = track.scrollLeft <= 2;
      next.disabled = track.scrollLeft >= max;
      slider.classList.toggle("is-static", max <= 0);
    };
    $$(".slider__btn", slider).forEach((b) => b.addEventListener("click", () => {
      const item = track.firstElementChild;
      const stepW = item ? item.getBoundingClientRect().width + 16 : track.clientWidth;
      const n = Math.max(1, Math.floor(track.clientWidth / stepW));
      track.scrollBy({ left: Number(b.dataset.dir) * stepW * n, behavior: "smooth" });
    }));
    track.addEventListener("scroll", () => requestAnimationFrame(update), { passive: true });
    window.addEventListener("resize", update);
    $$("img", track).forEach((img) => img.addEventListener("load", update));
    track.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") { e.preventDefault(); next.click(); }
      if (e.key === "ArrowLeft") { e.preventDefault(); prev.click(); }
    });
    // перетаскивание мышью на компьютере
    let down = false, startX = 0, startL = 0, moved = false;
    track.addEventListener("pointerdown", (e) => {
      if (e.pointerType !== "mouse") return;
      down = true; moved = false; startX = e.clientX; startL = track.scrollLeft;
    });
    window.addEventListener("pointermove", (e) => {
      if (!down) return;
      const dx = e.clientX - startX;
      if (Math.abs(dx) > 5) { moved = true; track.classList.add("is-dragging"); }
      if (moved) track.scrollLeft = startL - dx;
    });
    window.addEventListener("pointerup", () => { down = false; track.classList.remove("is-dragging"); });
    // после перетаскивания клик не открывает отзыв / видео
    track.addEventListener("click", (e) => { if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; } }, true);
    update();
  });

  const lightbox = $("#lightbox");
  document.addEventListener("click", (e) => {
    const shot = e.target.closest(".shot");
    if (!shot || !lightbox.showModal) return;
    const img = $("img", lightbox) || lightbox.appendChild(document.createElement("img"));
    img.src = shot.dataset.full;
    img.alt = $("img", shot).alt;
    lightbox.showModal();
  });
  // закрыть по крестику или клику мимо картинки
  lightbox.addEventListener("click", (e) => { if (e.target.tagName !== "IMG") lightbox.close(); });

  /* ---------- Команда: фото или инициалы, пока фото нет ---------- */
  const team = S.team && S.team.items.length ? S.team : null;
  $("#team").hidden = !team;
  $("#team-list").innerHTML = "";
  if (team) {
    const initials = (name) => name.split(/\s+/).map((w) => w[0] || "").join("").slice(0, 2).toUpperCase();
    $("#team-list").innerHTML = team.items
      .map((p) => `
      <figure class="person reveal">
        <div class="person__photo">${p.photo
          ? `<img src="${esc(p.photo)}" alt="${esc(p.name)}" loading="lazy" width="400" height="400">`
          : `<span aria-hidden="true">${esc(initials(p.name))}</span>`}</div>
        <figcaption>
          <strong class="person__name">${esc(p.name)}</strong>
          <span class="person__role">${esc(p.role)}</span>
          <p class="person__text">${esc(p.text)}</p>
        </figcaption>
      </figure>`)
      .join("");
  }

  const footerList = (items) => items.map((it) => `<li><a href="#contact" data-topic="${esc(it.title)}">${esc(it.title)}</a></li>`).join("");
  $("#footer-transport").innerHTML = footerList(S.transport.items);
  $("#footer-nav").innerHTML = S.nav.map((n) => `<li><a href="${esc(n.href)}">${esc(n.label)}</a></li>`).join("");

  /* ---------- Вопросы ---------- */
  $("#faq-list").innerHTML = S.faq.items
    .map((f) => `
      <details name="faq">
        <summary>${esc(f.q)}</summary>
        <div class="faq__body">${esc(f.a)}</div>
      </details>`)
    .join("");

  /* ---------- Форма заявки ---------- */
  const form = $("#lead-form");
  const modeSelect = $("#form-mode");
  const message = $("#form-message");

  modeSelect.innerHTML = [S.contact.dontKnow, ...(S.contact.modes || [])]
    .map((v) => `<option>${esc(v)}</option>`)
    .join("");
  message.placeholder = S.contact.messagePlaceholder;
  const budgetSelect = $("#form-budget");
  budgetSelect.innerHTML = `<option value="">Выберите бюджет</option>` + (S.contact.budgets || []).map((v) => `<option>${esc(v)}</option>`).join("");

  const countrySelect = $("#form-country");
  const options = (list) => list.map((v) => `<option>${esc(v)}</option>`).join("");

  /* ---------- Быстрая заявка на главном экране ---------- */
  // Открывает заявку в мессенджере. Текст ещё и копируется: если мессенджер его
  // не подставит, клиент просто вставит его в чат.
  const sendLead = (formEl, e, text) => {
    const viaWa = e.submitter && e.submitter.dataset.send === "wa";
    window.open(viaWa ? waLink(text) : leadLink(text), "_blank", "noopener");
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => { $(".form__copied", formEl).hidden = false; }, () => {});
    }
  };

  const quick = $("#quick-form");
  quick.hidden = !S.hero.quick;
  if (S.hero.quick) {
  const countries = [...PR.countries, "Другая страна"];
  const modes = [...(S.contact.modes || []), "Не знаю"];
  let quickMode = modes[modes.length - 1];

  $("#quick-country").innerHTML = options(countries);
  const qSeg = $("#quick-mode");
  qSeg.innerHTML = modes
    .map((c) => `<button type="button" role="radio" aria-checked="false" data-v="${esc(c)}">${esc(c)}</button>`)
    .join("");
  const paintSeg = () => $$("button", qSeg).forEach((b) => {
    const on = b.dataset.v === quickMode;
    b.classList.toggle("is-active", on);
    b.setAttribute("aria-checked", String(on));
  });
  qSeg.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    quickMode = b.dataset.v;
    paintSeg();
  });
  paintSeg();
  $("#quick-weight").placeholder = S.hero.quick.weightPlaceholder;

  quick.addEventListener("submit", (e) => {
    e.preventDefault();
    const w = quick.elements.weight.value.trim();
    const text = [
      "Заявка на расчёт с сайта",
      `Страна: ${quick.elements.country.value}`,
      `Доставка: ${quickMode}`,
      w && `Вес: ${w} кг`,
    ].filter(Boolean).join("\n");
    sendLead(quick, e, text);
  });
  }
  countrySelect.innerHTML = options([...PR.countries, "Другая страна"]);

  // Кнопки «Рассчитать» в карточках подставляют тему в заявку
  document.addEventListener("click", (e) => {
    const link = e.target.closest("[data-topic]");
    if (!link) return;
    message.value = `Интересует: ${link.dataset.topic}. `;
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = [
      "Заявка с сайта",
      `Страна: ${countrySelect.value}`,
      `Доставка: ${modeSelect.value}`,
      budgetSelect.value && `Бюджет: ${budgetSelect.value}`,
      message.value.trim() && `Груз: ${message.value.trim()}`,
    ].filter(Boolean).join("\n");
    sendLead(form, e, text);
  });

  /* ---------- Анимации ---------- */
  if (BUILD) return;
  const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Фоновое видео главного экрана. На телефоне — лёгкая версия; при «уменьшении движения»
  // и режиме экономии трафика остаётся только картинка-постер. За пределами экрана видео на паузе.
  const heroVideo = $("#hero-video");
  const saveData = navigator.connection && navigator.connection.saveData;
  // Видео начинает грузиться после самой страницы, чтобы не тормозить её открытие.
  const startHeroVideo = () => {
    heroVideo.muted = true;
    heroVideo.src = window.matchMedia("(max-width: 768px)").matches ? "assets/video/hero-mobile.mp4" : "assets/video/hero.mp4";
    heroVideo.preload = "auto";
    const play = () => { const p = heroVideo.play(); if (p && p.catch) p.catch(() => { /* автозапуск запрещён — остаётся постер */ }); };
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(([en]) => { if (en.isIntersecting && !document.hidden) play(); else heroVideo.pause(); })
        .observe(heroVideo.parentElement);
    } else play();
  };
  if (heroVideo && !calm && !saveData) {
    if (document.readyState === "complete") startHeroVideo();
    else window.addEventListener("load", startHeroVideo, { once: true });
  }

  // Заголовки выезжают по словам из-под «шторки». Только в браузере посетителя:
  // в index.html для поисковиков текст остаётся обычным.
  const splitWords = (el) => {
    let n = 0;
    const walk = (node) => [...node.childNodes].forEach((ch) => {
      if (ch.nodeType === 1) return walk(ch);
      if (ch.nodeType !== 3 || !ch.textContent.trim()) return;
      const frag = document.createDocumentFragment();
      ch.textContent.split(/(\s+)/).forEach((part) => {
        if (!part) return;
        if (/^\s+$/.test(part)) return frag.append(part);
        const w = document.createElement("span");
        const inner = document.createElement("span");
        w.className = "w";
        inner.textContent = part;
        inner.style.setProperty("--wi", n++);
        w.append(inner);
        frag.append(w);
      });
      ch.replaceWith(frag);
    });
    walk(el);
    el.classList.add("is-split");
  };
  if (!calm) $$(".hero__title, .section__title").forEach(splitWords);

  // Кнопки, которые слегка тянутся за курсором
  if (!calm && window.matchMedia("(hover: hover)").matches) {
    $$("[data-magnetic]").forEach((el) => {
      el.addEventListener("pointermove", (e) => {
        const r = el.getBoundingClientRect();
        el.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * 0.2}px, ${(e.clientY - r.top - r.height / 2) * 0.3}px)`;
      });
      el.addEventListener("pointerleave", () => { el.style.transform = ""; });
    });
  }

  // Полоса прокрутки вверху страницы
  const bar = $("#progress");
  let ticking = false;
  // Кнопка «Наверх»: появляется после первого экрана, кольцо показывает, сколько пролистано
  const toTop = $("#totop");
  const ring = $("#totop circle");
  const RING = 2 * Math.PI * 22;
  ring.style.strokeDasharray = RING;
  toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: calm ? "auto" : "smooth" }));

  // Главный экран при прокрутке: видео уходит медленнее страницы, текст растворяется (только на ПК)
  const hero = $(".hero");
  const heroInner = $("#hero-inner");
  const wide = window.matchMedia("(min-width: 1001px)");
  const paintHero = () => {
    const y = window.scrollY;
    const h = hero.offsetHeight;
    if (y > h) return;
    const k = y / h;
    heroVideo.style.transform = `translateY(${y * 0.35}px) scale(${1 + k * 0.08})`;
    heroInner.style.transform = wide.matches ? `translateY(${y * 0.18}px)` : "";
    heroInner.style.opacity = wide.matches ? String(Math.max(0, 1 - k * 1.2)) : "";
  };

  // Шапка прячется, когда листают вниз, и возвращается при прокрутке вверх
  let lastY = window.scrollY;
  const paintHeader = () => {
    const y = window.scrollY;
    const down = y > lastY && y > window.innerHeight * 0.6 && !document.body.classList.contains("nav-open");
    if (Math.abs(y - lastY) > 4) header.classList.toggle("is-hidden", down);
    lastY = y;
  };

  // Маршрут по этапам: линия и фура едут вместе с прокруткой, пройденные этапы загораются
  const route = $("#route");
  const stepEls = $$("#steps-list .step");
  const paintRoute = () => {
    const r = route.getBoundingClientRect();
    const vh = window.innerHeight;
    const p = Math.min(1, Math.max(0, (vh * 0.85 - r.top) / (r.height + vh * 0.3)));
    route.style.setProperty("--p", p.toFixed(3));
    stepEls.forEach((s, i) => s.classList.toggle("is-active", p >= i / stepEls.length + 0.02 || p > 0.99));
  };
  if (!calm) route.classList.add("is-live");

  const paintScroll = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const k = max > 0 ? window.scrollY / max : 0;
    bar.style.transform = `scaleX(${k})`;
    ring.style.strokeDashoffset = RING * (1 - k);
    toTop.classList.toggle("is-visible", window.scrollY > window.innerHeight * 0.8);
    paintHeader();
    if (!calm) { paintHero(); paintRoute(); }
    ticking = false;
  };
  window.addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(paintScroll); } }, { passive: true });
  window.addEventListener("resize", paintScroll);
  paintScroll();

  // Бегущая строка стран: едет в сторону прокрутки и разгоняется, когда листают быстрее
  const track = $("#countries-list");
  if (!calm) {
    const items = [...track.children];
    for (let k = 0; k < 2; k++) {
      items.forEach((li) => { const c = li.cloneNode(true); c.setAttribute("aria-hidden", "true"); track.append(c); });
    }
    track.classList.add("is-live");
    let x = 0, vel = 0, dir = 1, prevY = window.scrollY, running = false;
    const loop = () => {
      if (!running) return;
      const dy = window.scrollY - prevY;
      prevY = window.scrollY;
      if (dy) dir = dy > 0 ? 1 : -1;
      vel = vel * 0.92 + Math.abs(dy) * 0.08;
      const copy = track.scrollWidth / 3;
      x -= dir * (0.5 + vel * 0.6);
      if (x <= -copy) x += copy;
      if (x > 0) x -= copy;
      track.style.transform = `translateX(${x}px)`;
      requestAnimationFrame(loop);
    };
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(([en]) => {
        running = en.isIntersecting;
        if (running) { prevY = window.scrollY; requestAnimationFrame(loop); }
      }).observe(track.parentElement);
    }
  }

  // Числа в полосе сроков отсчитываются от нуля: «от 12 дней», «5–8 дней»
  const countUp = (el) => {
    const src = el.textContent;
    const nums = src.match(/\d+/g);
    if (!nums || calm) return;
    const t0 = performance.now();
    const dur = 1400;
    const step = (t) => {
      const k = Math.min(1, (t - t0) / dur);
      const ease = 1 - Math.pow(1 - k, 3);
      let i = 0;
      el.textContent = src.replace(/\d+/g, () => Math.round(Number(nums[i++]) * ease));
      if (k < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  /* ---------- Подсветка пункта меню и появление блоков ---------- */
  $$(".section__head").forEach((el) => el.classList.add("reveal"));

  if ("IntersectionObserver" in window) {
    const links = $$("#nav-links a");
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        links.forEach((a) => a.classList.toggle("is-active", a.getAttribute("href") === "#" + en.target.id));
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    S.nav.forEach((n) => { const sec = $(n.href); if (sec) spy.observe(sec); });

    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        const el = en.target;
        el.classList.add("is-in", "is-seen"); // is-seen остаётся навсегда — для черты над заголовком и слов в нём
        io.unobserve(el);
        if (el.matches(".mode")) countUp($(".chip", el)); // сроки на фото отсчитываются
        // после анимации возвращаем карточкам их собственный hover
        setTimeout(() => { el.classList.remove("reveal", "is-in"); el.style.transitionDelay = ""; }, 1000);
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    // каскад: соседние карточки появляются друг за другом
    $$(".reveal").forEach((el) => {
      const i = Array.prototype.indexOf.call(el.parentElement.children, el);
      el.style.transitionDelay = `${Math.min(i, 5) * 90}ms`;
      io.observe(el);
    });

    const statsIO = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        $$(".stat__value", en.target).forEach(countUp);
        statsIO.unobserve(en.target);
      });
    }, { threshold: 0.4 });
    statsIO.observe($("#stats"));
  } else {
    $$(".reveal").forEach((el) => el.classList.add("is-in", "is-seen"));
  }
  } catch (err) {
    console.error("[сайт] ошибка при отрисовке:", err);
    document.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-in"));
  }
})();
