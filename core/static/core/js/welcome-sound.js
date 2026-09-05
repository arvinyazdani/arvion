(() => {
  const SOUND_KEY = "rvion-welcome-sound";      // "on" | "off"
  const PLAYED_KEY = "rvion-welcome-sound-played";
  const source = document.documentElement.dataset.welcomeSound;
  if (!source) return;

  const read = (storage, key) => {
    try { return storage.getItem(key); } catch (error) { return null; }
  };
  const write = (storage, key, value) => {
    try { storage.setItem(key, value); } catch (error) {}
  };

  const enabled = () => read(localStorage, SOUND_KEY) !== "off";

  let audio = null;
  const load = () => {
    if (!audio) {
      audio = new Audio(source);
      audio.preload = "auto";
      audio.volume = 0.45;
    }
    return audio;
  };

  const play = () => {
    if (!enabled()) return Promise.reject();
    return load().play();
  };

  // Browsers block audio until the visitor has interacted with the page, so a
  // blocked attempt arms a one-shot listener instead of failing silently.
  const playWhenAllowed = () => {
    if (!enabled() || read(sessionStorage, PLAYED_KEY) === "yes") return;
    let armed = false;
    const markPlayed = () => write(sessionStorage, PLAYED_KEY, "yes");
    play().then(markPlayed).catch(() => {
      if (armed) return;
      armed = true;
      const retry = () => {
        play().then(markPlayed).catch(() => {});
        window.removeEventListener("pointerdown", retry);
        window.removeEventListener("keydown", retry);
      };
      window.addEventListener("pointerdown", retry, { once: true });
      window.addEventListener("keydown", retry, { once: true });
    });
  };

  const syncToggles = () => {
    const on = enabled();
    document.querySelectorAll("[data-sound-toggle]").forEach((button) => {
      const fa = document.documentElement.lang === "fa";
      button.setAttribute("aria-pressed", on ? "true" : "false");
      button.setAttribute(
        "aria-label",
        on ? (fa ? "خاموش‌کردن صدای خوش‌آمد" : "Turn welcome sound off")
           : (fa ? "روشن‌کردن صدای خوش‌آمد" : "Turn welcome sound on"),
      );
      button.title = button.getAttribute("aria-label");
      button.textContent = on ? "🔊" : "🔇";
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    syncToggles();
    document.querySelectorAll("[data-sound-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const next = enabled() ? "off" : "on";
        write(localStorage, SOUND_KEY, next);
        syncToggles();
        // Turning it on doubles as a preview, and the click itself satisfies
        // the browser's gesture requirement.
        if (next === "on") play().catch(() => {});
      });
    });
    playWhenAllowed();
  });
})();
