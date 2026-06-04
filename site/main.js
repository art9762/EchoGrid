/* ============================================================
   EchoGrid — promo landing logic
   - i18n (EN/RU) with localStorage persistence
   - hero <canvas> echo-grid animation (vanilla rAF)
   - scroll reveal + pipeline highlight + count-up via Motion (CDN ESM)
   - all motion gated behind prefers-reduced-motion; content never
     stays hidden if Motion fails to load
   ============================================================ */

/* ----------------------------------------------------------
   1. i18n dictionary
   ---------------------------------------------------------- */
const i18n = {
  en: {
    "skip": "Skip to content",
    "nav.what": "What",
    "nav.how": "How",
    "nav.features": "Features",
    "nav.ethics": "Ethics",
    "nav.demo": "Demo",
    "nav.github": "GitHub",

    "hero.eyebrow": "LLM-assisted synthetic society simulator",
    "hero.title": "Watch a message ripple across a synthetic society.",
    "hero.tagline": "EchoGrid simulates how a public event triggers reactions, travels through a media ecosystem, and gets amplified, distorted, or polarized by echo effects — using synthetic agents, not real people.",
    "hero.cta1": "View on GitHub",
    "hero.cta2": "See how it works",
    "hero.note": "Runs locally as a Streamlit app · Deterministic mock mode needs no API keys · MIT",
    "hero.scroll": "Scroll",

    "what.kicker": "Positioning",
    "what.title": "A hypothesis lab — not a crystal ball",
    "what.lead": "EchoGrid generates synthetic simulation outputs to explore communication dynamics. Treat them as ideas to test, never as measured public opinion.",
    "what.isLabel": "What it is",
    "what.isHead": "A synthetic society simulator",
    "what.is1": "Builds synthetic agents with demographic, economic, psychological, social, and media-consumption profiles.",
    "what.is2": "Simulates media framings of a public event and each agent's initial reaction.",
    "what.is3": "Propagates social and media echo items through multi-round cascades inside bubbles.",
    "what.is4": "Reports before/after metrics: amplification, trust, anger, distortion, polarization.",
    "what.notLabel": "What it is not",
    "what.notHead": "Not a poll, not a prediction",
    "what.not1": "Not a polling tool — it does not measure or predict actual public opinion.",
    "what.not2": "Not scientifically calibrated — mock mode is plausible and deterministic, not survey evidence.",
    "what.not3": "Not a persuasion optimizer — never for manipulation or political targeting.",
    "what.not4": "Not for harm — no harassment, radicalization, or targeting of vulnerable groups.",

    "how.kicker": "Pipeline",
    "how.title": "How it works",
    "how.lead": "One news event flows through six deterministic stages. Each stage feeds the next, ending in measurable before/after metrics.",
    "how.s1t": "News event",
    "how.s1d": "Enter or pick a public information event to test.",
    "how.s2t": "Synthetic population",
    "how.s2d": "Generate up to 1000 agents with rich profiles.",
    "how.s3t": "Media framings",
    "how.s3d": "Outlets frame the event across an ecosystem.",
    "how.s4t": "Initial reactions",
    "how.s4d": "Each agent reacts to the framings it sees.",
    "how.s5t": "Echo cascade",
    "how.s5d": "Echo items ripple through bubbles in rounds.",
    "how.s6t": "Final metrics",
    "how.s6d": "Compare before/after, then store and export.",

    "feat.kicker": "Capabilities",
    "feat.title": "Built for serious exploration",
    "feat.lead": "A full simulation stack — population, media, cascades, metrics, storage, and tunable run modes — running locally.",
    "feat.stat1": "synthetic agents",
    "feat.stat2": "demo scenarios",
    "feat.stat3": "run modes",
    "feat.stat4": "echo metrics",
    "feat.c1t": "Synthetic population profiles",
    "feat.c1d": "Agents with demographic, economic, psychological, social, and media-consumption attributes.",
    "feat.c2t": "Media ecosystem",
    "feat.c2d": "Configurable outlets and presets that frame the same event in competing ways.",
    "feat.c3t": "Multi-round echo cascades",
    "feat.c3d": "Bounded multi-round propagation of echo items inside social bubbles.",
    "feat.c4t": "Before / after metrics",
    "feat.c4d": "Amplification, trust, anger, distortion, and polarization, compared end to end.",
    "feat.c5t": "Storage & export",
    "feat.c5d": "SQLite persistence with CSV, JSON, and full ZIP bundle exports of every run.",
    "feat.c6t": "Three run modes",
    "feat.c6d": "Mock (fully local), Hybrid (bounded LLM calls), and capped Full LLM sample.",

    "scen.kicker": "Demo scenarios",
    "scen.title": "Seven events, ready to run",
    "scen.lead": "Built-in scenarios you can launch in mock mode without a single API key.",
    "scen.1": "Emissions-based car tax",
    "scen.2": "AI surveillance in public spaces",
    "scen.3": "Four-day work week proposal",
    "scen.4": "Mandatory digital ID",
    "scen.5": "Housing policy reform",
    "scen.6": "University bans phones in classrooms",
    "scen.7": "City restricts short-term rentals",

    "eth.kicker": "Responsible use",
    "eth.title": "Use it to understand, never to manipulate",
    "eth.lead": "EchoGrid produces synthetic outputs as hypothesis-generation artifacts. These boundaries are not optional.",
    "eth.allowLabel": "Allowed",
    "eth.allow1": "Research and hypothesis generation",
    "eth.allow2": "Education and teaching media literacy",
    "eth.allow3": "Communication-risk analysis",
    "eth.allow4": "Media-dynamics exploration",
    "eth.denyLabel": "Disallowed",
    "eth.deny1": "Optimizing manipulative persuasion",
    "eth.deny2": "Political targeting",
    "eth.deny3": "Harassment or radicalization",
    "eth.deny4": "Targeting vulnerable groups",

    "run.kicker": "Get started",
    "run.title": "Run it locally",
    "run.lead": "Clone the repo, install requirements, and launch the Streamlit dashboard. Mock mode runs with zero API keys.",
    "run.copy": "Copy",
    "run.copied": "Copied",
    "run.gh": "View on GitHub",
    "run.docs": "Read the docs",

    "footer.disclaimer": "All EchoGrid results are synthetic simulation outputs — not measurements of real public opinion.",
    "footer.docs": "Docs",
    "footer.license": "MIT License"
  },

  ru: {
    "skip": "Перейти к содержимому",
    "nav.what": "Что это",
    "nav.how": "Как работает",
    "nav.features": "Возможности",
    "nav.ethics": "Этика",
    "nav.demo": "Демо",
    "nav.github": "GitHub",

    "hero.eyebrow": "Симулятор синтетического общества на основе LLM",
    "hero.title": "Посмотрите, как сообщение расходится волнами по синтетическому обществу.",
    "hero.tagline": "EchoGrid моделирует, как публичное событие вызывает реакции, проходит через медиаэкосистему и усиливается, искажается или поляризуется эффектами эха — с помощью синтетических агентов, а не реальных людей.",
    "hero.cta1": "Открыть на GitHub",
    "hero.cta2": "Как это работает",
    "hero.note": "Запускается локально как приложение Streamlit · Детерминированный mock-режим не требует API-ключей · MIT",
    "hero.scroll": "Листайте",

    "what.kicker": "Позиционирование",
    "what.title": "Лаборатория гипотез, а не хрустальный шар",
    "what.lead": "EchoGrid создаёт синтетические результаты симуляции для изучения коммуникационной динамики. Воспринимайте их как идеи для проверки, но никогда — как измеренное общественное мнение.",
    "what.isLabel": "Что это такое",
    "what.isHead": "Симулятор синтетического общества",
    "what.is1": "Создаёт синтетических агентов с демографическими, экономическими, психологическими, социальными и медиапотребительскими профилями.",
    "what.is2": "Моделирует медиаподачи публичного события и первичную реакцию каждого агента.",
    "what.is3": "Распространяет социальные и медийные эхо-сообщения через многораундовые каскады внутри пузырей.",
    "what.is4": "Выдаёт метрики «до/после»: усиление, доверие, гнев, искажение, поляризация.",
    "what.notLabel": "Чем это не является",
    "what.notHead": "Не опрос и не прогноз",
    "what.not1": "Не инструмент опросов — он не измеряет и не предсказывает реальное общественное мнение.",
    "what.not2": "Не научно откалиброван — mock-режим правдоподобен и детерминирован, но это не данные опроса.",
    "what.not3": "Не оптимизатор убеждения — никогда для манипуляции или политического таргетинга.",
    "what.not4": "Не для причинения вреда — без преследования, радикализации и нацеливания на уязвимые группы.",

    "how.kicker": "Конвейер",
    "how.title": "Как это работает",
    "how.lead": "Одно новостное событие проходит шесть детерминированных этапов. Каждый этап питает следующий и завершается измеримыми метриками «до/после».",
    "how.s1t": "Новостное событие",
    "how.s1d": "Введите или выберите публичное событие для проверки.",
    "how.s2t": "Синтетическое население",
    "how.s2d": "Создаётся до 1000 агентов с детальными профилями.",
    "how.s3t": "Медиаподачи",
    "how.s3d": "Издания подают событие в рамках экосистемы.",
    "how.s4t": "Первичные реакции",
    "how.s4d": "Каждый агент реагирует на увиденные подачи.",
    "how.s5t": "Каскад эха",
    "how.s5d": "Эхо-сообщения расходятся по пузырям раундами.",
    "how.s6t": "Итоговые метрики",
    "how.s6d": "Сравнение «до/после», затем сохранение и экспорт.",

    "feat.kicker": "Возможности",
    "feat.title": "Создан для серьёзного исследования",
    "feat.lead": "Полный стек симуляции — население, медиа, каскады, метрики, хранилище и настраиваемые режимы запуска — локально.",
    "feat.stat1": "синтетических агентов",
    "feat.stat2": "демо-сценариев",
    "feat.stat3": "режима запуска",
    "feat.stat4": "метрик эха",
    "feat.c1t": "Профили синтетического населения",
    "feat.c1d": "Агенты с демографическими, экономическими, психологическими, социальными и медиапотребительскими характеристиками.",
    "feat.c2t": "Медиаэкосистема",
    "feat.c2d": "Настраиваемые издания и пресеты, подающие одно событие конкурирующими способами.",
    "feat.c3t": "Многораундовые каскады эха",
    "feat.c3d": "Ограниченное многораундовое распространение эхо-сообщений внутри социальных пузырей.",
    "feat.c4t": "Метрики «до / после»",
    "feat.c4d": "Усиление, доверие, гнев, искажение и поляризация — сравнение от начала до конца.",
    "feat.c5t": "Хранилище и экспорт",
    "feat.c5d": "Хранение в SQLite с экспортом каждого прогона в CSV, JSON и полный ZIP-архив.",
    "feat.c6t": "Три режима запуска",
    "feat.c6d": "Mock (полностью локальный), Hybrid (ограниченные вызовы LLM) и лимитированный Full LLM sample.",

    "scen.kicker": "Демо-сценарии",
    "scen.title": "Семь событий, готовых к запуску",
    "scen.lead": "Встроенные сценарии, которые можно запустить в mock-режиме без единого API-ключа.",
    "scen.1": "Налог на авто по выбросам",
    "scen.2": "ИИ-слежка в общественных местах",
    "scen.3": "Четырёхдневная рабочая неделя",
    "scen.4": "Обязательный цифровой ID",
    "scen.5": "Реформа жилищной политики",
    "scen.6": "Запрет телефонов в аудиториях вуза",
    "scen.7": "Ограничение краткосрочной аренды в городе",

    "eth.kicker": "Ответственное использование",
    "eth.title": "Используйте, чтобы понимать, а не манипулировать",
    "eth.lead": "EchoGrid выдаёт синтетические результаты как материал для генерации гипотез. Эти границы не являются опциональными.",
    "eth.allowLabel": "Разрешено",
    "eth.allow1": "Исследования и генерация гипотез",
    "eth.allow2": "Образование и обучение медиаграмотности",
    "eth.allow3": "Анализ коммуникационных рисков",
    "eth.allow4": "Изучение медиадинамики",
    "eth.denyLabel": "Запрещено",
    "eth.deny1": "Оптимизация манипулятивного убеждения",
    "eth.deny2": "Политический таргетинг",
    "eth.deny3": "Преследование или радикализация",
    "eth.deny4": "Нацеливание на уязвимые группы",

    "run.kicker": "Начало работы",
    "run.title": "Запустите локально",
    "run.lead": "Клонируйте репозиторий, установите зависимости и запустите панель Streamlit. Mock-режим работает без API-ключей.",
    "run.copy": "Копировать",
    "run.copied": "Скопировано",
    "run.gh": "Открыть на GitHub",
    "run.docs": "Читать документацию",

    "footer.disclaimer": "Все результаты EchoGrid — синтетические выходные данные симуляции, а не измерения реального общественного мнения.",
    "footer.docs": "Документация",
    "footer.license": "Лицензия MIT"
  }
};

const LANG_KEY = "echogrid-lang";
let currentLang = "en";

function setLang(lang) {
  if (!i18n[lang]) lang = "en";
  currentLang = lang;
  const dict = i18n[lang];

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key] != null) el.textContent = dict[key];
  });

  document.documentElement.lang = lang;
  try { localStorage.setItem(LANG_KEY, lang); } catch (e) {}

  document.querySelectorAll(".lang-btn").forEach((btn) => {
    const active = btn.dataset.lang === lang;
    btn.classList.toggle("is-active", active);
    btn.setAttribute("aria-pressed", String(active));
  });
}

function initI18n() {
  let saved = "en";
  try { saved = localStorage.getItem(LANG_KEY) || "en"; } catch (e) {}
  setLang(saved);

  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.addEventListener("click", () => setLang(btn.dataset.lang));
  });
}

/* ----------------------------------------------------------
   2. Mobile nav toggle
   ---------------------------------------------------------- */
function initNav() {
  const toggle = document.querySelector(".nav-toggle");
  const links = document.getElementById("nav-links");
  if (!toggle || !links) return;

  toggle.addEventListener("click", () => {
    const open = links.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(open));
  });

  // close on link click (mobile)
  links.querySelectorAll("a[href^='#']").forEach((a) => {
    a.addEventListener("click", () => {
      links.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

/* ----------------------------------------------------------
   3. Copy-command button
   ---------------------------------------------------------- */
function initCopy() {
  const btn = document.querySelector(".code-copy");
  if (!btn) return;
  const label = btn.querySelector(".code-copy-label");
  btn.addEventListener("click", async () => {
    const text = btn.dataset.copy || "";
    try {
      await navigator.clipboard.writeText(text);
    } catch (e) {
      const ta = document.createElement("textarea");
      ta.value = text; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); } catch (_) {}
      ta.remove();
    }
    btn.classList.add("is-done");
    if (label) label.textContent = i18n[currentLang]["run.copied"] || "Copied";
    setTimeout(() => {
      btn.classList.remove("is-done");
      if (label) label.textContent = i18n[currentLang]["run.copy"] || "Copy";
    }, 1600);
  });
}

/* ----------------------------------------------------------
   4. Hero echo-grid canvas animation
   ---------------------------------------------------------- */
function initHeroCanvas(reduceMotion) {
  const canvas = document.getElementById("echo-canvas");
  if (!canvas || reduceMotion) return; // CSS shows static fallback

  const ctx = canvas.getContext("2d");
  let w = 0, h = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
  let cols = 0, rows = 0, spacing = 0;
  let nodes = [];
  const waves = []; // active echo ripples
  let lastEvent = 0;
  let raf = null;
  let running = true;

  const COL_CYAN = [56, 189, 248];
  const COL_VIOLET = [139, 92, 246];

  function resize() {
    w = canvas.clientWidth;
    h = canvas.clientHeight;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.floor(w * dpr));
    canvas.height = Math.max(1, Math.floor(h * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    buildGrid();
  }

  function buildGrid() {
    spacing = w < 600 ? 46 : 60;
    cols = Math.ceil(w / spacing) + 1;
    rows = Math.ceil(h / spacing) + 1;
    nodes = [];
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        nodes.push({
          x: x * spacing,
          y: y * spacing,
          base: 0.10 + Math.random() * 0.06,
          glow: 0,         // 0..1 echo charge
          hue: 0,          // 0 cyan, 1 violet (blended toward source)
          phase: Math.random() * Math.PI * 2
        });
      }
    }
  }

  function spawnWave() {
    const cx = Math.random() * w;
    const cy = Math.random() * h * 0.85 + h * 0.05;
    const violet = Math.random() < 0.4;
    waves.push({
      x: cx, y: cy,
      r: 0,
      speed: 95 + Math.random() * 45, // px/s
      max: Math.max(w, h) * 0.9,
      strength: 1,
      violet
    });
  }

  function lerp(a, b, t) { return a + (b - a) * t; }

  function draw(now) {
    if (!running) return;
    raf = requestAnimationFrame(draw);
    const t = now / 1000;
    const dt = Math.min(0.05, (now - (draw._last || now)) / 1000);
    draw._last = now;

    // periodic echo events
    if (now - lastEvent > 2100) {
      lastEvent = now;
      spawnWave();
      if (Math.random() < 0.35) setTimeout(() => running && spawnWave(), 260);
    }

    ctx.clearRect(0, 0, w, h);

    // advance waves
    for (let i = waves.length - 1; i >= 0; i--) {
      const wv = waves[i];
      wv.r += wv.speed * dt;
      wv.strength = Math.max(0, 1 - wv.r / wv.max);
      if (wv.r > wv.max) waves.splice(i, 1);
    }

    // draw connecting grid lines (faint)
    ctx.lineWidth = 1;
    ctx.strokeStyle = "rgba(255,255,255,0.035)";
    ctx.beginPath();
    for (let y = 0; y < rows; y++) {
      ctx.moveTo(0, y * spacing);
      ctx.lineTo(w, y * spacing);
    }
    for (let x = 0; x < cols; x++) {
      ctx.moveTo(x * spacing, 0);
      ctx.lineTo(x * spacing, h);
    }
    ctx.stroke();

    // update + draw nodes
    for (let n = 0; n < nodes.length; n++) {
      const node = nodes[n];
      // decay glow
      node.glow *= 0.94;

      // wave influence
      for (let i = 0; i < waves.length; i++) {
        const wv = waves[i];
        const d = Math.hypot(node.x - wv.x, node.y - wv.y);
        const ring = Math.abs(d - wv.r);
        if (ring < 26) {
          const intensity = (1 - ring / 26) * wv.strength;
          if (intensity > node.glow) {
            node.glow = intensity;
            node.hue = wv.violet ? 1 : 0;
          }
        }
      }

      const twinkle = 0.5 + 0.5 * Math.sin(t * 1.4 + node.phase);
      const alpha = Math.min(1, node.base * (0.7 + 0.3 * twinkle) + node.glow * 0.95);
      const size = 1.3 + node.glow * 3.4;

      const c1 = COL_CYAN, c2 = COL_VIOLET;
      const r = Math.round(lerp(c1[0], c2[0], node.hue));
      const g = Math.round(lerp(c1[1], c2[1], node.hue));
      const b = Math.round(lerp(c1[2], c2[2], node.hue));

      if (node.glow > 0.12) {
        ctx.shadowBlur = 12 * node.glow;
        ctx.shadowColor = `rgba(${r},${g},${b},${node.glow})`;
      } else {
        ctx.shadowBlur = 0;
      }
      ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
      ctx.beginPath();
      ctx.arc(node.x, node.y, size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.shadowBlur = 0;

    // draw wave ring outlines (subtle)
    for (let i = 0; i < waves.length; i++) {
      const wv = waves[i];
      const col = wv.violet ? COL_VIOLET : COL_CYAN;
      ctx.strokeStyle = `rgba(${col[0]},${col[1]},${col[2]},${0.16 * wv.strength})`;
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.arc(wv.x, wv.y, wv.r, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  function start() { if (!raf) { running = true; raf = requestAnimationFrame(draw); } }
  function stop() { running = false; if (raf) { cancelAnimationFrame(raf); raf = null; } }

  let resizeT;
  window.addEventListener("resize", () => {
    clearTimeout(resizeT);
    resizeT = setTimeout(resize, 150);
  });

  // pause when hero off-screen (perf)
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => (e.isIntersecting ? start() : stop()));
    }, { threshold: 0.01 });
    io.observe(canvas);
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stop(); else start();
  });

  resize();
  // seed a couple of waves so it's alive immediately
  spawnWave();
  setTimeout(spawnWave, 700);
  start();
}

/* ----------------------------------------------------------
   4b. Subtle scroll-driven hero parallax (opacity only, cheap)
       Gated behind reduced-motion (already skipped if true).
   ---------------------------------------------------------- */
function initHeroParallax() {
  const hero = document.getElementById("hero");
  const inner = hero && hero.querySelector(".hero-inner");
  if (!hero || !inner) return;

  const onScroll = () => {
    const scrolled = window.scrollY;
    const heroH = hero.offsetHeight;
    // fade out the inner content slightly as we scroll away — 0→1 as scrolled goes 0→heroH/2
    const t = Math.min(1, scrolled / (heroH * 0.45));
    inner.style.opacity = String(1 - t * 0.35);
    inner.style.transform = "translateY(" + (scrolled * 0.12) + "px)";
  };
  window.addEventListener("scroll", onScroll, { passive: true });
}

/* ----------------------------------------------------------
   5. Motion-powered enhancements (reveal / pipeline / count-up)
      Loaded defensively — content is fully visible without it.

      FAILURE-PROOF GUARANTEES (all paths lead to opacity:1):
      A) CDN blocked / import() rejects  → catch block, content untouched (already visible)
      B) animate/inView not functions    → early return, content untouched
      C) reduceMotion                    → early return before any hide
      D) inView never fires              → global watchdog setTimeout(1200ms) force-shows all
      E) animation never resolves        → per-element watchdog (delay+dur+600ms) commits visible
      F) animate() throws                → try/catch per reveal, commit() called immediately

      CSS rule `.reveal { opacity: 1 }` is the authoritative default.
      We only set inline opacity:0 in the instant before we start the animation
      on that specific element — so any failure path leaves the element at
      the CSS default (fully visible).
   ---------------------------------------------------------- */
async function initMotion(reduceMotion) {
  if (reduceMotion) {
    // Finalize count-up numbers to their target values immediately.
    runCountUp(null);
    return;
  }

  // Global watchdog: after 1200ms, force-show any reveal that is still hidden.
  // This covers the case where inView never fires (element above fold, or IO fails).
  const globalWatchdog = setTimeout(() => {
    document.querySelectorAll(".reveal").forEach((el) => {
      if (el.style.opacity === "0" || el.style.opacity === "") {
        el.style.opacity = "1";
        el.style.transform = "none";
        el.style.willChange = "";
      }
    });
  }, 1200);

  let motion;
  try {
    // Pinned (not @latest): verified to export animate/inView/stagger.
    motion = await import("https://cdn.jsdelivr.net/npm/motion@11.18.0/+esm");
  } catch (e) {
    // CDN failed — content is already visible via CSS default (we have NOT
    // set any inline opacity:0 yet). Just finalize counters and clear watchdog.
    clearTimeout(globalWatchdog);
    runCountUp(null);
    return;
  }

  const { animate, inView, stagger } = motion;
  if (typeof animate !== "function" || typeof inView !== "function") {
    clearTimeout(globalWatchdog);
    runCountUp(null);
    return;
  }

  // CDN loaded successfully — clear the global watchdog now that reveals
  // will be managed per-element with their own guards.
  clearTimeout(globalWatchdog);

  const DUR = 0.48;     // seconds — kept in 150-300ms sweet spot (×2 for longer reveals)
  const RISE = 20;      // px translateY
  const EASE = "ease-out";

  // Failure-proof reveal: hide a target inline ONLY in the instant before we
  // animate it. The final visible state is committed in a microtask-safe
  // finally-equivalent (then + catch) AND a per-element watchdog timeout.
  // Any thrown error or a never-resolving promise still ends at opacity:1.
  function reveal(target, delay) {
    const els = target instanceof Element ? [target] : Array.from(target);
    if (!els.length) return;

    // hide inline right before animating (CSS default stays opacity:1)
    els.forEach((el) => {
      el.style.opacity = "0";
      el.style.transform = "translateY(" + RISE + "px)";
      el.style.willChange = "opacity, transform";
    });

    const commit = () => els.forEach((el) => {
      el.style.opacity = "1";
      el.style.transform = "none";
      el.style.willChange = "";
    });

    // watchdog: if the animation never resolves, show content anyway
    const totalMs = ((delay || 0) + DUR) * 1000 + 600;
    const guard = setTimeout(commit, totalMs);

    try {
      const controls = animate(
        target,
        { opacity: [0, 1], transform: ["translateY(" + RISE + "px)", "translateY(0px)"] },
        { duration: DUR, ease: EASE, delay: delay || 0 }
      );
      const fin = controls && controls.finished;
      if (fin && typeof fin.then === "function") {
        fin.then(() => { clearTimeout(guard); commit(); })
           .catch(() => { clearTimeout(guard); commit(); });
      } else {
        // no promise — commit after expected duration
        setTimeout(() => { clearTimeout(guard); commit(); }, ((delay || 0) + DUR) * 1000 + 40);
      }
    } catch (e) {
      clearTimeout(guard);
      commit();
    }
  }

  // Reveal hero immediately, staggered.
  const heroReveals = document.querySelectorAll(".hero-inner .reveal");
  heroReveals.forEach((el, i) => reveal(el, 0.06 * i));

  // Group the remaining reveals by their nearest meaningful container so a
  // section's children animate in with a small stagger when the group enters
  // view — rather than each block popping independently.
  const seen = new Set(heroReveals);
  const groupSelectors = [
    ".contrast-grid",   // What is / is not panels
    ".pipeline",        // pipeline steps
    ".stats",           // stat tiles (single reveal wrapper, fine)
    ".bento",           // feature cards
    ".chips"            // scenario chips wrapper
  ];

  groupSelectors.forEach((sel) => {
    document.querySelectorAll(sel).forEach((group) => {
      const kids = Array.from(group.querySelectorAll(".reveal"))
        .filter((el) => !seen.has(el));
      if (!kids.length) return;
      kids.forEach((el) => seen.add(el));
      inView(group, () => {
        // Staggered group reveal: each child gets a small incremental delay
        // capped so the last item never waits more than 420ms.
        kids.forEach((el, i) => reveal(el, Math.min(i * 0.08, 0.42)));
      }, { amount: 0.15 });
    });
  });

  // Any leftover reveal (section heads, ethics card, run card, lone wrappers)
  // animates individually as it scrolls in.
  document.querySelectorAll(".reveal").forEach((el) => {
    if (seen.has(el)) return;
    seen.add(el);
    inView(el, () => reveal(el, 0), { amount: 0.18 });
  });

  // Pipeline sequential highlight when in view
  const pipeline = document.querySelector(".pipeline");
  if (pipeline) {
    inView(pipeline, () => {
      const steps = pipeline.querySelectorAll(".pstep");
      steps.forEach((step, idx) => {
        setTimeout(() => {
          steps.forEach((s) => s.classList.remove("is-active"));
          step.classList.add("is-active");
          if (idx === steps.length - 1) {
            setTimeout(() => step.classList.remove("is-active"), 900);
          }
        }, idx * 520);
      });
    }, { amount: 0.4 });
  }

  // Subtle navbar elevation once the page is scrolled past the hero lip.
  initNavScroll();

  // Count-up when stats enter view.
  runCountUp(inView);
}

/* Subtle shadow/elevation change on the floating nav once scrolled. */
function initNavScroll() {
  const nav = document.querySelector(".nav");
  if (!nav) return;
  const onScroll = () => {
    nav.classList.toggle("is-scrolled", window.scrollY > 24);
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
}

/* ----------------------------------------------------------
   6. Count-up stats (cubic-ease-out, finalize to exact value)
   ---------------------------------------------------------- */
function runCountUp(inView) {
  const nums = document.querySelectorAll(".stat-num[data-count]");
  if (!nums.length) return;

  const animateNum = (el) => {
    const target = parseInt(el.dataset.count, 10) || 0;
    const dur = 1200;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min(1, (now - start) / dur);
      // cubic ease-out for a smooth deceleration feel
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased).toLocaleString();
      if (p < 1) requestAnimationFrame(tick);
      else el.textContent = target.toLocaleString();
    };
    requestAnimationFrame(tick);
  };

  if (!inView) {
    // reduced motion / no Motion: show final values directly
    nums.forEach((el) => {
      const target = parseInt(el.dataset.count, 10) || 0;
      el.textContent = target.toLocaleString();
    });
    return;
  }

  nums.forEach((el) => {
    inView(el, () => { animateNum(el); }, { amount: 0.5 });
  });
}

/* ----------------------------------------------------------
   7. Boot
   ---------------------------------------------------------- */
function boot() {
  const reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  initI18n();
  initNav();
  initCopy();
  initHeroCanvas(reduceMotion);
  if (!reduceMotion) initHeroParallax();
  initMotion(reduceMotion);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
