(() => {
  const KEYS = {
    welcome: "rvion-sound-welcome",
    notification: "rvion-sound-notification",
  };
  const PLAYED_KEY = "rvion-welcome-sound-played-v2";
  const read = (storage, key) => { try { return storage.getItem(key); } catch (error) { return null; } };
  const write = (storage, key, value) => { try { storage.setItem(key, value); } catch (error) {} };
  const enabled = (kind) => read(localStorage, KEYS[kind]) !== "off";
  let context;

  const audioContext = () => {
    if (!context) {
      const Context = window.AudioContext || window.webkitAudioContext;
      if (Context) context = new Context();
    }
    return context;
  };

  const tone = (frequency, start, duration, gainValue) => {
    const ctx = audioContext();
    if (!ctx || ctx.state !== "running") return false;
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(frequency, start);
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(gainValue, start + 0.025);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
    oscillator.connect(gain).connect(ctx.destination);
    oscillator.start(start);
    oscillator.stop(start + duration + 0.02);
    return true;
  };

  const playWelcome = async () => {
    if (!enabled("welcome") || read(sessionStorage, PLAYED_KEY) === "yes") return false;
    const ctx = audioContext();
    if (!ctx) return false;
    if (ctx.state === "suspended") await ctx.resume().catch(() => {});
    const start = ctx.currentTime + 0.01;
    if (!tone(523.25, start, 0.22, 0.032)) return false;
    tone(659.25, start + 0.09, 0.24, 0.025);
    write(sessionStorage, PLAYED_KEY, "yes");
    return true;
  };

  const playNotification = async (priority = "normal") => {
    if (!enabled("notification")) return false;
    const ctx = audioContext();
    if (!ctx) return false;
    if (ctx.state === "suspended") await ctx.resume().catch(() => {});
    const start = ctx.currentTime + 0.006;
    const urgent = priority === "critical" || priority === "high";
    if (!tone(urgent ? 740 : 660, start, 0.14, urgent ? 0.045 : 0.032)) return false;
    if (urgent) tone(880, start + 0.11, 0.12, 0.03);
    return true;
  };

  const sync = () => {
    const fa = document.documentElement.lang === "fa";
    document.querySelectorAll("[data-sound-toggle]").forEach((button) => {
      const kind = button.dataset.soundToggle || "all";
      const on = kind === "all" ? enabled("welcome") && enabled("notification") : enabled(kind);
      button.setAttribute("aria-pressed", String(on));
      if (!button.querySelector("b")) button.textContent = on ? "♪" : "×";
      const state = button.querySelector(`[data-sound-state="${kind}"]`);
      if (state) state.textContent = on ? (fa ? "روشن" : "On") : (fa ? "خاموش" : "Off");
      const label = on ? (fa ? "خاموش‌کردن صدا" : "Turn sound off") : (fa ? "روشن‌کردن صدا" : "Turn sound on");
      button.setAttribute("aria-label", label);
      button.title = label;
    });
  };

  const toggle = (kind) => {
    const targets = kind === "all" ? ["welcome", "notification"] : [kind];
    const turnOn = targets.some((target) => !enabled(target));
    targets.forEach((target) => write(localStorage, KEYS[target], turnOn ? "on" : "off"));
    sync();
    if (turnOn) (kind === "notification" ? playNotification() : playWelcome()).catch(() => {});
  };

  window.RvionSounds = { playWelcome, playNotification, enabled };

  const ready = () => {
    sync();
    document.querySelectorAll("[data-sound-toggle]").forEach((button) => {
      button.addEventListener("click", () => toggle(button.dataset.soundToggle || "all"));
    });
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ready, { once: true });
  else ready();

  // Try immediately, before images and secondary scripts finish. If autoplay
  // is blocked, only the first interaction in the next four seconds may play
  // it; an unrelated late click must never trigger a surprise welcome sound.
  playWelcome().catch(() => {});
  const retry = () => playWelcome().catch(() => {});
  window.addEventListener("pointerdown", retry, { once: true, passive: true });
  window.addEventListener("keydown", retry, { once: true });
  window.setTimeout(() => {
    window.removeEventListener("pointerdown", retry);
    window.removeEventListener("keydown", retry);
  }, 4000);
})();
