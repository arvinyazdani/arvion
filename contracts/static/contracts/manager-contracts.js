(() => {
  const copyStatus = document.querySelector("[data-copy-status]");
  document.querySelectorAll("[data-copy-target]").forEach(button => {
    button.addEventListener("click", async () => {
      const input = document.getElementById(button.dataset.copyTarget);
      if (!input) return;
      try {
        await navigator.clipboard.writeText(input.value);
        if (copyStatus) copyStatus.textContent = document.documentElement.lang === "fa" ? "لینک مشتری کپی شد." : "Customer link copied.";
      } catch (error) {
        input.focus();
        input.select();
        if (copyStatus) copyStatus.textContent = document.documentElement.lang === "fa" ? "کپی خودکار انجام نشد؛ لینک انتخاب شده است." : "Automatic copy failed; the link is selected.";
      }
    });
  });

  document.querySelectorAll("[data-print-contract]").forEach(button => {
    button.addEventListener("click", () => window.print());
  });
})();
