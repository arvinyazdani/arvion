(function () {
  "use strict";

  const PALETTES = {
    warm: ["#f16a3b", "#5b2833", "#fff0e8"],
    midnight: ["#2c3042", "#7c92ff", "#eef1ff"],
    sage: ["#527263", "#c78f45", "#edf4ef"],
    plum: ["#6c3f72", "#e09a71", "#f7edf8"],
    gold: ["#825f23", "#dfbd70", "#f6efdf"],
  };
  const STYLE_THEME = {minimal: "warm", modern: "midnight", editorial: "midnight", luxury: "sage", bold: "plum", industrial: "midnight", sage: "sage", plum: "plum"};
  const ALLOWED_THEMES = new Set(["warm", "midnight", "sage", "plum", "gold", "custom"]);
  const ALLOWED_PERSONALITIES = new Set(["minimal", "modern", "editorial", "luxury", "bold", "industrial"]);
  const ALLOWED_FEATURES = new Set(["payment", "booking", "catalog", "blog", "membership", "multilingual"]);

  const validHex = (value) => /^#[0-9a-f]{6}$/i.test(value || "");
  const readJson = (value) => {
    try { return JSON.parse(value); } catch (error) { return null; }
  };
  const relativeLuminance = (hex) => {
    const channels = [1, 3, 5].map((index) => parseInt(hex.slice(index, index + 2), 16) / 255);
    const linear = channels.map((channel) => channel <= 0.03928 ? channel / 12.92 : Math.pow((channel + 0.055) / 1.055, 2.4));
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
  };
  const contrastColour = (hex) => relativeLuminance(hex) > 0.42 ? "#171717" : "#ffffff";
  const readableAccent = (hex) => ((1.05 / (relativeLuminance(hex) + 0.05)) >= 4.5 ? hex : "#374151");

  // A page restored from the back-forward cache keeps the exact DOM it left
  // with, including a `submission_token` hidden field that the server has
  // already consumed. Reloading forces a fresh GET, which mints a new token
  // before the visitor can act on the restored page — the normal path never
  // reaches the server's stale-token fallback at all. This is convenience
  // only: the server enforces the real rule independently of it running.
  if (document.querySelector("[data-demo-form]")) {
    window.addEventListener("pageshow", (event) => { if (event.persisted) location.reload(); });
  }

  document.querySelectorAll("[data-demo-configurator]").forEach((root) => {
    const slug = root.dataset.demoSlug;
    const storageKey = `rvion-demo-${slug}`;
    const params = new URLSearchParams(window.location.search);
    const defaultStyle = root.dataset.defaultStyle || "minimal";
    const defaults = {
      brand: root.dataset.defaultBrand || "RVION DEMO",
      theme: root.dataset.defaultTheme || STYLE_THEME[defaultStyle] || "warm",
      customColor: root.dataset.defaultCustomColor || "#2563eb",
      personality: root.dataset.defaultPersonality || (ALLOWED_PERSONALITIES.has(defaultStyle) ? defaultStyle : "minimal"),
      features: (root.dataset.defaultFeatures || "").split(",").filter((item) => ALLOWED_FEATURES.has(item)),
      view: "desktop",
    };
    let stored = null;
    try { stored = readJson(sessionStorage.getItem(storageKey)); } catch (error) { stored = null; }
    const fromUrl = {
      brand: params.get("brand"), theme: params.get("theme"), customColor: params.get("color"),
      personality: params.get("personality"), features: params.has("features") ? params.get("features").split(",") : null,
      view: params.get("view"),
    };
    const state = Object.assign({}, defaults, stored || {});
    Object.keys(fromUrl).forEach((key) => { if (fromUrl[key] !== null) state[key] = fromUrl[key]; });
    state.brand = String(state.brand || defaults.brand).trim().slice(0, 48) || defaults.brand;
    state.theme = ALLOWED_THEMES.has(state.theme) ? state.theme : defaults.theme;
    state.customColor = validHex(state.customColor) ? state.customColor.toLowerCase() : defaults.customColor;
    state.personality = ALLOWED_PERSONALITIES.has(state.personality) ? state.personality : defaults.personality;
    state.features = Array.isArray(state.features) ? state.features.filter((item) => ALLOWED_FEATURES.has(item)).slice(0, 6) : defaults.features;
    state.view = state.view === "mobile" ? "mobile" : "desktop";

    const brandInput = root.querySelector('[name="brand_preview"]');
    const colourInput = root.querySelector('[name="custom_color"]');
    const featureLabels = {};
    root.querySelectorAll("[data-feature-label]").forEach((input) => { featureLabels[input.value] = input.dataset.featureLabel; });
    root.querySelectorAll("[data-feature-key]").forEach((item) => { featureLabels[item.dataset.featureKey] = item.textContent.trim(); });
    const categoryFeatures = new Set(Object.keys(featureLabels));
    // A stale tab/session or hand-edited URL may contain features from a
    // different category. Keep the live summary aligned with this sample;
    // the server independently applies the same category boundary on POST.
    state.features = Array.isArray(state.features) ? state.features.filter((item) => categoryFeatures.has(item)).slice(0, 6) : defaults.features.filter((item) => categoryFeatures.has(item));

    const controlValue = (name, value) => {
      root.querySelectorAll(`[name="${name}"]`).forEach((control) => {
        if (control.type === "radio") control.checked = control.value === value;
        else if (control.tagName === "SELECT") control.value = value;
      });
    };
    const selectedLabel = (name, value) => {
      const radio = root.querySelector(`[name="${name}"][value="${value}"]`);
      if (radio) return (radio.closest("label")?.textContent || value).trim();
      const select = root.querySelector(`[name="${name}"]`);
      return select?.selectedOptions?.[0]?.textContent.trim() || value;
    };
    const stateQuery = () => {
      const query = new URLSearchParams();
      query.set("brand", state.brand);
      query.set("theme", state.theme);
      if (state.theme === "custom") query.set("color", state.customColor);
      query.set("personality", state.personality);
      query.set("features", state.features.join(","));
      query.set("view", state.view);
      return query.toString();
    };
    const buildUrl = (path, hash) => `${path}?${stateQuery()}${hash || ""}`;
    const liveFeedback = root.querySelector("[data-live-edit-feedback]");
    const announceChange = (label, detail) => {
      if (!liveFeedback) return;
      liveFeedback.textContent = `${label}${detail ? ` · ${detail}` : ""}`;
      liveFeedback.classList.remove("is-changed");
      // Re-trigger a short visual confirmation without making every edit a
      // distracting animation. The text remains available to assistive tech.
      requestAnimationFrame(() => liveFeedback.classList.add("is-changed"));
    };

    function render() {
      if (brandInput && document.activeElement !== brandInput) brandInput.value = state.brand;
      if (colourInput) colourInput.value = state.customColor;
      controlValue("theme", state.theme);
      controlValue("personality", state.personality);
      root.querySelectorAll('[name="features"]').forEach((input) => { input.checked = state.features.includes(input.value); });

      const palette = state.theme === "custom"
        ? [state.customColor, state.customColor, `color-mix(in srgb, ${state.customColor} 12%, white)`]
        : PALETTES[state.theme];
      root.querySelectorAll("[data-demo-site]").forEach((site) => {
        site.style.setProperty("--demo-primary", palette[0]);
        site.style.setProperty("--demo-accent", palette[1]);
        site.style.setProperty("--demo-soft", palette[2]);
        site.style.setProperty("--demo-on-primary", contrastColour(palette[0]));
        site.style.setProperty("--demo-primary-text", readableAccent(palette[0]));
        site.style.setProperty("--demo-a", palette[0]);
        site.style.setProperty("--demo-b", palette[1]);
        site.dataset.personality = state.personality;
        site.dataset.category = root.dataset.demoCategory || "generic";
        site.classList.toggle("demo-site-jewelry", root.dataset.demoCategory === "jewelry");
      });
      root.querySelectorAll("[data-demo-brand]").forEach((item) => { item.textContent = state.brand; });
      root.querySelectorAll("[data-demo-initial]").forEach((item) => { item.textContent = state.brand.charAt(0).toUpperCase(); });
      root.querySelectorAll("[data-demo-stage]").forEach((stage) => { stage.dataset.view = state.view; });
      root.querySelectorAll("[data-demo-view]").forEach((button) => { button.setAttribute("aria-pressed", String(button.dataset.demoView === state.view)); });
      root.querySelectorAll("[data-demo-theme]").forEach((button) => { button.setAttribute("aria-pressed", String(button.dataset.demoTheme === state.theme)); });
      root.querySelectorAll("[data-demo-personality]").forEach((button) => { button.setAttribute("aria-pressed", String(button.dataset.demoPersonality === state.personality)); });
      root.querySelectorAll("[data-demo-hex]").forEach((output) => { output.textContent = state.customColor.toUpperCase(); });

      root.querySelectorAll("[data-demo-feature-summary]").forEach((container) => {
        container.replaceChildren();
        const choices = state.features.length ? state.features : [];
        if (!choices.length) {
          const empty = document.createElement("small");
          empty.textContent = document.documentElement.lang === "fa" ? "هنوز امکانی انتخاب نشده" : "No capabilities selected yet";
          container.appendChild(empty);
        } else {
          choices.forEach((feature) => {
            const chip = document.createElement("small");
            chip.textContent = featureLabels[feature] || feature;
            container.appendChild(chip);
          });
        }
      });
      const summary = `${state.brand} · ${selectedLabel("theme", state.theme)} · ${selectedLabel("personality", state.personality)} · ${state.features.length}`;
      root.querySelectorAll("[data-demo-summary]").forEach((item) => { item.textContent = summary; });

      try { sessionStorage.setItem(storageKey, JSON.stringify(state)); } catch (error) {}
      const currentPath = window.location.pathname;
      history.replaceState(null, "", `${currentPath}?${stateQuery()}${window.location.hash}`);
      root.querySelectorAll("[data-demo-full-link]").forEach((link) => { link.href = buildUrl(root.dataset.fullUrl); });
      root.querySelectorAll("[data-demo-back]").forEach((link) => { link.href = buildUrl(root.dataset.previewUrl, "#configurator"); });
    }

    brandInput?.addEventListener("input", () => { state.brand = brandInput.value.trim().slice(0, 48) || defaults.brand; render(); });
    brandInput?.addEventListener("change", () => announceChange(document.documentElement.lang === "fa" ? "نام پیش‌نمایش تغییر کرد" : "Preview name updated"));
    root.querySelectorAll('[name="theme"]').forEach((control) => control.addEventListener("change", () => { state.theme = control.value; render(); announceChange(selectedLabel("theme", state.theme), document.documentElement.lang === "fa" ? "روی نمونه اعمال شد" : "applied to the sample"); }));
    colourInput?.addEventListener("input", () => {
      if (!validHex(colourInput.value)) return;
      state.customColor = colourInput.value.toLowerCase(); state.theme = "custom"; render(); announceChange(state.customColor.toUpperCase(), document.documentElement.lang === "fa" ? "رنگ دلخواه اعمال شد" : "custom colour applied");
    });
    root.querySelectorAll('[name="personality"]').forEach((control) => control.addEventListener("change", () => { state.personality = control.value; render(); announceChange(selectedLabel("personality", state.personality), document.documentElement.lang === "fa" ? "شخصیت بصری تغییر کرد" : "design mood updated"); }));
    root.querySelectorAll('[name="features"]').forEach((control) => control.addEventListener("change", () => {
      state.features = Array.from(root.querySelectorAll('[name="features"]:checked')).map((item) => item.value).filter((item) => categoryFeatures.has(item)); render();
      announceChange(control.dataset.featureLabel || control.value, document.documentElement.lang === "fa" ? (control.checked ? "به امکانات نمونه اضافه شد" : "از امکانات نمونه برداشته شد") : (control.checked ? "added to the sample" : "removed from the sample"));
    }));
    root.querySelectorAll("[data-demo-view]").forEach((button) => button.addEventListener("click", () => { state.view = button.dataset.demoView; render(); }));
    root.querySelectorAll("[data-demo-reset]").forEach((button) => button.addEventListener("click", () => {
      Object.assign(state, defaults); try { sessionStorage.removeItem(storageKey); } catch (error) {} render();
    }));

    // Reduce accidental double submits by disabling the button once the
    // browser has already begun submitting the form. The server-side
    // submission_token is what actually prevents a duplicate DemoSelection,
    // so this is UX polish only and never blocks the real POST.
    const form = root.querySelector("[data-demo-form]");
    const submitButton = root.querySelector("[data-demo-submit]");
    if (form && submitButton) {
      form.addEventListener("submit", () => {
        if (submitButton.disabled) return;
        submitButton.disabled = true;
        const sendingLabel = submitButton.dataset.sendingLabel;
        if (sendingLabel) submitButton.textContent = sendingLabel;
      });
    }

    const mobileConfig = root.querySelector("[data-mobile-config]");
    const configToggle = root.querySelector("[data-config-toggle]");
    const configBackdrop = root.querySelector("[data-config-backdrop]");
    const mobileViewport = window.matchMedia("(max-width: 760px)");
    if (mobileConfig && configToggle) {
      const setConfigOpen = (open) => {
        const isMobile = mobileViewport.matches;
        const nextOpen = Boolean(open && isMobile);
        mobileConfig.classList.toggle("is-mobile-open", nextOpen);
        configToggle.setAttribute("aria-expanded", String(nextOpen));
        if (configBackdrop) configBackdrop.hidden = !nextOpen;
        document.body.classList.toggle("demo-config-open", nextOpen);
        if (isMobile && nextOpen) {
          mobileConfig.setAttribute("role", "dialog");
          mobileConfig.setAttribute("aria-modal", "true");
        } else {
          mobileConfig.setAttribute("role", "region");
          mobileConfig.removeAttribute("aria-modal");
        }
        if (nextOpen) mobileConfig.querySelector("input:not([type=hidden]), button:not([data-config-toggle]), a")?.focus({preventScroll: true});
        else if (isMobile && mobileConfig.contains(document.activeElement)) configToggle.focus({preventScroll: true});
      };
      configToggle.addEventListener("click", () => setConfigOpen(!mobileConfig.classList.contains("is-mobile-open")));
      root.querySelectorAll("[data-config-open]").forEach((button) => button.addEventListener("click", () => setConfigOpen(true)));
      configBackdrop?.addEventListener("click", () => setConfigOpen(false));
      document.addEventListener("keydown", (event) => {
        if (!mobileViewport.matches || !mobileConfig.classList.contains("is-mobile-open")) return;
        if (event.key === "Escape") { event.preventDefault(); setConfigOpen(false); return; }
        if (event.key !== "Tab") return;
        const items = Array.from(mobileConfig.querySelectorAll("button:not([disabled]), input:not([disabled]):not([type=hidden]), a[href], select:not([disabled]), textarea:not([disabled])")).filter((item) => item.getClientRects().length);
        if (!items.length) return;
        const first = items[0], last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      });
      mobileViewport.addEventListener("change", () => setConfigOpen(false));
      root.querySelectorAll("[data-demo-submit], [data-demo-full-link]").forEach((control) => {
        control.addEventListener("click", () => setConfigOpen(false));
      });
      mobileConfig.setAttribute("role", mobileViewport.matches ? "region" : "region");
      root.querySelectorAll("[data-demo-theme]").forEach((button) => button.addEventListener("click", () => {
        state.theme = button.dataset.demoTheme;
        render();
        announceChange(button.dataset.themeLabel || button.dataset.demoTheme, document.documentElement.lang === "fa" ? "روی نمونه اعمال شد" : "applied to your sample");
      }));
      root.querySelectorAll("[data-demo-personality]").forEach((button) => button.addEventListener("click", () => {
        state.personality = button.dataset.demoPersonality;
        render();
        announceChange(button.textContent.trim(), document.documentElement.lang === "fa" ? "سبک نمونه تغییر کرد" : "sample style updated");
      }));
    }

    root.querySelectorAll("[data-demo-action]").forEach((button) => button.addEventListener("click", () => {
      const parentGroup = button.closest("[data-demo-action-group]");
      if (parentGroup) parentGroup.querySelectorAll("[data-demo-action]").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
      else button.setAttribute("aria-pressed", String(button.getAttribute("aria-pressed") !== "true"));
      const status = root.querySelector("[data-demo-action-status]");
      if (status) {
        status.textContent = button.dataset.actionMessage || (document.documentElement.lang === "fa" ? "این تعامل فقط پیش‌نمایش است؛ جزئیات واقعی پس از نیازسنجی مشخص می‌شود." : "This is a preview interaction; final behaviour is defined during discovery.");
        status.hidden = false;
      }
    }));

    render();
  });
})();
