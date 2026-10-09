export const PALETTES = Object.freeze({olive: ['#3e5648', '#e9ece4', '#cdd5c8'], cobalt: ['#294c89', '#e8edf5', '#c7d3e6'], clay: ['#864933', '#f1e8df', '#dacabe']});
export const STYLES = Object.freeze(['editorial', 'minimal', 'industrial']);
export const FEATURES = Object.freeze(['catalog', 'basket', 'newsletter']);
export function initialState(params = new URLSearchParams()) {
  return {palette: Object.hasOwn(PALETTES, params.get('palette')) ? params.get('palette') : 'olive', style: STYLES.includes(params.get('style')) ? params.get('style') : 'editorial', features: params.has('features') ? FEATURES.filter(x => params.get('features').split(',').includes(x)) : ['catalog', 'basket']};
}
export function updateChoice(state, key, value) {
  if (key === 'palette' && Object.hasOwn(PALETTES, value)) return {...state, palette: value};
  if (key === 'style' && STYLES.includes(value)) return {...state, style: value};
  if (key === 'features' && Array.isArray(value)) return {...state, features: FEATURES.filter(x => value.includes(x))};
  return state;
}
export function activeChapter(rects, viewportHeight) {
  const point = viewportHeight * .42;
  const containing = rects.findIndex(rect => rect.top <= point && rect.bottom > point);
  if (containing >= 0) return containing;
  return rects.reduce((best, rect, index) => Math.abs(rect.top - point) < Math.abs(rects[best].top - point) ? index : best, 0);
}
export function addItem(cart, item) {
  if (!['chair', 'lamp'].includes(item)) return cart;
  return {...cart, [item]: Math.min(9, (cart[item] || 0) + 1)};
}
