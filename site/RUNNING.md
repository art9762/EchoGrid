# Running & Deploying the EchoGrid Site

How to preview the EchoGrid promo site (`index.html`) and interactive demo
(`demo.html`) locally, and how to deploy them to a static host.

> This site is **static** — plain HTML/CSS/JS, no build step, no backend.
> `main.js` and `demo.js` are native ES modules, so the site **must be served
> over HTTP** (see [Why `file://` does not work](#why-file-does-not-work)).

---

## TL;DR quickstart

```bash
cd /Users/artem/Dev/echogrid/site
python3 -m http.server 8765
```

Then open <http://localhost:8765/> (the demo is at
<http://localhost:8765/demo.html>). Stop the server with `Ctrl+C`.

---

## Why `file://` does not work

`index.html` loads `main.js` and `demo.html` loads `demo.js` as ES modules:

```html
<script src="main.js" type="module"></script>
```

Browsers apply CORS rules to module scripts, and the `file://` scheme is not a
valid CORS origin. Opening the HTML by double-clicking it (a `file://…` URL)
makes the browser **block the module** with an error like:

```
Access to script ... has been blocked by CORS policy:
Cross origin requests are only supported for protocol schemes: http, https, ...
```

With the module blocked, the language toggle is dead, the hero canvas never
animates, and the demo Run button does nothing. **Always serve over HTTP.**

---

## Local preview

Any of these work — none requires installing project dependencies.

### Option 1 — Python (no install, ships with macOS/Linux)

```bash
cd /Users/artem/Dev/echogrid/site
python3 -m http.server 8765      # any free port
# → http://localhost:8765/
```

### Option 2 — `npx serve` (needs Node, no project install)

```bash
cd /Users/artem/Dev/echogrid/site
npx serve .                      # prints the URL it picks, e.g. :3000
```

### Option 3 — VS Code Live Server

Install the **Live Server** extension, open the `site/` folder, then right-click
`index.html` → **Open with Live Server**. It serves over HTTP and live-reloads
on save.

---

## Deploying to a static host

The whole site is the contents of `site/`. Upload those files to any static
host and point the host at `index.html` as the entry document.

### Generic nginx (static root)

Copy the `site/` contents into the server root, then:

```nginx
server {
    listen 80;
    server_name echogrid.example.com;

    root /var/www/echogrid;   # contains index.html, demo.html, *.css, *.js
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

No special MIME config is needed — `.js` is already served as JavaScript by
nginx's default `mime.types`, which satisfies the ES-module requirement.

### GitHub Pages

The repo is public (`art9762/EchoGrid`) and the site lives in the **`/site`
subfolder**, not the repo root. GitHub Pages can only publish from one of two
fixed locations per branch: the repo **root (`/`)** or a **`/docs`** folder.
It cannot point directly at an arbitrary `/site` subfolder.

Pick the simplest path that fits the repo:

**A. Publish via GitHub Actions (keeps `site/` where it is — recommended).**
In the repo, go to **Settings → Pages → Build and deployment → Source:
GitHub Actions**, then add a workflow that uploads `site/` as the Pages
artifact. The key step is pointing the upload at the subfolder:

```yaml
# .github/workflows/pages.yml
name: Deploy site to Pages
on:
  push:
    branches: [main]
permissions:
  pages: write
  id-token: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site            # publish only the site/ folder
      - id: deployment
        uses: actions/deploy-pages@v4
```

**B. Move the site to `/docs`.** Rename `site/` to `docs/`, then set
**Settings → Pages → Source: Deploy from a branch → `main` / `/docs`**.
Simplest if you don't mind the folder name change.

**C. Publish the repo root.** Move the `site/` files to the repo root and set
**Source: `main` / `/ (root)`**. Only do this if the repo has nothing else at
the root you'd be exposing.

Whichever path you choose, the published URL is
`https://art9762.github.io/EchoGrid/` and the demo is at
`https://art9762.github.io/EchoGrid/demo.html`. All asset links in the HTML are
**relative** (`styles.css`, `main.js`, `demo.html`), so they work correctly
under a project-pages subpath — no base-href change required.

---

## External runtime dependency (one, optional)

| Page | Network needed? | What for |
|------|-----------------|----------|
| **Landing** (`index.html`) | Optional | `main.js` fetches `motion@11.18.0` from the jsDelivr CDN at runtime for the scroll-reveal animations. |
| **Demo** (`demo.html`) | **None** | `demo.js` is fully vanilla — zero CDN dependencies. Runs entirely offline once loaded. |

The landing **degrades gracefully** if the CDN is blocked or offline: `main.js`
wraps the `import()` in a `try/catch`, and the reveal logic only ever hides an
element *just before* animating it (with a watchdog `setTimeout` that force-shows
content if the animation never resolves). If Motion fails to load, every section
simply appears at full opacity with no animation. Counters still finalize to
their target values.

> Both pages also load **Google Fonts** (Exo + Roboto Mono) via a CSS `@import`
> in `styles.css`. If fonts are blocked, the browser falls back to
> `system-ui` / `ui-monospace` — layout is unaffected.

---

## Smoke-test checklist

After serving over HTTP, verify:

- [ ] **Language toggle** — click `RU`, all text swaps to Russian; reload the
      page and it stays Russian (persisted in `localStorage["echogrid-lang"]`,
      shared by landing and demo).
- [ ] **Nav anchors** — `What` / `How` / `Features` / `Ethics` scroll smoothly
      to their sections; `Demo` opens `demo.html`.
- [ ] **Scroll reveals** — every section below the hero becomes visible as you
      scroll (and stays visible even with the CDN blocked / DevTools offline).
- [ ] **Demo Run** — on `demo.html`, type an event or pick a scenario chip,
      press **Run simulation**: the echo-cascade canvas animates, and the
      results dashboard shows stance bars, before→after metric cards
      (Amplification / Trust / Anger / Distortion / Polarization), and
      synthetic comments tagged "synthetic — not real opinions".
- [ ] **Determinism** — re-running the *same* event + population + rounds
      produces *identical* results (seeded PRNG).
- [ ] **Mobile (375px width)** — no horizontal scroll; the hamburger nav opens.

---

See [README.md](README.md) for the file map, design system, i18n internals, and
how the demo mock works.
