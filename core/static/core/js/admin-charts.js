(() => {
  const canvas = document.querySelector("[data-traffic-chart]");
  const source = document.getElementById("traffic-chart-data");
  if (!canvas || !source) return;
  const data = JSON.parse(source.textContent || "[]");
  if (!data.length) return;
  const draw = () => {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(1, rect.width * ratio);
    canvas.height = Math.max(1, rect.height * ratio);
    const ctx = canvas.getContext("2d");
    ctx.scale(ratio, ratio);
    const width = canvas.width / ratio, height = canvas.height / ratio;
    const pad = {top: 20, right: 18, bottom: 42, left: 52};
    const plotW = width - pad.left - pad.right, plotH = height - pad.top - pad.bottom;
    const max = Math.max(5, ...data.flatMap(item => [item.views, item.visitors]));
    ctx.clearRect(0, 0, width, height);
    ctx.font = "11px Vazirmatn, Tahoma"; ctx.textAlign = "right"; ctx.fillStyle = "#7b8495";
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + plotH * i / 4, value = Math.round(max * (1 - i / 4));
      ctx.beginPath(); ctx.strokeStyle = "#e8ebf0"; ctx.moveTo(pad.left, y); ctx.lineTo(width - pad.right, y); ctx.stroke();
      ctx.fillText(String(value), pad.left - 9, y + 4);
    }
    const x = index => pad.left + (data.length === 1 ? plotW / 2 : plotW * index / (data.length - 1));
    const y = value => pad.top + plotH * (1 - value / max);
    const series = (key, color) => {
      ctx.beginPath(); data.forEach((item, index) => index ? ctx.lineTo(x(index), y(item[key])) : ctx.moveTo(x(index), y(item[key])));
      ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.lineJoin = "round"; ctx.lineCap = "round"; ctx.stroke();
      data.forEach((item, index) => { ctx.beginPath(); ctx.arc(x(index), y(item[key]), 3.5, 0, Math.PI * 2); ctx.fillStyle = "#fff"; ctx.fill(); ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke(); });
    };
    series("views", "#ff6b35"); series("visitors", "#3d68d8");
    ctx.textAlign = "center"; ctx.fillStyle = "#7b8495";
    data.forEach((item, index) => { if (data.length <= 8 || index % 2 === 0 || index === data.length - 1) ctx.fillText(item.date, x(index), height - 15); });
  };
  draw(); let timer; window.addEventListener("resize", () => { clearTimeout(timer); timer = setTimeout(draw, 120); });
})();
