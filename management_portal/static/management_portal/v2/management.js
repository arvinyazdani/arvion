(()=>{
  const menu=document.querySelector('.m-menu'),sidebar=document.querySelector('.m-sidebar'),scrim=document.querySelector('.m-scrim');
  if(menu&&sidebar&&scrim){const close=()=>{sidebar.classList.remove('open');scrim.classList.remove('open');menu.setAttribute('aria-expanded','false')};menu.addEventListener('click',()=>{const open=!sidebar.classList.contains('open');sidebar.classList.toggle('open',open);scrim.classList.toggle('open',open);menu.setAttribute('aria-expanded',String(open))});scrim.addEventListener('click',close);document.addEventListener('keydown',event=>{if(event.key==='Escape')close()})}
  const button=document.querySelector('.m-alert-enable');if(!button)return;const fa=document.documentElement.lang==='fa';
  const b64=value=>{const padding='='.repeat((4-value.length%4)%4);const raw=atob((value+padding).replace(/-/g,'+').replace(/_/g,'/'));return Uint8Array.from([...raw].map(ch=>ch.charCodeAt(0)))};
  const csrf=()=>document.cookie.split('; ').find(v=>v.startsWith('csrftoken='))?.split('=')[1]||'';
  const label=text=>{button.textContent=text};
  const enable=async()=>{
    if(!('serviceWorker'in navigator)||!('PushManager'in window)||!window.RVION_VAPID_PUBLIC_KEY){label(fa?'اعلان روی سرور آماده نیست':'Push is not configured');button.disabled=true;return}
    const permission=await Notification.requestPermission();if(permission!=='granted'){label(fa?'اعلان مسدود است':'Alerts blocked');return}
    const registration=await navigator.serviceWorker.register('/service-worker.js');await navigator.serviceWorker.ready;
    let subscription=await registration.pushManager.getSubscription();if(!subscription)subscription=await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:b64(window.RVION_VAPID_PUBLIC_KEY)});
    const response=await fetch(window.RVION_PUSH_SUBSCRIBE,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrf()},body:JSON.stringify(subscription.toJSON())});
    if(!response.ok)throw new Error('subscription_failed');label(fa?'اعلان این دستگاه فعال است':'Alerts enabled on this device');button.disabled=true;
  };
  button.addEventListener('click',()=>enable().catch(()=>label(fa?'فعال‌سازی ناموفق بود؛ دوباره بزنید':'Activation failed; retry')));
  if(Notification.permission==='granted'&&window.RVION_VAPID_PUBLIC_KEY)enable().catch(()=>{});else if(Notification.permission==='denied'){label(fa?'اعلان مسدود است':'Alerts blocked');button.disabled=true}
})();
