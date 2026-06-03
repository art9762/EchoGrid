/* ============================================================
   EchoGrid — interactive demo logic (ES module, vanilla rAF)
   - i18n (EN/RU), SAME localStorage key as the landing
   - deterministic client-side mock simulation (seeded PRNG)
   - echo-cascade canvas animation (mirrors the hero canvas)
   - results dashboard: animated stance bars, before→after
     metric cards with count-up, synthetic comment templates
   - all motion gated behind prefers-reduced-motion; results are
     always rendered visible first, animation only enhances.
   No external dependencies. Served over HTTP (won't run on file://).
   ============================================================ */

const REDUCE_MOTION =
  window.matchMedia &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ----------------------------------------------------------
   1. i18n dictionary (demo-specific; landing nav/footer keys
      are also included so the shared navbar + footer translate).
   ---------------------------------------------------------- */
const demoI18n = {
  en: {
    "skip": "Skip to content",
    "nav.what": "What", "nav.how": "How", "nav.features": "Features",
    "nav.ethics": "Ethics", "nav.demo": "Demo", "nav.github": "GitHub",

    "demo.kicker": "Interactive demo",
    "demo.title": "Run a synthetic echo simulation",
    "demo.disclaimer": "Everything below is synthetic — generated in your browser from a deterministic mock model. Not a poll, not a prediction, not real opinions.",

    "demo.setup.title": "Configure your run",
    "demo.setup.eventLabel": "Public event",
    "demo.setup.eventPlaceholder": "Enter a public event…",
    "demo.setup.chipsLabel": "Or pick a built-in scenario:",
    "demo.setup.popLabel": "Population size",
    "demo.setup.roundsLabel": "Echo rounds",
    "demo.setup.run": "Run simulation",
    "demo.setup.running": "Simulating…",

    "demo.stage.kicker": "Echo cascade",
    "demo.stage.idle": "Configure a run and press play.",
    "demo.stage.placeholder": "The synthetic echo grid appears here on run.",
    "demo.stage.seeding": "Seeding synthetic population…",
    "demo.stage.round": "Echo round {n} of {total} rippling…",
    "demo.stage.done": "Cascade settled · {n} agents.",

    "demo.results.title": "Simulation results",
    "demo.results.tag": "Synthetic — not real opinions",
    "demo.results.stanceTitle": "Stance distribution (after echo)",
    "demo.results.metricsTitle": "Before → after metrics",
    "demo.results.commentsTitle": "Representative synthetic reactions",
    "demo.results.sub": "{event} · {pop} synthetic agents · {rounds} echo rounds · deterministic mock",
    "demo.results.live": "Simulation complete.",

    "demo.stance.ss": "Strongly support",
    "demo.stance.s": "Support",
    "demo.stance.n": "Neutral",
    "demo.stance.o": "Oppose",
    "demo.stance.so": "Strongly oppose",

    "demo.metric.amplification": "Amplification",
    "demo.metric.trust": "Trust",
    "demo.metric.anger": "Anger",
    "demo.metric.distortion": "Distortion",
    "demo.metric.polarization": "Polarization",

    "demo.comment.synthetic": "synthetic agent",
    "demo.cstance.support": "Support",
    "demo.cstance.neutral": "Neutral",
    "demo.cstance.oppose": "Oppose",

    "footer.disclaimer": "All EchoGrid results are synthetic simulation outputs — not measurements of real public opinion.",
    "footer.docs": "Docs",
    "footer.license": "MIT License"
  },
  ru: {
    "skip": "Перейти к содержимому",
    "nav.what": "Что это", "nav.how": "Как работает", "nav.features": "Возможности",
    "nav.ethics": "Этика", "nav.demo": "Демо", "nav.github": "GitHub",

    "demo.kicker": "Интерактивное демо",
    "demo.title": "Запустите симуляцию синтетического эха",
    "demo.disclaimer": "Всё ниже — синтетика, сгенерированная в вашем браузере детерминированной mock-моделью. Не опрос, не прогноз и не реальные мнения.",

    "demo.setup.title": "Настройте прогон",
    "demo.setup.eventLabel": "Публичное событие",
    "demo.setup.eventPlaceholder": "Введите публичное событие…",
    "demo.setup.chipsLabel": "Или выберите встроенный сценарий:",
    "demo.setup.popLabel": "Размер населения",
    "demo.setup.roundsLabel": "Раунды эха",
    "demo.setup.run": "Запустить симуляцию",
    "demo.setup.running": "Симуляция…",

    "demo.stage.kicker": "Каскад эха",
    "demo.stage.idle": "Настройте прогон и нажмите запуск.",
    "demo.stage.placeholder": "Синтетическая эхо-сетка появится здесь при запуске.",
    "demo.stage.seeding": "Создаётся синтетическое население…",
    "demo.stage.round": "Раунд эха {n} из {total} расходится волной…",
    "demo.stage.done": "Каскад устоялся · {n} агентов.",

    "demo.results.title": "Результаты симуляции",
    "demo.results.tag": "Синтетика — не реальные мнения",
    "demo.results.stanceTitle": "Распределение позиций (после эха)",
    "demo.results.metricsTitle": "Метрики «до → после»",
    "demo.results.commentsTitle": "Репрезентативные синтетические реакции",
    "demo.results.sub": "{event} · {pop} синтетических агентов · раундов эха: {rounds} · детерминированный mock",
    "demo.results.live": "Симуляция завершена.",

    "demo.stance.ss": "Решительно за",
    "demo.stance.s": "За",
    "demo.stance.n": "Нейтрально",
    "demo.stance.o": "Против",
    "demo.stance.so": "Решительно против",

    "demo.metric.amplification": "Усиление",
    "demo.metric.trust": "Доверие",
    "demo.metric.anger": "Гнев",
    "demo.metric.distortion": "Искажение",
    "demo.metric.polarization": "Поляризация",

    "demo.comment.synthetic": "синтетический агент",
    "demo.cstance.support": "За",
    "demo.cstance.neutral": "Нейтрально",
    "demo.cstance.oppose": "Против",

    "footer.disclaimer": "Все результаты EchoGrid — синтетические выходные данные симуляции, а не измерения реального общественного мнения.",
    "footer.docs": "Документация",
    "footer.license": "Лицензия MIT"
  }
};

const SCENARIO_KEYS = {
  1: "scen.1", 2: "scen.2", 3: "scen.3", 4: "scen.4",
  5: "scen.5", 6: "scen.6", 7: "scen.7"
};
const SCENARIOS = {
  en: {
    "scen.1": "Emissions-based car tax",
    "scen.2": "AI surveillance in public spaces",
    "scen.3": "Four-day work week proposal",
    "scen.4": "Mandatory digital ID",
    "scen.5": "Housing policy reform",
    "scen.6": "University bans phones in classrooms",
    "scen.7": "City restricts short-term rentals"
  },
  ru: {
    "scen.1": "Налог на авто по выбросам",
    "scen.2": "ИИ-слежка в общественных местах",
    "scen.3": "Четырёхдневная рабочая неделя",
    "scen.4": "Обязательный цифровой ID",
    "scen.5": "Реформа жилищной политики",
    "scen.6": "Запрет телефонов в аудиториях вуза",
    "scen.7": "Ограничение краткосрочной аренды в городе"
  }
};

const LANG_KEY = "echogrid-lang";
let currentLang = "en";

function t(key, vars) {
  const dict = demoI18n[currentLang] || demoI18n.en;
  const scen = SCENARIOS[currentLang] || SCENARIOS.en;
  let s = dict[key] != null ? dict[key] : (scen[key] != null ? scen[key] : key);
  if (vars) for (const k in vars) s = s.replace("{" + k + "}", vars[k]);
  return s;
}

function setLang(lang) {
  if (!demoI18n[lang]) lang = "en";
  currentLang = lang;
  const dict = demoI18n[lang];
  const scen = SCENARIOS[lang];

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key] != null) el.textContent = dict[key];
    else if (scen[key] != null) el.textContent = scen[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (dict[key] != null) el.setAttribute("placeholder", dict[key]);
  });

  document.documentElement.lang = lang;
  try { localStorage.setItem(LANG_KEY, lang); } catch (e) {}

  document.querySelectorAll(".lang-btn").forEach((btn) => {
    const active = btn.dataset.lang === lang;
    btn.classList.toggle("is-active", active);
    btn.setAttribute("aria-pressed", String(active));
  });

  // Re-render dynamic result text (bars/metrics/comments) in the new language.
  if (lastResult) renderResults(lastResult, true);
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
   2. Mobile nav toggle (mirrors landing)
   ---------------------------------------------------------- */
function initNav() {
  const toggle = document.querySelector(".nav-toggle");
  const links = document.getElementById("nav-links");
  if (!toggle || !links) return;
  toggle.addEventListener("click", () => {
    const open = links.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  links.querySelectorAll("a").forEach((a) => {
    a.addEventListener("click", () => {
      links.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

/* ----------------------------------------------------------
   3. Deterministic PRNG — seeded from the event string so the
      same event re-runs identically. (xmur3 hash + mulberry32)
   ---------------------------------------------------------- */
function xmur3(str) {
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return function () {
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return h >>> 0;
  };
}
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let tt = Math.imul(a ^ (a >>> 15), 1 | a);
    tt = (tt + Math.imul(tt ^ (tt >>> 7), 61 | tt)) ^ tt;
    return ((tt ^ (tt >>> 14)) >>> 0) / 4294967296;
  };
}

/* ----------------------------------------------------------
   4. Mock reaction model — the real EchoGrid media FRAMES.
   ---------------------------------------------------------- */
const FRAME_EFFECTS = {
  neutral:          { support: 0,   anger: -6,  trust: 8 },
  technocratic:     { support: 5,   anger: -10, trust: 6 },
  progressive:      { support: 8,   anger: 2,   trust: 0 },
  populist:         { support: -8,  anger: 13,  trust: -8 },
  skeptical:        { support: -6,  anger: 6,   trust: -7 },
  tabloid_outrage:  { support: -12, anger: 22,  trust: -18 }
};
const FRAMES = Object.keys(FRAME_EFFECTS);
const STANCE_ORDER = ["ss", "s", "n", "o", "so"];

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

/* Build a synthetic population + run the framing & echo cascade.
   Lightweight: we aggregate as we go and never store per-agent DOM. */
function simulate(event, population, rounds) {
  const seedFn = xmur3(event + "::" + population + "::" + rounds);
  const rng = mulberry32(seedFn());

  // Each agent gets a media diet weighting over the 6 frames, plus a
  // baseline support/anger/trust. Frame mix is event-seeded so different
  // events tilt the ecosystem differently (authentic to the real model).
  const frameTilt = FRAMES.map(() => 0.5 + rng() * 0.9);

  let supBefore = 0, angBefore = 0, truBefore = 0;
  let supAfter = 0, angAfter = 0, truAfter = 0;
  const stanceAfter = { ss: 0, s: 0, n: 0, o: 0, so: 0 };
  const sample = []; // a few representative agents for comment templates

  for (let i = 0; i < population; i++) {
    // baseline disposition (centred, mild spread)
    let support = (rng() - 0.5) * 30;
    let anger = 18 + rng() * 22;
    let trust = 52 + (rng() - 0.5) * 26;
    supBefore += support; angBefore += anger; truBefore += trust;

    // pick the frame this agent mostly consumes (weighted by event tilt)
    let wsum = 0;
    const w = frameTilt.map((ft) => { const x = ft * (0.4 + rng()); wsum += x; return x; });
    let pick = rng() * wsum, fi = 0;
    for (; fi < w.length; fi++) { pick -= w[fi]; if (pick <= 0) break; }
    const frame = FRAMES[Math.min(fi, FRAMES.length - 1)];
    const fx = FRAME_EFFECTS[frame];

    // initial reaction to the framing (per-agent seeded jitter)
    support += fx.support * (0.7 + rng() * 0.6);
    anger += fx.anger * (0.7 + rng() * 0.6);
    trust += fx.trust * (0.7 + rng() * 0.6);

    // echo cascade: each round nudges the agent further along its lean,
    // with diminishing per-round strength (bounded propagation in bubbles).
    for (let r = 0; r < rounds; r++) {
      const decay = 1 - r * 0.28;
      const lean = support >= 0 ? 1 : -1;
      support += lean * (2.4 + rng() * 3.0) * decay;
      anger += Math.abs(fx.anger) * 0.18 * (0.5 + rng()) * decay;
      trust -= Math.abs(fx.trust) * 0.10 * (0.5 + rng()) * decay;
    }

    support = clamp(support, -100, 100);
    anger = clamp(anger, 0, 100);
    trust = clamp(trust, 0, 100);
    supAfter += support; angAfter += anger; truAfter += trust;

    // bucket into a 5-point stance scale
    let st;
    if (support >= 35) st = "ss";
    else if (support >= 10) st = "s";
    else if (support > -10) st = "n";
    else if (support > -35) st = "o";
    else st = "so";
    stanceAfter[st]++;

    if (sample.length < 24) sample.push({ frame, stance: st, support, anger, trust, r: rng() });
  }

  const n = population;
  const avg = (x) => x / n;

  // before vs after aggregate metrics (0..100-ish scales)
  const trustB = avg(truBefore), trustA = avg(truAfter);
  const angerB = avg(angBefore), angerA = avg(angAfter);

  // amplification = how much echo widened opinion spread vs baseline
  const ampBefore = 100;
  const spread = Math.sqrt(
    STANCE_ORDER.reduce((s, k, idx) => {
      const c = stanceAfter[k] / n;
      return s + c * Math.pow(idx - 2, 2);
    }, 0)
  );
  const ampAfter = Math.round(100 * (1 + spread * (0.35 + rounds * 0.18)));

  // distortion = drift of the framed signal from neutral baseline
  const distBefore = Math.round(10 + (truBefore ? 0 : 0));
  const distAfter = Math.round(
    clamp(12 + spread * 22 + rounds * 6 + (angerA - angerB) * 0.4, 5, 95)
  );

  // polarization = mass at the two extremes
  const polBefore = Math.round(8 + spread * 4);
  const polAfter = Math.round(
    clamp(((stanceAfter.ss + stanceAfter.so) / n) * 100 + rounds * 2, 0, 100)
  );

  const metrics = {
    amplification: { before: ampBefore, after: ampAfter, dir: "up-bad", unit: "%" },
    trust:         { before: Math.round(trustB), after: Math.round(trustA), dir: "up-good", unit: "" },
    anger:         { before: Math.round(angerB), after: Math.round(angerA), dir: "up-bad", unit: "" },
    distortion:    { before: distBefore || 10, after: distAfter, dir: "up-bad", unit: "" },
    polarization:  { before: polBefore, after: polAfter, dir: "up-bad", unit: "" }
  };

  return { event, population, rounds, stance: stanceAfter, metrics, sample };
}

/* ----------------------------------------------------------
   5. Echo-cascade canvas (mirrors the hero canvas aesthetic).
      Driven explicitly per run: emits `rounds` ripple waves.
   ---------------------------------------------------------- */
const COL_CYAN = [56, 189, 248];
const COL_VIOLET = [139, 92, 246];

function createCascade(canvas) {
  const ctx = canvas.getContext("2d");
  let w = 0, h = 0, dpr = 1, spacing = 0, cols = 0, rows = 0;
  let nodes = [];
  let waves = [];
  let raf = null, running = false, idleT = 0;

  function resize() {
    w = canvas.clientWidth; h = canvas.clientHeight;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.floor(w * dpr));
    canvas.height = Math.max(1, Math.floor(h * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    build();
  }
  function build() {
    spacing = w < 520 ? 30 : 38;
    cols = Math.ceil(w / spacing) + 1;
    rows = Math.ceil(h / spacing) + 1;
    nodes = [];
    for (let y = 0; y < rows; y++)
      for (let x = 0; x < cols; x++)
        nodes.push({ x: x * spacing, y: y * spacing, base: 0.08 + Math.random() * 0.05, glow: 0, hue: 0, phase: Math.random() * Math.PI * 2 });
  }
  function spawnWave(violet) {
    waves.push({
      x: w * (0.42 + Math.random() * 0.16),
      y: h * (0.40 + Math.random() * 0.20),
      r: 0, speed: 150 + Math.random() * 60,
      max: Math.hypot(w, h) * 1.05, strength: 1, violet
    });
  }
  const lerp = (a, b, t) => a + (b - a) * t;

  function draw(now) {
    if (!running) return;
    raf = requestAnimationFrame(draw);
    const dt = Math.min(0.05, (now - (draw._last || now)) / 1000);
    draw._last = now;
    const time = now / 1000;

    ctx.clearRect(0, 0, w, h);

    for (let i = waves.length - 1; i >= 0; i--) {
      const wv = waves[i];
      wv.r += wv.speed * dt;
      wv.strength = Math.max(0, 1 - wv.r / wv.max);
      if (wv.r > wv.max) waves.splice(i, 1);
    }

    // faint grid lines
    ctx.lineWidth = 1;
    ctx.strokeStyle = "rgba(255,255,255,0.03)";
    ctx.beginPath();
    for (let y = 0; y < rows; y++) { ctx.moveTo(0, y * spacing); ctx.lineTo(w, y * spacing); }
    for (let x = 0; x < cols; x++) { ctx.moveTo(x * spacing, 0); ctx.lineTo(x * spacing, h); }
    ctx.stroke();

    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      node.glow *= 0.945;
      for (let j = 0; j < waves.length; j++) {
        const wv = waves[j];
        const ring = Math.abs(Math.hypot(node.x - wv.x, node.y - wv.y) - wv.r);
        if (ring < 22) {
          const intensity = (1 - ring / 22) * wv.strength;
          if (intensity > node.glow) { node.glow = intensity; node.hue = wv.violet ? 1 : 0; }
        }
      }
      const twinkle = 0.5 + 0.5 * Math.sin(time * 1.4 + node.phase);
      const alpha = Math.min(1, node.base * (0.7 + 0.3 * twinkle) + node.glow * 0.95);
      const size = 1.1 + node.glow * 3.2;
      const r = Math.round(lerp(COL_CYAN[0], COL_VIOLET[0], node.hue));
      const g = Math.round(lerp(COL_CYAN[1], COL_VIOLET[1], node.hue));
      const b = Math.round(lerp(COL_CYAN[2], COL_VIOLET[2], node.hue));
      if (node.glow > 0.12) { ctx.shadowBlur = 11 * node.glow; ctx.shadowColor = `rgba(${r},${g},${b},${node.glow})`; }
      else ctx.shadowBlur = 0;
      ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
      ctx.beginPath();
      ctx.arc(node.x, node.y, size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.shadowBlur = 0;

    for (let j = 0; j < waves.length; j++) {
      const wv = waves[j];
      const col = wv.violet ? COL_VIOLET : COL_CYAN;
      ctx.strokeStyle = `rgba(${col[0]},${col[1]},${col[2]},${0.18 * wv.strength})`;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(wv.x, wv.y, wv.r, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  function start() { if (!raf && !REDUCE_MOTION) { running = true; raf = requestAnimationFrame(draw); } }
  function stop() { running = false; if (raf) { cancelAnimationFrame(raf); raf = null; } }

  // gentle ambient pulse so the idle grid feels alive
  function idle() {
    clearInterval(idleT);
    idleT = setInterval(() => { if (running && waves.length === 0) spawnWave(Math.random() < 0.4); }, 2600);
  }

  let resizeT;
  window.addEventListener("resize", () => { clearTimeout(resizeT); resizeT = setTimeout(resize, 150); });
  if ("IntersectionObserver" in window) {
    new IntersectionObserver((es) => es.forEach((e) => (e.isIntersecting ? start() : stop())), { threshold: 0.01 }).observe(canvas);
  }
  document.addEventListener("visibilitychange", () => { if (document.hidden) stop(); else start(); });

  resize();
  return {
    start, stop, resize,
    ambient() { idle(); spawnWave(false); start(); },
    /* Emit ripples for each echo round, resolving when the cascade settles.
       Returns a promise so we can sequence the status text + results reveal. */
    runCascade(rounds, onRound) {
      return new Promise((resolve) => {
        if (REDUCE_MOTION) { resolve(); return; }
        start();
        waves = [];
        let round = 0;
        const fire = () => {
          round++;
          if (onRound) onRound(round);
          spawnWave(false);
          setTimeout(() => spawnWave(true), 180);
          if (round < rounds) setTimeout(fire, 900);
          else setTimeout(resolve, 1100);
        };
        fire();
      });
    }
  };
}

/* ----------------------------------------------------------
   6. Count-up helper (vanilla rAF; instant when reduced motion)
   ---------------------------------------------------------- */
function countUp(el, target, suffix) {
  suffix = suffix || "";
  if (REDUCE_MOTION) { el.textContent = target.toLocaleString() + suffix; return; }
  const start = performance.now(), dur = 900;
  const tick = (now) => {
    const p = Math.min(1, (now - start) / dur);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(target * eased).toLocaleString() + suffix;
    if (p < 1) requestAnimationFrame(tick);
    else el.textContent = target.toLocaleString() + suffix;
  };
  requestAnimationFrame(tick);
}

/* ----------------------------------------------------------
   7. Render results dashboard (bars, metric cards, comments).
      `quiet` = re-render after a language switch (no count-up).
   ---------------------------------------------------------- */
let lastResult = null;

// metric direction → delta colour class. "up-good": rising is green.
function deltaClass(dir, delta) {
  if (delta === 0) return "is-flat";
  const rising = delta > 0;
  if (dir === "up-good") return rising ? "is-up" : "is-down";
  return rising ? "is-down" : "is-up"; // up-bad: rising is red
}

// mild, obviously-synthetic comment templates per stance group
const COMMENT_TEMPLATES = {
  en: {
    support: [
      "Reads this as a reasonable step; mostly fine with the direction.",
      "Cautiously in favour after seeing the coverage on it.",
      "Thinks the upside outweighs the downside here."
    ],
    neutral: [
      "Undecided — wants to see more detail before forming a view.",
      "Neither here nor there; waiting for the specifics.",
      "Notes some pros and cons and leans on neither side yet."
    ],
    oppose: [
      "Has reservations and would prefer a slower rollout.",
      "Not convinced; worries about the practical trade-offs.",
      "Leans against it but in a measured, low-key way."
    ]
  },
  ru: {
    support: [
      "Считает это разумным шагом; в целом согласен с направлением.",
      "Осторожно поддерживает после знакомства с освещением темы.",
      "Полагает, что плюсы здесь перевешивают минусы."
    ],
    neutral: [
      "Не определился — хочет больше деталей, прежде чем решать.",
      "Ни туда ни сюда; ждёт конкретики.",
      "Видит и плюсы, и минусы и пока ни на чьей стороне."
    ],
    oppose: [
      "Есть оговорки; предпочёл бы более плавное внедрение.",
      "Не убеждён; беспокоится о практических компромиссах.",
      "Скорее против, но сдержанно и без резкости."
    ]
  }
};

function stanceGroup(st) {
  if (st === "ss" || st === "s") return "support";
  if (st === "n") return "neutral";
  return "oppose";
}

function renderResults(res, quiet) {
  lastResult = res;
  const eventLabel = res.eventLabel || res.event;

  // sub-line
  const sub = document.getElementById("demo-results-sub");
  if (sub) sub.textContent = t("demo.results.sub", { event: eventLabel, pop: res.population.toLocaleString(), rounds: res.rounds });

  // --- stance bars ---
  const barsEl = document.getElementById("demo-bars");
  barsEl.innerHTML = "";
  const maxCount = Math.max(1, ...STANCE_ORDER.map((k) => res.stance[k]));
  STANCE_ORDER.forEach((st) => {
    const count = res.stance[st];
    const pct = Math.round((count / res.population) * 100);
    const row = document.createElement("div");
    row.className = "demo-bar-row";
    row.dataset.stance = st;
    row.innerHTML =
      `<span class="demo-bar-label">${t("demo.stance." + st)}</span>` +
      `<span class="demo-bar-track"><span class="demo-bar-fill"></span></span>` +
      `<span class="demo-bar-count"><span class="demo-bar-n">0</span> <span class="demo-bar-pct">(${pct}%)</span></span>`;
    barsEl.appendChild(row);
    const fill = row.querySelector(".demo-bar-fill");
    const nEl = row.querySelector(".demo-bar-n");
    const widthPct = (count / maxCount) * 100;
    if (quiet || REDUCE_MOTION) {
      fill.style.width = widthPct + "%";
      nEl.textContent = count.toLocaleString();
    } else {
      requestAnimationFrame(() => { fill.style.width = widthPct + "%"; });
      countUp(nEl, count, "");
    }
  });

  // --- metric cards ---
  const metricsEl = document.getElementById("demo-metrics");
  metricsEl.innerHTML = "";
  Object.keys(res.metrics).forEach((key) => {
    const m = res.metrics[key];
    const delta = m.after - m.before;
    const dcls = deltaClass(m.dir, delta);
    const arrow = delta > 0 ? "▲" : delta < 0 ? "▼" : "—";
    const sign = delta > 0 ? "+" : "";
    const card = document.createElement("div");
    card.className = "demo-metric";
    card.innerHTML =
      `<div class="demo-metric-name">${t("demo.metric." + key)}</div>` +
      `<div class="demo-metric-row">` +
        `<span class="demo-metric-before">${m.before}${m.unit}</span>` +
        `<span class="demo-metric-arrow">→</span>` +
        `<span class="demo-metric-after">0${m.unit}</span>` +
      `</div>` +
      `<div class="demo-metric-delta ${dcls}">${arrow} ${sign}${delta}${m.unit}</div>`;
    metricsEl.appendChild(card);
    const afterEl = card.querySelector(".demo-metric-after");
    if (quiet || REDUCE_MOTION) afterEl.textContent = m.after + m.unit;
    else countUp(afterEl, m.after, m.unit);
  });

  // --- representative synthetic comments ---
  const commentsEl = document.getElementById("demo-comments");
  commentsEl.innerHTML = "";
  const tpl = COMMENT_TEMPLATES[currentLang] || COMMENT_TEMPLATES.en;
  // pick 3 representative agents spanning the stance spectrum
  const picks = pickRepresentatives(res.sample);
  picks.forEach((a, i) => {
    const grp = stanceGroup(a.stance);
    const variants = tpl[grp];
    const text = variants[Math.floor(a.r * variants.length) % variants.length];
    const stCls = grp === "support" ? "is-support" : grp === "neutral" ? "is-neutral" : "is-oppose";
    const stLabel = t("demo.cstance." + (grp === "support" ? "support" : grp === "neutral" ? "neutral" : "oppose"));
    const li = document.createElement("li");
    li.className = "demo-comment";
    li.innerHTML =
      `<div class="demo-comment-head">` +
        `<span class="demo-comment-avatar" aria-hidden="true">A${i + 1}</span>` +
        `<span class="demo-comment-meta">${t("demo.comment.synthetic")} · ${a.frame.replace(/_/g, " ")}</span>` +
        `<span class="demo-comment-stance ${stCls}">${stLabel}</span>` +
      `</div>` +
      `<p class="demo-comment-body">${text}</p>`;
    commentsEl.appendChild(li);
  });
}

// choose up to 3 agents covering support / neutral / oppose if available
function pickRepresentatives(sample) {
  const byGroup = { support: [], neutral: [], oppose: [] };
  sample.forEach((a) => byGroup[stanceGroup(a.stance)].push(a));
  const out = [];
  ["support", "neutral", "oppose"].forEach((g) => { if (byGroup[g][0]) out.push(byGroup[g][0]); });
  let idx = 0;
  while (out.length < 3 && idx < sample.length) {
    if (!out.includes(sample[idx])) out.push(sample[idx]);
    idx++;
  }
  return out.slice(0, 3);
}

/* ----------------------------------------------------------
   8. Wiring: chips, sliders, run handler
   ---------------------------------------------------------- */
function initControls(cascade) {
  const form = document.getElementById("demo-form");
  const input = document.getElementById("demo-event");
  const chips = Array.from(document.querySelectorAll(".demo-chip"));
  const popRange = document.getElementById("demo-pop");
  const popVal = document.getElementById("demo-pop-val");
  const roundsRange = document.getElementById("demo-rounds");
  const roundsVal = document.getElementById("demo-rounds-val");
  const runBtn = document.getElementById("demo-run");
  const runLabel = runBtn.querySelector("span");
  const statusEl = document.getElementById("demo-status");
  const results = document.getElementById("demo-results");
  const live = document.getElementById("demo-live");
  const wrap = document.querySelector(".demo-canvas-wrap");

  let selectedScenario = null;

  const syncSliders = () => {
    popVal.textContent = popRange.value;
    roundsVal.textContent = roundsRange.value;
  };
  popRange.addEventListener("input", syncSliders);
  roundsRange.addEventListener("input", syncSliders);
  syncSliders();

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const id = chip.dataset.scenario;
      selectedScenario = id;
      chips.forEach((c) => c.classList.toggle("is-selected", c === chip));
      // mirror scenario text into the input (translated label)
      input.value = t(SCENARIO_KEYS[id]);
    });
  });
  // typing a custom event clears the scenario selection
  input.addEventListener("input", () => {
    selectedScenario = null;
    chips.forEach((c) => c.classList.remove("is-selected"));
  });

  let busy = false;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (busy) return;

    // resolve the event: scenario key (stable seed) or custom text
    const raw = input.value.trim();
    let seedEvent, eventLabel;
    if (selectedScenario) {
      seedEvent = "scenario:" + selectedScenario;          // language-stable seed
      eventLabel = t(SCENARIO_KEYS[selectedScenario]);
    } else if (raw) {
      seedEvent = "custom:" + raw.toLowerCase();
      eventLabel = raw;
    } else {
      // default to scenario 1 if nothing entered
      selectedScenario = "1";
      chips[0].classList.add("is-selected");
      input.value = t(SCENARIO_KEYS["1"]);
      seedEvent = "scenario:1";
      eventLabel = t(SCENARIO_KEYS["1"]);
    }

    const population = parseInt(popRange.value, 10);
    const rounds = parseInt(roundsRange.value, 10);

    busy = true;
    runBtn.disabled = true;
    runLabel.textContent = t("demo.setup.running");
    wrap.classList.add("is-active");
    statusEl.textContent = t("demo.stage.seeding");

    // compute synthetically (sync but fast; yield a frame so UI updates first)
    await new Promise((r) => requestAnimationFrame(() => r()));
    const res = simulate(seedEvent, population, rounds);
    res.eventLabel = eventLabel;

    // Render results VISIBLE first (never hide-then-fail), then animate cascade.
    results.hidden = false;

    await cascade.runCascade(rounds, (n) => {
      statusEl.textContent = t("demo.stage.round", { n, total: rounds });
    });

    statusEl.textContent = t("demo.stage.done", { n: population.toLocaleString() });
    renderResults(res, false);
    live.textContent = t("demo.results.live");

    busy = false;
    runBtn.disabled = false;
    runLabel.textContent = t("demo.setup.run");
  });
}

/* ----------------------------------------------------------
   9. Hero-lite background canvas (ambient, like landing hero)
   ---------------------------------------------------------- */
function initHeroLite() {
  const canvas = document.getElementById("demo-hero-canvas");
  if (!canvas || REDUCE_MOTION) return; // CSS fallback shows static grid
  const hero = createCascade(canvas);
  hero.ambient();
}

/* ----------------------------------------------------------
   10. Boot
   ---------------------------------------------------------- */
function boot() {
  initI18n();
  initNav();
  initHeroLite();

  const cascadeCanvas = document.getElementById("demo-cascade");
  const cascade = createCascade(cascadeCanvas);
  if (!REDUCE_MOTION) cascade.start(); // idle grid visible (no waves until run)
  initControls(cascade);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
