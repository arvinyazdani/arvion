(() => {
  const root = document.documentElement;
  const toFa = value => value.replace(/[0-9]/g, digit => "۰۱۲۳۴۵۶۷۸۹"[digit]);
  const toAscii = value => value
    .replace(/[۰-۹]/g, digit => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)))
    .replace(/[٠-٩]/g, digit => String("٠١٢٣٤٥٦٧٨٩".indexOf(digit)))
    .replace(/٫/g, ".").replace(/٬/g, ",");

  if (root.lang === "fa") {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (!node.parentElement?.closest("script, style, code, pre, textarea, [data-ascii]") && /[0-9]/.test(node.nodeValue)) {
        node.nodeValue = toFa(node.nodeValue);
      }
    }
  }

  document.querySelectorAll('input[type="number"]').forEach(input => {
    input.type = "text";
    input.inputMode = input.step && input.step !== "1" ? "decimal" : "numeric";
    input.dataset.numericInput = "true";
  });

  document.querySelectorAll("form").forEach(form => form.addEventListener("submit", () => {
    form.querySelectorAll('[data-numeric-input="true"], input[type="tel"], input[name*="phone"]').forEach(input => {
      input.value = toAscii(input.value);
    });
  }));
})();
