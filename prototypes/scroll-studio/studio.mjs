import {PALETTES, initialState, updateChoice, activeChapter, addItem} from './model.mjs';

const en = {
  skip:'Skip to your design summary', prototype:'Design preview · no real order is placed', display:'Display preferences', motionOff:'Reduce motion', motionOn:'Motion reduced', themeLight:'Light mode', themeDark:'Dark mode', kicker:'The Rvion live studio', hero:'From an idea,<br>to a site of your own.', lead:'Scroll to see a shop take shape. Choose its colour and style yourself. Your changes happen here, live.', explore:'Explore the story', skipShort:'Go straight to settings & summary', story:'From idea to enquiry',
  c1title:'First, your business.', c1text:'A homeware shop. Products, collections and a recognisable identity come together—not an empty website mockup.', c1detail:'The brand and products in this sample are fictional.', nextIdentity:'Next: your identity ↓', c2title:'Now, your signature.', c2text:'Olive or blue? Quiet and minimal or editorial? More than a colour changes: the composition and character change too.', chooseColor:'Try a colour', olive:'Olive', cobalt:'Blue', clay:'Clay', editDesign:'Change colour & style', c3title:'Good looks aren’t enough.', c3text:'Open a product, explore its details and add it to a sample basket. A website should work, not just look good.', detailCapability:'Readable, touch-friendly details', basketCapability:'A basket with clear feedback', mobileCapability:'A layout made for phones', tryProduct:'Try a product', c4title:'Your choices. A clear start.', c4text:'Colour, style and features become one brief. In the connected version, these choices will travel with your enquiry to Rvion.', boundary:'This is an isolated demo: no order, payment or customer information is saved to the system.', seeSummary:'See my design summary', preview:'Storefront preview', live:'Live preview', storeName:'Noor Home', storeNav:'New collection', basket:'Basket', collection:'Simple objects. Slower living.', storeTitle:'A place to<br>live a little slower.', storeLead:'Wood, light and thoughtful shapes that make a house a home.', viewCollection:'Explore the collection', room:'Original illustration of a wooden chair, lamp and vase', artLabel:'Fictional product illustration', chairName:'Ara chair', chairMaterial:'Wood & fabric', lampName:'Sepid lamp', lampMaterial:'Light & texture', summaryPreview:'Your chosen design is ready to review.', sampleOnly:'Fictional shop · no real purchases', yourDesign:'Your chosen design', finishTitle:'This time, you chose.', finishLead:'A concrete starting point for your website brief—not a final quote or a build commitment.', business:'Business', businessValue:'Homeware shop', color:'Colour', style:'Style', features:'Features', review:'Review sample enquiry', notSent:'Nothing is sent by this demo. Your choices reset when you close the page.', footer:'A design and usability prototype, separate from the live website.', backTop:'Back to top ↑', customize:'Customise this design', summary:'Summary', liveSettings:'Live changes', settingsTitle:'Make it yours.', close:'Close', editorial:'Editorial', editorialHelp:'Large imagery, narrative & generous space', minimal:'Minimal', minimalHelp:'Quiet, product-led composition', industrial:'Industrial', industrialHelp:'Strong lines & technical structure', catalog:'Product catalogue', basketFeature:'Sample basket', newsletter:'Newsletter section', settingsNote:'Changes apply immediately. Closing this panel does not undo them.', reset:'Reset design', seeDesign:'View design', material:'Material', purpose:'Status', illustrative:'Illustrative details, fictional product', addBasket:'Add to sample basket', cartTitle:'Your sample basket', noCheckout:'This basket demonstrates the experience. No payment or real purchase is possible.', clearCart:'Empty sample basket', enquiryTitle:'Sample enquiry preview', enquiryNote:'In the connected version, these choices will enter the enquiry form. No personal information or real order is collected here.', returnDesign:'Return to design', emptyCart:'Your basket is empty. Try opening a product.', added:'Added to the sample basket.', basketOff:'Enable the catalogue and basket in settings to try this action.', noFeatures:'No features selected', updated:'Design updated.', resetDone:'Design reset. Your sample basket is empty.', chapter0:'Your business', chapter1:'Your identity', chapter2:'The experience', chapter3:'Your project', chairDescription:'An illustrative lounge chair with a wooden frame and a soft fabric seat. These are sample specifications, not a product listing.', lampDescription:'An illustrative standing lamp with a woven shade. This sample demonstrates product detail and basket interactions.', newsletterPreview:'Newsletter preview: a place for the shop’s next collection.', noscript:'You can read this preview without JavaScript. Colour changes and basket interactions require JavaScript. No real order is placed.'
};
const faExtra = {emptyCart:'سبد شما خالی است. یک محصول را امتحان کنید.', added:'به سبد نمونه اضافه شد.', basketOff:'برای امتحان این بخش، کاتالوگ و سبد را از تنظیمات روشن کنید.', noFeatures:'امکاناتی انتخاب نشده', updated:'طرح به‌روز شد.', resetDone:'طرح بازنشانی و سبد نمونه خالی شد.', chapter0:'شناخت کسب‌وکار', chapter1:'هویت شما', chapter2:'تجربه استفاده', chapter3:'شروع پروژه', chairDescription:'یک صندلی نمایشی با قاب چوبی و نشیمن پارچه‌ای. این مشخصات برای نمونه طراحی است و محصول واقعی برای فروش نیست.', lampDescription:'یک چراغ ایستاده نمایشی با کلاهک بافته‌شده. برای امتحان جزئیات محصول و سبد نمونه طراحی شده است.', newsletterPreview:'نمونه بخش خبرنامه: جایی برای معرفی مجموعه بعدی فروشگاه.'};
const fa = {...faExtra};
document.querySelectorAll('[data-i18n]').forEach(el => {fa[el.dataset.i18n] = el.innerHTML;});
const params = new URLSearchParams(location.search);
const lang = params.get('lang') === 'en' ? 'en' : 'fa';
const t = key => (lang === 'en' ? en : fa)[key] || '';
en.notSent = 'Nothing is sent. Your design can be restored from this demo URL; the basket resets on reload.';
document.documentElement.lang = lang;
document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr';
document.title = lang === 'fa' ? 'استودیوی زنده آرویون — دموی طراحی' : 'Rvion live studio — design prototype';
document.querySelectorAll('[data-i18n]').forEach(el => {el.innerHTML = t(el.dataset.i18n);});
document.querySelectorAll('[data-label]').forEach(el => el.setAttribute('aria-label', t(el.dataset.label)));
const number = value => new Intl.NumberFormat(lang === 'fa' ? 'fa-IR' : 'en-US').format(value);
const counter = value => `${number(value).padStart(2, lang === 'fa' ? '۰' : '0')} / ${number(4).padStart(2, lang === 'fa' ? '۰' : '0')}`;
document.querySelectorAll('[data-number]').forEach(el => {el.textContent = counter(+el.dataset.number);});
document.getElementById('language').textContent = lang === 'fa' ? 'English' : 'فارسی';
document.getElementById('language').lang = lang === 'fa' ? 'en' : 'fa';

let state = initialState(params);
let cart = {};
let currentProduct = 'chair';
let active = 0;
let opener = null;
const stage = document.querySelector('.preview-rail .stage');
// Read-only copies of the scene share one in-memory state. No duplicate controls/ids.
document.querySelectorAll('[data-mobile]').forEach((slot, index) => {
  const copy = stage.cloneNode(true);
  copy.dataset.scene = String(index);
  copy.querySelectorAll('[id]').forEach(el => {
    const original = el.id;
    el.id = `${original}-scene-${index}`;
    copy.querySelectorAll('[fill]').forEach(shape => {
      if (shape.getAttribute('fill') === `url(#${original})`) shape.setAttribute('fill', `url(#${el.id})`);
    });
    copy.querySelectorAll('[stroke]').forEach(shape => {
      if (shape.getAttribute('stroke') === `url(#${original})`) shape.setAttribute('stroke', `url(#${el.id})`);
    });
  });
  slot.append(copy);
});
document.documentElement.dataset.enhanced = 'true';
document.querySelectorAll('button:disabled,input:disabled').forEach(el => {el.disabled = false;});

function announce(text) {document.getElementById('status').textContent = text;}
function summaryNode() {
  const dl = document.createElement('dl');
  const values = {business:t('businessValue'), color:t(state.palette), style:t(state.style), features:state.features.map(x => t(x === 'basket' ? 'basketFeature' : x)).join(lang === 'fa' ? '، ' : ', ') || t('noFeatures')};
  Object.entries(values).forEach(([key, value]) => {
    const row = document.createElement('div'); const dt = document.createElement('dt'); const dd = document.createElement('dd');
    dt.textContent = t(key); dd.textContent = value; row.append(dt, dd); dl.append(row);
  });
  return dl;
}
function render() {
  document.querySelectorAll('.stage').forEach(scene => {
    const colors = PALETTES[state.palette];
    scene.style.setProperty('--sample-accent', colors[0]); scene.style.setProperty('--sample-tint', colors[1]); scene.style.setProperty('--sample-line', colors[2]);
    const store = scene.querySelector('[data-store]'); store.dataset.style = state.style;
    store.dataset.catalog = String(state.features.includes('catalog')); store.dataset.basket = String(state.features.includes('basket') && state.features.includes('catalog'));
    let newsletter = store.querySelector('.newsletter-demo');
    if (state.features.includes('newsletter')) {
      if (!newsletter) {newsletter = document.createElement('div'); newsletter.className = 'newsletter-demo'; store.querySelector('.store-footer').before(newsletter);}
      newsletter.textContent = t('newsletterPreview');
    } else newsletter?.remove();
    scene.querySelector('[data-style-label]').textContent = t(state.style);
    scene.querySelector('[data-scene-counter]').textContent = counter(+scene.dataset.scene + 1);
    scene.querySelector('[data-scene-label]').textContent = t('chapter' + scene.dataset.scene);
    scene.querySelector('.scene-progress i').style.width = `${(+scene.dataset.scene + 1) * 25}%`;
    let selectionCaption = store.querySelector('.selection-caption');
    if (!selectionCaption) {selectionCaption = document.createElement('span'); selectionCaption.className = 'selection-caption'; store.querySelector('.store-summary').append(selectionCaption);}
    selectionCaption.textContent = `${t(state.palette)} / ${t(state.style)}`;
    scene.querySelectorAll('[data-open="product"],[data-open="lamp"]').forEach(button => {
      button.disabled = !state.features.includes('catalog');
      button.title = button.disabled ? t('basketOff') : '';
    });
  });
  document.querySelectorAll('input[name="palette"],input[name="quick-palette"]').forEach(input => {input.checked = input.value === state.palette;});
  document.querySelectorAll('input[name="style"]').forEach(input => {input.checked = input.value === state.style;});
  document.querySelectorAll('input[name="feature"]').forEach(input => {input.checked = state.features.includes(input.value);});
  document.querySelector('[data-summary="palette"]').textContent = t(state.palette);
  document.querySelector('[data-summary="style"]').textContent = t(state.style);
  document.querySelector('[data-summary="features"]').textContent = state.features.map(x => t(x === 'basket' ? 'basketFeature' : x)).join(lang === 'fa' ? '، ' : ', ') || t('noFeatures');
  document.querySelectorAll('[data-cart-count]').forEach(el => {el.textContent = number(Object.values(cart).reduce((a, b) => a + b, 0));});
  const allowed = state.features.includes('catalog') && state.features.includes('basket');
  document.getElementById('add-cart').disabled = !allowed;
  if (!allowed) {
    document.getElementById('product-feedback').textContent = t('basketOff');
    if (document.getElementById('cart').open) document.getElementById('cart').close();
  }
  const url = new URL(location.href);
  url.search = new URLSearchParams({lang, palette:state.palette, style:state.style, features:state.features.join(',')}).toString();
  document.getElementById('language').href = '?' + new URLSearchParams({lang:lang === 'fa' ? 'en' : 'fa', palette:state.palette, style:state.style, features:state.features.join(',')});
  history.replaceState(null, '', url);
}
function renderCart() {
  const container = document.getElementById('cart-items'); container.replaceChildren();
  Object.entries(cart).forEach(([key, quantity]) => {
    const row = document.createElement('div'); row.className = 'cart-row';
    const title = document.createElement('span'); title.textContent = t(key === 'chair' ? 'chairName' : 'lampName');
    const amount = document.createElement('strong'); amount.textContent = `${number(quantity)} ×`; row.append(title, amount); container.append(row);
  });
  if (!container.children.length) {const empty = document.createElement('p'); empty.textContent = t('emptyCart'); container.append(empty);}
  document.getElementById('clear-cart').disabled = Object.keys(cart).length === 0;
}
function openDialog(name, trigger) {
  opener = trigger;
  if (name === 'product' || name === 'lamp') {
    if (!state.features.includes('catalog')) return;
    currentProduct = name === 'lamp' ? 'lamp' : 'chair'; name = 'product';
    document.getElementById('product-title').textContent = t(currentProduct === 'chair' ? 'chairName' : 'lampName');
    document.getElementById('product-description').textContent = t(currentProduct === 'chair' ? 'chairDescription' : 'lampDescription');
    document.getElementById('material-value').textContent = t(currentProduct === 'chair' ? 'chairMaterial' : 'lampMaterial');
    const art = document.getElementById('product').querySelector('.product-dialog-art');
    const sceneArt = stage.querySelector('.room-art svg').cloneNode(true);
    // The detail illustration keeps context rather than implying real photography.
    sceneArt.querySelectorAll('[id]').forEach(el => {
      const previous = el.id; el.id = previous + '-detail';
      sceneArt.querySelectorAll('[fill],[stroke]').forEach(shape => ['fill','stroke'].forEach(attr => {
        if (shape.getAttribute(attr) === `url(#${previous})`) shape.setAttribute(attr, `url(#${el.id})`);
      }));
    });
    art.replaceChildren(sceneArt);
    document.getElementById('product-feedback').textContent = state.features.includes('basket') ? '' : t('basketOff');
  }
  if (name === 'cart') {
    if (!state.features.includes('basket') || !state.features.includes('catalog')) return;
    renderCart();
  }
  if (name === 'enquiry') document.getElementById('enquiry-summary').replaceChildren(summaryNode());
  const dialog = document.getElementById(name);
  if (dialog && !dialog.open) {dialog.showModal(); dialog.querySelector('[data-close]')?.focus();}
}
document.addEventListener('click', event => {
  const trigger = event.target.closest('[data-open]'); if (trigger && !trigger.disabled) openDialog(trigger.dataset.open, trigger);
  const close = event.target.closest('[data-close]'); if (close) close.closest('dialog').close();
});
document.querySelectorAll('dialog').forEach(dialog => {
  dialog.addEventListener('close', () => opener?.focus());
  dialog.addEventListener('keydown', event => {
    if (event.key !== 'Tab') return;
    const controls = [...dialog.querySelectorAll('button:not(:disabled),input:not(:disabled),a[href],[tabindex="0"]')].filter(el => el.getClientRects().length);
    const first = controls[0]; const last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) {event.preventDefault(); last?.focus();}
    else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first?.focus();}
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
});
document.addEventListener('change', event => {
  const input = event.target;
  if (input.name === 'palette' || input.name === 'quick-palette') state = updateChoice(state, 'palette', input.value);
  else if (input.name === 'style') state = updateChoice(state, 'style', input.value);
  else if (input.name === 'feature') state = updateChoice(state, 'features', [...document.querySelectorAll('input[name="feature"]:checked')].map(x => x.value));
  else return;
  render(); announce(t('updated'));
});
document.getElementById('reset').addEventListener('click', () => {state = initialState(); cart = {}; render(); announce(t('resetDone'));});
document.getElementById('add-cart').addEventListener('click', () => {
  if (!state.features.includes('basket') || !state.features.includes('catalog')) return;
  if ((cart[currentProduct] || 0) >= 9) {
    document.getElementById('product-feedback').textContent = lang === 'fa' ? 'برای این محصول، سقف سبد نمایشی ۹ عدد است.' : 'This sample basket allows up to 9 of this product.';
    return;
  }
  cart = addItem(cart, currentProduct); render(); document.getElementById('product-feedback').textContent = t('added');
});
document.getElementById('clear-cart').addEventListener('click', () => {cart = {}; renderCart(); render();});
document.getElementById('review').addEventListener('click', event => openDialog('enquiry', event.currentTarget));
document.getElementById('theme').addEventListener('click', event => {
  const dark = document.documentElement.dataset.theme === 'dark'; document.documentElement.dataset.theme = dark ? 'light' : 'dark';
  event.currentTarget.textContent = t(dark ? 'themeDark' : 'themeLight');
});
const reducedQuery = matchMedia('(prefers-reduced-motion: reduce)');
let manualReduced = false;
function motionPreference() {
  const reduced = manualReduced || reducedQuery.matches;
  document.documentElement.dataset.reduced = String(reduced);
  const button = document.getElementById('motion'); button.setAttribute('aria-pressed', String(reduced)); button.textContent = t(reduced ? 'motionOn' : 'motionOff');
}
document.getElementById('motion').addEventListener('click', () => {manualReduced = !manualReduced; motionPreference();});
reducedQuery.addEventListener('change', motionPreference); motionPreference();
let scheduled = false;
function updateScene() {
  scheduled = false;
  const chapters = [...document.querySelectorAll('[data-chapter]')];
  const next = activeChapter(chapters.map(el => el.getBoundingClientRect()), innerHeight);
  if (active !== next) {active = next; stage.dataset.scene = String(active); chapters.forEach((el, index) => el.classList.toggle('is-active', index === active)); render();}
}
addEventListener('scroll', () => {if (!scheduled && !document.hidden) {scheduled = true; requestAnimationFrame(updateScene);}}, {passive:true});
addEventListener('resize', () => {if (!scheduled) {scheduled = true; requestAnimationFrame(updateScene);}});
render(); updateScene();
