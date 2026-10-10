/* One visit from the entry gateway; no cookies, session keys or storage. */
(function () {
  'use strict';
  function start() {
    const source = document.getElementById('os-path-data');
    if (!source || new URL(location.href).searchParams.get('from') !== 'entry') return;
    const url = new URL(location.href); url.searchParams.delete('from'); history.replaceState(history.state, '', url);
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    if (motion.matches) return;
    const data = JSON.parse(source.textContent), fa = data.lang === 'fa', project = data.kind === 'project';
    const say = (a, b) => fa ? a : b;
    const node = (tag, cls, text) => {const n = document.createElement(tag); n.className = cls; if (text !== undefined) n.textContent = text; return n;};
    const captions = project ? [
      [say('نیازسنجی', 'Discovery'), say('هدف، مخاطب و امکانات پروژه را روشن می‌کنیم.', 'Define the goals, audience and useful features.')],
      [say('توافق شفاف', 'A clear agreement'), say('دامنه، هزینه و مراحل تحویل را بررسی و تأیید می‌کنید.', 'Review and agree on scope, cost and delivery stages.')],
      [say('ساخت و توسعه', 'Design & development'), say('طراحی و کدنویسی مطابق دامنهٔ توافق‌شده پیش می‌رود.', 'Design and implementation follow the agreed scope.')],
      [say('آزمایش و بازبینی', 'Testing & review'), say('مسیرها، موبایل و عملکرد پیش از انتشار بررسی می‌شوند.', 'Review the journeys, mobile layout and behaviour before launch.')],
      [say('تحویل و راه‌اندازی', 'Delivery & launch'), say('پس از تأیید، نسخهٔ آماده راه‌اندازی و تحویل می‌شود.', 'Launch and hand over the approved release.')],
      [say('پشتیبانی', 'Ongoing support'), say('نگه‌داری و توسعه طبق شرایط توافق‌شده ادامه دارد.', 'Maintenance and development follow the agreed support terms.')]
    ] : [
      [say('زمان مشخص، مسیر روشن', 'A clear time limit'), data.exams.map(e => e.title + ': ' + new Intl.NumberFormat(fa ? 'fa' : 'en').format(e.questions) + say(' سؤال · ', ' questions · ') + new Intl.NumberFormat(fa ? 'fa' : 'en').format(e.minutes) + say(' دقیقه', ' minutes')).join(' / ') || say('جزئیات هر آزمون پیش از شروع نمایش داده می‌شود.', 'See the details of each assessment before starting.')],
      [say('ساختار مهارتی', 'A structured assessment'), say('سهم و موضوع هر بخش از نسخهٔ منتشرشده نمایش داده می‌شود.', 'See each skill section and its allocation in the published version.')],
      [say('سلامت آزمون', 'Assessment integrity'), say('کپی، خروج از صفحه و زمان پاسخ ثبت می‌شوند؛ این داده‌ها به‌تنهایی حکم تقلب نیستند.', 'Copy attempts, page exits and answer timing are recorded—not a conclusive cheating verdict.')],
      [say('گزارش و مرور پاسخ‌ها', 'Results & answer review'), say('تحلیل قانون‌محور، توضیح پاسخ‌ها و گواهی قابل بررسی؛ هدیهٔ حساب جدید یک نوبت در مجموع است.', 'Rule-based analysis, answer explanations and a verifiable certificate. Eligible new accounts receive one attempt in total.')]
    ];
    let closed = false, timer = 0, last = performance.now(), remaining = project ? 18000 : 10400, paused = false;
    const root = node('section', 'os-intro'); root.setAttribute('role', 'dialog'); root.setAttribute('aria-modal', 'true'); root.setAttribute('aria-label', say('معرفی مسیر', 'Your journey')); root.dir = fa ? 'rtl' : 'ltr';
    root.style.setProperty('--os-duration', remaining + 'ms'); root.style.setProperty('--os-count', String(captions.length));
    const previous = document.activeElement, background = [...document.body.children].filter(n => !['SCRIPT', 'STYLE', 'LINK'].includes(n.tagName)).map(n => [n, n.inert]);
    const header = node('header', 'os-intro-head'); header.append(node('strong', '', 'RVION'), node('span', '', project ? say('از ایده تا راه‌اندازی', 'FROM IDEA TO LAUNCH') : say('پیش از انتخاب آزمون', 'BEFORE YOU CHOOSE')));
    const track = node('div', 'os-intro-track'), progress = node('div', 'os-intro-progress'); progress.append(node('i', ''));
    captions.forEach(([title, description], i) => {
      const act = node('article', 'os-intro-act os-act-' + (project ? 'project-' : 'exam-') + i);
      const art = node('div', 'os-intro-art'); art.setAttribute('aria-hidden', 'true');
      if (project && i === 0) {const paper = node('div', 'os-film-form'); for (let j=0;j<4;j++) {const line=node('div','os-film-line'); line.append(node('i',''),node('b','')); paper.append(line);} paper.append(node('span','os-film-chips',say('فروشگاه · کلینیک · CRM','Store · Clinic · CRM'))); art.append(paper, node('span','os-film-stamp',say('نیاز شما','YOUR BRIEF')), node('span','os-film-plane','➤'));}
      else if (project && i === 1) {const paper=node('div','os-film-paper'); [say('دامنه','Scope'),say('هزینه','Cost'),say('تحویل','Delivery')].forEach(t=>{const r=node('div','os-film-line',t);r.append(node('i','os-film-tick','✓'));paper.append(r);}); paper.append(node('span','os-film-sign','⌁'),node('b','os-film-approved',say('تأیید','AGREED')));art.append(paper);}
      else if (project && i === 2) {const editor=node('div','os-film-code'); for(let j=0;j<6;j++) {const line=node('i','');line.style.setProperty('--os-size',(45+j%3*20)+'%');editor.append(line);} const site=node('div','os-film-site');for(let j=0;j<4;j++)site.append(node('i',''));art.append(editor,site);}
      else if (project && i === 3) {art.append(node('div','os-film-phone','✓'),node('div','os-film-monitor','✓')); const list=node('div','os-film-checks');[say('مسیرها','Journeys'),say('موبایل','Mobile'),say('عملکرد','Performance')].forEach(t=>list.append(node('span','', '✓ '+t)));art.append(list);}
      else if (project && i === 4) {const site=node('div','os-film-browser');site.append(node('span','', 'your-brand.example'),node('b','',say('آمادهٔ تحویل','READY TO LAUNCH')));art.append(site);for(let j=0;j<12;j++){const confetti=node('i','os-film-confetti');confetti.style.setProperty('--os-x',(j-6)*24+'px');confetti.style.setProperty('--os-delay',j*.04+'s');art.append(confetti);}}
      else if (project && i === 5 || !project && i === 3) {const bars=node('div','os-film-bars');[45,70,55,85,65].forEach(v=>{const b=node('i','');b.style.setProperty('--os-size',v+'%');bars.append(b);});art.append(bars,node('div','os-film-shield',project?'✓':say('گزارش','REPORT')));}
      else if (i === 0) {art.append(node('div','os-film-ring',say('زمان','TIME')));}
      else if (i === 1) {const bars=node('div','os-film-segments');(data.exams[0]?.sections || []).forEach(s=>{const b=node('i','');b.style.setProperty('--os-size',String(s.count));bars.append(b);}); art.append(bars);}
      else {art.append(node('div','os-film-shield','✓'),node('span','os-film-chips',say('کپی · زمان پاسخ · خروج از صفحه','Copy · Answer timing · Page exits')));}
      act.append(art,node('h2','',title),node('p','',description)); track.append(act);
    });
    const labels=node('div','os-intro-labels'); captions.forEach(([t])=>labels.append(node('span','',t)));
    const controls=node('footer','os-intro-controls'); const pause=node('button','',say('توقف','Pause')), skip=node('button','',say('رد کردن مقدمه','Skip intro'));pause.type=skip.type='button';controls.append(pause,skip);
    root.append(header,progress,track,labels,controls);
    const close=()=>{if(closed)return;closed=true;clearTimeout(timer);root.remove();background.forEach(([n,inert])=>{n.inert=inert;});document.documentElement.removeAttribute('data-path-intro');document.removeEventListener('visibilitychange',visibility);document.removeEventListener('keydown',keyboard);window.removeEventListener('pagehide',close);motion.removeEventListener?.('change',close);previous?.focus({preventScroll:true});document.dispatchEvent(new Event('rvion:path-intro-done'));};
    function schedule(){clearTimeout(timer);if(closed||paused||document.hidden)return;last=performance.now();timer=setTimeout(close,remaining);}
    function suspend(){if(timer){remaining=Math.max(0,remaining-(performance.now()-last));clearTimeout(timer);timer=0;}}
    function visibility(){suspend();root.classList.toggle('os-intro-paused',paused||document.hidden);schedule();}
    function keyboard(e){if(e.key==='Escape')close();if(e.key==='Tab'){e.preventDefault();(document.activeElement===skip?pause:skip).focus();}}
    pause.addEventListener('click',()=>{suspend();paused=!paused;root.classList.toggle('os-intro-paused',paused);pause.textContent=paused?say('ادامه','Resume'):say('توقف','Pause');pause.setAttribute('aria-pressed',String(paused));schedule();});skip.addEventListener('click',close);
    try{document.body.append(root);document.documentElement.dataset.pathIntro='active';background.forEach(([n])=>{n.inert=true;});document.addEventListener('visibilitychange',visibility);document.addEventListener('keydown',keyboard);window.addEventListener('pagehide',close);motion.addEventListener?.('change',close);skip.focus({preventScroll:true});schedule();}catch(error){close();}
  }
  if(document.readyState==='complete')start();else window.addEventListener('load',start,{once:true});
})();
