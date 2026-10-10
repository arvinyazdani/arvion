/* Fictional, local-only design specimens; rendered lazily by the visible step. */
(function () {
  'use strict';
  const n = (tag, cls, text) => {const el = document.createElement(tag); if (cls) el.className = cls; if (text !== undefined) el.textContent = text; return el;};
  const topics = {
    ecommerce: [['محصولات', 'Products'], ['ارسال سفارش', 'Delivery'], ['پرداخت', 'Checkout']],
    restaurant: [['منوی فصل', 'Seasonal menu'], ['رزرو میز', 'Book a table'], ['سفارش آنلاین', 'Online orders']],
    clinic: [['خدمات', 'Services'], ['پزشکان', 'Practitioners'], ['دریافت نوبت', 'Appointments']],
    corporate: [['خدمات', 'Services'], ['پروژه‌ها', 'Projects'], ['تیم ما', 'Our team']],
    portfolio: [['آثار منتخب', 'Selected work'], ['دربارهٔ من', 'About me'], ['ارتباط', 'Contact']],
    education: [['دوره‌ها', 'Courses'], ['مدرسان', 'Instructors'], ['ثبت‌نام', 'Enrolment']],
    jewelry: [['کالکشن‌ها', 'Collections'], ['استعلام قیمت', 'Price enquiry'], ['ساخت سفارشی', 'Custom pieces']],
    crm: [['مشتریان', 'Customers'], ['فروش', 'Sales'], ['گزارش‌ها', 'Reports']],
    other: [['هدف شما', 'Your goal'], ['نیازهای شما', 'Your needs'], ['مشاوره', 'Consultation']]
  };
  const looks = {
    modern: ['پنجرهٔ داشبورد، کارت‌های روشن و شبکهٔ منظم', 'Dashboard window, clear cards and a precise grid'],
    industrial: ['مشخصات فنی، ابزار و خطوط صریح', 'Technical specifications, utility and bold rules'],
    cinematic: ['پوستر، نور، قاب‌های داستان و نقل‌قول', 'Poster, light, story frames and a testimonial'],
    video: ['فضای سفر، جستجوی شیشه‌ای و ریلز', 'Travel atmosphere, glass search and reels'],
    classic: ['قاب طاقی، تزئین و چیدمان لوکس', 'Arched frame, ornament and a luxury composition'],
    soft: ['گوشی، گفت‌وگو و فرم‌های نرم', 'Phone, conversation and soft forms']
  };
  const lookCode = {
    modern: '.layout { display: grid; gap: 24px }\n.card { border-radius: 16px; box-shadow: 0 12px 40px #0002 }',
    industrial: '.panel { border: 3px solid; border-radius: 0 }\n.hazard { background: repeating-linear-gradient(45deg, #111 0 8px, #ffc400 8px 16px) }',
    cinematic: '.poster { aspect-ratio: 21 / 9; isolation: isolate }\n.frame { transform: translateY(0); opacity: 1 }',
    video: '.search { backdrop-filter: blur(16px) }\n.reels { display: grid; grid-template-columns: repeat(3, 1fr) }',
    classic: '.arch { border-radius: 50% 50% 0 0 }\n.heading { font-family: Georgia, serif; letter-spacing: .02em }',
    soft: '.card { border-radius: 32px }\n.chat { display: flex; flex-direction: column; gap: 12px }'
  };
  function site(ctx) {
    const {say, icon, topic, look, name, copy, selected} = ctx;
    const el = n('div', 'os-site os-look-' + look); el.dataset.palette = ctx.palette;
    const brand = cls => {const b = n('strong', cls, name); b.dataset.osBrand = ''; return b;};
    const motif = cls => {const m = n('div', cls); m.append(intro(topic)); return m;};
    const row = (cls, values) => {const r = n('div', cls); values.forEach(v => r.append(n('span', '', v))); return r;};
    const header = n('div', 'os-site-head'); header.append(brand('os-site-brand'), n('span', 'os-site-links', topics[topic].map(pair => say(...pair)).join(' · ')));
    const text = n('div', 'os-hero-copy'), headline = n('h3'); headline.append(brand('os-hero-brand'), n('span', '', copy[0])); text.append(n('span', 'os-eyebrow', copy[2]), headline, n('p', '', copy[1]), n('span', 'os-mock-cta', say('بیشتر ببینید ←', 'Explore more →')));
    const hero = n('div', 'os-hero');
    function dashboard() {
      const dash = n('div', 'os-dashboard'); dash.append(n('div', 'os-dash-title', say('فضای کار نمونه · امروز', 'SAMPLE WORKSPACE · TODAY')));
      dash.append(row('os-kpis', [say('۲۴ سفارش', '24 orders'), say('۸ پیگیری', '8 follow-ups'), say('۱۲ کاربر', '12 users')]));
      const bars = n('div', 'os-chart'); [35, 60, 42, 80, 65, 95, 75].forEach(h => {const b = n('i'); b.style.setProperty('--os-bar', h + '%'); bars.append(b);}); dash.append(bars, row('os-dash-bottom', [say('برنامهٔ این هفته', 'This week'), say('● در حال انجام', '● In progress')])); return dash;
    }
    if (look === 'industrial') {
      el.append(row('os-utility', [say('ابزار / مشخصات / کاتالوگ', 'TOOLS / SPECS / CATALOGUE'), 'B2B — DEMO']), header);
      const spec = n('div', 'os-spec'); spec.append(motif('os-spec-motif'), n('strong', '', say('مشخصات فنی نمونه', 'Sample specifications')));
      [[say('ظرفیت', 'Capacity'), '120 t/h'], [say('توان', 'Power'), '450 kW'], [say('مدل', 'Model'), 'X–240']].forEach(v => spec.append(row('os-spec-row', v)));
      hero.append(text, spec); el.append(hero, n('div', 'os-hazard'), row('os-industrial-stats', [say('۰۱ طراحی', '01 Design'), say('۰۲ ساخت', '02 Build'), say('۰۳ کنترل', '03 Check')]));
    } else if (look === 'cinematic') {
      el.append(header); const poster = n('div', 'os-poster'); poster.append(n('i', 'os-spotlight'), motif('os-poster-motif'), text, n('span', 'os-timecode', 'SCENE 01 / 00:24')); el.append(poster);
      el.append(row('os-film-frames', [say('۰۱ ایده', '01 Idea'), say('۰۲ جزئیات', '02 Detail'), say('۰۳ تجربه', '03 Experience')]));
    } else if (look === 'video') {
      el.append(header); const travel = n('div', 'os-travel'); travel.append(n('i', 'os-landscape'), motif('os-travel-motif'), text, n('span', 'os-video-time', '▷ 00:12 ━━━━━ 00:40'));
      travel.append(row('os-glass-search', [say('کجا؟', 'Where?'), say('چه زمانی؟', 'When?'), say('چند نفر؟', 'Guests?'), say('جستجو ←', 'Search →')])); el.append(travel);
      el.append(row('os-reels', [say('اقامت', 'Stay'), say('تجربه', 'Explore'), say('سفر', 'Journey')]));
    } else if (look === 'classic') {
      el.append(n('div', 'os-utility', say('◇ مجموعهٔ نمایشی ◇', '◇ AN ILLUSTRATIVE COLLECTION ◇')), header);
      const arch = n('div', 'os-arch'); arch.append(motif('os-arch-motif'), n('span', 'os-ornament', '◇ — ◇')); hero.append(text, arch); el.append(hero);
      el.append(row('os-prices', [say('منتخب / ۰۱', 'Selection / 01'), say('ویژه / ۰۲', 'Signature / 02'), say('قیمت پس از استعلام', 'Price on enquiry')]));
    } else if (look === 'soft') {
      el.append(header); const phone = n('div', 'os-phone'); phone.append(n('span', 'os-phone-notch'), motif('os-phone-motif'), n('strong', '', say('همراه شما', 'Here for you')), n('span', 'os-chat', say('سلام، چطور کمک کنیم؟', 'Hi, how can we help?')), n('span', 'os-chat os-chat-reply', say('برای شروع راهنمایی می‌خواهم', 'I would like some guidance')), n('span', 'os-chat', say('با هم قدم اول را برمی‌داریم', 'Let’s take the first step together'))); hero.append(text, phone); el.append(hero, row('os-soft-rating', ['● ● ●', say('★★★★★ امتیاز نمایشی', '★★★★★ Illustrative rating')]));
    } else {
      el.append(header); const visual = n('div', 'os-modern-visual'); visual.append(motif('os-modern-motif'), dashboard(), n('span', 'os-float-note', say('✓ سفارش نمونه دریافت شد', '✓ Sample order received'))); hero.append(text, visual); el.append(hero, row('os-logo-row', ['NOVA', 'FORM', 'STUDIO', 'ATELIER']));
    }
    const cards = n('div', 'os-modules'); topics[topic].forEach((pair, i) => {const card = n('div', 'os-module'); card.append(n('span', 'os-card-number', String(i + 1).padStart(2, '0')), icon(topic), n('strong', '', say(...pair)), n('span', '', say('بخشی از این طرح نمایشی', 'Part of this illustrative design'))); cards.append(card);}); el.append(cards);
    if (look === 'industrial') el.append(row('os-certificates', ['ISO 9001', 'ISO 14001', say('گواهی‌های فرضی نمونه', 'Fictional sample certificates')]));
    if (['cinematic', 'classic'].includes(look)) el.append(n('blockquote', 'os-quote', say('«جزئیات، تجربه را می‌سازند.» — نقل‌قول فرضی', '“Details shape the experience.” — Fictional testimonial')));
    selected.forEach(([key, label]) => el.append(section(key, label, ctx)));
    el.append(n('div', 'os-site-footer', name + ' · ' + say('نمونهٔ طراحی', 'Design sample'))); return el;
  }
  function section(key, label, ctx) {
    const {say, topic, icon} = ctx; const box = n('section', 'os-designed-section'); box.dataset.feature = key;
    box.append(n('span', 'os-eyebrow', say('بخش نمایشی', 'ILLUSTRATIVE SECTION')), n('h4', '', label));
    const chips = values => {const r = n('div', 'os-section-chips'); values.forEach(v => r.append(n('span', '', v))); return r;};
    const rows = values => {values.forEach((v, i) => {const r = n('div', 'os-section-row'); r.append(n('span', '', v), n('span', '', i ? '✓' : '●')); box.append(r);});};
    if (/booking|appointment/.test(key)) {
      box.append(chips([say('شنبه', 'Sat'), say('یکشنبه', 'Sun'), say('دوشنبه', 'Mon')]), chips(['10:00', '11:30', '15:00']), n('span', 'os-mock-cta', topic === 'restaurant' ? say('رزرو میز', 'Book a table') : say('ثبت نوبت', 'Book appointment')));
    } else if (/payment/.test(key)) {
      const card = n('div', 'os-credit-card'); card.append(n('span', '', '▦'), n('strong', '', '••••  ••••  ••••  4242')); box.append(card, chips([say('سبد', 'Cart'), say('پرداخت', 'Payment'), say('رسید', 'Receipt')]));
    } else if (/catalog/.test(key)) {
      rows(topic === 'restaurant' ? [say('پاستای زعفرانی', 'Saffron pasta'), say('سالاد فصل', 'Seasonal salad'), say('تارت انجیر', 'Fig tart')] : topic === 'jewelry' ? [say('حلقهٔ منتخب · ۱۸ عیار', 'Signature ring · 18K'), say('گردنبند ظریف', 'Fine necklace'), say('دستبند سفارشی', 'Custom bracelet')] : [say('محصول نمونهٔ یک', 'Sample product one'), say('محصول نمونهٔ دو', 'Sample product two'), say('محصول نمونهٔ سه', 'Sample product three')]);
    } else if (/sales|pipeline/.test(key)) {box.append(chips([say('جدید', 'New'), say('مذاکره', 'Negotiation'), say('توافق', 'Won')])); rows([say('فرصت نمونهٔ یک', 'Sample opportunity one'), say('فرصت نمونهٔ دو', 'Sample opportunity two')]);
    } else if (/security|role/.test(key)) {box.append(chips(['MFA ✓', say('مدیر', 'Admin'), say('مشاهده', 'Viewer')])); rows([say('ورود امن', 'Secure sign-in'), say('دسترسی‌های مشخص', 'Defined permissions')]);
    } else if (/automation|workflows/.test(key)) {box.append(chips([say('درخواست ← تأیید ← اعلان', 'Request → Approve → Notify')]));
    } else if (/visits/.test(key)) {rows([say('ویزیت نمونهٔ یک · اقدام بعدی', 'Sample visit one · Next action'), say('ویزیت نمونهٔ دو · گزارش ثبت شد', 'Sample visit two · Report saved')]);
    } else if (/correspondence/.test(key)) {rows([say('نامهٔ وارده · در بررسی', 'Incoming letter · In review'), say('نامهٔ صادره · پیش‌نویس', 'Outgoing letter · Draft')]);
    } else if (/accounting/.test(key)) {rows([say('فاکتور نمونه · صادر شد', 'Sample invoice · Issued'), say('دریافت نمونه · ثبت شد', 'Sample receipt · Recorded'), say('پرداخت نمونه · در انتظار', 'Sample payment · Pending')]);
    } else if (/channels/.test(key)) {box.append(chips([say('پیامک', 'SMS'), say('ایمیل', 'Email'), say('گفت‌وگو', 'Chat')])); rows([say('پیام نمونه · دریافت شد', 'Sample message · Received')]);
    } else if (/mobile/.test(key)) {box.append(chips([say('موبایل', 'Mobile'), say('آفلاین', 'Offline'), say('همگام‌سازی', 'Sync')])); rows([say('یادداشت نمونه · ذخیره روی دستگاه', 'Sample note · Saved on device')]);
    } else if (/ai/.test(key)) {rows([say('پیشنهاد نمونه · نیازمند بررسی شما', 'Sample suggestion · Needs your review'), say('خلاصهٔ فعالیت نمونه', 'Sample activity summary')]);
    } else if (/portal/.test(key)) {rows([say('درخواست نمونه · در حال انجام', 'Sample request · In progress'), say('سند نمونه · آمادهٔ مشاهده', 'Sample document · Ready to view')]);
    } else if (/inventory|report|membership|webapp/.test(key)) {
      [say('پیشرفت نمونهٔ یک', 'Sample progress one'), say('پیشرفت نمونهٔ دو', 'Sample progress two')].forEach((v, i) => {const r = n('div', 'os-progress-row'); r.append(n('span', '', v)); const track = n('div', 'os-progress-track'), fill = n('i'); fill.style.setProperty('--os-progress', i ? '35%' : '72%'); track.append(fill); r.append(track); box.append(r);});
    } else if (/multilingual/.test(key)) {box.append(chips(['FA ←', 'EN →'])); rows([say('دو زبان، دو جهت', 'Two languages, two directions')]);
    } else if (/blog/.test(key)) {rows([say('راهنمای انتخاب · ۶ دقیقه', 'Choosing well · 6 min'), say('پرسش‌های رایج · ۴ دقیقه', 'Common questions · 4 min')]);
    } else if (/care|support/.test(key)) {rows([say('درخواست جدید · در بررسی', 'New request · In review'), say('گزارش دوره‌ای · آماده', 'Periodic report · Ready')]);
    } else if (/customer|contact/.test(key)) {rows([say('شرکت نمونهٔ یک · فعال', 'Sample company one · Active'), say('شرکت نمونهٔ دو · پیگیری', 'Sample company two · Follow-up')]);
    } else {box.append(icon(topic)); rows([label + ' · ' + say('مورد نمونهٔ یک', 'Sample item one'), label + ' · ' + say('مورد نمونهٔ دو', 'Sample item two')]);}
    return box;
  }
  function intro(topic, icon) {
    const scene = n('div', 'os-topic-art os-topic-art-' + topic);
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('viewBox', '0 0 320 200'); svg.setAttribute('aria-hidden', 'true');
    const paths = {
      ecommerce: ['M105 65H215L225 165H95Z', 'M130 65V45Q160 10 190 45V65', 'M120 90H145V115H120ZM175 90H200V115H175ZM145 130H175V155H145', 'M225 140l15 15 25-30'],
      restaurant: ['M95 105a65 65 0 1 0 130 0a65 65 0 1 0-130 0', 'M115 105a45 45 0 1 0 90 0a45 45 0 1 0-90 0', 'M60 45V165M45 45V80H75V45M260 45V165M245 45V105H260', 'M135 65Q120 50 135 30M160 65Q145 50 160 30M185 65Q170 50 185 30'],
      clinic: ['M30 110H95L115 70L140 140L160 90L175 110H235', 'M220 30H245V55H270V80H245V105H220V80H195V55H220Z', 'M200 130H275V185H200ZM200 145H275M220 120V137M255 120V137', 'M220 165l10 10 25-25'],
      corporate: ['M65 170V90H120V170M130 170V45H185V170M195 170V70H250V170M35 170H285', 'M80 110H105M80 130H105M145 65H170M145 85H170M145 105H170M210 90H235M210 110H235', 'M65 65L155 20L235 35M220 20L235 35L215 45'],
      portfolio: ['M55 65H165V160H55ZM105 35H225V145H105ZM165 85H275V180H165Z', 'M180 155l25-35 20 20 20-30 15 45', 'M200 105a8 8 0 1 0 16 0a8 8 0 1 0-16 0', 'M70 135l20 40 5-20 20-5Z'],
      education: ['M45 75Q100 50 160 85Q220 50 275 75V170Q220 145 160 180Q100 145 45 170ZM160 85V180', 'M85 40L160 10L235 40L160 70ZM110 50V70Q160 95 210 70V50M235 40V85', 'M65 110H125M65 130H125M195 110H255M195 130H255'],
      jewelry: ['M75 70L110 25H210L245 70L160 180ZM75 70H245M110 25L160 180L210 25M110 25L135 70L160 25L185 70L210 25', 'M45 35V55M35 45H55M265 125V155M250 140H280M260 20V40M250 30H270'],
      crm: ['M130 75H190V135H130Z', 'M130 75L75 40M190 75L245 40M190 105H275M190 135L245 170M130 135L75 170M130 105H45', 'M55 20H95V60H55ZM225 20H265V60H225ZM255 85H295V125H255ZM225 150H265V190H225ZM55 150H95V190H55ZM25 85H65V125H25'],
      other: ['M125 145Q125 120 105 100Q65 35 160 20Q255 35 215 100Q195 120 195 145ZM125 160H195M140 180H180', 'M145 145L135 85L160 105L185 85L175 145M160 0V10M55 35L75 50M245 50L265 35M45 100H70M250 100H275']
    };
    (paths[topic] || paths.other).forEach((d, i) => {const p = document.createElementNS(svg.namespaceURI, 'path'); p.setAttribute('d', d); p.style.setProperty('--os-i', i); svg.append(p);}); scene.append(svg); return scene;
  }
  window.RvionOrderArt = {site, section, intro, looks, lookCode};
})();
