(function(){
  var STORAGE_KEY='rvion-theme';
  var root=document.documentElement;
  function apply(theme){
    if(theme==='light'||theme==='dark'){root.setAttribute('data-theme',theme)}
    else{root.removeAttribute('data-theme')}
  }
  var saved=null;
  try{saved=localStorage.getItem(STORAGE_KEY)}catch(e){}
  if(saved){apply(saved)}
  document.addEventListener('DOMContentLoaded',function(){
    var buttons=document.querySelectorAll('[data-theme-toggle]');
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
})();
