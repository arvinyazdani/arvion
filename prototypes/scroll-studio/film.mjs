import {clamp,phase,frame} from './film-model.mjs';
const $=id=>document.getElementById(id), scene=$('scene'), story=$('story'), slider=$('timeline');
const parts=['orbits','seed','web','shell','chrome','blueprint','site','navigation','copy','illustration','tiles','phone','connections','nodes'].reduce((o,id)=>(o[id]=$(id),o),{});
const descriptions=[['یک ایده','همه‌چیز از همین نقطه شروع می‌شود.','حرکت تو، زمانِ این صحنه است.'],['نقشه اولیه','ایده، ساختار پیدا می‌کند.','خطوط به جایگاه محتوا و مسیر کاربر تبدیل می‌شوند.'],['هویت و محتوا','حالا یک سایت زنده پیش روی توست.','تصویر، نوشته و دکمه‌ها در همان نقشه جان می‌گیرند.'],['روی هر صفحه','یک تجربه، در دو اندازه.','همان سایت برای صفحه موبایل دوباره شکل می‌گیرد.'],['سیستم یکپارچه','زیبایی، به کار واقعی متصل می‌شود.','سایت، سفارش‌ها و پرونده مشتری؛ در یک مسیر.']];
let progress=0, queued=false, mobile=matchMedia('(max-width:600px)'), os=matchMedia('(prefers-reduced-motion:reduce)'), manual=false;
function attr(el,values){for(const [k,v] of Object.entries(values))el.setAttribute(k,String(v));}
function transform(el,x=0,y=0,s=1,angle=0){attr(el,{transform:`translate(${x} ${y}) translate(600 365) rotate(${angle}) scale(${s}) translate(-600 -365)`});}
for(let i=0;i<30;i++){const node=document.createElementNS('http://www.w3.org/2000/svg','circle');node.setAttribute('r',i%3===0?'3':'1.6');$('particles').append(node);}
const particles=[...$('particles').children];const paths=[...parts.connections.querySelectorAll('path')];const lengths=paths.map(p=>p.getTotalLength());
function render(p){
 const reduced=os.matches||manual;const f=frame(reduced?1:p);progress=p;document.body.classList.toggle('reduced',reduced);
 scene.setAttribute('viewBox',mobile.matches?'140 80 940 690':'0 0 1200 760');
 const {blueprint:b,site:s,phone:m,network:n}=f;
 attr(parts.orbits,{opacity:1-phase(f.p,0,.26),transform:`rotate(${f.p*105} 600 365)`});
 attr(parts.seed,{opacity:1-phase(f.p,.05,.25)});transform(parts.seed,0,0,1+phase(f.p,0,.24)*4);
 particles.forEach((node,i)=>{const a=i*2.399+f.p*.9,r=22+phase(f.p,0,.26)*(100+(i%6)*45);attr(node,{cx:600+Math.cos(a)*r,cy:365+Math.sin(a)*r*.62,opacity:(1-phase(f.p,.18,.38))*.7});});
 attr(parts.web,{opacity:phase(f.p,.08,.2)});transform(parts.web,-m*(mobile.matches?56:65),-n*25,.58+b*.42-m*.13,-12*(1-b)-m*3);
 attr(parts.shell,{fill:s>.01?'#171b27':'none',opacity:.3+b*.7});attr(parts.chrome,{opacity:b});
 attr(parts.blueprint,{opacity:b*(1-s), 'stroke-dashoffset':(1-b)*80});
 attr(parts.site,{opacity:s});
 transform(parts.navigation,0,(1-phase(f.p,.35,.45))*-20);attr(parts.navigation,{opacity:phase(f.p,.35,.45)});
 transform(parts.copy,(1-phase(f.p,.39,.54))*-70,0);attr(parts.copy,{opacity:phase(f.p,.39,.54)});
 transform(parts.illustration,(1-phase(f.p,.4,.58))*80,0,.85+phase(f.p,.4,.58)*.15);attr(parts.illustration,{opacity:phase(f.p,.4,.58)});
 transform(parts.tiles,0,(1-phase(f.p,.49,.63))*40);attr(parts.tiles,{opacity:phase(f.p,.49,.63)});
 attr(parts.phone,{opacity:m});transform(parts.phone,(1-m)*180+(mobile.matches?-55:0),(1-m)*75, .75+m*.25,18*(1-m));
 attr(parts.connections,{opacity:n});paths.forEach((path,i)=>attr(path,{'stroke-dasharray':lengths[i],'stroke-dashoffset':lengths[i]*(1-n)}));attr(parts.nodes,{opacity:n});transform(parts.nodes,0,(1-n)*30);
 const d=descriptions[f.chapter];$('chapter').textContent=d[0];$('headline').textContent=d[1];$('description').textContent=d[2];
 document.querySelector('.intro').style.opacity=String(1-phase(f.p,.05,.23));
 slider.value=String(Math.round(f.p*1000));$('percent').value=Math.round(f.p*100).toLocaleString('fa-IR')+'٪';
 slider.disabled=reduced;$('motion').setAttribute('aria-pressed',String(reduced));$('motion').textContent=os.matches?'حرکت مطابق دستگاه':manual?'فعال کردن حرکت':'کاهش حرکت';$('motion').disabled=os.matches;
 scene.dataset.progress=f.p.toFixed(3);
}
function read(){queued=false;const rect=story.getBoundingClientRect();render(clamp(-rect.top/Math.max(1,story.offsetHeight-innerHeight)));}
function schedule(){if(!queued){queued=true;requestAnimationFrame(read);}}
addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);os.addEventListener('change',schedule);mobile.addEventListener('change',schedule);
function scrub(p){window.scrollTo({top:story.offsetTop+p*(story.offsetHeight-innerHeight),behavior:'instant'});render(p);}
slider.addEventListener('input',()=>scrub(Number(slider.value)/1000));
slider.addEventListener('keydown',event=>{
 const deltas={ArrowRight:1,ArrowUp:1,ArrowLeft:-1,ArrowDown:-1,PageUp:100,PageDown:-100};
 if(event.key==='Home'||event.key==='End'||event.key in deltas){event.preventDefault();scrub(event.key==='Home'?0:event.key==='End'?1:clamp((Number(slider.value)+deltas[event.key])/1000));}
});
$('motion').addEventListener('click',()=>{manual=!manual;render(progress);schedule();});
$('replay').addEventListener('click',()=>{window.scrollTo({top:0,behavior:'instant'});read();slider.focus({preventScroll:true});});
$('replay').disabled=false;$('motion').disabled=false;read();
