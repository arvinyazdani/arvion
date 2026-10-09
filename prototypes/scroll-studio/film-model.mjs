export const clamp = n => Math.max(0, Math.min(1, Number.isFinite(n) ? n : 0));
export const phase = (p, start, end) => {const t = clamp((p-start)/(end-start));return t*t*(3-2*t);};
export function frame(progress){
 const p=clamp(progress);return {p,blueprint:phase(p,.1,.35),site:phase(p,.35,.62),phone:phase(p,.63,.84),network:phase(p,.84,1),chapter:Math.min(4,Math.floor(p*5))};
}
