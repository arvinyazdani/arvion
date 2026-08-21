(() => {
  const button = document.querySelector("[data-export-share]");
  const status = document.querySelector("[data-export-status]");
  const documentText = document.querySelector(".export-preview__document")?.textContent?.trim() || "";
  if (!button || !documentText) return;

  const fa = document.documentElement.lang === "fa";
  const filename = document.querySelector(".export-preview__meta bdi")?.textContent?.trim() || "rvion-export.txt";
  const title = document.querySelector("#export-preview-title")?.textContent?.trim() || "Rvion export";
  const announce = (message, isError = false) => {
    if (!status) return;
    status.textContent = message;
    status.dataset.tone = isError ? "error" : "success";
  };

  button.addEventListener("click", async () => {
    if (button.getAttribute("aria-busy") === "true") return;
    button.setAttribute("aria-busy", "true");
    try {
      const file = new File([`${documentText}\n`], filename, { type: "text/plain;charset=utf-8" });
      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ title, files: [file] });
        announce(fa ? "فایل برای اشتراک‌گذاری آماده شد." : "The file is ready to share.");
      } else if (navigator.share) {
        await navigator.share({ title, text: documentText });
        announce(fa ? "متن برای اشتراک‌گذاری آماده شد." : "The text is ready to share.");
      } else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(documentText);
        announce(fa ? "متن کپی شد؛ حالا می‌توانید آن را ارسال کنید." : "Text copied. You can paste it into another app.");
      } else {
        throw new Error("share_unavailable");
      }
    } catch (error) {
      if (error?.name !== "AbortError") {
        announce(fa ? "اشتراک‌گذاری در این دستگاه ممکن نشد؛ از دکمه دانلود استفاده کنید." : "Sharing is unavailable on this device. Use Download instead.", true);
      }
    } finally {
      button.removeAttribute("aria-busy");
    }
  });
})();
