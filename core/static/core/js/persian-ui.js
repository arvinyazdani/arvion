(() => {
  const root = document.documentElement;
  const toFa = value => value.replace(/[0-9]/g, digit => "۰۱۲۳۴۵۶۷۸۹"[digit]);
  const toAscii = value => value
    .replace(/[۰-۹]/g, digit => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)))
    .replace(/[٠-٩]/g, digit => String("٠١٢٣٤٥٦٧٨٩".indexOf(digit)))
    .replace(/٫/g, ".").replace(/٬/g, ",");

  document.querySelectorAll("strong, dd, .price").forEach(element => {
    if (element.closest("[data-ascii]")) return;
    element.childNodes.forEach(node => {
      if (node.nodeType !== Node.TEXT_NODE) return;
      node.nodeValue = node.nodeValue.replace(/\b\d{4,}(?=\s*(?:ریال|IRR))/g, value =>
        Number(value).toLocaleString("en-US")
      );
    });
  });

  if (root.lang === "fa") {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (!node.parentElement?.closest("script, style, code, pre, textarea, [data-ascii]") && /[0-9]/.test(node.nodeValue)) {
        node.nodeValue = toFa(node.nodeValue);
      }
    }
  } else {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (!node.parentElement?.closest("script, style, code, pre, textarea, [data-persian-digits]") && /[۰-۹٠-٩]/.test(node.nodeValue)) {
        node.nodeValue = toAscii(node.nodeValue);
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
