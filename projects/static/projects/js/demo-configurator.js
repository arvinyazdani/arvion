(function () {
  "use strict";

  function renderSectorExperience(experience, goal) {
    const panels = Array.from(experience.querySelectorAll('[data-sector-panel]'));
    const selected = panels.find((panel) => panel.dataset.sectorPanel === goal);
    panels.forEach((panel, index) => { panel.hidden = selected ? panel !== selected : index !== 0; });
    experience.querySelectorAll('[data-sector-goal]').forEach((button) => {
      button.disabled = false;
      button.setAttribute('aria-pressed', String(Boolean(selected) && button.dataset.sectorGoal === goal));
    });
    experience.querySelector('[data-sector-unspecified]').hidden = Boolean(selected);
    return selected || null;
  }
  // Exercise the same renderer in Node without bootstrapping browser UI.
  if (typeof module !== 'undefined' && module.exports && typeof document === 'undefined') {
    module.exports = {renderSectorExperience};
    return;
  }

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
  const contrastColour = (hex) => {
    const luminance = relativeLuminance(hex);
    const whiteContrast = 1.05 / (luminance + 0.05);
    const darkContrast = (luminance + 0.05) / (relativeLuminance("#171717") + 0.05);
    return darkContrast >= whiteContrast ? "#171717" : "#ffffff";
  };
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
      view: window.matchMedia("(max-width: 760px)").matches ? "mobile" : "desktop",
    };
    let stored = null;
    try { stored = readJson(sessionStorage.getItem(storageKey)); } catch (error) { stored = null; }
    const fromUrl = {
      brand: params.get("brand"), theme: params.get("theme"), customColor: params.get("color"),
      personality: params.get("personality"), features: params.has("features") ? params.get("features").split(",") : null,
      view: params.get("view"),
    };
    const state = Object.assign({}, defaults, stored || {});
    const storedBrief = state.brief || {};
    state.brief = {};
    root.querySelectorAll('[data-brief-key]').forEach((control) => {
      const key = control.dataset.briefKey;
      const value = params.get(`brief_${key}`) ?? storedBrief[key] ?? "";
      state.brief[key] = Array.from(control.options).some((option) => option.value === value) ? value : "";
    });
    Object.keys(fromUrl).forEach((key) => { if (fromUrl[key] !== null) state[key] = fromUrl[key]; });
    state.brand = String(state.brand || defaults.brand).trim().slice(0, 48) || defaults.brand;
    state.theme = ALLOWED_THEMES.has(state.theme) ? state.theme : defaults.theme;
    state.customColor = validHex(state.customColor) ? state.customColor.toLowerCase() : defaults.customColor;
    state.personality = ALLOWED_PERSONALITIES.has(state.personality) ? state.personality : defaults.personality;
    state.features = Array.isArray(state.features) ? state.features.filter((item) => ALLOWED_FEATURES.has(item)).slice(0, 6) : defaults.features;
    state.view = state.view === "mobile" ? "mobile" : "desktop";
    // On phones, never revive a desktop-sized frame from a previous visit.
    if (window.matchMedia("(max-width: 760px)").matches) state.view = "mobile";

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
      Object.entries(state.brief).forEach(([key, value]) => { if (value) query.set(`brief_${key}`, value); });
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
      root.querySelectorAll('[data-brief-key]').forEach((control) => { control.value = state.brief[control.dataset.briefKey] || ""; });
      // The enquiry's validated goal owns both the settings and live scene.
      root.querySelectorAll('[data-sector-experience]').forEach((experience) => {
        // Keep the hero above the controls stable: changing its line count
        // while the visitor edits a lower chapter would move the tap target.
        renderSectorExperience(experience, state.brief.goal);
      });
      root.querySelectorAll('[name="features"]').forEach((input) => { input.checked = state.features.includes(input.value); });
      root.querySelectorAll('[data-sector-feature-status]').forEach((status) => {
        const enabled = state.features.includes(status.dataset.sectorFeatureStatus);
        const fa = document.documentElement.lang === 'fa';
        status.textContent = enabled ? (fa ? 'در طراحی شما فعال' : 'Enabled in your design') : (fa ? 'هنوز انتخاب نشده' : 'Not selected yet');
        status.dataset.enabled = String(enabled);
      });

      const palette = state.theme === "custom"
        ? [state.customColor, state.customColor, `color-mix(in srgb, ${state.customColor} 12%, white)`]
        : PALETTES[state.theme];
      if (document.body.classList.contains("demo-designer-page")) {
        document.body.style.setProperty("--studio-accent", palette[0]);
        document.body.style.setProperty("--studio-on-accent", contrastColour(palette[0]));
      }
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
      root.querySelectorAll("[data-feature-module]").forEach((module) => {
        const enabled = state.features.includes(module.dataset.featureModule);
        module.hidden = !enabled;
        module.setAttribute("aria-hidden", String(!enabled));
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
      const featureCount = new Intl.NumberFormat(document.documentElement.lang === "fa" ? "fa" : "en").format(state.features.length);
      const summary = `${state.brand} · ${selectedLabel("theme", state.theme)} · ${selectedLabel("personality", state.personality)} · ${featureCount}`;
      root.querySelectorAll("[data-demo-summary]").forEach((item) => { item.textContent = summary; });

      try { sessionStorage.setItem(storageKey, JSON.stringify(state)); } catch (error) {}
      const currentPath = window.location.pathname;
      history.replaceState(null, "", `${currentPath}?${stateQuery()}${window.location.hash}`);
      root.querySelectorAll("[data-demo-full-link]").forEach((link) => { link.href = buildUrl(root.dataset.fullUrl); });
      root.querySelectorAll("[data-demo-back]").forEach((link) => { link.href = buildUrl(root.dataset.previewUrl, "#configurator"); });
    }

    brandInput?.addEventListener("input", () => { state.brand = brandInput.value.trim().slice(0, 48) || defaults.brand; render(); });
    brandInput?.addEventListener("change", () => announceChange(document.documentElement.lang === "fa" ? "نام پیش‌نمایش تغییر کرد" : "Preview name updated"));
    root.querySelectorAll('[data-brief-key]').forEach((control) => control.addEventListener("change", () => {
      state.brief[control.dataset.briefKey] = control.value;
      render();
      announceChange(document.documentElement.lang === "fa" ? "جزئیات سفارش به‌روز شد" : "Order details updated");
    }));
    root.querySelectorAll('[data-sector-goal]').forEach((button) => button.addEventListener('click', () => {
      const control = root.querySelector('[data-brief-key="goal"]');
      if (!control || !Array.from(control.options).some((option) => option.value === button.dataset.sectorGoal)) return;
      control.value = button.dataset.sectorGoal;
      control.dispatchEvent(new Event('change', {bubbles: true}));
    }));
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
      Object.assign(state, defaults, {brief: {}}); try { sessionStorage.removeItem(storageKey); } catch (error) {} render();
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
      let opener = configToggle;
      let isolated = [];
      const setConfigOpen = (open, trigger) => {
        const isMobile = mobileViewport.matches;
        const nextOpen = Boolean(open && isMobile);
        if (open && !isMobile) {
          mobileConfig.scrollIntoView({block: "nearest"});
          mobileConfig.querySelector("input:not([type=hidden])")?.focus({preventScroll: true});
        }
        mobileConfig.classList.toggle("is-mobile-open", nextOpen);
        configToggle.setAttribute("aria-expanded", String(nextOpen));
        if (configBackdrop) configBackdrop.hidden = !nextOpen;
        document.body.classList.toggle("demo-config-open", nextOpen);
        isolated.forEach(([element, wasInert]) => { element.inert = wasInert; });
        isolated = [];
        if (isMobile && nextOpen) {
          opener = trigger || opener;
          // Isolate siblings at each level without disabling the sheet itself.
          for (let branch = mobileConfig; branch.parentElement && branch !== document.body; branch = branch.parentElement) {
            Array.from(branch.parentElement.children).forEach((element) => {
              if (element === branch || element === configBackdrop || ["SCRIPT", "STYLE", "LINK"].includes(element.tagName)) return;
              isolated.push([element, element.inert]);
              element.inert = true;
            });
          }
          mobileConfig.setAttribute("role", "dialog");
          mobileConfig.setAttribute("aria-modal", "true");
        } else {
          mobileConfig.setAttribute("role", "region");
          mobileConfig.removeAttribute("aria-modal");
        }
        if (nextOpen) mobileConfig.querySelector("input:not([type=hidden]), button:not([data-config-toggle]), a")?.focus({preventScroll: true});
        else if (isMobile && mobileConfig.contains(document.activeElement)) opener.focus({preventScroll: true});
      };
      configToggle.addEventListener("click", () => setConfigOpen(!mobileConfig.classList.contains("is-mobile-open"), configToggle));
      root.querySelectorAll("[data-config-open]").forEach((button) => {
        button.disabled = false;
        button.addEventListener("click", () => setConfigOpen(true, button));
      });
      configBackdrop?.addEventListener("click", () => setConfigOpen(false));
      document.addEventListener("keydown", (event) => {
        if (!mobileViewport.matches || !mobileConfig.classList.contains("is-mobile-open")) return;
        if (event.key === "Escape") { event.preventDefault(); setConfigOpen(false); return; }
        if (event.key !== "Tab") return;
        const items = Array.from(mobileConfig.querySelectorAll("button:not([disabled]), input:not([disabled]):not([type=hidden]), a[href], select:not([disabled]), textarea:not([disabled]), summary")).filter((item) => item.getClientRects().length);
        if (!items.length) return;
        const first = items[0], last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      });
      mobileViewport.addEventListener("change", () => {
        setConfigOpen(false);
        if (mobileViewport.matches) { state.view = "mobile"; render(); }
      });
      root.querySelectorAll("[data-demo-submit], [data-demo-full-link]").forEach((control) => {
        control.addEventListener("click", () => setConfigOpen(false));
      });
      mobileConfig.setAttribute("role", "region");
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
      const parentGroup = button.closest("[data-demo-action-group], [data-demo-choice-group]");
      if (parentGroup) parentGroup.querySelectorAll("[data-demo-action]").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
      else button.setAttribute("aria-pressed", String(button.getAttribute("aria-pressed") !== "true"));
      const feedbackHost = parentGroup || button.parentElement;
      let status = feedbackHost.querySelector(":scope > [data-inline-demo-status]");
      if (!status) {
        status = document.createElement("p");
        status.className = "demo-action-status";
        status.dataset.inlineDemoStatus = "";
        status.setAttribute("role", "status");
        feedbackHost.appendChild(status);
      }
      const choiceSummary = root.querySelector("[data-demo-choice-summary]");
      const groupSummary = parentGroup?.querySelector("[data-demo-group-summary]");
      const selectedTime = button.textContent.trim();
      if (groupSummary) {
        groupSummary.textContent = document.documentElement.lang === "fa"
          ? `موضوع انتخابی شما: ${selectedTime} · این انتخاب هنوز ارسال نشده است.`
          : `Your selected topic: ${selectedTime} · this choice has not been sent.`;
      }
      if (choiceSummary && (button.closest("[data-demo-choice-group]") || button.closest("[data-demo-choice-day-group]"))) refreshChoiceSummary();
      if (status) {
        status.textContent = button.dataset.actionMessage || (document.documentElement.lang === "fa" ? "این تعامل فقط پیش‌نمایش است؛ جزئیات واقعی پس از نیازسنجی مشخص می‌شود." : "This is a preview interaction; final behaviour is defined during discovery.");
        status.hidden = false;
      }
    }));

    function refreshChoiceSummary() {
      const group = root.querySelector("[data-demo-choice-group]");
      const selectedTime = group?.querySelector('[aria-pressed="true"]')?.textContent.trim();
      const dayGroup = root.querySelector("[data-demo-choice-day-group]");
      const selectedDay = dayGroup?.querySelector('[aria-pressed="true"]')?.textContent.trim();
      const select = root.querySelector("[data-demo-choice-select]");
      const visitType = select?.selectedOptions?.[0]?.textContent.trim();
      const summary = root.querySelector("[data-demo-choice-summary]");
      if (!summary) return;
      const parts = [selectedDay, selectedTime, visitType].filter(Boolean);
      const isPersian = document.documentElement.lang === "fa";
      summary.textContent = parts.length
        ? `${parts.join(" · ")} · ${isPersian ? "رزرو فقط در حد پیش‌نمایش" : "preview only"}`
        : (isPersian ? "برای تکمیل خلاصه نمونه، روز و ساعت را انتخاب کنید." : "Choose a sample day and time to complete the preview summary.");
    }
    root.querySelectorAll("[data-demo-choice-select]").forEach((select) => select.addEventListener("change", refreshChoiceSummary));

    const updateAttributeSummary = () => {
      const values = Array.from(root.querySelectorAll("[data-demo-attribute]")).map((field) => {
        const value = field.selectedOptions?.[0]?.textContent.trim() || field.value.trim();
        return value ? `${field.dataset.demoAttributeLabel || ""} ${value}`.trim() : "";
      }).filter(Boolean);
      root.querySelectorAll("[data-demo-attribute-summary]").forEach((summary) => {
        summary.textContent = values.length
          ? `${document.documentElement.lang === "fa" ? "انتخاب نمایشی شما" : "Your sample choices"}: ${values.join(" · ")}`
          : (document.documentElement.lang === "fa" ? "جزئیات موردنظر را انتخاب کنید." : "Choose the details that matter to you.");
      });
    };
    root.querySelectorAll("[data-demo-attribute]").forEach((field) => field.addEventListener("change", updateAttributeSummary));
    updateAttributeSummary();

    const activeFilters = new Map();
    root.querySelectorAll("[data-demo-filter]").forEach((button) => button.addEventListener("click", () => {
      const group = button.closest("[data-demo-filter-group]");
      if (!group) return;
      const groupKey = group.dataset.demoFilterGroup;
      activeFilters.set(groupKey, button.dataset.demoFilter);
      group.querySelectorAll("[data-demo-filter]").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
      applyFilters(groupKey);
    }));

    function applyFilters(groupKey) {
      const selected = activeFilters.get(groupKey) || "all";
      const query = Array.from(root.querySelectorAll("[data-demo-search]"))
        .find((input) => (input.dataset.filterGroup || "shop") === groupKey)?.value.trim().toLocaleLowerCase() || "";
      root.querySelectorAll("[data-filter-item]").forEach((item) => {
        if (item.dataset.filterGroup !== groupKey) return;
        const categoryMatches = selected === "all" || item.dataset.filterItem === selected;
        const textMatches = !query || (item.dataset.searchItem || item.textContent).toLocaleLowerCase().includes(query);
        item.hidden = !categoryMatches || !textMatches;
      });
      updateFilteredEmptyState(groupKey);
    }

    function updateFilteredEmptyState(groupKey) {
      const items = Array.from(root.querySelectorAll("[data-filter-item]")).filter((item) => item.dataset.filterGroup === groupKey);
      const empty = root.querySelector(`[data-demo-empty-filter][data-filter-group="${groupKey}"]`);
      if (empty) empty.hidden = !items.length || items.some((item) => !item.hidden);
    }

    root.querySelectorAll("[data-demo-search]").forEach((input) => {
      const clear = document.createElement("button");
      clear.type = "button";
      clear.className = "demo-search-clear";
      clear.textContent = document.documentElement.lang === "fa" ? "پاک کردن" : "Clear";
      clear.hidden = !input.value;
      input.parentElement.appendChild(clear);
      const update = () => {
        clear.hidden = !input.value;
        applyFilters(input.dataset.filterGroup || "shop");
      };
      input.addEventListener("input", (event) => { if (!event.isComposing) update(); });
      input.addEventListener("compositionend", update);
      clear.addEventListener("click", () => { input.value = ""; update(); input.focus(); });
    });

    let sampleBasketCount = 0;
    const formatCount = (value) => new Intl.NumberFormat(document.documentElement.lang === "fa" ? "fa-IR" : "en-US").format(value);
    root.querySelectorAll("[data-demo-cart-add]").forEach((button) => button.addEventListener("click", () => {
      sampleBasketCount += 1;
      root.querySelectorAll("[data-demo-cart-count]").forEach((counter) => { counter.textContent = formatCount(sampleBasketCount); });
      const status = root.querySelector("[data-demo-action-status]");
      const name = button.closest("[data-product-name]")?.dataset.productName || "";
      if (status) {
        status.textContent = document.documentElement.lang === "fa"
          ? `${name} به سبد نمایشی اضافه شد؛ هیچ سفارش یا پرداخت واقعی ثبت نمی‌شود.`
          : `${name} was added to the sample basket. No real order or payment was created.`;
        status.hidden = false;
      }
    }));

    render();
  });
})();
