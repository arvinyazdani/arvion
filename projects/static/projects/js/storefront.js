(function () {
  "use strict";
  document.querySelectorAll("[data-storefront]").forEach((root) => {
    const catalog = JSON.parse(root.querySelector("#storefront-catalog").textContent);
    const basket = window.RvionStoreModel.create(catalog);
    const fa = catalog.lang === "fa";
    const t = (a, b) => fa ? a : b;
    const money = (value) => new Intl.NumberFormat(fa ? "fa-IR" : "en-US").format(value) + t(" تومان", " Toman");
    const find = (selector) => root.querySelector(selector);
    const detail = find("[data-store-detail]"), cart = find("[data-store-cart]");
    const shipping = find("[data-store-shipping]");
    const detailError = find("[data-store-error]"), cartError = find("[data-store-cart-error]");
    const quantityError = t("تعداد باید عدد صحیح بین ۱ و موجودی باشد؛ تعداد قبلی در سبد را هم در نظر بگیرید.", "Use a whole quantity between 1 and available stock, including items already in the basket.");
    let product, mode = "basket", opener;
    function selectedVariant() {
      return product.variants.find((v) => v.color_id === find("[data-store-variant]").value && v.size_id === find("[data-store-size]").value);
    }
    function node(tag, text, className) {
      const element = document.createElement(tag);
      if (text !== undefined) element.textContent = text;
      if (className) element.className = className;
      return element;
    }
    function show(dialog, source) {
      opener = source;
      if (typeof dialog.showModal !== "function") {
        find("[data-store-status]").textContent = t("مرورگر شما این پیش‌نمایش تعاملی را پشتیبانی نمی‌کند؛ مشخصات کلی و سفارش طراحی در دسترس‌اند.", "This browser does not support the interactive preview. Product information and the design enquiry remain available.");
        return;
      }
      dialog.showModal();
      dialog.querySelector("h2").focus();
    }
    [detail, cart].forEach((dialog) => {
      dialog.querySelector("[data-store-close]").addEventListener("click", () => dialog.close());
      dialog.addEventListener("close", () => { if (opener?.isConnected) opener.focus(); });
    });
    function count() {
      find("[data-store-count]").textContent = new Intl.NumberFormat(fa ? "fa-IR" : "en-US").format(basket.totals(shipping.value).count);
    }
    function variantChanged() {
      const variant = selectedVariant();
      find("[data-store-price]").textContent = money(variant.price);
      find("[data-store-specs] dd:last-child").textContent = product.sizes.find((s) => s.id === variant.size_id).label;
      find("[data-store-stock]").textContent = variant.stock ? t("موجودی فرضی: ", "Sample stock: ") + new Intl.NumberFormat(fa ? "fa-IR" : "en-US").format(variant.stock) : t("این رنگ فعلاً ناموجود است؛ رنگ دیگری انتخاب کنید.", "This finish is unavailable. Choose another.");
      find("[data-store-add]").disabled = !variant.stock;
      find("[data-store-quantity]").max = variant.stock || 1;
      find("[data-store-detail-art]").style.setProperty("--store-finish", variant.color);
      detailError.textContent = "";
      find("[data-store-quantity]").removeAttribute("aria-invalid");
    }
    root.querySelectorAll("[data-store-product]").forEach((button) => button.addEventListener("click", () => {
      product = catalog.products.find((p) => p.id === button.dataset.storeProduct);
      find("#store-detail-title").textContent = product.name;
      find("[data-store-description]").textContent = product.description;
      find("[data-store-care]").textContent = product.care;
      const specs = find("[data-store-specs]"); specs.replaceChildren();
      product.specs.forEach((spec) => specs.append(node("dt", spec.label), node("dd", spec.value)));
      const art = button.closest("article").querySelector(".store-art").cloneNode(true);
      find("[data-store-detail-art]").replaceChildren(art);
      const options = find("[data-store-variant]"); options.replaceChildren();
      product.colors.forEach((color) => { const option = node("option", color.label); option.value = color.id; options.append(option); });
      const sizes = find("[data-store-size]"); sizes.replaceChildren();
      product.sizes.forEach((size) => { const option = node("option", size.label); option.value = size.id; sizes.append(option); });
      find("[data-store-quantity]").value = 1;
      variantChanged(); show(detail, button);
    }));
    find("[data-store-variant]").addEventListener("change", variantChanged);
    find("[data-store-size]").addEventListener("change", variantChanged);
    find("[data-store-add]").addEventListener("click", () => {
      try {
        basket.add(product.id, selectedVariant().id, Number(find("[data-store-quantity]").value));
        detailError.textContent = ""; find("[data-store-quantity]").removeAttribute("aria-invalid"); count();
        find("[data-store-stock]").textContent = t("به سبد نمایشی اضافه شد. می‌توانید سبد را ببینید یا رنگ دیگری انتخاب کنید.", "Added to the demo basket. View your basket or choose another finish.");
        find("[data-store-status]").textContent = product.name + t(" به سبد نمایشی اضافه شد.", " added to the demo basket.");
      } catch (_) { detailError.textContent = quantityError; find("[data-store-quantity]").setAttribute("aria-invalid", "true"); find("[data-store-quantity]").focus(); }
    });
    function renderCart() {
      const lines = basket.lines();
      find("#store-cart-title").textContent = mode === "review" ? t("مرور سفارش نمایشی", "Review demo order") : mode === "done" ? t("تجربه خرید کامل شد", "Your shopping walkthrough is complete") : t("سبد خرید نمایشی", "Demo shopping basket");
      const body = find("[data-store-cart-body]"); body.replaceChildren();
      cartError.textContent = "";
      if (mode === "done") body.append(node("p", t("هیچ مبلغی پرداخت و هیچ سفارش واقعی ثبت نشد. این همان مسیری است که می‌توانیم برای فروشگاه شما بسازیم. برای سفارش طراحی، به تنظیمات نمونه برگردید.", "No payment was taken and no real order was placed. This is a journey we can build for your shop. Return to the sample settings to enquire about its design."), "store-confirmation"));
      else if (!lines.length) body.append(node("p", t("سبد خالی است؛ یک محصول و رنگ دلخواه انتخاب کنید.", "Your basket is empty. Choose a product and finish."), "store-empty"));
      else lines.forEach((line) => {
        const row = node("div", undefined, "store-cart-line");
        const text = node("div"); text.append(node("h3", line.product.name), node("p", line.variant.label + " · " + money(line.variant.price)));
        row.append(text);
        if (mode === "basket") {
          const label = node("label", t("تعداد", "Quantity"), "store-field");
          const input = node("input"); input.type = "number"; input.min = 1; input.max = line.variant.stock; input.value = line.quantity; input.inputMode = "numeric";
          cartError.id = "store-cart-quantity-error"; input.setAttribute("aria-describedby", cartError.id);
          input.addEventListener("input", () => {
            try {
              basket.setQuantity(line.key, Number(input.value)); count(); updateTotals();
              row.querySelector("strong").textContent = money(Number(input.value) * line.variant.price);
              cartError.textContent = ""; input.removeAttribute("aria-invalid"); find("[data-store-next]").disabled = false;
            } catch (_) { cartError.textContent = quantityError; input.setAttribute("aria-invalid", "true"); find("[data-store-next]").disabled = true; }
          });
          input.addEventListener("change", () => {
            if (find("[data-store-next]").disabled) {
              input.value = basket.lines().find((item) => item.key === line.key).quantity;
              input.removeAttribute("aria-invalid");
              find("[data-store-next]").disabled = false;
            }
          });
          row.dataset.lineKey = line.key; label.append(input); row.append(label);
          const remove = node("button", t("حذف", "Remove"), "store-remove"); remove.type = "button"; remove.setAttribute("aria-label", t("حذف ", "Remove ") + line.product.name);
          remove.addEventListener("click", () => { basket.remove(line.key); count(); renderCart(); find("#store-cart-title").focus(); }); row.append(remove);
        } else row.append(node("span", t("تعداد: ", "Quantity: ") + new Intl.NumberFormat(fa ? "fa-IR" : "en-US").format(line.quantity)));
        row.append(node("strong", money(line.quantity * line.variant.price))); body.append(row);
      });
      if (mode !== "done" && find(".store-shipping").hidden) body.append(node("p", t("امکان پرداخت در تنظیمات نمونه خاموش است؛ برای امتحان مرور سفارش آن را روشن کنید.", "Payment is off in the sample settings. Enable it to try order review."), "store-notice"));
      const summary = find("[data-store-totals]"); summary.replaceChildren(); summary.hidden = mode === "done" || !lines.length;
      if (!summary.hidden) updateTotals();
      if (mode === "review") body.append(node("p", catalog.shipping.find((s) => s.id === shipping.value).label, "store-notice"));
      find(".store-shipping").style.display = mode === "basket" && lines.length ? "" : "none";
      const next = find("[data-store-next]"); next.disabled = !lines.length; next.style.display = mode === "done" ? "none" : "";
      next.textContent = mode === "review" ? t("پایان تجربه · بدون پرداخت", "Finish walkthrough · no payment") : t("مرور سفارش نمایشی", "Review demo order");
      find("[data-store-return]").textContent = mode === "review" ? t("بازگشت و ویرایش سبد", "Back & edit basket") : mode === "done" ? t("بازگشت به نمونه و تنظیمات", "Return to sample & settings") : t("ادامه دیدن محصولات", "Keep browsing");
    }
    function updateTotals() {
      const totals = basket.totals(shipping.value), summary = find("[data-store-totals]");
      summary.replaceChildren();
      [[t("جمع محصولات", "Subtotal"), totals.subtotal], [t("ارسال", "Delivery"), totals.shipping], [t("مجموع", "Total"), totals.total]].forEach(([label, value]) => summary.append(node("dt", label), node("dd", money(value))));
    }
    function openBasket(source) { mode = "basket"; renderCart(); show(cart, source); }
    find("[data-store-basket]").addEventListener("click", (event) => openBasket(event.currentTarget));
    find("[data-store-detail-basket]").addEventListener("click", () => { detail.close(); openBasket(find("[data-store-basket]")); });
    shipping.addEventListener("change", renderCart);
    find("[data-store-return]").addEventListener("click", () => {
      if (mode === "review") { mode = "basket"; renderCart(); find("#store-cart-title").focus(); }
      else { const done = mode === "done"; cart.close(); if (done) root.closest("[data-demo-configurator]").querySelector("[data-config-open], [data-demo-back]")?.click(); }
    });
    find("[data-store-next]").addEventListener("click", () => {
      if (!basket.lines().length) return;
      if (mode === "review") { mode = "done"; basket.clear(); count(); } else mode = "review";
      renderCart(); find("#store-cart-title").focus();
    });
    // Capability toggles must not leave a hidden catalogue's dialog open.
    function syncCapabilities() {
      const disabled = find('[data-feature-module="catalog"]').hidden;
      find("[data-store-basket]").disabled = disabled;
      if (find(".store-shipping").hidden) shipping.value = "pickup";
      if (disabled) { if (detail.open) detail.close(); if (cart.open) cart.close(); }
      else if (cart.open) renderCart();
    }
    new MutationObserver((mutations) => {
      if (mutations.some((mutation) => mutation.target.hasAttribute("data-feature-module"))) syncCapabilities();
    }).observe(root.closest("[data-demo-configurator]"), { attributes: true, attributeFilter: ["hidden"], subtree: true });
    syncCapabilities();
    count();
  });
})();
