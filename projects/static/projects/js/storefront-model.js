/* A transient demo basket, not an order or payment service. */
(function (scope) {
  "use strict";
  function create(catalog) {
    const items = new Map();
    function resolve(productId, variantId) {
      const product = catalog.products.find((p) => p.id === productId);
      const variant = product?.variants.find((v) => v.id === variantId);
      if (!variant || !Number.isSafeInteger(variant.price) || variant.price < 0) throw new Error("invalid");
      return { product, variant, key: product.id + ":" + variant.id };
    }
    function validate(quantity, stock) {
      if (!Number.isSafeInteger(quantity) || quantity < 1 || quantity > stock) throw new Error("quantity");
    }
    return {
      add(productId, variantId, quantity) {
        const line = resolve(productId, variantId);
        const next = (items.get(line.key)?.quantity || 0) + quantity;
        validate(quantity, line.variant.stock);
        validate(next, line.variant.stock);
        items.set(line.key, { ...line, quantity: next });
      },
      setQuantity(key, quantity) {
        const line = items.get(key);
        if (!line) throw new Error("invalid");
        validate(quantity, line.variant.stock);
        items.set(key, { ...line, quantity });
      },
      remove(key) { items.delete(key); },
      lines() { return Array.from(items.values(), (line) => ({ ...line })); },
      totals(shippingId) {
        const shipping = catalog.shipping.find((s) => s.id === shippingId);
        if (!shipping) throw new Error("invalid");
        const subtotal = Array.from(items.values()).reduce((sum, line) => sum + line.quantity * line.variant.price, 0);
        const count = Array.from(items.values()).reduce((sum, line) => sum + line.quantity, 0);
        const fee = count ? shipping.fee : 0;
        return { subtotal, shipping: fee, total: subtotal + fee, count };
      },
      clear() { items.clear(); },
    };
  }
  if (typeof module !== "undefined" && module.exports) module.exports = { create };
  else scope.RvionStoreModel = { create };
})(typeof window !== "undefined" ? window : globalThis);
