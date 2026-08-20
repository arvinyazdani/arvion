(function(){
  var STORAGE_KEY='rvion-theme';
  var root=document.documentElement;
  function apply(theme){
    if(theme==='light'||theme==='dark'){root.setAttribute('data-theme',theme)}
    else{root.removeAttribute('data-theme')}
    updateButtons();
  }
  function effectiveTheme(){
    var explicit=root.getAttribute('data-theme');
    if(explicit==='light'||explicit==='dark')return explicit;
    return window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
  }
  function updateButtons(){
    var dark=effectiveTheme()==='dark';
    var fa=root.lang==='fa';
    document.querySelectorAll('[data-theme-toggle]').forEach(function(btn){
      btn.setAttribute('aria-pressed',dark?'true':'false');
      btn.setAttribute('aria-label',dark?(fa?'فعال‌کردن حالت روشن':'Switch to light mode'):(fa?'فعال‌کردن حالت تیره':'Switch to dark mode'));
      btn.title=btn.getAttribute('aria-label');
    });
  }
  var saved=null;
  try{saved=localStorage.getItem(STORAGE_KEY)}catch(e){}
  if(saved){apply(saved)}
  document.addEventListener('DOMContentLoaded',function(){
    var buttons=document.querySelectorAll('[data-theme-toggle]');
    updateButtons();
    buttons.forEach(function(btn){
      btn.addEventListener('click',function(){
        var current=root.getAttribute('data-theme');
        var prefersDark=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;
        var effectiveDark=current?current==='dark':prefersDark;
        var next=effectiveDark?'light':'dark';
        apply(next);
        try{localStorage.setItem(STORAGE_KEY,next)}catch(e){}
      });
    });
  });
  if(window.matchMedia){
    var colorScheme=window.matchMedia('(prefers-color-scheme: dark)');
    var syncSystem=function(){if(!root.hasAttribute('data-theme'))updateButtons()};
    if(colorScheme.addEventListener)colorScheme.addEventListener('change',syncSystem);
  }
})();
