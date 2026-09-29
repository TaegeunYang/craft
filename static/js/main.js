/* Same Scene, Different Task — page interactions (no dependencies). */
(function () {
  "use strict";

  // ---------------------------------------------------------------
  // Data: CRAFT success (%) per undemonstrated combination
  // (paper Figures D.1 and D.2; mean over three evaluation seeds).
  // null marks a demonstrated combination.
  // ---------------------------------------------------------------
  const COLORS = ["red", "blue", "green", "yellow"];
  const MODELS = { pi05: "π0.5", pi0: "π0", gr00t: "GR00T N1.7" };
  function modelLabel(m) {
    const f = document.createDocumentFragment();
    if (m === "gr00t") { f.append("GR00T N1.7"); return f; }
    const sub = document.createElement("sub");
    sub.textContent = m === "pi05" ? "0.5" : "0";
    f.append("π", sub);
    return f;
  }

  // Pick-Place: [cube][plate], order red, blue, green, yellow
  const PP = {
    pi05:  [[null, 89.3, 90.7, 86.7], [84.7, null, 40.0, 86.0], [90.0, 99.3, null, 93.3], [96.7, 91.3, 62.7, null]],
    pi0:   [[null, 77.3, 69.3, 71.3], [65.3, null, 43.3, 57.3], [71.3, 65.3, null, 70.0], [60.0, 49.3, 72.0, null]],
    gr00t: [[null, 82.7, 30.7, 77.3], [70.7, null, 32.7, 69.3], [94.0, 80.7, null, 94.7], [63.3, 84.0, 84.7, null]],
  };
  // Pick-Place-Press: [button][cube][plate], order red, blue
  const PPP = {
    pi05:  [[[null, 89.3], [39.3, 52.7]], [[68.0, 76.7], [49.3, null]]],
    pi0:   [[[null, 30.0], [47.3, 37.3]], [[42.7, 52.7], [34.0, null]]],
    gr00t: [[[null, 13.3], [57.3, 13.3]], [[19.3, 76.0], [12.0, null]]],
  };

  // Video file conventions (see README.md)
  const videoPath = (sel, method) =>
    sel.bench === "pp"
      ? `static/videos/explorer/pick_place/${sel.cube}_${sel.plate}_${method}.mp4`
      : `static/videos/explorer/pick_place_press/${sel.cube}_${sel.plate}_${sel.button}_${method}.mp4`;

  // ---------------------------------------------------------------
  // Sequential green scale (one hue, light -> dark), as in the paper heatmaps
  // ---------------------------------------------------------------
  const STOPS = [
    [0, [241, 248, 238]],
    [25, [205, 233, 196]],
    [50, [148, 206, 139]],
    [75, [80, 163, 92]],
    [100, [29, 106, 52]],
  ];
  const INK = [22, 24, 27];
  const WHITE = [255, 255, 255];

  function scaleColor(v) {
    v = Math.max(0, Math.min(100, v));
    for (let i = 1; i < STOPS.length; i++) {
      const [v1, c1] = STOPS[i];
      const [v0, c0] = STOPS[i - 1];
      if (v <= v1) {
        const t = (v - v0) / (v1 - v0);
        return c0.map((c, k) => Math.round(c + t * (c1[k] - c)));
      }
    }
    return STOPS[STOPS.length - 1][1];
  }
  function luminance(rgb) {
    const f = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2]);
  }
  function contrast(a, b) {
    const [l1, l2] = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (l1 + 0.05) / (l2 + 0.05);
  }
  const rgb = (c) => `rgb(${c.join(",")})`;

  // ---------------------------------------------------------------
  // Explorer
  // ---------------------------------------------------------------
  const matrixEl = document.getElementById("matrix");
  if (matrixEl) initExplorer();

  function initExplorer() {
    const state = {
      bench: "pp",
      model: "pi05",
      pp: { cube: "yellow", plate: "green" },
      ppp: { cube: "red", plate: "blue", button: "red" },
    };
    const tagEl = document.getElementById("combo-tag");
    const statsEl = document.getElementById("combo-stats");
    const instrEl = document.getElementById("instr");
    const slotFt = document.getElementById("v-ft");
    const slotCraft = document.getElementById("v-craft");

    document.querySelector(".scale-bar").style.background =
      `linear-gradient(90deg, ${STOPS.map(([v, c]) => `${rgb(c)} ${v}%`).join(", ")})`;

    document.querySelectorAll("[data-bench]").forEach((b) =>
      b.addEventListener("click", () => { state.bench = b.dataset.bench; render(); }));
    document.querySelectorAll("[data-model]").forEach((b) =>
      b.addEventListener("click", () => { state.model = b.dataset.model; render(); }));

    function value(bench, model, sel) {
      const ci = COLORS.indexOf(sel.cube), pi = COLORS.indexOf(sel.plate);
      if (bench === "pp") return PP[model][ci][pi];
      return PPP[model][COLORS.indexOf(sel.button)][ci][pi];
    }

    function makeCell(bench, sel) {
      const v = value(bench, state.model, sel);
      const cur = state[bench];
      const selected = sel.cube === cur.cube && sel.plate === cur.plate && (bench === "pp" || sel.button === cur.button);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "cell";
      btn.setAttribute("aria-pressed", String(selected));
      const what = `cube ${sel.cube}, plate ${sel.plate}` + (bench === "ppp" ? `, button ${sel.button}` : "");
      if (v === null) {
        btn.classList.add("is-demo");
        btn.textContent = "Demo.";
        btn.setAttribute("aria-label", `${what}: demonstrated combination`);
      } else {
        const bg = scaleColor(v);
        btn.style.background = rgb(bg);
        btn.style.color = rgb(contrast(bg, WHITE) >= 4.5 ? WHITE : INK);
        btn.textContent = v.toFixed(1);
        btn.setAttribute("aria-label", `${what}: undemonstrated, CRAFT success ${v.toFixed(1)}% with ${MODELS[state.model]}`);
      }
      btn.addEventListener("click", () => { state[bench] = { ...sel }; render(); });
      return btn;
    }

    function head(cls, color, kind) {
      const el = document.createElement("div");
      el.className = cls;
      const sw = document.createElement("i");
      sw.className = `sw ${kind} ${color}`;
      el.append(sw, document.createTextNode(color[0].toUpperCase() + color.slice(1)));
      return el;
    }

    function buildMatrix(bench, colors, button) {
      const mx = document.createElement("div");
      mx.className = "mx";
      if (button) {
        const t = document.createElement("div");
        t.className = "mx-title";
        const sw = document.createElement("i");
        sw.className = `sw button ${button}`;
        t.append(sw, document.createTextNode(`Press: ${button} button`));
        mx.append(t);
      }
      const ax = document.createElement("div");
      ax.className = "mx-axis-x";
      ax.textContent = "Place: plate";
      const frame = document.createElement("div");
      frame.className = "mx-frame";
      const ay = document.createElement("div");
      ay.className = "mx-axis-y";
      ay.textContent = "Pick: cube";
      const grid = document.createElement("div");
      grid.className = "mx-grid";
      grid.style.setProperty("--n", colors.length);
      grid.append(document.createElement("div"));
      colors.forEach((c) => grid.append(head("mx-colhead", c, "plate")));
      colors.forEach((cube) => {
        grid.append(head("mx-rowhead", cube, "cube"));
        colors.forEach((plate) => grid.append(makeCell(bench, { bench, cube, plate, button })));
      });
      frame.append(ay, grid);
      mx.append(ax, frame);
      return mx;
    }

    function entity(color, noun, kind) {
      const span = document.createElement("span");
      span.className = "ent";
      const sw = document.createElement("i");
      sw.className = `sw ${kind} ${color}`;
      span.append(sw, document.createTextNode(`${color} ${noun}`));
      return span;
    }

    function render() {
      document.querySelectorAll("[data-bench]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.bench === state.bench)));
      document.querySelectorAll("[data-model]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.model === state.model)));

      matrixEl.replaceChildren();
      if (state.bench === "pp") {
        matrixEl.append(buildMatrix("pp", COLORS));
      } else {
        ["red", "blue"].forEach((btn) => matrixEl.append(buildMatrix("ppp", ["red", "blue"], btn)));
      }

      const sel = { bench: state.bench, ...state[state.bench] };
      const v = value(state.bench, state.model, sel);
      const demo = v === null;

      tagEl.textContent = demo ? "Demonstrated combination" : "Undemonstrated combination";
      tagEl.classList.toggle("is-demo", demo);

      statsEl.replaceChildren();
      if (demo) {
        statsEl.textContent = "Included in the fine-tuning demonstrations";
      } else {
        statsEl.append(document.createTextNode("CRAFT success: "));
        Object.keys(MODELS).forEach((m, i) => {
          if (i) statsEl.append(document.createTextNode(" · "));
          const b = document.createElement("b");
          b.textContent = `${value(state.bench, m, sel).toFixed(1)}%`;
          statsEl.append(b, " ", modelLabel(m));
        });
      }

      instrEl.replaceChildren(
        document.createTextNode("“pick the "), entity(sel.cube, "cube", "cube"),
        document.createTextNode(" and place it on the "), entity(sel.plate, "plate", "plate"));
      if (sel.bench === "ppp") {
        instrEl.append(document.createTextNode(", then press the "), entity(sel.button, "button", "button"));
      }
      instrEl.append(document.createTextNode("”"));

      loadVideo(slotFt, videoPath(sel, "ft"));
      loadVideo(slotCraft, videoPath(sel, "craft"));
    }

    render();
  }

  // ---------------------------------------------------------------
  // Video slots: show the video when the file exists, a placeholder otherwise
  // ---------------------------------------------------------------
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function loadVideo(slot, src) {
    const video = slot.querySelector("video");
    const path = slot.querySelector(".ph-path");
    if (path) path.textContent = src;
    slot.classList.remove("has-video");
    video.onloadeddata = () => {
      slot.classList.add("has-video");
      if (reduceMotion) video.controls = true;
      else video.play().catch(() => {});
    };
    video.onerror = () => slot.classList.remove("has-video");
    video.src = src;
  }

  // Transparent videos: WebKit (Safari, all iOS browsers) plays HEVC with alpha; others play VP9 WebM with alpha
  function prefersHevcAlpha() {
    const ua = navigator.userAgent;
    const iOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
    const safari = /Safari\//.test(ua) && !/Chrome|Chromium|CriOS|Edg|OPR|Firefox|FxiOS|Android/.test(ua);
    return iOS || safari;
  }

  document.querySelectorAll(".vslot[data-src], .vslot[data-src-webm]").forEach((slot) => {
    const d = slot.dataset;
    loadVideo(slot, d.srcWebm ? (prefersHevcAlpha() ? d.srcHevc : d.srcWebm) : d.src);
  });

  // ---------------------------------------------------------------
  // Live instruction under a video: follows the frame, highlights the entity of the current skill
  // ---------------------------------------------------------------
  function setupLiveInstruction(slot) {
    const schedule = JSON.parse(slot.dataset.schedule);
    const fps = Number(slot.dataset.fps) || 30;
    const video = slot.querySelector("video");
    const out = slot.querySelector(".live-text");
    let cur = -1;

    function chip(color, noun, current, changed, markIn) {
      const span = document.createElement("span");
      span.className = "ent" + (current ? (markIn ? " mark-in" : "") : " no-mark") + (changed ? " is-changed" : "");
      const sw = document.createElement("i");
      sw.className = `sw ${noun} ${color}`;
      span.append(sw, `${color} ${noun}`);
      return span;
    }

    function render(i) {
      const [, cube, plate, op] = schedule[i];
      const prev = i > cur && cur >= 0 ? schedule[cur] : null; // no change effects on loop restart
      out.replaceChildren(
        "pick the ", chip(cube, "cube", op === "pick", prev && prev[1] !== cube, prev && prev[3] !== op),
        " and place it on the ", chip(plate, "plate", op === "place", prev && prev[2] !== plate, prev && prev[3] !== op));
      cur = i;
    }

    function update(t) {
      const frame = Math.floor(t * fps + 1e-3);
      let i = 0;
      while (i + 1 < schedule.length && frame >= schedule[i + 1][0]) i++;
      if (i !== cur) render(i);
    }

    if ("requestVideoFrameCallback" in HTMLVideoElement.prototype) {
      const onFrame = (_, meta) => { update(meta.mediaTime); video.requestVideoFrameCallback(onFrame); };
      video.requestVideoFrameCallback(onFrame);
    } else {
      const loop = () => { update(video.currentTime); requestAnimationFrame(loop); };
      requestAnimationFrame(loop);
    }
    video.addEventListener("seeked", () => update(video.currentTime));
    render(0);
  }

  document.querySelectorAll(".vslot[data-schedule]").forEach(setupLiveInstruction);

  // ---------------------------------------------------------------
  // Top nav: highlight the section in view
  // ---------------------------------------------------------------
  const links = [...document.querySelectorAll(".topnav-links a")];
  const byId = new Map(links.map((a) => [a.getAttribute("href").slice(1), a]));
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        links.forEach((a) => a.classList.remove("is-active"));
        const a = byId.get(e.target.id);
        if (a) a.classList.add("is-active");
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    byId.forEach((_, id) => { const s = document.getElementById(id); if (s) io.observe(s); });
  }

  // Fade the nav edge only when the links overflow
  const navLinks = document.querySelector(".topnav-links");
  if (navLinks) {
    const fit = () => {
      navLinks.classList.remove("is-overflowing");
      navLinks.classList.toggle("is-overflowing", navLinks.scrollWidth > navLinks.clientWidth + 1);
    };
    fit();
    window.addEventListener("resize", fit);
  }

  // ---------------------------------------------------------------
  // BibTeX copy
  // ---------------------------------------------------------------
  const copyBtn = document.getElementById("copy-bib");
  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      const text = document.getElementById("bib").textContent;
      try {
        await navigator.clipboard.writeText(text);
        copyBtn.textContent = "Copied";
      } catch (_) {
        const r = document.createRange();
        r.selectNodeContents(document.getElementById("bib"));
        const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
        copyBtn.textContent = "Selected";
      }
      setTimeout(() => { copyBtn.textContent = "Copy"; }, 1600);
    });
  }
})();
