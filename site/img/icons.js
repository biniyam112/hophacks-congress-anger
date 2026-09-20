/* inline SVG icons for the forecast ladder */
window.ICONS = {
  nothing: `<svg viewBox="0 0 48 48" class="ico"><circle cx="24" cy="24" r="22" fill="#f1f0ec" stroke="#c3c2b7"/><text x="24" y="32" text-anchor="middle" font-size="26" font-family="Georgia,serif" fill="#898781">?</text></svg>`,
  dem: `<svg viewBox="0 0 48 48" class="ico"><circle cx="24" cy="24" r="22" fill="#2a78d6"/><text x="24" y="33" text-anchor="middle" font-size="27" font-weight="700" font-family="system-ui,sans-serif" fill="#fff">D</text></svg>`,
  clock: (h, m = 0, dark = false) => {
    const a = ((h % 12) + m / 60) * 30, b = m * 6, r = (d) => (d - 90) * Math.PI / 180;
    return `<svg viewBox="0 0 48 48" class="ico"><circle cx="24" cy="24" r="22" fill="${dark ? "#2b2b2b" : "#fff"}" stroke="#c3c2b7"/>
      ${[0,90,180,270].map(d => `<line x1="${24+19*Math.cos(r(d))}" y1="${24+19*Math.sin(r(d))}" x2="${24+16*Math.cos(r(d))}" y2="${24+16*Math.sin(r(d))}" stroke="${dark?"#bbb":"#898781"}" stroke-width="2"/>`).join("")}
      <line x1="24" y1="24" x2="${24+10*Math.cos(r(a))}" y2="${24+10*Math.sin(r(a))}" stroke="${dark?"#fff":"#0b0b0b"}" stroke-width="3" stroke-linecap="round"/>
      <line x1="24" y1="24" x2="${24+15*Math.cos(r(b))}" y2="${24+15*Math.sin(r(b))}" stroke="${dark?"#fff":"#0b0b0b"}" stroke-width="2" stroke-linecap="round"/>
      <circle cx="24" cy="24" r="2" fill="${dark?"#fff":"#0b0b0b"}"/></svg>`;
  },
  silhouette: `<span class="ico unknown">👤</span>`,
  // a coin that spins from an anonymous silhouette to the person's portrait on hover
  portrait: (src, alt) => `<span class="ico coin"><span class="inner"><span class="face front">${window.ICONS.silhouette}</span><span class="face back"><img src="${src}" alt="${alt}"></span></span></span>`,
};
