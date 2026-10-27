// Symmetry Engine high-resolution export (VIP). Renders kaleidoscope strokes (model coords in [-1,1]) at print size.
// window.SE_EXPORT_KALEIDO({strokes, n, mirrors, size=4096, background='#ffffff'}) downloads a PNG.
(function () {
  function rosette(n, mirrors) { const out = []; for (let k = 0; k < n; k++) { const t = 2 * Math.PI * k / n, c = Math.cos(t), s = Math.sin(t); out.push([c, -s, s, c]); if (mirrors) out.push([c, s, s, -c]); } return out; }
  window.SE_EXPORT_KALEIDO = function ({ strokes, n, mirrors, size = 4096, background = '#ffffff', filename }) {
    const cv = document.createElement('canvas'); cv.width = cv.height = size; const c = cv.getContext('2d'); const R = size / 2, k = size / 600;
    c.fillStyle = background; c.fillRect(0, 0, size, size); c.lineCap = c.lineJoin = 'round';
    for (const s of strokes) { c.strokeStyle = s.col; c.lineWidth = (s.w || 3) * k;
      for (const o of rosette(n, mirrors)) { c.beginPath(); s.pts.forEach(([x, y], i) => { const X = o[0] * x + o[1] * y, Y = o[2] * x + o[3] * y; const px = R + R * X, py = R - R * Y; i ? c.lineTo(px, py) : c.moveTo(px, py); }); c.stroke(); } }
    cv.toBlob(b => { const a = document.createElement('a'); a.download = filename || `symmetry-${mirrors ? 'D' : 'C'}${n}-${size}px.png`; a.href = URL.createObjectURL(b); a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 4000); }, 'image/png');
  };
})();
