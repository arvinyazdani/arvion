/* Same renderer/geometry as the main-thread reference; no application data. */
let engine=null,viewport=null,metricsTimer=0,initializing=false;
importScripts('vendor/three-r128.min.js','vendor/post-r128.js','engine.js?v=5');
const publish=()=>{if(engine)postMessage({type:'stats',stats:engine.stats()});};
let failed=false;
const fail=()=>{if(failed)return;failed=true;clearInterval(metricsTimer);engine?.dispose();engine=null;postMessage({type:'failed',reason:'renderer-unavailable'});close();};
onmessage=async({data})=>{
 try{
  if(data.type==='init'){
   if(initializing)return;initializing=true;
   if(typeof requestAnimationFrame!=='function'||!self.fonts||typeof FontFace!=='function')throw new Error('capability');
   viewport=data.viewport;
   data.canvas.addEventListener?.('webglcontextlost',event=>{event.preventDefault();fail();});
   const fonts=[['Regular','400'],['Bold','700 800'],['Black','900']];
   await Promise.all(fonts.map(async([name,weight],i)=>{const url=data.options.fonts?.[i]||new URL('../fonts/Vazirmatn-'+name+'.woff2',location.href).href;const face=new FontFace('Vazirmatn',`url(${url})`,{weight});await face.load();self.fonts.add(face);}));
   engine=await self.RvionStudioEngine.create(data.canvas,{...data.options,viewport});
   engine.renderOnce();postMessage({type:'ready',stats:engine.stats()});
   metricsTimer=setInterval(publish,1000);
  }else if(engine){
   if(data.type==='size'){Object.assign(viewport,data.viewport);engine.size();}
   else if(data.type==='progress')engine.setP(data.value);
   else if(data.type==='pointer')engine.setPointer(data.x,data.y);
   else if(data.type==='visible')engine.setVisible(data.value);
   else if(data.type==='start'){engine.playIntro();engine.start();}
   else if(data.type==='quality')engine.setQuality(data.value);
   else if(data.type==='stop')engine.stop();
   else if(data.type==='dispose'){clearInterval(metricsTimer);engine.dispose();engine=null;close();}
  }
 }catch(error){fail();}
};
