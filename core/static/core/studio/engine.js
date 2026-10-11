/* ===== ARVION studio — cinematic miniature diorama (Three.js r128 + bloom + tilt-shift grade) ===== */
window.RvionStudioEngine=(()=>{
let textureScale=1, COVERS={};
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x)),lerp=(a,b,t)=>a+(b-a)*t,sm=t=>{t=clamp(t);return t*t*(3-2*t)},D=Math.PI/180;
const rnd=i=>{const s=Math.sin(i*91.7+3.1)*43758.5;return s-Math.floor(s)};
const OR=0xff8a2a;                                   /* brand orange */
const hdr=(c,k)=>new THREE.Color(c).multiplyScalar(k);
const at=(m,x=0,y=0,z=0)=>{m.position.set(x,y,z);return m};
const grp=(...k)=>{const g=new THREE.Group();k.forEach(o=>o&&g.add(o));return g};
const GEO={};const geo=(k,f)=>GEO[k]||(GEO[k]=f());

/* ---------- materials ---------- */
const MAT={};
const std=(k,o)=>MAT[k]||(MAT[k]=new THREE.MeshStandardMaterial(o));
const charcoal=()=>std('ch',{color:0x24262b,roughness:.52,metalness:.3,envMapIntensity:.9});
const charcoal2=()=>std('ch2',{color:0x1a1c20,roughness:.45,metalness:.45,envMapIntensity:1});
const black=()=>std('bk',{color:0x101216,roughness:.3,metalness:.7,envMapIntensity:1.6});
const steel=()=>std('st',{color:0x8c9099,roughness:.35,metalness:.9,envMapIntensity:1.1});
const concrete=()=>std('cn',{color:0xb9bcc2,roughness:.7,metalness:.05});
const glowM=(k=1.6,c=OR,op)=>{const key='gl'+k+'_'+c+'_'+op;return MAT[key]||(MAT[key]=new THREE.MeshBasicMaterial({color:hdr(c,k),transparent:op!=null,opacity:op==null?1:op,depthWrite:op==null}))};
const addM=(c,op,k=1)=>{const key='ad'+c+op+k;return MAT[key]||(MAT[key]=new THREE.MeshBasicMaterial({color:hdr(c,k),transparent:true,opacity:op,blending:THREE.AdditiveBlending,depthWrite:false,side:THREE.DoubleSide}))};
const box=(w,h,d,m,x,y,z)=>{const o=new THREE.Mesh(geo('b'+[w,h,d],()=>new THREE.BoxGeometry(w,h,d)),m);o.position.set(x||0,y||0,z||0);return o};
const cyl=(rt,rb,h,m,x,y,z,s=28)=>{const o=new THREE.Mesh(geo('c'+[rt,rb,h,s],()=>new THREE.CylinderGeometry(rt,rb,h,s)),m);o.position.set(x||0,y||0,z||0);return o};
const sph=(r,m,x,y,z,s=20)=>{const o=new THREE.Mesh(geo('s'+r+s,()=>new THREE.SphereGeometry(r,s,Math.max(8,s*.7|0))),m);o.position.set(x||0,y||0,z||0);return o};
const cone=(r,h,m,x,y,z,s=24)=>{const o=new THREE.Mesh(geo('k'+[r,h,s],()=>new THREE.ConeGeometry(r,h,s)),m);o.position.set(x||0,y||0,z||0);return o};
const tor=(r,t,m,x,y,z,s=48)=>{const o=new THREE.Mesh(geo('t'+[r,t,s],()=>new THREE.TorusGeometry(r,t,10,s)),m);o.position.set(x||0,y||0,z||0);return o};
function slab(w,h,d,m,r=.1,x,y,z){
  const g=geo('r'+[w,h,d,r],()=>{const s=new THREE.Shape(),hw=w/2,hh=h/2,rr=Math.min(r,hw,hh);
    s.moveTo(-hw+rr,-hh);s.lineTo(hw-rr,-hh);s.quadraticCurveTo(hw,-hh,hw,-hh+rr);s.lineTo(hw,hh-rr);s.quadraticCurveTo(hw,hh,hw-rr,hh);s.lineTo(-hw+rr,hh);s.quadraticCurveTo(-hw,hh,-hw,hh-rr);s.lineTo(-hw,-hh+rr);s.quadraticCurveTo(-hw,-hh,-hw+rr,-hh);
    const g=new THREE.ExtrudeGeometry(s,{depth:d,bevelEnabled:true,bevelSize:.012,bevelThickness:.012,bevelSegments:2,curveSegments:6});g.translate(0,0,-d/2);return g});
  return at(new THREE.Mesh(g,m),x,y,z);
}
const shadows=o=>{o.traverse(c=>{if(c.isMesh){c.castShadow=true;c.receiveShadow=true}});return o};

/* ---------- canvas textures ---------- */
function ctex(w,h,draw,opt){
  const c=document.createElement('canvas'),scale=Math.min(textureScale,1024/Math.max(w,h));c.width=Math.max(1,Math.round(w*scale));c.height=Math.max(1,Math.round(h*scale));const context=c.getContext('2d');context.scale(c.width/w,c.height/h);draw(context,w,h);
  const t=new THREE.CanvasTexture(c);t.anisotropy=2;if(opt&&opt.repeat){t.wrapS=t.wrapT=THREE.RepeatWrapping}return t;
}
const FONT='Vazirmatn, system-ui, sans-serif';
function spaced(x,txt,px,py,sp,align){let w=0;[...txt].forEach(ch=>w+=x.measureText(ch).width+sp);w-=sp;let cx=align==='center'?px-w/2:align==='right'?px-w:px;[...txt].forEach(ch=>{x.fillText(ch,cx,py);cx+=x.measureText(ch).width+sp})}
function rr(x,X,Y,W,H,r){x.beginPath();x.moveTo(X+r,Y);x.arcTo(X+W,Y,X+W,Y+H,r);x.arcTo(X+W,Y+H,X,Y+H,r);x.arcTo(X,Y+H,X,Y,r);x.arcTo(X,Y,X+W,Y,r);x.closePath()}
function aMark(x,cx,cy,s,col){const h=s*.9;x.fillStyle=col==='#ffffff'?'#ffffff':'#f47749';rr(x,cx-h*.62,cy-h*.62,h*1.24,h*1.24,h*.34);x.fill();x.fillStyle='#0b1220';x.font='900 '+h*1.05+'px Arial,sans-serif';x.textAlign='center';x.textBaseline='middle';x.fillText('R',cx,cy+h*.04);}
function wordmark(x,cx,cy,size,col,sub){
  x.font='800 '+size+'px '+FONT;x.fillStyle=col;x.textBaseline='middle';
  const t='RVION',sp=size*.16;let w=0;[...t].forEach(ch=>w+=x.measureText(ch).width+sp);w-=sp;const aw=size*.78;
  const left=cx-(w+aw+sp)/2;aMark(x,left+aw/2,cy,size*.62,'#ff8a2a');x.fillStyle=col;spaced(x,t,left+aw+sp,cy+size*.02,sp,'left');
  if(sub){x.font='500 '+size*.26+'px '+FONT;x.fillStyle='rgba(255,255,255,.55)';spaced(x,sub,cx,cy+size*.78,size*.07,'center')}
}
/* mock UIs shown on the cards / screens */
const UI={
 idea(x,w,h){x.fillStyle='#f4f2ec';x.fillRect(0,0,w,h);x.strokeStyle='#6a6e78';x.lineWidth=3;x.strokeRect(w*.12,h*.1,w*.76,h*.46);x.beginPath();x.moveTo(w*.12,h*.1);x.lineTo(w*.88,h*.56);x.moveTo(w*.88,h*.1);x.lineTo(w*.12,h*.56);x.stroke();
   x.fillStyle='#f4f2ec';x.beginPath();x.arc(w*.5,h*.33,w*.15,0,7);x.fill();x.strokeStyle='#2b2f3a';x.lineWidth=4;x.beginPath();x.arc(w*.5,h*.31,w*.12,0,7);x.stroke();x.strokeRect(w*.45,h*.43,w*.1,h*.04);
   x.strokeStyle='#ff8a2a';x.beginPath();[-1,0,1].forEach(k=>{x.moveTo(w*.5+k*w*.2,h*.12);x.lineTo(w*.5+k*w*.26,h*.08)});x.stroke();
   x.fillStyle='#14161b';x.font='800 '+h*.07+'px '+FONT;x.textAlign='left';x.fillText('Your Idea',w*.1,h*.84);x.fillStyle='#ff8a2a';x.fillRect(w*.1,h*.9,w*.14,4)},
 design(x,w,h){x.fillStyle='#fafafa';x.fillRect(0,0,w,h);x.fillStyle='#101216';rr(x,w*.06,h*.07,w*.88,h*.5,16);x.fill();
   const g=x.createRadialGradient(w*.74,h*.3,0,w*.74,h*.3,w*.22);g.addColorStop(0,'#bdbdc4');g.addColorStop(1,'#34353b');x.fillStyle=g;x.beginPath();x.arc(w*.74,h*.31,w*.2,0,7);x.fill();
   x.fillStyle='#fff';x.font='800 '+h*.058+'px '+FONT;x.textAlign='left';x.fillText('Stunning',w*.12,h*.27);x.fillText('Web Design',w*.12,h*.34);x.fillStyle='#ff8a2a';rr(x,w*.12,h*.42,w*.22,h*.04,6);x.fill();
   x.fillStyle='#d9dbe0';[0,1,2].forEach(i=>{x.fillRect(w*.08,h*.64+i*h*.07,w*(i==1?.5:.84),h*.025)});x.fillStyle='#eceef2';[0,1,2].forEach(i=>rr(x,w*.08+i*w*.29,h*.86,w*.26,h*.08,8)||x.fill())},
 code(x,w,h){x.fillStyle='#0d0f13';x.fillRect(0,0,w,h);const cols=['#ff8a2a','#7aa2ff','#9be28f','#e9e9ee','#c58cff'];
   for(let i=0;i<24;i++){const y=h*.07+i*h*.03,ind=(i%5)*w*.04+(i%7===0?0:w*.02);let X=w*.1+ind;const n=2+(i*3%4);for(let k=0;k<n;k++){const ww=w*(.06+rnd(i*7+k)*.16);x.fillStyle=cols[(i+k*2)%5];x.globalAlpha=.9;x.fillRect(X,y,ww,h*.012);x.globalAlpha=1;X+=ww+w*.025}x.fillStyle='#4a4f5c';x.fillRect(w*.04,y,w*.03,h*.012)}
   x.fillStyle='#fff';x.font='800 '+h*.06+'px '+FONT;x.textAlign='left';x.fillText('Clean Code',w*.1,h*.9)},
 live(x,w,h){const sk=x.createLinearGradient(0,0,0,h*.62);sk.addColorStop(0,'#4d7fb8');sk.addColorStop(1,'#d9e6f2');x.fillStyle='#f5f6f8';x.fillRect(0,0,w,h);x.fillStyle=sk;x.fillRect(0,0,w,h*.62);
   x.fillStyle='#35506c';x.beginPath();x.moveTo(0,h*.6);x.lineTo(w*.2,h*.36);x.lineTo(w*.34,h*.48);x.lineTo(w*.55,h*.24);x.lineTo(w*.78,h*.5);x.lineTo(w,h*.4);x.lineTo(w,h*.62);x.lineTo(0,h*.62);x.fill();
   x.fillStyle='#e8eef5';x.beginPath();x.moveTo(w*.55,h*.24);x.lineTo(w*.5,h*.31);x.lineTo(w*.54,h*.3);x.lineTo(w*.58,h*.33);x.lineTo(w*.61,h*.3);x.fill();
   x.fillStyle='#fff';x.font='800 '+h*.06+'px '+FONT;x.textAlign='left';x.fillText('Live',w*.08,h*.2);x.fillText('Website',w*.08,h*.27);x.fillStyle='#ff8a2a';rr(x,w*.08,h*.33,w*.16,h*.035,6);x.fill();
   x.fillStyle='#d6d9df';[0,1,2].forEach(i=>x.fillRect(w*.08,h*.7+i*h*.06,w*(i==1?.5:.8),h*.02))},
 dash(x,w,h,acc){acc=acc||'#ff8a2a';x.fillStyle='#10131a';x.fillRect(0,0,w,h);x.fillStyle='#171b24';rr(x,w*.03,h*.06,w*.94,h*.88,12);x.fill();
   x.fillStyle='#e9eaf0';x.font='700 '+h*.06+'px '+FONT;x.textAlign='left';x.fillText('Overview',w*.07,h*.16);
   const bars=[.4,.62,.5,.78,.58,.9,.7,.84];bars.forEach((b,i)=>{x.fillStyle=i%2?'#3b4254':acc;x.fillRect(w*.08+i*w*.075,h*.82-h*.4*b,w*.05,h*.4*b)});
   x.strokeStyle='#7aa2ff';x.lineWidth=3;x.beginPath();bars.forEach((b,i)=>{const X=w*.105+i*w*.075,Y=h*.74-h*.3*b;i?x.lineTo(X,Y):x.moveTo(X,Y)});x.stroke();
   x.fillStyle='#232938';[0,1].forEach(i=>rr(x,w*.7,h*.22+i*h*.3,w*.24,h*.24,8)||x.fill());x.fillStyle='#fff';x.fillRect(w*.73,h*.3,w*.1,h*.02);x.fillRect(w*.73,h*.6,w*.14,h*.02)},
};
function belt(){return ctex(256,128,(x,w,h)=>{x.fillStyle='#16171a';x.fillRect(0,0,w,h);for(let i=0;i<16;i++){x.fillStyle=i%2?'#0f1012':'#202226';x.fillRect(i*16,0,8,h)}x.fillStyle='rgba(255,255,255,.04)';x.fillRect(0,0,w,3);x.fillRect(0,h-3,w,3)},{repeat:1})}
function concreteTex(){return ctex(512,512,(x,w,h)=>{x.fillStyle='#4a4c52';x.fillRect(0,0,w,h);for(let i=0;i<5200;i++){const g=40+rnd(i)*50|0;x.fillStyle='rgba('+g+','+g+','+(g+4)+','+(.05+rnd(i+9)*.12)+')';x.fillRect(rnd(i+3)*w,rnd(i+5)*h,1+rnd(i+7)*2,1+rnd(i+11)*2)}x.strokeStyle='rgba(0,0,0,.18)';x.lineWidth=2;for(let i=0;i<=4;i++){x.beginPath();x.moveTo(i*128,0);x.lineTo(i*128,h);x.moveTo(0,i*128);x.lineTo(w,i*128);x.stroke()}},{repeat:1})}
let GT=null;
function glowTex(){if(GT)return GT;const c=document.createElement('canvas');c.width=c.height=128;const x=c.getContext('2d'),g=x.createRadialGradient(64,64,0,64,64,64);g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(.3,'rgba(255,255,255,.35)');g.addColorStop(1,'rgba(255,255,255,0)');x.fillStyle=g;x.fillRect(0,0,128,128);return GT=new THREE.CanvasTexture(c)}
const sprite=(col,size,op,k=1)=>{const s=new THREE.Sprite(new THREE.SpriteMaterial({map:glowTex(),color:hdr(col,k),blending:THREE.AdditiveBlending,transparent:true,opacity:op,depthWrite:false}));s.scale.set(size,size,1);return s};
const decal=(w,h,tex,x,y,z,rx,ry,op)=>{const m=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({map:tex,transparent:true,opacity:op==null?1:op,depthWrite:false}));m.position.set(x,y,z);m.rotation.set(rx||0,ry||0,0);return m};

/* ---------- people, plants, robots ---------- */
function person(o){
  o=o||{};const g=new THREE.Group(),sk=std('skin',{color:0xc99b7c,roughness:.7}),cl=std('cloth',{color:0x0e0f12,roughness:.65,metalness:.1}),hr=std('hair',{color:0x15110e,roughness:.8});
  const sit=!!o.sit;
  const hip=sit?.52:.92;
  if(sit){g.add(box(.3,.16,.55,cl,-.14,hip,.18),box(.3,.16,.55,cl,.14,hip,.18),cyl(.07,.07,.5,cl,-.14,.27,.44,10),cyl(.07,.07,.5,cl,.14,.27,.44,10))}
  else{g.add(cyl(.085,.07,.92,cl,-.12,.46,0,10),cyl(.085,.07,.92,cl,.12,.46,0,10))}
  const tz=sit?-.02:0;
  g.add(slab(.46,.62,.26,cl,.12,0,hip+.34,tz));
  g.add(cyl(.05,.05,.1,sk,0,hip+.7,tz,8));
  g.add(sph(.13,sk,0,hip+.86,tz,14),sph(.135,hr,0,hip+.9,tz-.015,14));
  const ar=(x,rz,rx)=>{const a=grp();a.position.set(x,hip+.58,tz);a.rotation.set(rx||0,0,rz||0);a.add(cyl(.055,.05,.5,cl,0,-.25,0,8),sph(.05,sk,0,-.52,0,8));return a};
  g.add(ar(-.27,.05,o.armL||0),ar(.27,-.05,o.armR||0));
  const logo=new THREE.Mesh(new THREE.PlaneGeometry(.13,.13),new THREE.MeshBasicMaterial({map:logoTex(),transparent:true}));logo.position.set(0,hip+.5,tz-.135);logo.rotation.y=Math.PI;g.add(logo);
  const lg2=logo.clone();lg2.position.z=tz+.135;lg2.rotation.y=0;g.add(lg2);
  g.scale.setScalar(o.s||1);return g;
}
let LT=null;const logoTex=()=>LT||(LT=ctex(64,64,(x,w,h)=>{aMark(x,32,34,36,'#ff8a2a')}));
function plant(s,seed){
  const g=new THREE.Group(),pot=std('pot',{color:0xc9c9cc,roughness:.75});
  g.add(cyl(.34*s,.26*s,.5*s,pot,0,.25*s,0,18));
  const leaf=std('leaf',{color:0x2a5a33,roughness:.55,metalness:.05,emissive:0x07160a});
  const lg=geo('leaf',()=>{const q=new THREE.SphereGeometry(1,8,6);q.scale(.11,.015,.5);q.translate(0,0,.5);return q});
  for(let i=0;i<22;i++){const m=new THREE.Mesh(lg,i%5===0?std('leaf2',{color:0x37733f,roughness:.5}):leaf);const a=rnd(i+seed)*6.28,t=.25+rnd(i+seed+3)*.9;m.rotation.set(-t,a,0,'YXZ');m.position.set(0,.5*s,0);m.scale.setScalar(s*(.9+rnd(i+seed+7)*.9));g.add(m)}
  return g;
}
function arm(){
  const g=new THREE.Group(),yaw=grp(),sh=grp(),el=grp(),wr=grp();
  g.add(cyl(.62,.7,.32,black(),0,.16,0,32),cyl(.46,.5,.5,charcoal2(),0,.55,0,32),tor(.47,.035,glowM(1.4),0,.32,0,40).rotateX(Math.PI/2));
  const ring=g.children[2];ring.rotation.x=Math.PI/2;
  const lg=new THREE.Mesh(new THREE.PlaneGeometry(.34,.34),new THREE.MeshBasicMaterial({map:logoTex(),transparent:true}));lg.position.set(0,.5,.52);g.add(lg);
  yaw.position.set(0,.8,0);g.add(yaw);
  yaw.add(cyl(.34,.34,.4,black(),0,.1,0,28),sph(.34,black(),0,.55,0,24));
  sh.position.set(0,.55,0);yaw.add(sh);
  sh.add(cyl(.2,.17,1.9,black(),0,.95,0,20),tor(.2,.03,glowM(1.3),0,.2,0,24));
  el.position.set(0,1.9,0);sh.add(el);el.add(sph(.28,black(),0,0,0,20),cyl(.15,.13,1.6,black(),0,.8,0,18));
  wr.position.set(0,1.6,0);el.add(wr);wr.add(sph(.2,black(),0,0,0,16),box(.5,.1,.14,charcoal2(),0,.14,0),box(.07,.34,.12,steel(),-.2,.3,0),box(.07,.34,.12,steel(),.2,.3,0));
  g.userData={yaw,sh,el,wr};return shadows(g);
}

/* ---------- the assembly line (hero) ---------- */
const STAGES=[-7.0,-3.7,-.4,2.9];
function buildAssembly(){
  const g=new THREE.Group(),A={};
  /* conveyor */
  const L=14.6,cx=-1.8;
  g.add(box(L,.56,1.9,charcoal2(),cx,.5,0));
  [-1,1].forEach(s=>g.add(cyl(.5,.5,1.7,black(),cx+s*(L/2),.6,0,28).rotateX(Math.PI/2)));
  g.children.slice(-2).forEach(m=>m.rotation.x=Math.PI/2);
  const bt=belt();bt.repeat.set(L/1.6,1);A.beltTex=bt;
  const top=new THREE.Mesh(new THREE.PlaneGeometry(L,1.5),new THREE.MeshStandardMaterial({map:bt,roughness:.6,metalness:.1}));top.rotation.x=-Math.PI/2;top.position.set(cx,.79,0);g.add(top);
  g.add(box(L,.1,.1,glowM(1.6),cx,.8,.82),box(L,.1,.1,glowM(1.6),cx,.8,-.82));
  [-6,-1,3.5].forEach(x=>{g.add(box(.3,.4,1.9,charcoal2(),x,.2,0))});
  /* front panel with stage labels */
  const lab=ctex(2048,160,(x,w,h)=>{x.clearRect(0,0,w,h);const names=['IDEA','DESIGN','DEVELOP','LAUNCH'];
    x.strokeStyle='rgba(255,138,42,.55)';x.setLineDash([4,10]);x.lineWidth=2;x.beginPath();x.moveTo(w*.03,h*.3);x.lineTo(w*.97,h*.3);x.stroke();x.setLineDash([]);
    names.forEach((n,i)=>{const X=w*((STAGES[i]-(cx-(L-.6)/2))/(L-.6));x.fillStyle='#ffb061';x.beginPath();x.arc(X,h*.3,10,0,7);x.fill();x.fillStyle='rgba(255,138,42,.35)';x.beginPath();x.arc(X,h*.3,20,0,7);x.fill();
      x.fillStyle='rgba(235,238,245,.92)';x.font='500 52px '+FONT;x.textAlign='center';x.textBaseline='middle';spaced(x,n,X,h*.72,6,'center')})});
  g.add(decal(L-.6,1.0,lab,cx,.52,.955,0,0));
  /* cards */
  const defs=[['idea',0xf4f2ec],['design',0xfafafa],['code',0x16181d],['live',0xf1f2f4]];A.cards=defs.map(([k,c],i)=>{
    const card=new THREE.Group();card.position.set(STAGES[i],.84,.05);card.rotation.y=-.62;card.scale.setScalar(1.18);
    const tx=ctex(512,700,(x,w,h)=>UI[k](x,w,h));
    card.add(slab(1.18,1.58,.07,std('bz'+k,{color:new THREE.Color(c).multiplyScalar(.82).getHex(),roughness:.4,metalness:.2}),.07,0,.82,0));
    const sc=new THREE.Mesh(new THREE.PlaneGeometry(1.06,1.46),new THREE.MeshBasicMaterial({map:tx,color:0xdedede}));sc.position.set(0,.82,.075);card.add(sc);
    card.add(box(.5,.05,.28,black(),0,.03,-.05));
    const rim=new THREE.Mesh(new THREE.PlaneGeometry(1.34,1.74),new THREE.MeshBasicMaterial({map:glowTex(),color:hdr(OR,2.2),transparent:true,opacity:0,blending:THREE.AdditiveBlending,depthWrite:false}));rim.position.set(0,.82,-.05);card.add(rim);card.userData.rim=rim;card.userData.i=i;
    card.rotation.x=-.04;g.add(shadows(card));return card});
  /* pendant lamps over the line */
  STAGES.forEach(x=>{const lm=new THREE.Group();lm.position.set(x,6.2,.2);lm.add(cyl(.012,.012,2.6,black(),0,1.3,0,6),cyl(.26,.34,.28,black(),0,0,0,18),cyl(.22,.22,.04,glowM(2.4,0xffd6a0),0,-.15,0,18));
    const cn=new THREE.Mesh(geo('lc',()=>new THREE.ConeGeometry(1.7,5.4,28,1,true)),addM(0xffc890,.045));cn.position.set(0,-2.85,0);lm.add(cn);g.add(lm)});
  /* arms */
  const a1=arm();a1.position.set(-3.8,0,-2.8);a1.rotation.y=.2;g.add(a1);
  const a2=arm();a2.position.set(3.6,0,-3.0);a2.rotation.y=.1;g.add(a2);A.arms=[a1,a2];
  /* portal */
  const P=new THREE.Group();P.position.set(7.5,0,0);P.rotation.y=-Math.PI/2;g.add(P);
  const face=ctex(2048,2048,(x,w,h)=>{const gr=x.createLinearGradient(0,0,0,h);gr.addColorStop(0,'#2a2c32');gr.addColorStop(1,'#1d1f24');x.fillStyle=gr;x.fillRect(0,0,w,h);
      x.strokeStyle='rgba(255,255,255,.05)';x.lineWidth=2;for(let i=1;i<5;i++){x.beginPath();x.moveTo(0,i*h/5);x.lineTo(w,i*h/5);x.stroke()}
      wordmark(x,w*.5,h*.18,220,'#f2f2f4');x.fillStyle='rgba(255,255,255,.62)';x.font='500 80px '+FONT;x.textAlign='center';spaced(x,'WE BUILD',w*.5,h*.31,12,'center');spaced(x,'BETTER WEBSITES',w*.5,h*.38,12,'center')});
  P.add(box(8.2,9.2,3.6,charcoal(),0,4.6,0));
  const fp=new THREE.Mesh(new THREE.PlaneGeometry(8.2,9.2),new THREE.MeshStandardMaterial({map:face,roughness:.55,metalness:.3}));fp.position.set(0,4.6,1.81);P.add(fp);
  /* opening (dark cavity + orange portal) */
  P.add(box(3.7,4.1,.3,std('cav',{color:0x120a05,roughness:1}),0,2.1,1.78));
  const pg=ctex(256,256,(x,w,h)=>{const gr=x.createLinearGradient(0,0,0,h);gr.addColorStop(0,'#ff9b3a');gr.addColorStop(.6,'#f06d12');gr.addColorStop(1,'#8f3a08');x.fillStyle=gr;x.fillRect(0,0,w,h)});
  const inner=new THREE.Mesh(new THREE.PlaneGeometry(3.3,3.8),new THREE.MeshBasicMaterial({map:pg,color:hdr(0xffffff,.95)}));inner.position.set(0,2.05,1.93);P.add(inner);A.portal=inner;
  const fr=glowM(2.0);[[0,4.25,3.9,.16],[ -1.82,2.15,.16,4.2],[1.82,2.15,.16,4.2]].forEach(([x,y,w,h])=>P.add(box(w,h,.2,fr,x,y,1.98)));
  P.add(box(4.4,.1,.1,glowM(1.2),0,.06,2.1));
  /* roof terrace: rail + plants */
  P.add(box(8.4,.1,.1,glowM(1.7),0,9.55,1.7),box(8.4,.7,.1,addM(OR,.1),0,9.9,1.7));
  [-3,-1.2,1.8,3.2].forEach((x,i)=>{const pl=plant(.9+rnd(i)*.4,i*5);pl.position.set(x,9.2,.6);P.add(pl)});
  /* portal light */

  const spill=sprite(OR,15,.38,1.2);spill.position.set(0,.25,5.2);spill.material.rotation=0;P.add(spill);
  /* floor glow outlines */
  const outl=(x1,z1,x2,z2)=>{const l=Math.hypot(x2-x1,z2-z1),m=box(l,.03,.07,glowM(1.5),(x1+x2)/2,.03,(z1+z2)/2);m.rotation.y=-Math.atan2(z2-z1,x2-x1);return m};
  g.add(outl(-11,4.2,5.5,4.2),outl(-11,4.2,-11,-5),outl(5.5,4.2,5.5,-5));
  /* big plinth cubes with copy */
  const cube=(txt,fa,x,z,ry,w,h,d)=>{const m=ctex(512,512,(c,W,H)=>{c.fillStyle='#202227';c.fillRect(0,0,W,H);c.fillStyle='rgba(255,255,255,.55)';c.font='500 44px '+FONT;c.textAlign=fa?'right':'left';c.direction=fa?'rtl':'ltr';txt.forEach((t,i)=>{c.fillText(t,fa?W*.9:W*.1,H*.34+i*54)});if(fa){c.fillStyle='#ff8a2a';c.fillRect(W*.9-80,H*.84,80,5)}});
    const b=box(w,h,d,charcoal(),x,h/2,z);b.rotation.y=ry;const f=new THREE.Mesh(new THREE.PlaneGeometry(w*.96,h*.96),new THREE.MeshStandardMaterial({map:m,roughness:.6,metalness:.2}));f.position.set(0,0,d/2+.01);b.add(f);b.add(box(w,.05,.05,glowM(1.4),0,-h/2+.04,d/2+.02));return b};
  g.add(shadows(cube(['GREAT','WEBSITES','FOR A BRIGHTER','TOMORROW'],false,-12.8,-1.6,.5,2.6,2.8,2.6)));
  g.add(shadows(cube(['طراحی وب‌سایت','سئو و بهینه‌سازی','هویت بصری','پشتیبانی و توسعه'],true,8.6,8.2,-.1,3.4,2.2,3.0)));
  /* glass panel + rocket */
  const gp=new THREE.Group();gp.position.set(11.6,0,3.6);gp.rotation.y=-.95;
  gp.add(box(3.6,3.2,.08,std('glass',{color:0xaab8d0,roughness:.05,metalness:0,transparent:true,opacity:.13,envMapIntensity:1.6,depthWrite:false}),0,1.9,0),box(3.7,.06,.1,glowM(1.5),0,3.5,0));
  gp.add(decal(2.9,1.2,ctex(512,256,(x,w,h)=>{x.fillStyle='#fff';x.font='700 54px '+FONT;x.textAlign='right';x.direction='rtl';x.fillText('کسب‌وکار شما',w*.96,h*.4);x.fillText('شایستهٔ بهترین‌هاست',w*.96,h*.72)}),0,2.0,.06));g.add(gp);
  const rk=new THREE.Group();rk.position.set(12.4,0,6.8);
  rk.add(cyl(.9,1.05,.18,black(),0,.09,0,32),tor(.95,.03,glowM(1.6),0,.2,0).rotateX(Math.PI/2));rk.children[1].rotation.x=Math.PI/2;
  const body=std('rk',{color:0xe8e9ee,roughness:.35,metalness:.3});
  rk.add(cyl(.38,.42,1.6,body,0,1.15,0,24),cyl(.04,.38,.8,body,0,2.35,0,24),cyl(.4,.4,.16,glowM(1.3),0,.9,0,24));
  [0,1,2].forEach(i=>{const f=box(.06,.5,.38,body,Math.cos(i*2.09)*.45,.55,Math.sin(i*2.09)*.45);f.rotation.y=-i*2.09;rk.add(f)});
  const fl=new THREE.Mesh(new THREE.ConeGeometry(.28,1.2,16),addM(0xffa040,.8,2));fl.position.set(0,-.05+.28,0);fl.rotation.x=Math.PI;fl.position.y=.28;rk.add(fl);A.flame=fl;
  const lgR=new THREE.Mesh(new THREE.PlaneGeometry(.3,.3),new THREE.MeshBasicMaterial({map:logoTex(),transparent:true}));lgR.position.set(0,1.45,.43);rk.add(lgR);
  A.rocket=rk;g.add(shadows(rk));

  /* desk */
  const dk=new THREE.Group();dk.position.set(-3.2,0,5.8);dk.rotation.y=.12;
  dk.add(box(4.2,.12,1.6,black(),0,1.05,0),box(.1,1.05,1.5,charcoal2(),-2,.52,0),box(.1,1.05,1.5,charcoal2(),2,.52,0),box(4,.9,.12,charcoal2(),0,.52,-.7));
  const scr=(x,ry,w,h,k)=>{const s=grp();s.position.set(x,1.9,-.15);s.rotation.y=ry;s.add(slab(w,h,.06,black(),.05,0,0,0),(()=>{const m=new THREE.Mesh(new THREE.PlaneGeometry(w-.1,h-.1),new THREE.MeshBasicMaterial({map:ctex(512,320,(c,W,H)=>UI.dash(c,W,H,k))}));m.position.z=.04;return m})(),box(.06,.5,.06,black(),0,-h/2-.2,0));return s};
  dk.add(scr(-.7,.12,1.7,1.1),scr(.95,-.18,1.2,.8,'#7aa2ff'));
  dk.add(box(.9,.03,.3,charcoal2(),-.5,1.13,.45));
  const chair=grp(box(.8,.12,.8,black(),0,.7,0),box(.8,1.0,.1,black(),0,1.2,-.4),cyl(.06,.06,.6,black(),0,.38,0,8),cyl(.45,.45,.06,black(),0,.05,0,16));chair.position.set(-.8,0,1.7);dk.add(chair);
  const worker=person({sit:true,armL:-1.0,armR:-1.0});worker.position.set(-.8,.07,1.65);worker.rotation.y=Math.PI;dk.add(worker);
  g.add(shadows(dk));
  /* staff */
  const p1=person({s:1.02,armR:-.2});p1.position.set(-5.2,0,2.3);p1.rotation.y=Math.PI*1.05;g.add(shadows(p1));
  const p2=person({s:1.02,armR:-.9});p2.position.set(1.4,0,2.2);p2.rotation.y=Math.PI*1.1;g.add(shadows(p2));
  const p3=person({s:1.0});p3.position.set(10.4,0,6.6);p3.rotation.y=Math.PI*.7;g.add(shadows(p3));
  /* plants on the floor */
  [[-10.4,-1.2,-1.5,1.3],[-6.4,-5.0,-.3,1.1],[9.6,-4.6,-3.2,1.2],[6.0,5.2,.4,1.0],[-.8,-5.4,-4.8,1.2]].forEach(([x,y,z,s],i)=>{const p=plant(s,i*13);p.position.set(x,0,z);g.add(shadows(p))});
  A.root=g;return A;
}

/* ---------- shared prop helpers ---------- */
function coverTex(key){const t=new THREE.Texture();const src=COVERS[key];if(!src)return ctex(32,32,(c,w,h)=>{c.fillStyle='#24262b';c.fillRect(0,0,w,h)});const im=new Image();im.onload=()=>{t.image=im;t.needsUpdate=true;t.anisotropy=2};im.src=src;return t}
function sign(en,fa,w,h,o){o=o||{};return ctex(1024,Math.round(1024*h/w),(x,W,H)=>{x.fillStyle=o.bg||'#202227';x.fillRect(0,0,W,H);
  x.fillStyle='#ff8a2a';x.fillRect(W*.07,H*.2,W*.012,H*.6);x.fillStyle='#f2f2f4';x.font='800 '+H*.34+'px '+FONT;x.textAlign='left';x.textBaseline='middle';spaced(x,en,W*.11,H*.38,H*.05,'left');
  x.fillStyle='rgba(255,255,255,.62)';x.font='600 '+H*.2+'px '+FONT;x.direction='rtl';x.textAlign='left';x.fillText(fa,W*.11,H*.74)})}
const panelM=(tex,k)=>new THREE.MeshStandardMaterial({map:tex,roughness:.55,metalness:.25});
function monitor(w,h,tex,ry){const g=grp();g.rotation.y=ry||0;g.add(slab(w,h,.07,black(),.05,0,0,0));
  const sc=new THREE.Mesh(new THREE.PlaneGeometry(w-.1,h-.1),new THREE.MeshBasicMaterial({map:tex,color:0xdcdcdc}));sc.position.z=.045;g.add(sc);return g}
function desk(w,d){const g=grp();g.add(box(w,.1,d,black(),0,1.0,0),box(.1,1.0,d-.1,charcoal2(),-w/2+.1,.5,0),box(.1,1.0,d-.1,charcoal2(),w/2-.1,.5,0),box(w-.2,.7,.08,charcoal2(),0,.55,-d/2+.1),box(w,.04,.04,glowM(1.4),0,1.02,d/2));return g}
function chair(){return grp(box(.8,.12,.8,black(),0,.7,0),box(.8,1.0,.1,black(),0,1.2,-.42),cyl(.06,.06,.6,black(),0,.38,0,8),cyl(.42,.42,.06,black(),0,.05,0,16))}
function laptop(tex,ry){const g=grp();g.rotation.y=ry||0;g.add(box(.9,.03,.62,charcoal2(),0,0,0));const lid=grp();lid.position.set(0,.02,-.3);lid.rotation.x=-.28;lid.add(box(.9,.58,.03,black(),0,.29,0));const s=new THREE.Mesh(new THREE.PlaneGeometry(.84,.52),new THREE.MeshBasicMaterial({map:tex,color:0xdddddd}));s.position.set(0,.29,.02);lid.add(s);g.add(lid);return g}
function trimLoop(w,d,y){const g=grp(),m=glowM(1.5);g.add(box(w,.03,.07,m,0,y,-d/2),box(w,.03,.07,m,0,y,d/2),box(.07,.03,d,m,-w/2,y,0),box(.07,.03,d,m,w/2,y,0));return g}
function booksWall(w,h,seed,accent){
  const g=grp();g.add(box(w,h,.5,std('shelfbg',{color:0x15161a,roughness:.8}),0,h/2,0));
  const levels=6,per=Math.floor(w*3.4),n=levels*per,books=new THREE.InstancedMesh(geo('bk1',()=>new THREE.BoxGeometry(1,1,1)),std('bkm',{color:0xffffff,roughness:.65,metalness:.1}),n),mtx=new THREE.Matrix4(),col=new THREE.Color();
  const pal=[0x6b3f2a,0x2f3947,0x8a6a3f,0x3b2a2a,0x4a5a46,0xb98a4a,0x23262c,0x7a4a38,0xd9d2c0];let i=0;
  for(let l=0;l<levels;l++){g.add(box(w,.07,.6,charcoal2(),0,.55+l*(h-.9)/levels,.05));let x=-w/2+.15;for(let k=0;k<per;k++){const bw=.12+rnd(seed+i)*.14,bh=.5+rnd(seed+i+3)*.5;if(x+bw>w/2-.1)break;
      mtx.compose(new THREE.Vector3(x+bw/2,.6+l*(h-.9)/levels+bh/2,.1),new THREE.Quaternion(),new THREE.Vector3(bw,bh,.42));books.setMatrixAt(i,mtx);col.setHex(pal[(i*7+l)%pal.length]);books.setColorAt(i,col);x+=bw+.012;i++}}
  books.count=i;g.add(books);g.add(box(w,.05,.05,glowM(1.3,accent||0xffb060),0,h-.1,.34));return g;
}
function holo(col,r,h,seg){const m=new THREE.Mesh(new THREE.CylinderGeometry(r,r*.82,h,seg||40,1,true),addM(col,.14,1.4));return m}
function lampTall(){const g=grp();g.add(cyl(.02,.02,2.4,black(),0,1.2,0,6),cyl(.3,.4,.34,black(),0,2.4,0,18),cyl(.28,.28,.04,glowM(2.4,0xffd6a0),0,2.22,0,18));const cn=new THREE.Mesh(geo('lc2',()=>new THREE.ConeGeometry(1.5,2.2,24,1,true)),addM(0xffc890,.06));cn.position.y=1.1;g.add(cn);return g}

/* ---------- zones ---------- */
function zExam(){
  const g=grp(),Z={};
  g.add(trimLoop(22,14,.03));
  const wall=grp();wall.position.set(0,0,-6);g.add(wall);
  wall.add(box(16,7,.4,charcoal(),0,3.5,0));
  const res=ctex(1024,512,(x,W,H)=>{x.fillStyle='#16181d';x.fillRect(0,0,W,H);x.strokeStyle='rgba(255,255,255,.1)';x.lineWidth=18;x.beginPath();x.arc(W*.25,H*.5,H*.32,0,7);x.stroke();x.strokeStyle='#ff8a2a';x.lineCap='round';x.beginPath();x.arc(W*.25,H*.5,H*.32,-1.57,-1.57+6.28*.92);x.stroke();
     x.fillStyle='#fff';x.font='800 120px '+FONT;x.textAlign='center';x.textBaseline='middle';x.fillText('92',W*.25,H*.5);x.font='600 34px '+FONT;x.fillStyle='rgba(255,255,255,.6)';x.fillText('SCORE',W*.25,H*.68);
     [['Grammar',.9],['Vocabulary',.84],['Language use',.78],['Reading',.95]].forEach(([n,v],i)=>{const y=H*.2+i*H*.19;x.fillStyle='rgba(255,255,255,.7)';x.font='500 34px '+FONT;x.textAlign='left';x.fillText(n,W*.5,y);x.fillStyle='rgba(255,255,255,.1)';rr(x,W*.5,y+22,W*.42,12,6);x.fill();x.fillStyle=i%2?'#ffb061':'#ff8a2a';rr(x,W*.5,y+22,W*.42*v,12,6);x.fill()})});
  wall.add(monitor(9,4.5,res,0));wall.children[wall.children.length-1].position.set(0,3.8,.25);
  wall.add(box(9.4,.08,.1,glowM(1.8),0,6.1,.3),box(9.4,.08,.1,glowM(1.4),0,1.5,.3));
  const sg=new THREE.Mesh(new THREE.PlaneGeometry(4.4,1.1),new THREE.MeshBasicMaterial({map:sign('EXAM CENTER','مرکز آزمون',4.4,1.1)}));sg.position.set(-5.4,6.3,.25);wall.add(sg);
  /* booths */
  [-5.5,-1.8,1.9].forEach((x,i)=>{
    const d=desk(2.8,1.4);d.position.set(x,0,-.8);g.add(d);
    const lt=laptop(ctex(512,320,(c,W,H)=>{c.fillStyle='#f5f5f7';c.fillRect(0,0,W,H);c.fillStyle='#111';c.font='700 26px '+FONT;c.textAlign='left';c.fillText('Question '+(i+7)+' / 30',24,40);c.fillStyle='#ff8a2a';c.fillRect(24,52,W*.5,5);c.fillStyle='#222';c.font='500 22px '+FONT;c.fillText('Choose the correct sentence:',24,100);
       [0,1,2,3].forEach(k=>{c.strokeStyle=k===1?'#ff8a2a':'#c9ccd3';c.lineWidth=3;rr(c,24,120+k*46,W-48,36,8);c.stroke();c.fillStyle=k===1?'#ff8a2a':'#c9ccd3';c.beginPath();c.arc(46,138+k*46,7,0,7);c.fill()})}),0);lt.position.set(0,1.05,-.1);d.add(lt);
    const ch=chair();ch.position.set(x,0,1.3);g.add(ch);const p=person({sit:true,armL:-1.1,armR:-1.1});p.position.set(x,.07,1.25);p.rotation.y=Math.PI;g.add(p);
    const part=grp();part.position.set(x,0,-.9);part.add(box(.05,2.0,.05,black(),1.5,1.0,0),new THREE.Mesh(new THREE.BoxGeometry(.03,1.2,1.4),addM(0x9fb4d8,.06)));part.children[1].position.set(1.5,1.9,.3);g.add(part)});
  /* timer hologram + certificate */
  const ring=tor(1.2,.03,glowM(2,OR),-1.8,5.2,-1,64);g.add(ring);Z.ring=ring;const ring2=tor(.9,.02,glowM(1.4,0xffc080),-1.8,5.2,-1,64);g.add(ring2);Z.ring2=ring2;
  const cert=grp();cert.position.set(8,0,2.5);cert.rotation.y=-.5;cert.add(box(1.5,1.1,1.1,charcoal(),0,.55,0));
  const ct=ctex(512,380,(x,W,H)=>{x.fillStyle='#f4efe3';x.fillRect(0,0,W,H);x.strokeStyle='#c99a56';x.lineWidth=6;x.strokeRect(14,14,W-28,H-28);x.fillStyle='#222';x.font='800 36px '+FONT;x.textAlign='center';x.fillText('CERTIFICATE',W/2,90);x.font='500 22px '+FONT;x.fillText('of achievement',W/2,125);x.fillStyle='#bbb';[0,1].forEach(i=>x.fillRect(W*.2,175+i*32,W*.6,6));x.fillStyle='#ff8a2a';x.beginPath();x.arc(W*.5,300,34,0,7);x.fill();aMark(x,W*.5,302,34,'#fff')});
  const pl=slab(1.5,1.1,.05,black(),.05,0,1.45,0);pl.rotation.x=-.35;cert.add(pl);const cs=new THREE.Mesh(new THREE.PlaneGeometry(1.42,1.02),new THREE.MeshBasicMaterial({map:ct,color:0xe0e0e0}));cs.position.set(0,1.45,.035);cs.rotation.x=-.35;cert.add(cs);g.add(cert);
  const pr=person({});pr.position.set(-9,0,2.8);pr.rotation.y=Math.PI*1.2;g.add(pr);
  [[-9.5,-4],[9.5,-3.5],[6,5]].forEach(([x,z],i)=>{const p=plant(1.2,i*7+3);p.position.set(x,0,z);g.add(p)});
  g.add(lampTall());g.children[g.children.length-1].position.set(5.5,0,-3);
  Z.accent=[0,2.5,1];return{g,Z,upd(t){Z.ring.rotation.y=t*.6;Z.ring2.rotation.y=-t*.8;Z.ring.rotation.x=Math.PI/2.3;Z.ring2.rotation.x=Math.PI/2.1}};
}
function zLibrary(){
  const g=grp(),Z={};g.add(trimLoop(22,14,.03));
  [-7.2,0,7.2].forEach((x,i)=>{const b=booksWall(6.6,7.2,i*50+5);b.position.set(x,0,-6);g.add(b)});
  const sg=new THREE.Mesh(new THREE.PlaneGeometry(4.2,1.05),new THREE.MeshBasicMaterial({map:sign('LIBRARY','کتابخانه',4.2,1.05)}));sg.position.set(0,7.9,-5.6);g.add(sg);
  /* ladder */
  const ld=grp();ld.position.set(3.8,0,-5.4);ld.rotation.z=.08;[-.35,.35].forEach(x=>ld.add(box(.06,5.2,.06,steel(),x,2.6,0)));for(let i=0;i<9;i++)ld.add(box(.7,.05,.05,steel(),0,.5+i*.55,0));g.add(ld);
  /* reading table */
  const tb=grp();tb.position.set(-2.2,0,1.4);tb.add(box(5.2,.12,1.8,black(),0,1.0,0),box(.12,1,1.6,charcoal2(),-2.3,.5,0),box(.12,1,1.6,charcoal2(),2.3,.5,0),box(5.2,.04,.04,glowM(1.4,0xffb060),0,1.02,.9));
  const lp=lampTall();lp.scale.setScalar(.45);lp.position.set(-1.8,1.06,0);tb.add(lp);
  tb.add(laptop(ctex(512,320,(x,W,H)=>UI.dash(x,W,H,'#ffb061')),0));tb.children[tb.children.length-1].position.set(.8,1.07,.1);
  [0,1,2].forEach(i=>tb.add(box(.7,.1,.5,std('bkc'+i,{color:[0x8a6a3f,0x2f3947,0xb98a4a][i],roughness:.6}),-.6,1.11+i*.1,.1)));
  g.add(tb);
  const rd=person({sit:true,armL:-.9,armR:-.9});rd.position.set(-.2,.07,2.6);rd.rotation.y=Math.PI;g.add(rd);const c2=chair();c2.position.set(-.2,0,2.7);g.add(c2);
  const rd2=person({sit:true,armL:-.9,armR:-.9});rd2.position.set(-3.6,.07,2.6);rd2.rotation.y=Math.PI;g.add(rd2);const c3=chair();c3.position.set(-3.6,0,2.7);g.add(c3);
  /* cover exhibits */
  const keys=Object.keys(COVERS).slice(0,4);
  Z.frames=keys.map((k,i)=>{const f=grp();f.position.set(4.2+((i%2)*3.7),0,.8+Math.floor(i/2)*3.6);f.rotation.y=-.5;f.add(box(.16,1.5,.16,black(),-1.2,.75,-.2),box(.16,1.5,.16,black(),1.2,.75,-.2),slab(3.0,1.7,.1,black(),.06,0,2.0,0));
    const im=new THREE.Mesh(new THREE.PlaneGeometry(2.86,1.5),new THREE.MeshBasicMaterial({map:coverTex(k),color:0xe0e0e0}));im.position.set(0,2.0,.06);f.add(im);f.add(box(3.1,.04,.04,glowM(1.6),0,1.12,.05));g.add(f);return f});
  Z.pages=[0,1,2,3,4,5].map(i=>{const p=slab(.9,1.2,.02,std('pg',{color:0xe9e3d3,roughness:.8,emissive:0x2a2418}),.04);g.add(p);return p});
  [[-10,3.8],[9.8,-3.6],[-8.5,-3.8]].forEach(([x,z],i)=>{const p=plant(1.2,i*11+5);p.position.set(x,0,z);g.add(p)});
  Z.accent=[0,3,1];return{g,Z,upd(t){Z.pages.forEach((p,i)=>{const q=((t*.12+i/6)%1);p.position.set(-1.8+Math.sin(q*6.28+i)*1.6,3+q*3.2,1.4+Math.cos(q*6.28+i)*.8);p.rotation.set(q*3,q*5,q*2);p.scale.setScalar(Math.max(.01,sm(q/.12)*(1-sm((q-.85)/.15))))});
    Z.frames.forEach((f,i)=>{f.position.y=Math.sin(t*.8+i)*.03})}};
}
function zShowroom(){
  const g=grp(),Z={};g.add(trimLoop(24,14,.03));
  const back=box(20,7.5,.4,charcoal(),0,3.75,-6);g.add(back);
  const demos=['academy','clinic','store'];
  const site=(kind,W,H)=>ctex(W,H,(x)=>{const dark=kind==='clinic';x.fillStyle=dark?'#0e1a1f':kind==='store'?'#f7f3ec':'#f6f7fb';x.fillRect(0,0,W,H);
    const acc=kind==='academy'?'#ff8a2a':kind==='clinic'?'#3ee0c8':'#222';x.fillStyle=dark?'#162830':'#fff';x.fillRect(0,0,W,H*.1);x.fillStyle=acc;x.fillRect(W*.04,H*.035,W*.1,H*.03);x.fillStyle=dark?'#889':'#99a';[0,1,2,3].forEach(i=>x.fillRect(W*(.55+i*.1),H*.04,W*.07,H*.022));
    const hg=x.createLinearGradient(0,H*.1,W,H*.6);hg.addColorStop(0,dark?'#173844':kind==='store'?'#e8dcc8':'#dfe7ff');hg.addColorStop(1,dark?'#0e1a1f':kind==='store'?'#f3e9d8':'#f6f7fb');x.fillStyle=hg;x.fillRect(0,H*.1,W,H*.5);
    x.fillStyle=dark?'#fff':'#14161b';x.font='800 '+H*.075+'px '+FONT;x.textAlign='left';x.fillText(kind==='academy'?'Learn. Grow. Succeed.':kind==='clinic'?'Book your visit online':'New season, new look',W*.05,H*.3);x.fillStyle=acc;rr(x,W*.05,H*.38,W*.16,H*.07,H*.02);x.fill();
    x.fillStyle=dark?'#1c3540':'#e9ecf3';[0,1,2].forEach(i=>{rr(x,W*.05+i*W*.31,H*.66,W*.28,H*.28,10);x.fill()});
    if(kind==='store'){x.fillStyle='#caa77a';[0,1,2].forEach(i=>{x.beginPath();x.arc(W*.19+i*W*.31,H*.78,H*.07,0,7);x.fill()})}
    x.fillStyle=acc;x.beginPath();x.arc(W*.76,H*.32,H*.14,0,7);x.fill()});
  Z.screens=demos.map((k,i)=>{const m=monitor(5.2,3.3,site(k,1024,640),0);m.position.set(-6+i*6,4,-5.7);g.add(m);g.add(box(5.4,.06,.08,glowM(1.7),-6+i*6,2.3,-5.65));
    const pd=box(2.4,.8,.6,charcoal(),-6+i*6,.4,-4.7);g.add(pd);return m});
  const sg=new THREE.Mesh(new THREE.PlaneGeometry(4.2,1.05),new THREE.MeshBasicMaterial({map:sign('SHOWROOM','نمایشگاه',4.2,1.05)}));sg.position.set(-7.2,7.1,-5.7);g.add(sg);
  /* turntable with device */
  const tt=grp();tt.position.set(2,0,2);tt.add(cyl(2.2,2.2,.3,black(),0,.15,0,48),tor(2.2,.04,glowM(1.8),0,.32,0,64));tt.children[1].rotation.x=Math.PI/2;
  const rot=grp();tt.add(rot);Z.rot=rot;
  const ph=ctex(360,720,(x,W,H)=>{x.fillStyle='#f6f7fb';x.fillRect(0,0,W,H);x.fillStyle='#ff8a2a';x.fillRect(0,0,W,H*.3);x.fillStyle='#fff';x.font='800 40px '+FONT;x.textAlign='left';x.fillText('Arvion',24,70);x.font='600 26px '+FONT;x.fillText('Welcome back',24,120);x.fillStyle='#e3e6ee';[0,1,2,3].forEach(i=>{rr(x,24,H*.34+i*128,W-48,108,14);x.fill()})});
  rot.add(slab(1.15,2.3,.1,black(),.14,0,1.9,0));const ps=new THREE.Mesh(new THREE.PlaneGeometry(1.05,2.18),new THREE.MeshBasicMaterial({map:ph,color:0xdddddd}));ps.position.set(0,1.9,.06);rot.add(ps);
  const ps2=ps.clone();ps2.position.z=-.06;ps2.rotation.y=Math.PI;rot.add(ps2);
  const bm=new THREE.Mesh(geo('lc3',()=>new THREE.ConeGeometry(2.4,5.6,32,1,true)),addM(0xffd0a0,.05));bm.position.set(0,3.1,0);tt.add(bm);
  g.add(tt);
  [[-4,2.6],[-6.5,3.4]].forEach(([x,z],i)=>{const p=person({s:1.02,armR:-.4});p.position.set(x,0,z);p.rotation.y=Math.PI*(1.15+i*.1);g.add(p)});
  [[-10.5,-3.5],[10.4,-3.8],[9,4.2]].forEach(([x,z],i)=>{const p=plant(1.25,i*17+2);p.position.set(x,0,z);g.add(p)});
  [-6,0,6].forEach(x=>{const lp=lampTall();lp.position.set(x,0,-2.8);lp.scale.setScalar(1.2);g.add(lp)});
  Z.accent=[2,3,3];return{g,Z,upd(t){Z.rot.rotation.y=t*.5}};
}
function zCrm(){
  const g=grp(),Z={};g.add(trimLoop(24,15,.03));
  const kinds=['#ff8a2a','#7aa2ff','#3ee0c8','#ffb061','#9a8bff'];
  Z.mons=kinds.map((c,i)=>{const a=(i-2)*.36,m=monitor(4.0,2.4,ctex(640,384,(x,W,H)=>UI.dash(x,W,H,c)),0);m.position.set(Math.sin(a)*9,3.6,-Math.cos(a)*9+3);m.rotation.y=-a;g.add(m);return m});
  g.add(box(24,.1,.1,glowM(1.4),0,1.6,-6.4));
  const sg=new THREE.Mesh(new THREE.PlaneGeometry(4.2,1.05),new THREE.MeshBasicMaterial({map:sign('CONTROL','مرکز کنترل',4.2,1.05)}));sg.position.set(-8.2,7,-5.9);sg.rotation.y=.28;g.add(sg);
  const op=grp();op.position.set(0,0,2.2);op.add(desk(6.4,1.8));[-2.1,0,2.1].forEach(x=>{const lt=laptop(ctex(512,320,(c,W,H)=>UI.dash(c,W,H,'#7aa2ff')),0);lt.position.set(x,1.05,0);op.add(lt)});g.add(op);
  [-2.1,2.1].forEach(x=>{const p=person({sit:true,armL:-1.1,armR:-1.1});p.position.set(x,.07,3.8);p.rotation.y=Math.PI;g.add(p);const c=chair();c.position.set(x,0,3.9);g.add(c)});
  /* radar floor + funnel */
  const rg=ctex(512,512,(x,W,H)=>{const gr=x.createConicGradient?x.createConicGradient(0,W/2,H/2):null;if(gr){gr.addColorStop(0,'rgba(255,138,42,.0)');gr.addColorStop(.18,'rgba(255,138,42,.55)');gr.addColorStop(.19,'rgba(255,138,42,0)');gr.addColorStop(1,'rgba(255,138,42,0)');x.fillStyle=gr;x.beginPath();x.arc(W/2,H/2,W/2,0,7);x.fill()}x.strokeStyle='rgba(255,170,90,.5)';x.lineWidth=3;[.2,.4,.6,.8,.98].forEach(r=>{x.beginPath();x.arc(W/2,H/2,W/2*r,0,7);x.stroke()})});
  const rad=new THREE.Mesh(new THREE.PlaneGeometry(9,9),new THREE.MeshBasicMaterial({map:rg,transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,opacity:.8}));rad.rotation.x=-Math.PI/2;rad.position.set(0,.04,-1.5);g.add(rad);Z.rad=rad;
  Z.funnel=[0,1,2,3].map(i=>{const m=holo(OR,2.6-i*.55,.7,48);m.position.set(0,3+i*.85,-1.5);g.add(m);const rg2=tor(2.6-i*.55,.02,glowM(1.8),0,3+i*.85+.35,-1.5,64);rg2.rotation.x=Math.PI/2;g.add(rg2);return m});
  /* racks */
  [[-10.5,-1.5],[10.5,-1.5]].forEach(([x,z])=>{const r=grp();r.position.set(x,0,z);r.add(box(1.4,4.4,1.4,black(),0,2.2,0));const led=ctex(64,256,(c,W,H)=>{for(let i=0;i<24;i++){c.fillStyle=rnd(i)>.4?'#ff8a2a':'#3ee0c8';c.globalAlpha=.4+rnd(i+5)*.6;c.fillRect(8+(i%3)*18,6+i*10,10,5)}});const f=new THREE.Mesh(new THREE.PlaneGeometry(1.2,4),new THREE.MeshBasicMaterial({map:led,transparent:true}));f.position.set(0,2.2,.71);r.add(f);g.add(r)});
  [[-8,4.4],[8.5,4.2]].forEach(([x,z],i)=>{const p=plant(1.2,i*9+1);p.position.set(x,0,z);g.add(p)});
  Z.accent=[0,3,0];return{g,Z,upd(t){Z.rad.rotation.z=-t*.9;Z.funnel.forEach((m,i)=>{m.rotation.y=t*(.3+i*.1)})}};
}
function zReception(){
  const g=grp(),Z={};g.add(trimLoop(22,14,.03));
  const wall=grp();wall.position.set(0,0,-6);g.add(wall);wall.add(box(18,7.5,.4,charcoal(),0,3.75,0));
  for(let i=0;i<24;i++)wall.add(box(.12,6.6,.12,charcoal2(),-8.6+i*.75,3.5,.28));
  const lg=ctex(1024,512,(x,W,H)=>{x.clearRect(0,0,W,H);wordmark(x,W/2,H*.4,170,'#ffffff','WEB DESIGN STUDIO')});
  const lm=new THREE.Mesh(new THREE.PlaneGeometry(8,4),new THREE.MeshBasicMaterial({map:lg,transparent:true,color:hdr(0xffffff,1.0)}));lm.position.set(0,4.2,.4);wall.add(lm);
  wall.add(box(8.6,.08,.1,glowM(1.8),0,6.4,.4),box(8.6,.08,.1,glowM(1.4),0,2.0,.4));
  const dk=grp();dk.position.set(0,0,-1.2);dk.add(box(8,1.2,1.6,charcoal(),0,.6,0),box(8.1,.12,1.7,black(),0,1.25,0),box(8,.05,.05,glowM(1.8),0,.06,.82),box(8,.05,.05,glowM(1.4),0,1.2,.84));g.add(dk);
  const rc=person({sit:true,armL:-1,armR:-1});rc.position.set(1.4,.07,-2.7);g.add(rc);const rcc=chair();rcc.position.set(1.4,0,-2.8);rcc.rotation.y=Math.PI;g.add(rcc);
  dk.add(monitor(1.3,.8,ctex(512,320,(x,W,H)=>UI.dash(x,W,H,'#ff6b8b')),0));dk.children[dk.children.length-1].position.set(1.4,2.0,-.2);
  /* contact glass */
  const gp=grp();gp.position.set(-8,0,2.5);gp.rotation.y=.5;gp.add(box(3.4,3.4,.06,std('glass2',{color:0xaab8d0,roughness:.05,metalness:0,transparent:true,opacity:.12,depthWrite:false,envMapIntensity:1.6}),0,1.9,0),box(3.5,.05,.08,glowM(1.6),0,3.6,0));
  gp.add(decal(3.0,3.0,ctex(512,512,(x,W,H)=>{x.fillStyle='#fff';x.font='700 40px '+FONT;x.textAlign='right';x.direction='rtl';x.fillText('با ما در تماس باشید',W*.95,H*.2);
     [['☎','تلفن'],['✉','ایمیل'],['⌖','آدرس']].forEach(([ic,t],i)=>{x.fillStyle='#ff8a2a';x.font='700 54px '+FONT;x.textAlign='center';x.fillText(ic,W*.85,H*.42+i*H*.2);x.fillStyle='rgba(255,255,255,.85)';x.font='500 36px '+FONT;x.textAlign='right';x.fillText(t,W*.72,H*.43+i*H*.2)})}),0,1.9,.05));g.add(gp);
  /* lounge */
  const sf=grp();sf.position.set(7,0,2.6);sf.rotation.y=-.6;sf.add(box(3.2,.5,1.3,charcoal2(),0,.4,0),box(3.2,.9,.3,charcoal2(),0,.95,-.5),box(.3,.8,1.3,charcoal2(),-1.5,.7,0),box(.3,.8,1.3,charcoal2(),1.5,.7,0),box(3.3,.04,.04,glowM(1.3),0,.18,.66));g.add(sf);
  const ct=cyl(.7,.7,.12,black(),5,.55,4.4,32);g.add(ct,cyl(.06,.06,.5,black(),5,.28,4.4,8));
  Z.bubble=grp();Z.bubble.position.set(-1.5,3.6,0);const bm=glowM(1.6,0xffffff,.9);Z.bubble.add(box(1.8,.05,.05,bm,0,.5,0),box(1.8,.05,.05,bm,0,-.5,0),box(.05,1.0,.05,bm,-.9,0,0),box(.05,1.0,.05,bm,.9,0,0));[-.4,0,.4].forEach(x=>Z.bubble.add(sph(.07,glowM(2,OR),x,0,0,10)));Z.bubble.add(cone(.2,.4,bm,-.5,-.75,0,3));Z.bubble.children[Z.bubble.children.length-1].rotation.z=Math.PI;g.add(Z.bubble);
  [[-5,3.8],[10,-3],[-10,-3]].forEach(([x,z],i)=>{const p=plant(1.3,i*5+9);p.position.set(x,0,z);g.add(p)});
  const pp=person({s:1.02,armR:-.3});pp.position.set(3.4,0,1.4);pp.rotation.y=Math.PI*1.1;g.add(pp);
  Z.accent=[0,3,1];return{g,Z,upd(t){Z.bubble.position.y=3.6+Math.sin(t*1.3)*.15;Z.bubble.rotation.y=Math.sin(t*.5)*.3}};
}

/* ---------- engine ---------- */
async function create(canvas,o){
  const breathe=()=>new Promise(resolve=>setTimeout(resolve,0));
  o=o||{};const lite=!!o.lite,reduced=!!o.reduced;
  COVERS=o.covers||{};textureScale=lite?.5:1;
  const R=new THREE.WebGLRenderer({canvas,antialias:false,alpha:false,powerPreference:'high-performance',preserveDrawingBuffer:!!o.keep});
  const pr=Math.min(devicePixelRatio||1,lite?1.25:1.5);R.setPixelRatio(pr);R.setClearColor(0x07080a,1);
  R.info.autoReset=false;
  await breathe();
  if(!lite){R.shadowMap.enabled=true;R.shadowMap.type=THREE.PCFSoftShadowMap}
  const sc=new THREE.Scene();sc.fog=new THREE.FogExp2(0x08090c,.012);
  /* studio environment for glossy reflections */
  (function(){const e=new THREE.Scene();e.add(new THREE.Mesh(new THREE.BoxGeometry(60,30,60),new THREE.MeshBasicMaterial({color:0x08090b,side:THREE.BackSide})));
    const pn=(w,h,c,k,x,y,z,rx,ry)=>{const m=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({color:hdr(c,k),side:THREE.DoubleSide}));m.position.set(x,y,z);m.rotation.set(rx||0,ry||0,0);e.add(m)};
    pn(24,4,0xfff0dd,4.5,0,14,0,Math.PI/2);pn(5,18,0xffa050,5,-20,5,4,0,Math.PI/2);pn(5,14,0xaec4ff,2.2,20,6,-4,0,-Math.PI/2);pn(18,2,0xffffff,2.5,0,6,-24,0,0);
    const pm=new THREE.PMREMGenerator(R);sc.environment=pm.fromScene(e,.03).texture;pm.dispose()})();
  sc.add(new THREE.HemisphereLight(0x9aa4c8,0x2a1a0c,.72));
  const front=new THREE.PointLight(0xffd7ae,1.5,46,1.4);front.position.set(-10,7,9);sc.add(front);
  const fill=new THREE.DirectionalLight(0x6f8cff,.45);fill.position.set(-18,8,-4);sc.add(fill);
  const key=new THREE.DirectionalLight(0xffe2c0,1.3);key.position.set(-10,16,12);
  if(!lite){key.castShadow=true;key.shadow.mapSize.set(2048,2048);const s=key.shadow.camera;s.left=-18;s.right=22;s.top=14;s.bottom=-12;s.near=1;s.far=60;key.shadow.bias=-.0004;key.shadow.radius=3}
  sc.add(key);sc.add(key.target);
  const acc=new THREE.PointLight(0xff8a2a,2.6,26,1.7);acc.position.set(6,2.4,0);sc.add(acc);
  const cam=new THREE.PerspectiveCamera(28,1,.5,400);
  /* floor */
  const ct=concreteTex();ct.repeat.set(40,40);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.MeshStandardMaterial({map:ct,color:0x8d9099,roughness:.52,metalness:.4,envMapIntensity:1.1,transparent:true,opacity:lite?1:.6}));
  floor.rotation.x=-Math.PI/2;floor.receiveShadow=true;floor.renderOrder=1;sc.add(floor);
  let refl=null;
  if(!lite&&THREE.Reflector){refl=new THREE.Reflector(new THREE.PlaneGeometry(200,200),{clipBias:.003,textureWidth:Math.round(innerWidth*pr*.5),textureHeight:Math.round(innerHeight*pr*.5),color:0xa0a4ae});refl.rotation.x=-Math.PI/2;refl.position.y=-.01;sc.add(refl)}
  /* the hero set */
  await breathe();const A=buildAssembly();sc.add(A.root);await breathe();
  const ZC=[[50,0,-14],[50,0,-50],[0,0,-62],[-50,0,-50],[-50,0,-14]];
  const zones=[];
  for(const build of [zExam,zLibrary,zShowroom,zCrm,zReception]){zones.push(build());await breathe();}
  zones.forEach((z,i)=>{z.g.position.set(...ZC[i]);z.c=new THREE.Vector3(...ZC[i]);sc.add(shadows(z.g))});
  /* bokeh lights in the far background */
  const bgG=new THREE.Group();sc.add(bgG);
  const bk=[];for(let i=0;i<46;i++){const s=sprite(i%3?OR:0xffe2bf,2+rnd(i)*4,.35+rnd(i+4)*.4,i%3?1.3:1);s.position.set(-30+rnd(i+1)*70,1+rnd(i+2)*9,-14-rnd(i+3)*30);bgG.add(s);bk.push(s)}
  const rack=(x,z,w,h,seed)=>{const r=new THREE.Group();r.position.set(x,0,z);r.add(box(w,h,1.2,std('bgb',{color:0x131419,roughness:.8}),0,h/2,0));
    for(let i=0;i<5;i++){r.add(box(w*.92,.1,.1,glowM(.9,0xffa24a,.9),0,h*(.16+i*.17),.66));
      for(let k=0;k<7;k++){if(rnd(seed+i*9+k)<.55)r.add(box(.5+rnd(seed+k)*.7,.5+rnd(seed+i+k)*.6,.4,std('bgp'+(k%3),{color:[0x2a2c33,0x3a2f25,0x20262e][k%3],roughness:.7}),-w*.4+k*(w*.8/6),h*(.2+i*.17),.5))}}
    bgG.add(r)};
  rack(-30,-24,14,15,1);rack(-14,-30,16,17,40);rack(4,-34,18,16,77);rack(24,-28,14,15,120);rack(40,-18,12,14,160);rack(-40,-8,12,14,200);
  // Only immutable background boxes: animated arms/cards/room props are excluded.
  bgG.updateMatrixWorld(true);
  const boxes=new Map();bgG.traverse(m=>{if(m.isMesh&&m.geometry.type==='BoxGeometry'&&!m.material.transparent){const list=boxes.get(m.material)||[];list.push(m);boxes.set(m.material,list)}});
  for(const [material,meshes] of boxes){if(meshes.length<2)continue;const batch=new THREE.InstancedMesh(geo('unit-bg-box',()=>new THREE.BoxGeometry(1,1,1)),material,meshes.length);
    meshes.forEach((m,i)=>{const p=m.geometry.parameters,matrix=m.matrixWorld.clone().multiply(new THREE.Matrix4().makeScale(p.width,p.height,p.depth));batch.setMatrixAt(i,matrix);m.parent.remove(m)});bgG.add(batch);}
  const haze=sprite(0xff8a2a,22,.16,1);haze.position.set(7,4,-4);bgG.add(haze);const haze2=sprite(0xffb070,16,.1,1);haze2.position.set(-4,2.5,3);bgG.add(haze2);
  /* dust motes */
  const dn=lite?60:160,dp=new Float32Array(dn*3);for(let i=0;i<dn;i++){dp[i*3]=-12+rnd(i)*34;dp[i*3+1]=.5+rnd(i+3)*9;dp[i*3+2]=-8+rnd(i+6)*20}
  const dg=new THREE.BufferGeometry();dg.setAttribute('position',new THREE.BufferAttribute(dp,3));
  const dust=new THREE.Points(dg,new THREE.PointsMaterial({color:0xffc78a,size:2.2*pr,sizeAttenuation:false,transparent:true,opacity:.55,depthWrite:false,blending:THREE.AdditiveBlending}));sc.add(dust);
  /* post */
  let comp=null,bloom=null,fin=null;
  const FIN={uniforms:{tDiffuse:{value:null},uTime:{value:0},uRes:{value:new THREE.Vector2(1,1)},uFocus:{value:.58},uBlur:{value:1.0},uFade:{value:1}},
   vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
   fragmentShader:`uniform sampler2D tDiffuse;uniform float uTime,uFocus,uBlur,uFade;uniform vec2 uRes;varying vec2 vUv;
   float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
   void main(){
     vec2 uv=vUv;float d=uv.y>uFocus?(uv.y-uFocus)*.95:(uFocus-uv.y)*.75;float b=smoothstep(.16,.6,d)*uBlur;
     vec2 c=uv-.5;float r2=dot(c,c);
     vec3 col=vec3(0.);float ang=fract(52.9829189*fract(dot(gl_FragCoord.xy,vec2(.06711056,.00583715))))*6.2831;float tot=0.;
     for(int i=0;i<20;i++){float fi=float(i);float rad=sqrt((fi+.5)/20.)*b*.011;float a=fi*2.3999+ang;vec2 o=vec2(cos(a),sin(a)*uRes.x/uRes.y)*rad;
       vec3 s=texture2D(tDiffuse,uv+o+c*r2*.008).rgb;float w=1.+dot(s,vec3(.33))*b*1.4;col+=s*w;tot+=w;}
     col/=tot;
     col*=1.14;col=col/(1.+max(col-.85,0.)*.65);
     col=pow(col,vec3(.94));col=mix(vec3(dot(col,vec3(.333))),col,1.12);
     col+=vec3(.012,.007,.003)*(1.-col);
     col*=1.-smoothstep(.2,.75,r2*2.)*.5;
     col+=(h(uv*uRes+uTime*1.7)-.5)*.016;
     gl_FragColor=vec4(col*uFade,1.);}`};
  function buildPost(){
    const isGL2=R.capabilities.isWebGL2;
    const rt=new THREE.WebGLRenderTarget(4,4,{type:isGL2?THREE.HalfFloatType:THREE.UnsignedByteType,format:THREE.RGBAFormat});
    comp=new THREE.EffectComposer(R,rt);comp.setPixelRatio(pr);
    comp.addPass(new THREE.RenderPass(sc,cam));
    bloom=new THREE.UnrealBloomPass(new THREE.Vector2(256,256),lite?.5:.62,.6,.86);comp.addPass(bloom);
    fin=new THREE.ShaderPass(FIN);comp.addPass(fin);
  }
  buildPost();
  /* camera shots */
  let W=0,H=0,portrait=false,P=0,pd=0,vis=true,raf=0,mx=0,my=0,t0=performance.now(),fixedT=null,intro=1,cur=null,introOn=false,introT=0,qual=0,running=false;
  let lastFrame=0, samples=[], lastStats={fps:0,calls:0,tris:0,frames:0};
  const SHOTS=[];
  function shots(){SHOTS.length=0;const p=portrait,k=p?1.35:1.55,ox=p?0:(o.rtl?-.26:.26),oy=0,f=p?44:29;
    const ov=o.cam;if(ov){SHOTS.push({pos:ov.slice(0,3),tgt:ov.slice(3,6),fov:ov[6],focus:.5,ox:ov[7]||0,oy:ov[8]||0});return}
    SHOTS.push({pos:p?[-18,9,26]:[-22,10.4,21.4],tgt:p?[3,2.2,-.5]:[3.2,2.8,-.6],fov:p?36:28,focus:.5,ox,oy:p?-.1:0});
    SHOTS.push({pos:p?[-14,6.2,22]:[-9.5,4.6,9.6],tgt:[3.4,2.2,-.4],fov:f,focus:.5,ox,oy:p?.12:0});
    [[ -13.5,6.4,13.5,0,2.4,-1.8],[-14,6.8,13.5,0,2.6,-1.2],[-14.5,7,14,0,2.8,-1.2],[-13.5,6.6,14,0,2.9,-1],[-14,6.6,13.5,0,2.8,-1.4]].forEach((v,i)=>{const c=ZC[i];
      SHOTS.push({pos:[c[0]+v[0]*k,v[1]*(p?1.1:1.12),c[2]+v[2]*k],tgt:[c[0]+v[3],v[4],c[2]+v[5]],fov:f,focus:.5,ox,oy:p?.12:0,i})});
    SHOTS.forEach((shot,index)=>{shot.room=index});
    if(o.shotIndices){const selected=o.shotIndices.map(index=>SHOTS[index]);SHOTS.splice(0,SHOTS.length,...selected)}
  }
  function size(){W=canvas.clientWidth||innerWidth;H=canvas.clientHeight||innerHeight;R.setSize(W,H,false);comp.setSize(W,H);fin.uniforms.uRes.value.set(W,H);const np=W<H*.95;if(np!==portrait||!SHOTS.length){portrait=np;shots()}cam.aspect=W/H}
  const cp=new THREE.Vector3(),ct2=new THREE.Vector3();let near=0,ZA=new THREE.Vector3(6,2.4,0);
  function camAt(p){const f=clamp(p)*(SHOTS.length-1),i=Math.min(SHOTS.length-2,Math.floor(f)),u=f-i,e=sm((u-.15)/.7),a=SHOTS[i],b=SHOTS[i+1];
    const L=(x,y)=>lerp(x,y,e),dist=Math.hypot(b.pos[0]-a.pos[0],b.pos[2]-a.pos[2]);
    const lift=Math.sin(Math.PI*e)*Math.min(7,dist*.12);
    return{pos:[L(a.pos[0],b.pos[0]),L(a.pos[1],b.pos[1])+lift,L(a.pos[2],b.pos[2])],tgt:[L(a.tgt[0],b.tgt[0]),L(a.tgt[1],b.tgt[1]),L(a.tgt[2],b.tgt[2])],fov:L(a.fov,b.fov),focus:L(a.focus,b.focus),ox:L(a.ox,b.ox),oy:L(a.oy,b.oy),near:e<.5?a.room:b.room,dist:Math.abs(f-Math.round(f)),e}}
  function frame(now){
    if(!running||!vis||document.hidden){raf=0;return;}raf=requestAnimationFrame(frame);
    const t=fixedT!=null?fixedT:(reduced?0:(now-t0)/1000);
    pd+=(P-pd)*(reduced?1:.2);
    const s=cur=camAt(pd);
    const sway=reduced?0:1;
    if(introOn){intro=clamp((now-introT)/3200);if(intro>=1)introOn=false}
    const ie=1-sm(intro);
    cam.fov=s.fov;cam.position.set(s.pos[0]+mx*.9*sway+Math.sin(t*.25)*.12*sway-ie*9,s.pos[1]+my*.5*sway+ie*9,s.pos[2]+ie*12);cam.lookAt(s.tgt[0],s.tgt[1],s.tgt[2]);
    cam.setViewOffset(W,H,s.ox*W,s.oy*H,W,H);cam.updateProjectionMatrix();
    /* shared lights follow the shot */
    ct2.set(s.tgt[0],0,s.tgt[2]);key.position.set(s.tgt[0]-10,16,s.tgt[2]+12);key.target.position.set(s.tgt[0],0,s.tgt[2]);front.position.set(s.tgt[0]-9,7,s.tgt[2]+9);
    const zi=s.near>=2?s.near-2:-1,ap=zi>=0?zones[zi].c.clone().add(new THREE.Vector3(...zones[zi].Z.accent)):new THREE.Vector3(6,2.4,0);
    ZA.lerp(ap,.08);acc.position.copy(ZA);acc.intensity=2.5+Math.sin(t*3.1)*.2+Math.sin(t*7.3)*.1;
    /* animate */
    A.beltTex.offset.x=-(t*.18)%1;
    A.cards.forEach((c,i)=>{const ph=((t*.22)-i*.25)%1,act=sm(1-Math.abs(((ph+1)%1)-.1)*6);c.position.y=.84+Math.sin(t*1.3+i)*.02+act*.08;c.userData.rim.material.opacity=act*.3});
    const [a1,a2]=A.arms;let u=a1.userData;u.yaw.rotation.y=Math.sin(t*.5)*.35+.5;u.sh.rotation.z=-.55+Math.sin(t*.6)*.18;u.el.rotation.z=-.95+Math.sin(t*.8+1)*.2;u.wr.rotation.z=.2;
    u=a2.userData;u.yaw.rotation.y=Math.sin(t*.45+2)*.4-.2;u.sh.rotation.z=.5+Math.sin(t*.5)*.15;u.el.rotation.z=.9+Math.sin(t*.7)*.2;
    A.portal.material.color.setScalar(.95+Math.sin(t*2.4)*.05);
    A.flame.scale.set(1,.85+Math.sin(t*18)*.15,1);A.rocket.position.y=Math.sin(t*1.2)*.03;
    dust.rotation.y=t*.01;dust.position.y=Math.sin(t*.3)*.2;
    zones.forEach(z=>{const near=z.c.distanceTo(ct2)<58;z.g.visible=near;if(near)z.upd(t)});
    A.root.visible=bgG.visible=ct2.distanceTo(new THREE.Vector3(2,0,0))<58;
    fin.uniforms.uTime.value=t%100;fin.uniforms.uFocus.value=s.focus;fin.uniforms.uFade.value=clamp(intro*2.2);
    R.info.reset();comp.render();
    if(lastFrame)samples.push(now-lastFrame);lastFrame=now;if(samples.length>90)samples.shift();
    lastStats={fps:samples.length?1000/(samples.reduce((a,b)=>a+b,0)/samples.length):0,calls:R.info.render.calls,tris:R.info.render.triangles,frames:lastStats.frames+1,quality:qual};
  }
  const wake=()=>{cancelAnimationFrame(raf);raf=0;lastFrame=0;samples=[];if(running&&vis&&!document.hidden)raf=requestAnimationFrame(frame)};
  const pointer=e=>{if(e.pointerType==='touch')return;const r=canvas.getBoundingClientRect();mx=(e.clientX-r.left)/r.width-.5;my=(e.clientY-r.top)/r.height-.5};
  addEventListener('resize',size);document.addEventListener('visibilitychange',wake);
  canvas.parentElement.addEventListener('pointermove',pointer);
  const observer='IntersectionObserver' in window?new IntersectionObserver(es=>{vis=es[0].isIntersecting;wake()}):null;observer?.observe(canvas);
  size();
  return{setP(p,hard){P=clamp(p);if(hard||reduced)pd=P},size,start(){running=true;wake()},stop(){running=false;wake()},
    dispose(){running=false;wake();observer?.disconnect();removeEventListener('resize',size);document.removeEventListener('visibilitychange',wake);canvas.parentElement.removeEventListener('pointermove',pointer);comp.dispose?.();R.dispose();},
    renderOnce(){running=true;frame(performance.now());running=false;cancelAnimationFrame(raf)},freeze(t){fixedT=t},setIntro(v){intro=v},playIntro(){introT=performance.now();intro=0;introOn=true},
    setQuality(q){if(q<=qual)return;qual=q;if(q>=1){if(refl)refl.visible=false;floor.material.opacity=1;floor.material.needsUpdate=true;R.setPixelRatio(1);comp.setPixelRatio(1);size()}if(q>=2){bloom.enabled=false}},get quality(){return qual},pick:()=>-1,
    stats(){return{...lastStats,geos:R.info.memory.geometries,tex:R.info.memory.textures}},get info(){return R.info},get pr(){return R.getPixelRatio()},get cur(){return cur},cam,comp,A,N:6};
}
return{create};
})();
