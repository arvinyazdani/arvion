(()=>{
  const menu=document.querySelector('.m-menu'),sidebar=document.querySelector('.m-sidebar'),scrim=document.querySelector('.m-scrim');
  if(menu&&sidebar&&scrim){const close=()=>{sidebar.classList.remove('open');scrim.classList.remove('open');menu.setAttribute('aria-expanded','false')};menu.addEventListener('click',()=>{const open=!sidebar.classList.contains('open');sidebar.classList.toggle('open',open);scrim.classList.toggle('open',open);menu.setAttribute('aria-expanded',String(open))});scrim.addEventListener('click',close);document.addEventListener('keydown',event=>{if(event.key==='Escape')close()})}
  const languageLink=document.querySelector('.m-top-actions a.m-lang');if(languageLink){const target=document.documentElement.lang==='fa'?'en':'fa';languageLink.href=location.pathname.replace(/^\/(fa|en)(?=\/)/,`/${target}`)+location.search}
  const buttons=[...document.querySelectorAll('.m-alert-enable')];if(!buttons.length)return;
  const fa=document.documentElement.lang==='fa',help=document.querySelector('[data-notification-help]');
  const b64=value=>{const padding='='.repeat((4-value.length%4)%4);const raw=atob((value+padding).replace(/-/g,'+').replace(/_/g,'/'));return Uint8Array.from([...raw].map(ch=>ch.charCodeAt(0)))};
  const csrf=()=>document.cookie.split('; ').find(v=>v.startsWith('csrftoken='))?.split('=')[1]||'';
  const label=(text,state='')=>buttons.forEach(button=>{button.textContent=text;button.dataset.state=state});
  const explainBlocked=()=>{const iphone=/iPhone|iPad|iPod/i.test(navigator.userAgent);const text=iphone?(fa?'اعلان در آیفون مسدود است. Settings ← Notifications ← Rvion را باز و Allow Notifications را روشن کنید. برنامه باید از Home Screen اجرا شود.':'Notifications are blocked. Open Settings → Notifications → Rvion and enable Allow Notifications. Launch Rvion from the Home Screen.'):(fa?'مجوز قبلاً مسدود شده است. کنار آدرس سایت روی آیکن تنظیمات بزنید، Notifications را روی Allow قرار دهید و صفحه را دوباره بارگذاری کنید.':'Permission was previously blocked. Open site settings beside the address bar, set Notifications to Allow, then reload.');if(help)help.textContent=text;label(fa?'راهنمای رفع مسدودی اعلان':'How to unblock alerts','blocked')};
  const enable=async()=>{
    if(!('Notification'in window)||!('serviceWorker'in navigator)||!('PushManager'in window)){if(help)help.textContent=fa?'این مرورگر از اعلان وب پشتیبانی نمی‌کند. در آیفون، ابتدا سایت را به Home Screen اضافه کنید.':'This browser does not support web push. On iPhone, add the site to the Home Screen first.';label(fa?'اعلان در این مرورگر آماده نیست':'Alerts unavailable','unsupported');return}
    if(!window.RVION_VAPID_PUBLIC_KEY){label(fa?'تنظیمات سرور اعلان کامل نیست':'Server push is not configured','error');return}
    if(Notification.permission==='denied'){explainBlocked();return}
    label(fa?'در حال فعال‌سازی…':'Enabling…','loading');
    const permission=await Notification.requestPermission();if(permission!=='granted'){explainBlocked();return}
    const registration=await navigator.serviceWorker.register('/service-worker.js');await registration.update();await navigator.serviceWorker.ready;
    let subscription=await registration.pushManager.getSubscription();if(!subscription)subscription=await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:b64(window.RVION_VAPID_PUBLIC_KEY)});
    const response=await fetch(window.RVION_PUSH_SUBSCRIBE,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrf()},body:JSON.stringify(subscription.toJSON())});
    if(!response.ok)throw new Error('subscription_failed');if(help)help.textContent=fa?'این دستگاه با موفقیت برای همه رویدادهای مدیریتی ثبت شد.':'This device is registered for all management events.';label(fa?'اعلان این دستگاه فعال است':'Alerts enabled on this device','ready');
  };
  buttons.forEach(button=>button.addEventListener('click',()=>enable().catch(()=>{if(help)help.textContent=fa?'اتصال اعلان کامل نشد. اینترنت را بررسی و دوباره تلاش کنید.':'Alert setup failed. Check your connection and retry.';label(fa?'تلاش دوباره':'Try again','error')})));
  if('Notification'in window){if(Notification.permission==='granted')enable().catch(()=>label(fa?'تلاش دوباره':'Try again','error'));else if(Notification.permission==='denied')explainBlocked();}
})();
