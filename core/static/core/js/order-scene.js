/* /start/ only, progressively enhanced after load. Private brand stays in memory. */
(function () {
  'use strict';
  const boot = () => {
    if (document.documentElement.dataset.pathIntro === 'active') {document.addEventListener('rvion:path-intro-done', boot, {once: true}); return;}
    const data = document.getElementById('order-wizard-data');
    const form = document.getElementById('os-handoff');
    if (!data || !form || !window.RvionOrderState || !window.RvionOrderMotion || !window.RvionOrderArt || document.querySelector('[data-os-error]')) return;
    const catalogue = JSON.parse(data.textContent), api = window.RvionOrderState, fa = catalogue.lang === 'fa';
    const say = (a, b) => fa ? a : b;
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const clock = window.RvionOrderMotion.create(window), art = window.RvionOrderArt;
    let state = api.create(catalogue), paused = false, closed = false, preview = 0, introducing = false;
    const headings = [say('رنگِ شما، شروعِ داستان', 'Your colour. Your starting point.'), say('حال‌وهوای سایت را انتخاب کنید', 'Find your visual character.'), say('برای چه کسب‌وکاری می‌سازیم؟', 'What are we building for?'), say('چه امکاناتی لازم دارید؟', 'What should your website do?'), say('این نقطهٔ شروع شماست', 'Your starting point is ready.')];
    const stepNames = [say('رنگ', 'Colour'), say('سبک', 'Look'), say('موضوع', 'Topic'), say('امکانات', 'Features'), say('مرور', 'Review')];
    const copy = {
      ecommerce: [say('ویترینی برای انتخاب بهتر', 'A storefront worth exploring'), say('محصولات را پیدا کنید، مقایسه کنید و انتخاب کنید.', 'Discover, compare and choose products.'), say('کالکشن جدید', 'New collection')],
      restaurant: [say('طعم یک تجربهٔ تازه', 'A taste of something different'), say('منو، فضای رستوران و راه رزرو، در یک قاب.', 'Explore the menu, the atmosphere and your next table.'), say('منوی فصل', 'Seasonal menu')],
      clinic: [say('مراقبت از اولین ارتباط', 'Care starts with a connection'), say('معرفی خدمات، پزشکان و مسیر روشن دریافت نوبت.', 'Clear services, practitioner profiles and appointment journeys.'), say('خدمات کلینیک', 'Clinic services')],
      corporate: [say('توانایی شما، روشن و حرفه‌ای', 'Expertise, clearly presented'), say('خدمات، تجربه‌ها و راه ارتباط با تیم شما.', 'Your services, projects and a direct route to your team.'), say('راهکارهای ما', 'Our solutions')],
      portfolio: [say('کار شما، در مرکز توجه', 'Your work, centre stage'), say('پروژه‌ها و داستان پشت هر انتخاب خلاقانه.', 'Selected projects and the thinking behind every detail.'), say('آثار منتخب', 'Selected work')],
      education: [say('جایی برای رشد و یادگیری', 'Make room for learning'), say('دوره، محتوای آموزشی و مسیر همراهی هنرجو.', 'Courses, learning materials and a connected learner journey.'), say('مسیرهای یادگیری', 'Learning paths')],
      jewelry: [say('جزئیاتی که می‌درخشند', 'Details that shine'), say('کالکشن‌ها، مشخصات ساخت و انتخابی آگاهانه.', 'Collections, craftsmanship and considered choices.'), say('کالکشن منتخب', 'Selected collection')],
      crm: [say('همهٔ ارتباط‌ها، یک تصویر روشن', 'Every relationship, one clear view'), say('مشتری، فروش و پیگیری در یک فضای کاری.', 'Customers, sales and follow-ups in a connected workspace.'), say('فضای کار تیم', 'Team workspace')],
      other: [say('از یک ایده، تا یک تجربه', 'From an idea to an experience'), say('مسیر مناسب را با شناخت نیاز واقعی شما پیدا می‌کنیم.', 'Find a useful direction by understanding your needs.'), say('ایدهٔ شما', 'Your idea')]
    };
    const glyphs = {ecommerce: 'M8 9h16l2 17H6L8 9Zm4 0V7a4 4 0 0 1 8 0v2', restaurant: 'M4 16h24M7 16a9 9 0 0 1 18 0M16 3v3M6 22h20M11 26h10', clinic: 'M12 4h8v8h8v8h-8v8h-8v-8H4v-8h8Z', corporate: 'M5 28V10h9v18M14 28V4h13v24M8 14h3m-3 5h3m6-11h6m-6 5h6m-6 5h6M2 28h28', portfolio: 'M4 4h10v10H4ZM18 4h10v16H18ZM4 18h10v10H4ZM18 24h10v4H18Z', education: 'M3 6c5-2 9-1 13 2 4-3 8-4 13-2v20c-5-2-9-1-13 2-4-3-8-4-13-2ZM16 8v20', jewelry: 'm4 11 6-7h12l6 7-12 17ZM4 11h24M10 4l6 24 6-24', crm: 'M12 12h8v8h-8ZM4 4h4v4H4ZM24 4h4v4h-4ZM4 24h4v4H4ZM24 24h4v4h-4ZM8 8l4 4m8 0 4-4M8 24l4-4m8 0 4 4', other: 'M10 22c0-5-4-5-4-11a10 10 0 0 1 20 0c0 6-4 6-4 11ZM11 26h10M13 30h6'};
    const node = (tag, cls, text) => {const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined) n.textContent = text; return n;};
    const button = (text, action, cls = 'os-choice') => {const b = node('button', cls, text); b.type = 'button'; b.addEventListener('click', action); return b;};
    const icon = topic => {const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('viewBox', '0 0 32 32'); svg.setAttribute('aria-hidden', 'true'); const p = document.createElementNS(svg.namespaceURI, 'path'); p.setAttribute('d', glyphs[topic] || glyphs.other); svg.append(p); return svg;};
    const root = node('section', 'os-root'); root.setAttribute('role', 'dialog'); root.setAttribute('aria-modal', 'true'); root.setAttribute('aria-labelledby', 'os-title'); root.dir = fa ? 'rtl' : 'ltr'; root.hidden = true;
    const head = node('header', 'os-head'); head.append(node('strong', 'os-logo', 'RVION'), node('span', 'os-kicker', say('استودیوی انتخاب شما', 'YOUR DESIGN STUDIO')));
    const pause = button('', () => {paused = !paused; introducing = false; render(); schedule();}, 'os-tool');
    const simple = button(say('فرم ساده', 'Simple form'), close, 'os-tool');
    head.append(pause, simple);
    const nav = node('nav', 'os-steps'); nav.setAttribute('aria-label', say('مراحل انتخاب', 'Design steps'));
    const body = node('div', 'os-body'), panel = node('div', 'os-panel'), stage = node('div', 'os-stage');
    const title = node('h2', 'os-title'); title.id = 'os-title'; title.tabIndex = -1;
    const hint = node('p', 'os-hint'), choices = node('div', 'os-choices');
    panel.append(title, hint, choices); body.append(panel, stage);
    const foot = node('footer', 'os-foot'), status = node('p', 'os-status'); status.setAttribute('role', 'status');
    const back = button(say('بازگشت', 'Back'), () => dispatch({type: 'go', step: Math.max(0, state.step - 1)}), 'os-tool');
    const next = button('', advance, 'os-next'); foot.append(back, status, next); root.append(head, nav, body, foot);
    const fallback = document.querySelector('.project-start-shell');
    const siblings = [...document.body.children].filter(n => !['SCRIPT', 'LINK', 'STYLE'].includes(n.tagName));
    const saved = siblings.map(n => [n, n.inert]);
    const previousFocus = document.activeElement;
    function close() {
      if (closed) return; closed = true; clock.stop();
      document.removeEventListener('visibilitychange', visibility); document.removeEventListener('keydown', keyboard);
      window.removeEventListener('pagehide', close); motion.removeEventListener?.('change', motionChange);
      root.remove(); document.body.classList.remove('os-open'); saved.forEach(([n, inert]) => {n.inert = inert;});
      if (previousFocus?.isConnected) previousFocus.focus(); fallback.querySelector('h1')?.scrollIntoView({block: 'start'});
    }
    function syncPause() {pause.textContent = paused ? say('ادامهٔ حرکت', 'Resume motion') : say('توقف حرکت', 'Pause motion'); pause.setAttribute('aria-pressed', String(paused)); root.classList.toggle('os-paused', paused || document.hidden);}
    function schedule() {
      clock.cycle(state.step === 0 ? 4200 : 4300,
        () => !closed && !paused && !motion.matches && !document.hidden && state.step < 2 && !state[state.step === 0 ? 'palette' : 'look'],
        () => {preview++; drawScene(true); schedule();});
    }
    function dispatch(action) {
      const focused = document.activeElement?.textContent, oldStep = state.step;
      state = api.transition(state, action, catalogue);
      introducing = false;
      render(action.type === 'choose' || state.step < 2); schedule();
      if (oldStep !== state.step) {body.scrollTop = 0; stage.scrollTop = 0; title.focus({preventScroll: true});}
      else [...root.querySelectorAll('button')].find(b => b.textContent === focused)?.focus({preventScroll: true});
    }
    function advance() {
      if (introducing) return;
      if (state.step === 4) {submit(); return;}
      if (state.step === 2 && state.topic && !motion.matches && !paused && !document.hidden && api.transition(state, {type: 'next'}, catalogue).step === 3) {
        clock.stop(); introducing = true; next.disabled = true;
        const overlay = node('div', 'os-topic-intro'); overlay.append(art.intro(state.topic, icon), node('h3', '', catalogue.topics.find(t => t.key === state.topic).title), node('p', '', copy[state.topic][1]));
        const finish = () => {if (!introducing) return; dispatch({type: 'next'});};
        const skip = button(say('رد کردن مقدمه', 'Skip introduction'), finish, 'os-tool'); overlay.append(skip); overlay.dataset.palette = state.palette;
        (window.matchMedia('(max-width: 700px)').matches ? root : stage).append(overlay);
        skip.focus({preventScroll: true}); clock.after(3600, finish); return;
      }
      dispatch({type: 'next'});
      title.focus({preventScroll: true});
    }
    function pick(field, value) {dispatch({type: 'choose', field, value});}
    function edit(step) {dispatch({type: 'edit', step}); title.focus({preventScroll: true});}
    function checkList(rows, field, container = choices) {
      rows.forEach(([key, label]) => {
        const b = button(label, () => {
          const adding = !state[field].includes(key); dispatch({type: 'toggle', field, value: key});
          if (!adding) {status.textContent = label + say(' برداشته شد.', ' removed.'); return;}
          status.textContent = label + say(' اضافه شد.', ' added.');
          if (!motion.matches && !paused && !document.hidden) {
            const pop = node('div', 'os-feature-pop'); pop.dataset.palette = state.palette;
            pop.append(art.section(key, label, sceneContext()));
            (window.matchMedia('(max-width: 700px)').matches ? root : stage).append(pop);
            clock.after(2000, () => {pop.remove(); const section = [...stage.querySelectorAll('.os-designed-section')].find(n => n.dataset.feature === key); if (section) {section.classList.add('os-section-new'); const page = stage.querySelector('.os-page'); page.scrollTo({top: section.offsetTop - page.offsetTop - 24, behavior: 'smooth'});}});
          }
        });
        b.setAttribute('aria-pressed', String(state[field].includes(key))); container.append(b);
      });
    }
    function render(play = state.step < 2) {
      root.querySelectorAll('.os-topic-intro, .os-feature-pop').forEach(n => n.remove());
      root.dataset.step = String(state.step); nav.replaceChildren(); choices.replaceChildren();
      // Review is a real document flow: the complete sample, then its controls.
      if (state.step === 4) body.append(stage, panel, foot);
      else {body.append(panel, stage); root.append(foot);}
      stepNames.forEach((name, i) => {const b = button(name, () => dispatch({type: 'go', step: i}), 'os-step'); b.disabled = i > state.visited; if (i === state.step) b.setAttribute('aria-current', 'step'); nav.append(b);});
      title.textContent = headings[state.step];
      hint.textContent = state.step < 2 ? say('یک انتخاب کنید؛ پیش‌نمایش همان لحظه تغییر می‌کند.', 'Choose an option to see it change live.') : state.step === 2 ? say('نام برند اختیاری است و فقط روی همین صفحه نمایش داده می‌شود.', 'Brand is optional and appears only on this page.') : state.step === 3 ? say('فقط موارد موردنیازتان را روشن کنید. چیزی از قبل انتخاب نشده است.', 'Select only what you need. Nothing is preselected.') : say('این نمونهٔ نمایشی است؛ دامنه و هزینه بعد از نیازسنجی تعیین می‌شود.', 'An illustrative sample; scope and cost are agreed after discovery.');
      if (state.step < 2) {
        const field = state.step === 0 ? 'palette' : 'look';
        catalogue[field === 'palette' ? 'palettes' : 'looks'].forEach(([key, label]) => {
          const b = button(label, () => pick(field, key)); b.dataset[field] = key; b.setAttribute('aria-pressed', String(state[field] === key));
          if (field === 'palette') b.prepend(node('i', 'os-swatch')); choices.append(b);
        });
      } else if (state.step === 2) {
        catalogue.topics.forEach(topic => {const b = button(topic.title, () => pick('topic', topic.key)); b.prepend(icon(topic.key)); b.setAttribute('aria-pressed', String(state.topic === topic.key)); choices.append(b);});
        const label = node('label', 'os-brand-label', say('نام نمایشی برند (اختیاری)', 'Preview brand (optional)')); label.htmlFor = 'os-brand';
        const input = node('input', 'os-brand'); input.id = 'os-brand'; input.type = 'text'; input.maxLength = 40; input.autocomplete = 'off'; input.value = state.brand;
        input.addEventListener('input', () => {state = api.transition(state, {type: 'brand', value: input.value}, catalogue); stage.querySelectorAll('[data-os-brand]').forEach(n => {n.textContent = state.brand || say('برند شما', 'Your brand');});}); choices.append(label, input);
      } else if (state.step === 3) {
        const topic = catalogue.topics.find(t => t.key === state.topic);
        checkList(topic?.features || [], 'features');
        if (topic?.extensions.length) {choices.append(node('h3', 'os-group-title', say('توسعه‌های بعدی', 'Future extensions'))); checkList(topic.extensions, 'extensions');}
        if (!topic?.features.length) choices.append(node('p', '', say('ایده را در فرم بعدی توضیح دهید؛ امکانات را با هم مشخص می‌کنیم.', 'Describe your idea in the next form; we will define the features together.')));
        choices.append(node('h3', 'os-group-title', say('همراه پروژه', 'Alongside your project'))); checkList(catalogue.addons, 'addons');
        const consult = button(catalogue.consultation, () => dispatch({type: 'consult'})); consult.setAttribute('aria-pressed', String(state.consult)); choices.append(consult);
        if (!fa && topic?.specialist_fa && !state.consult) choices.append(node('p', 'os-hint', 'The specialist form is currently in Persian. Consultation is available in English.'));
      } else {
        [['palette', catalogue.palettes, 0], ['look', catalogue.looks, 1], ['topic', catalogue.topics.map(t => [t.key, t.title]), 2]].forEach(([field, rows, step]) => {
          const row = node('div', 'os-summary-row'); row.append(node('span', '', stepNames[step]), node('strong', '', rows.find(r => r[0] === state[field])?.[1] || '—'), button(say('ویرایش', 'Edit'), () => edit(step), 'os-edit')); choices.append(row);
        });
        const topic = catalogue.topics.find(t => t.key === state.topic);
        const selected = [...(topic?.features || []).filter(r => state.features.includes(r[0])), ...(topic?.extensions || []).filter(r => state.extensions.includes(r[0])), ...catalogue.addons.filter(r => state.addons.includes(r[0]))];
        const row = node('div', 'os-summary-row'); row.append(node('span', '', stepNames[3]), node('strong', '', selected.map(r => r[1]).join(' · ') || say('بدون انتخاب اضافه', 'No extra features')), button(say('ویرایش', 'Edit'), () => edit(3), 'os-edit')); choices.append(row);
        if (state.consult) choices.append(node('p', 'os-hint', catalogue.consultation));
        const gallery = node('a', 'os-gallery', say('مشاهدهٔ گالری نمونه‌ها', 'Explore the sample gallery')); gallery.href = catalogue.gallery_url; choices.append(gallery);
      }
      back.hidden = state.step === 0; next.disabled = state.step === 0 && !state.palette || state.step === 1 && !state.look || state.step === 2 && !state.topic;
      next.textContent = state.step === 4 ? say('ادامه به فرم نیازسنجی', 'Continue to discovery') : state.editing && state.step !== 2 ? say('ذخیره و بازگشت', 'Save and return') : say('ادامه', 'Continue');
      status.textContent = say('مرحلهٔ ', 'Step ') + new Intl.NumberFormat(fa ? 'fa' : 'en').format(state.step + 1) + say(' از ۵', ' of 5'); drawScene(play); syncPause();
    }
    function sceneContext() {
      const palette = state.palette || catalogue.palettes[state.step === 0 ? preview % catalogue.palettes.length : 0][0];
      const look = state.look || catalogue.looks[state.step === 1 ? preview % catalogue.looks.length : 0][0];
      const topic = state.topic || 'corporate', content = copy[topic], name = state.brand || say('برند شما', 'Your brand');
      const topicData = catalogue.topics.find(t => t.key === topic);
      const selected = [...(topicData?.features || []).filter(r => state.features.includes(r[0])), ...(topicData?.extensions || []).filter(r => state.extensions.includes(r[0])), ...catalogue.addons.filter(r => state.addons.includes(r[0]))];
      return {say, icon, palette, look, topic, name, copy: content, selected};
    }
    function drawScene(play = false) {
      clock.stop(); const ctx = sceneContext(); const {palette, look, topic} = ctx;
      stage.replaceChildren(); stage.dataset.palette = palette;
      const windowBar = node('div', 'os-windowbar', say('نمونهٔ نمایشی · نه سایت نهایی', 'ILLUSTRATIVE SAMPLE · NOT A FINAL WEBSITE')); windowBar.prepend(node('span', 'os-window-dots', '● ● ●')); stage.append(windowBar);
      if (state.step === 1) {
        const stories = node('div', 'os-stories'), prevStory = button('‹', () => browse(-1), 'os-story-arrow'); prevStory.setAttribute('aria-label', say('سبک قبلی', 'Previous look')); stories.append(prevStory);
        catalogue.looks.forEach(([key]) => {const segment = node('span', 'os-story'); segment.setAttribute('aria-hidden', 'true'); segment.dataset.active = String(key === look); stories.append(segment);}); const nextStory = button('›', () => browse(1), 'os-story-arrow'); nextStory.setAttribute('aria-label', say('سبک بعدی', 'Next look')); stories.append(nextStory); stage.append(stories);
      }
      const playback = node('div', 'os-playback'), page = node('div', 'os-page'); page.tabIndex = 0; page.setAttribute('aria-label', say('پیش‌نمایش طراحی؛ قابل پیمایش', 'Scrollable design preview')); page.append(art.site(ctx)); playback.append(page); stage.append(playback);
      const caption = node('div', 'os-scene-caption'); caption.append(node('strong', '', catalogue.looks.find(r => r[0] === look)[1]), node('span', '', say(...art.looks[look]))); stage.append(caption);
      let startX = null; playback.addEventListener('pointerdown', e => {startX = e.clientX;}); playback.addEventListener('pointercancel', () => {startX = null;}); playback.addEventListener('pointerup', e => {if (startX !== null && state.step === 1 && Math.abs(e.clientX - startX) > 50) browse(e.clientX > startX ? -1 : 1); startX = null;});
      if (play && !motion.matches && !paused && !document.hidden) {
        playback.classList.add('os-building'); const editor = node('div', 'os-editor'); editor.setAttribute('aria-hidden', 'true');
        const pre = node('pre'), build = node('div', 'os-build'); build.append(node('i')); editor.append(node('span', '', state.step === 2 ? 'site.config.js' : 'design.css'), pre, node('span', 'os-code-chip'), build); playback.append(editor);
        // Palette values have one owner: CSS. Never replace the contrast-adjusted warm token.
        const tokens = getComputedStyle(stage.querySelector('.os-site'));
        const code = state.step === 0 ? '/* palette — ' + catalogue.palettes.find(r => r[0] === palette)[1] + ' */\n:root {\n  --brand: ' + tokens.getPropertyValue('--s-ac').trim() + ';\n  --surface: ' + tokens.getPropertyValue('--s-bg').trim() + ';\n  --radius: 16px\n}' : state.step === 1 ? '/* look — ' + look + ' */\n' + art.lookCode[look] : 'site.type = ' + JSON.stringify(topic) + ';\nsite.name = ' + JSON.stringify(ctx.name) + ';\nsite.modules = ' + JSON.stringify(ctx.selected.map(r => r[0])) + ';';
        clock.animate(950, p => {pre.textContent = code.slice(0, Math.floor(code.length * p)); build.style.setProperty('--os-built', p);});
        clock.after(1250, () => {pre.textContent = code; playback.classList.remove('os-building'); playback.classList.add('os-page-arrived'); editor.remove();});
        clock.after(1650, () => {const distance = Math.min(420, page.scrollHeight - page.clientHeight); if (distance > 0) clock.animate(2400, p => {page.scrollTop = distance * (p * p * (3 - 2 * p));});});
      }
      if (state.step === 4) {
        const top = node('div', 'os-top-pens');
        [[1, say('ادیت سبک', 'Edit look')], [0, say('ادیت رنگ', 'Edit colour')]].forEach(([step, label]) => top.append(button(label, () => edit(step), 'os-review-edit')));
        playback.append(top);
      }
    }
    function browse(delta) {const current = state.look ? catalogue.looks.findIndex(r => r[0] === state.look) : preview; preview = (current + delta + catalogue.looks.length) % catalogue.looks.length; if (state.look) {pick('look', catalogue.looks[preview][0]);} else {drawScene(true); schedule();}}
    function submit() {
      next.disabled = true; next.textContent = say('در حال آماده‌سازی فرم…', 'Preparing your form…');
      // Never serialize brand, arbitrary URLs, or presentation copy.
      form.querySelectorAll('[data-os-field]').forEach(n => n.remove());
      const append = (key, value) => {const input = node('input'); input.type = 'hidden'; input.name = key; input.value = value; input.dataset.osField = ''; form.append(input);};
      Object.entries(api.choices(state)).forEach(([key, value]) => append(key, value));
      if (state.topic !== 'crm') state.features.forEach(value => append('features', value));
      form.requestSubmit();
    }
    function visibility() {introducing = false; render(); schedule();}
    function motionChange() {introducing = false; render(); schedule();}
    function keyboard(event) {
      if (event.key === 'Escape') {close(); return;}
      if (event.key !== 'Tab') return;
      const controls = [...root.querySelectorAll('button:not([disabled]),input,a[href]')].filter(n => n.getClientRects().length);
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {event.preventDefault(); last.focus();}
      else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first.focus();}
    }
    try {
      render(false); document.body.append(root); root.hidden = false;
      if (getComputedStyle(root).position !== 'fixed') {close(); return;}
      drawScene(state.step < 2);
      saved.forEach(([n]) => {n.inert = true;}); document.body.classList.add('os-open');
      document.addEventListener('visibilitychange', visibility); document.addEventListener('keydown', keyboard); window.addEventListener('pagehide', close); motion.addEventListener?.('change', motionChange);
      title.focus({preventScroll: true}); schedule();
    } catch (error) {close();}
  };
  if (document.readyState === 'complete') boot(); else window.addEventListener('load', boot, {once: true});
})();
