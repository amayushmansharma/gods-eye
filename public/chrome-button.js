/**
 * God's Eye - Liquid Chrome Scan Button
 * Ported from ThreeUI GetStartedButton
 * 
 * Source: https://threeui.com/source-code/get-started-button.json
 * Key file: src/shaders/get-started-button/sources/get-started-button.html
 * SHA-256: b1dcac0a1e4cabb2031271842b370ce42f6f8cf579ff4208be312fa98e4cf9ff
 * License: ThreeUI Terms of Use / Commercial & Personal Component Rights
 *
 * Tactile liquid-chrome control with refractive spectral ring, crystal center,
 * floating particles, and pointer-drawn light scratches.
 */

(() => {
  'use strict';

  // Palette configuration: 'mono' (faint emerald #34d399 + chrome) or 'authored' (ThreeUI amber)
  const PALETTE = 'mono';

  // Inject component CSS
  const styleEl = document.createElement('style');
  styleEl.textContent = `
    @font-face {
      font-family: "Geist Mono";
      font-weight: 300;
      font-style: normal;
      font-display: swap;
      src: url(data:font/woff2;base64,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) format("woff2");
    }

    .chrome-scan-btn {
      --w: 130px;
      --h: 44px;
      --u: calc(var(--w) / 758);
      --bg: #222225;
      --ink: #4c4c52;
      --ink-hover: #0f0f12;
      --chev: #2c2c33;
      --chev-hover: ${PALETTE === 'mono' ? '#a7f3d0' : '#fff3e4'};
      --accent: ${PALETTE === 'mono' ? '52, 211, 153' : '255, 138, 40'};
      --ease-io: cubic-bezier(.45, 0, .2, 1);
      --ease-out: cubic-bezier(.16, .84, .3, 1);

      position: relative;
      width: var(--w);
      height: var(--h);
      padding: 0;
      margin: 0;
      border: 0;
      background: transparent;
      border-radius: 9999px;
      cursor: pointer;
      appearance: none;
      -webkit-tap-highlight-color: transparent;
      outline: none;
      isolation: isolate;
      overflow: hidden;
      flex-shrink: 0;
      transition: transform .18s var(--ease-out);
    }

    .chrome-scan-btn:focus-visible {
      outline: 2px solid #34d399;
      outline-offset: 3px;
    }

    .chrome-scan-btn:active,
    .chrome-scan-btn.is-pressed {
      transform: translateY(2px) scale(.98);
    }

    /* Halo light */
    .chrome-scan-btn .halo {
      position: absolute;
      z-index: 1;
      pointer-events: none;
      left: calc(456 * var(--u));
      top: calc(-20 * var(--u));
      width: calc(260 * var(--u));
      height: calc(260 * var(--u));
      border-radius: 50%;
      background: radial-gradient(circle, rgba(var(--accent), .45) 0%, rgba(var(--accent), .16) 35%, rgba(var(--accent), 0) 66%);
      opacity: 0;
      transition: opacity .42s cubic-bezier(.6, 0, .35, 1);
    }

    /* Face canvas */
    .chrome-scan-btn .face {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 2;
    }
    .chrome-scan-btn .face canvas {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      display: block;
    }

    /* Label text & icon */
    .chrome-scan-btn .label {
      position: absolute;
      left: calc(125 * var(--u));
      top: 50%;
      transform: translateY(-50%);
      font-family: "Geist Mono", "JetBrains Mono", ui-monospace, monospace;
      font-weight: 500;
      font-size: max(11px, calc(64 * var(--u)));
      line-height: 1;
      letter-spacing: calc(2.5 * var(--u));
      white-space: pre;
      color: var(--ink);
      -webkit-text-stroke: calc(0.35 * var(--u)) currentColor;
      pointer-events: none;
      user-select: none;
      z-index: 5;
      transition: color .3s var(--ease-io) .15s;
    }

    /* Crystal knob & overlay */
    .chrome-scan-btn .knob {
      position: absolute;
      left: calc(528 * var(--u));
      top: calc(54 * var(--u));
      width: calc(176 * var(--u));
      height: calc(176 * var(--u));
      border-radius: 50%;
      overflow: hidden;
      pointer-events: none;
      z-index: 6;
      -webkit-mask-image: radial-gradient(circle, #000 99%, transparent 100%);
      mask-image: radial-gradient(circle, #000 99%, transparent 100%);
    }
    .chrome-scan-btn .knob > * {
      position: absolute;
      inset: 0;
      border-radius: 50%;
    }
    .chrome-scan-btn .glow {
      width: 0;
      height: 0;
      inset: auto;
      opacity: 0;
      transition: opacity .42s cubic-bezier(.6, 0, .35, 1);
    }

    /* Pen SVG */
    .chrome-scan-btn .pen {
      overflow: visible;
      width: 100%;
      height: 100%;
    }
    .chrome-scan-btn .pen path {
      fill: none;
      stroke: var(--chev);
      stroke-width: 4.4;
      stroke-linecap: round;
      stroke-linejoin: round;
      transition: stroke .15s var(--ease-io) .15s;
    }
    .chrome-scan-btn .pen-move {
      transform: translate(calc(-6 * var(--u)), 0) rotate(0deg);
      transform-origin: 68px 108px;
      transition: transform .5s var(--ease-io) .05s;
    }
    .chrome-scan-btn .pen-wiggle {
      transform-origin: 68px 108px;
    }
    .chrome-scan-btn .scribble {
      stroke: var(--chev-hover);
      stroke-dasharray: 36;
      stroke-dashoffset: 36;
      transition: stroke-dashoffset .45s var(--ease-io);
    }
    @keyframes pen-write {
      0% { transform: rotate(-4deg) translate(0, 0); }
      50% { transform: rotate(3deg) translate(0, calc(-1.5 * var(--u))); }
      100% { transform: rotate(-4deg) translate(0, 0); }
    }

    /* Hover / Focus states */
    .chrome-scan-btn:hover .halo,
    .chrome-scan-btn:focus-visible .halo,
    .chrome-scan-btn.is-hover .halo {
      opacity: 1;
      transition: opacity .4s cubic-bezier(.5, 0, .3, 1) .1s;
    }
    .chrome-scan-btn:hover .label,
    .chrome-scan-btn:focus-visible .label,
    .chrome-scan-btn.is-hover .label {
      color: var(--ink-hover);
      transition: color .38s cubic-bezier(.55, 0, .25, 1) .1s;
    }
    .chrome-scan-btn:hover .glow,
    .chrome-scan-btn:focus-visible .glow,
    .chrome-scan-btn.is-hover .glow {
      opacity: 1;
      transition: opacity .32s cubic-bezier(.5, 0, .3, 1) .1s;
    }
    .chrome-scan-btn:hover .pen path,
    .chrome-scan-btn:focus-visible .pen path,
    .chrome-scan-btn.is-hover .pen path {
      stroke: var(--chev-hover);
      transition: stroke .34s var(--ease-io) .1s;
    }
    .chrome-scan-btn:hover .pen-move,
    .chrome-scan-btn:focus-visible .pen-move,
    .chrome-scan-btn.is-hover .pen-move {
      transform: translate(calc(20 * var(--u)), calc(-1 * var(--u))) rotate(-6deg);
      transition: transform .9s cubic-bezier(.5, 0, .3, 1) .1s;
    }
    .chrome-scan-btn:hover .scribble,
    .chrome-scan-btn:focus-visible .scribble,
    .chrome-scan-btn.is-hover .scribble {
      stroke-dashoffset: 0;
      transition: stroke-dashoffset .9s cubic-bezier(.5, 0, .3, 1) .1s;
    }
    .chrome-scan-btn:hover .pen-wiggle,
    .chrome-scan-btn:focus-visible .pen-wiggle,
    .chrome-scan-btn.is-hover .pen-wiggle {
      animation: pen-write 1.1s ease-in-out 1.1s infinite;
    }

    /* Scanning state */
    .chrome-scan-btn.is-scanning {
      cursor: wait;
      opacity: 0.95;
    }
    .chrome-scan-btn.is-scanning .halo {
      opacity: 0.85;
      animation: pulseHalo 1.8s ease-in-out infinite alternate;
    }
    @keyframes pulseHalo {
      0% { opacity: 0.45; transform: scale(0.96); }
      100% { opacity: 0.95; transform: scale(1.05); }
    }

    /* Done state flash */
    .chrome-scan-btn.is-done .halo {
      opacity: 1;
      filter: brightness(1.6);
      transition: filter .3s ease-out;
    }

    /* Graceful WebGL fallback */
    .chrome-scan-btn.no-gl {
      background: #ffffff !important;
      color: #000000 !important;
      border-radius: 9999px !important;
      padding: 8px 16px !important;
      width: auto !important;
      height: auto !important;
      min-height: 40px !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
      overflow: visible !important;
    }
    .chrome-scan-btn.no-gl .face,
    .chrome-scan-btn.no-gl .halo,
    .chrome-scan-btn.no-gl .knob,
    .chrome-scan-btn.no-gl .knob-fallback {
      display: none !important;
    }
    .chrome-scan-btn.no-gl .label {
      position: static !important;
      transform: none !important;
      color: #000000 !important;
      -webkit-text-stroke: 0 !important;
      font-family: inherit !important;
      font-size: 12px !important;
      font-weight: 600 !important;
      letter-spacing: normal !important;
      display: inline-flex !important;
      align-items: center !important;
    }
    .chrome-scan-btn.no-gl:hover {
      background: #e4e4e7 !important;
    }
    .chrome-scan-btn.no-gl:active {
      transform: scale(0.95) !important;
    }

    @media (prefers-reduced-motion: reduce) {
      .chrome-scan-btn, .chrome-scan-btn *, .chrome-scan-btn::before {
        transition-duration: .01s !important;
        animation: none !important;
      }
    }
  `;
  document.head.appendChild(styleEl);

  // Initialize button controller
  function initChromeButton() {
    const cta = document.getElementById('scanSubmitBtn');
    if (!cta) return;

    // Check prefers-reduced-motion
    const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

    const cv = cta.querySelector('canvas');
    const clock = cta.querySelector('.glow');
    const labelSpan = cta.querySelector('.label .btn-text');
    const iconSpan = cta.querySelector('.label .scan-icon');

    if (!cv) {
      cta.classList.add('no-gl');
      return;
    }

    // Attempt WebGL2 context creation
    let gl = null;
    try {
      gl = cv.getContext('webgl2', {
        alpha: true,
        premultipliedAlpha: true,
        antialias: false,
        powerPreference: 'low-power'
      });
    } catch (e) {
      cta.classList.add('no-gl');
      return;
    }

    if (!gl) {
      cta.classList.add('no-gl');
      return;
    }

    // WebGL Shaders
    const QUAD_VS = `#version 300 es
    in vec2 aPos; void main(){ gl_Position = vec4(aPos, 0., 1.); }`;

    const FACE_FS = `#version 300 es
    precision highp float;
    uniform vec2 uRes; uniform float uU; uniform float uTime; uniform float uHover;
    uniform sampler2D uScratch;
    out vec4 fragColor;

    float hash21(vec2 p){ vec3 q=fract(vec3(p.xyx)*.1031); q+=dot(q,q.yzx+33.33); return fract((q.x+q.y)*q.z); }
    vec2 hash22(vec2 p){ vec3 q=fract(vec3(p.xyx)*vec3(.1031,.1030,.0973)); q+=dot(q,q.yzx+33.33); return fract((q.xx+q.yz)*q.zy); }
    float vnoise(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
      return mix(mix(hash21(i),hash21(i+vec2(1,0)),f.x), mix(hash21(i+vec2(0,1)),hash21(i+vec2(1,1)),f.x), f.y); }
    float fbm(vec2 p){ float a=.5, s=0.; for(int i=0;i<4;i++){ s+=a*vnoise(p); p=p*2.02+vec2(31.7,17.3); a*=.5; } return s; }

    vec3 voro(vec2 p){ vec2 i=floor(p), f=fract(p); float d1=9., d2=9.; vec2 id=vec2(0);
      for(int y=-1;y<=1;y++) for(int x=-1;x<=1;x++){ vec2 g=vec2(float(x),float(y)); vec2 r=g+hash22(i+g)-f; float d=dot(r,r);
        if(d<d1){ d2=d1; d1=d; id=i+g; } else if(d<d2){ d2=d; } }
      return vec3(sqrt(d1), sqrt(d2), hash21(id)); }
    float tone(float y){ float t=y/232.; float v=mix(.965,.90,smoothstep(.12,.32,t)); v=mix(v,.70,smoothstep(.32,.64,t)); return mix(v,.50,smoothstep(.64,1.,t)); }

    float fbm3(vec2 p){ float a=.5, s=0.; for(int i=0;i<3;i++){ s+=a*vnoise(p); p=p*2.02+vec2(31.7,17.3); a*=.5; } return s; }
    float H(vec2 p, float t){
      vec2 w = vec2(fbm3(p*.8 + vec2(0., t*.13)), fbm3(p*.8 + vec2(5.2, -t*.09)));
      return fbm3(p + (w-.5)*1.2 + vec2(t*.04, 0.));
    }
    vec3 env(vec3 R){
      float y = R.y;
      vec3 c = vec3(.07,.07,.08);
      c += vec3(.98,.98,1.) * smoothstep(.03,.28,y) * (1.-smoothstep(.55,.90,y));
      c += vec3(.30) * smoothstep(.90,1.,y);
      c += vec3(.36,.36,.40) * (1.-smoothstep(0.,.09,abs(y)));
      c += vec3(.22,.22,.25) * smoothstep(-.80,-.40,y) * (1.-smoothstep(-.32,-.10,y));
      c *= .92 + .08*R.x;
      return c;
    }

    float ringS(vec2 p){
      if (p.x < 116.) { vec2 v = p - vec2(116.,116.); return 1312.4 + atan(-v.x, v.y)*116.; }
      if (p.x > 590.) { vec2 v = p - vec2(590.,116.); return 474. + atan(v.x, -v.y)*116.; }
      return p.y < 116. ? (p.x - 116.) : 838.4 + (590. - p.x);
    }
    float wrapd(float a, float b){ return mod(a - b + 838.4, 1676.8) - 838.4; }

    vec3 metal(vec2 p, float d, vec2 n, vec2 kp, float px, out float alpha){
      float T = 26.;
      alpha = 1. - smoothstep(T-px, T+px, d);
      if (alpha <= 0.) return vec3(0.);
      float u_ = clamp(2.*d/T - 1., -1., 1.);
      float hz = sqrt(max(0., 1.-u_*u_));
      float dh = -u_/max(hz,.12);
      float sA = ringS(p);
      float t = uTime * (1. + .15*uHover);
      float k = 6.2832/1676.8;
      float a1 = k*3.*sA - t*.55, a2 = k*5.*sA + t*.42 + 1.7, a3 = k*8.*sA - t*.85 + 4.1;
      float flow = (sin(a1) + .7*sin(a2) + .5*sin(a3)) / 2.2;
      float dflow = (3.*cos(a1) + 3.5*cos(a2) + 4.*cos(a3)) * k / 2.2;
      float g1 = wrapd(sA, mod(t*105., 1676.8));
      float g2 = wrapd(sA, mod(2200. - t*75., 1676.8));
      float drop = exp(-g1*g1/1600.) + exp(-g2*g2/1600.);
      vec2 tau = vec2(-n.y, n.x);
      vec2 grad = dh*n*(.9 + .3*flow + .6*drop) + tau*dflow*34.;
      vec3 N = normalize(vec3(-grad.x, grad.y, 1.));
      vec3 V = vec3(0.,0.,1.);
      vec3 R = reflect(-V, N);
      vec3 c = env(R) * vec3(.96,.97,1.);
      c *= .90 + .18*flow;
      ${PALETTE === 'mono' ? `
      // Mono palette: desaturated chrome with faint cool/emerald (#34d399) tint
      c += drop * .5 * hz*hz * mix(vec3(1.), vec3(0.85, 1.0, 0.94), uHover);
      c += .16*pow(1.-N.z, 3.);
      c *= .55 + .45*smoothstep(0., 3., d);
      c += uHover * vec3(0.20, 0.83, 0.60) * .20 * smoothstep(200.,70.,length(kp)) * (.4+.6*hz);
      ` : `
      // Authored palette: warm amber glint
      c += drop * .5 * hz*hz * mix(vec3(1.), vec3(1.,.78,.5), uHover);
      c += .16*pow(1.-N.z, 3.);
      c *= .55 + .45*smoothstep(0., 3., d);
      c += uHover * vec3(1.,.45,.12) * .22 * smoothstep(200.,70.,length(kp)) * (.4+.6*hz);
      `}
      return c;
    }

    vec3 crystal(vec2 kp, float kr, float px, vec3 under){
      vec2 q = kp/88.;
      float t = q.y*.5+.5;
      float rw = kr/88.;
      vec3 well = vec3(mix(.34,.60,t));
      well *= 1. - .40*smoothstep(.70,1.,rw)*(1.-t);
      well += .28*smoothstep(.90,.985,rw)*t;
      float R = 80.; float rs = kr/R;
      well *= 1. - .35*smoothstep(R+7., R, kr);
      float sph = 1. - smoothstep(R-px, R+px, kr);
      if (sph <= 0.) return well;
      float z = sqrt(max(0., 1.-rs*rs));
      vec3 N = vec3(q.x*88./R, -q.y*88./R, z);
      vec3 V = vec3(0.,0.,1.);
      float fres = pow(1.-z, 2.6);
      vec3 Rf = refract(-V, N, 1./1.5);
      vec2 uv = N.xy*.5 + Rf.xy*1.1 + vec2(uTime*.02, -uTime*.013);
      vec3 vr = voro(uv*3.0);
      float facet = 1. - smoothstep(0., .14, vr.y - vr.x);
      float shard = .7 + .3*vr.z;
      float mott = fbm(uv*4.);
      float tr = clamp(.5 - (q.y + Rf.y*.8)*.5, 0., 1.);
      vec3 floorC = vec3(mix(.16,.34,tr)) * (.85+.3*mott);
      vec3 glass = mix(floorC, vec3(.62,.66,.80), .22*shard + .18*(1.-z)) * (.8+.2*z);
      float depth = pow(rs, 1.5);
      ${PALETTE === 'mono' ? `
      // Mono palette: emerald/cool chrome core
      vec3 core = mix(vec3(.03,.18,.12), vec3(.20,.83,.60), depth) * (.75+.5*shard);
      core = mix(core, vec3(.55, 1.0, .80), smoothstep(.5,1.,rs)*smoothstep(-.1,.9,-N.y));
      vec3 interior = mix(glass, core, uHover);
      interior += facet * mix(vec3(.80,.84,1.)*(.55+.45*z), vec3(.40, .95, .75)*.6, uHover);
      float pt = smoothstep(.10, 0., vr.x) * (.5+.5*sin(uTime*2.+vr.z*40.));
      interior += pt * mix(vec3(.9,.92,1.), vec3(.75, 1.0, .88), uHover) * (.55+.45*uHover);
      // lighting
      vec3 L1 = normalize(vec3(-.45,.75,.5));
      float blob = smoothstep(.72,.985, dot(N, normalize(vec3(-.18,.72,.67))));
      float spec = pow(max(dot(reflect(-L1,N),V),0.), 90.);
      vec3 rimCol = mix(vec3(.96,.96,1.), vec3(.60, 1.0, .82), uHover);
      vec3 c = interior*(1.-.45*fres) + rimCol*fres*.9;
      c += blob*.42*(1.-.5*uHover) + spec*.9;
      float glint = smoothstep(.55,1.,rs) * smoothstep(.15,1.,-N.y);
      c += mix(vec3(.78,.74,.92), vec3(.20,.83,.60), uHover) * glint * .55;
      ` : `
      // Authored palette: warm amber core
      vec3 core = mix(vec3(.26,.05,0.), vec3(.95,.36,.03), depth) * (.75+.5*shard);
      core = mix(core, vec3(1.,.66,.22), smoothstep(.5,1.,rs)*smoothstep(-.1,.9,-N.y));
      vec3 interior = mix(glass, core, uHover);
      interior += facet * mix(vec3(.80,.84,1.)*(.55+.45*z), vec3(1.,.70,.35)*.6, uHover);
      float pt = smoothstep(.10, 0., vr.x) * (.5+.5*sin(uTime*2.+vr.z*40.));
      interior += pt * mix(vec3(.9,.92,1.), vec3(1.,.92,.75), uHover) * (.55+.45*uHover);
      // lighting
      vec3 L1 = normalize(vec3(-.45,.75,.5));
      float blob = smoothstep(.72,.985, dot(N, normalize(vec3(-.18,.72,.67))));
      float spec = pow(max(dot(reflect(-L1,N),V),0.), 90.);
      vec3 rimCol = mix(vec3(.96,.96,1.), vec3(1.,.72,.40), uHover);
      vec3 c = interior*(1.-.45*fres) + rimCol*fres*.9;
      c += blob*.42*(1.-.5*uHover) + spec*.9;
      float glint = smoothstep(.55,1.,rs) * smoothstep(.15,1.,-N.y);
      c += mix(vec3(.78,.74,.92), vec3(1.,.50,.12), uHover) * glint * .55;
      `}
      return mix(well, c, sph);
    }

    void main(){
      // Shift origin by 26 units inside 758x284 design space to clip cleanly
      vec2 p = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y) / uU - vec2(26.);
      float px = 1./uU;
      vec2 c = vec2(clamp(p.x,116.,590.),116.);
      vec2 dv = p - c; float dist = length(dv);
      float d = dist - 116.;
      vec2 kp = p - vec2(590.,116.); float kr = length(kp);
      float cover = 1. - smoothstep(-px, px, d);
      if (cover <= .001){
        float ma; vec3 mc = metal(p, d, dv/max(dist,1e-4), kp, px, ma);
        fragColor = vec4(mc*ma, ma); return;
      }
      float inside = -d;
      vec2 n = dist > 0. ? dv/dist : vec2(0.,-1.);
      float lit = -n.y;
      float base = tone(p.y) * (1. + .05*(fbm(p*.03)-.5));
      float k = .42 - .22*lit, w = 34. - 10.*lit;
      float f = pow(max(0., 1.-(inside-2.5)/w), 1.25);
      float L = base * (1. - k*f);
      float rim = 1. - smoothstep(2.0, 3.2, inside);
      L = mix(L, .34, rim);
      vec2 cell = floor(p*.5); vec2 fc = fract(p*.5)-.5;
      float dotm = smoothstep(.72,.22,length(fc));
      float h1=hash21(cell), h2=hash21(cell+11.3), h3=hash21(cell+23.7), h4=hash21(cell+37.1);
      float envD = .15 + .85*smoothstep(.05,.40,p.y/232.);
      float fleck = step(h1,.42) * (.25+.55*h2) * dotm * envD;
      L *= 1. - .30*fleck;
      float tw = .6 + .4*sin(uTime*(.8+1.6*h3) + h4*6.2832);
      float spark = step(h3,.10) * h2*h2 * dotm * tw;
      L += .38*spark*(.5+.5*smoothstep(.1,.5,p.y/232.));
      vec2 tc = gl_FragCoord.xy / uRes;
      float s0 = texture(uScratch, tc).r;
      float sU = texture(uScratch, tc + vec2(0., 1./uRes.y)).r;
      float sD = texture(uScratch, tc - vec2(0., 1./uRes.y)).r;
      L += (.58*(sU - sD) - .05*s0) * (1.-rim);
      vec3 col = vec3(L);
      ${PALETTE === 'mono' ? `
      col += uHover * vec3(0.20, 0.83, 0.60) * .20 * smoothstep(175.,88.,kr) * (1.-rim);
      ` : `
      col += uHover * vec3(1.,.45,.10) * .22 * smoothstep(175.,88.,kr) * (1.-rim);
      `}
      float wellA = 1. - smoothstep(88.-px, 88.+px, kr);
      if (wellA > 0.) col = mix(col, crystal(kp, kr, px, col), wellA);
      if (cover < .999){ float ma; vec3 mc = metal(p, max(d,0.), dv/max(dist,1e-4), kp, px, ma); col = mix(mc, col, cover); cover = max(cover, ma); }
      fragColor = vec4(col*cover, cover);
    }`;

    const PTS_VS = `#version 300 es
    in vec4 aSeed;
    uniform vec2 uRes; uniform float uU, uTime, uHover;
    out float vA; out vec3 vCol;
    void main(){
      float s0=aSeed.x, s1=aSeed.y, s2=aSeed.z, s3=aSeed.w;
      float speed = (.10 + .30*s3) * (1. + 2.*uHover);
      float t = uTime*speed + s0*6.2832;
      float rad = .18 + .72*s1;
      float tilt = s2*3.1416, yaw = s3*6.2832;
      vec3 pl = vec3(cos(t), 0., sin(t)) * rad;
      vec3 p1 = vec3(pl.x, pl.y*cos(tilt)-pl.z*sin(tilt), pl.y*sin(tilt)+pl.z*cos(tilt));
      vec3 p = vec3(p1.x*cos(yaw)+p1.z*sin(yaw), p1.y, -p1.x*sin(yaw)+p1.z*cos(yaw));
      float esc = step(.74, s1) * uHover;
      float rise = fract(uTime*.22 + s0);
      p.y += esc * rise * 1.9; p.x += esc * sin(rise*9. + s2*6.) * .18 * rise;
      float fade = 1. - esc*smoothstep(.5, 1., rise);
      vec2 ref = vec2(590.,116.) + vec2(p.x, -p.y) * 80. + vec2(26.);
      vec2 px = ref * uU; px.y = uRes.y - px.y;
      gl_Position = vec4(px/uRes*2.-1., 0., 1.);
      float depth = p.z*.5+.5;
      gl_PointSize = max(1., (1.5 + 2.8*s2) * uU * (.55+.55*depth));
      float tw = .6 + .4*sin(uTime*(1.+2.*s2) + s1*6.28);
      vA = (.42 + .58*uHover) * (.3 + .7*depth) * tw * fade;
      ${PALETTE === 'mono' ? `
      vCol = mix(vec3(.80,.85,.92), vec3(.35,.95,.72), uHover);
      ` : `
      vCol = mix(vec3(.80,.82,.95), vec3(1.,.66,.28), uHover);
      `}
    }`;

    const PTS_FS = `#version 300 es
    precision mediump float; in float vA; in vec3 vCol; out vec4 o;
    void main(){ float d=length(gl_PointCoord-.5)*2.; float a=smoothstep(1.,.12,d); a*=a*vA; o=vec4(vCol*a, a); }`;

    const LINE_VS = `#version 300 es
    in vec2 aP; in float aW; uniform vec2 uRes; uniform float uU; out float vW;
    void main(){ vec2 px = (aP + vec2(26.)) * uU; px.y = uRes.y - px.y; gl_Position = vec4(px/uRes*2.-1., 0., 1.); vW = aW; }`;

    const LINE_FS = `#version 300 es
    precision mediump float; in float vW; out vec4 o; void main(){ o = vec4(vW); }`;

    const FADE_FS = `#version 300 es
    precision mediump float; uniform float uFade; out vec4 o; void main(){ o = vec4(uFade); }`;

    // Shader compilation
    const compile = (type, src) => {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        throw new Error(gl.getShaderInfoLog(s));
      }
      return s;
    };

    const program = (vs, fs) => {
      const p = gl.createProgram();
      gl.attachShader(p, compile(gl.VERTEX_SHADER, vs));
      gl.attachShader(p, compile(gl.FRAGMENT_SHADER, fs));
      gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
        throw new Error(gl.getProgramInfoLog(p));
      }
      return p;
    };

    let faceProg, ptsProg, lineProg, fadeProg;
    const U = {};
    let vaoQuad, vaoPts, vaoLine, lb;
    const N_PTS = 64; // Refined particle count for ~31px knob footprint

    try {
      faceProg = program(QUAD_VS, FACE_FS);
      ptsProg = program(PTS_VS, PTS_FS);
      lineProg = program(LINE_VS, LINE_FS);
      fadeProg = program(QUAD_VS, FADE_FS);
    } catch (e) {
      console.warn('ChromeScanButton shader compilation fallback:', e);
      cta.classList.add('no-gl');
      return;
    }

    for (const k of ['uRes', 'uU', 'uTime', 'uHover']) {
      U['f_' + k] = gl.getUniformLocation(faceProg, k);
      U['p_' + k] = gl.getUniformLocation(ptsProg, k);
    }
    U.f_uScratch = gl.getUniformLocation(faceProg, 'uScratch');
    U.l_uRes = gl.getUniformLocation(lineProg, 'uRes');
    U.l_uU = gl.getUniformLocation(lineProg, 'uU');
    U.fade = gl.getUniformLocation(fadeProg, 'uFade');

    // Quad VAO
    vaoQuad = gl.createVertexArray();
    gl.bindVertexArray(vaoQuad);
    const qb = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, qb);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const aPos = gl.getAttribLocation(faceProg, 'aPos');
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

    // Particle seeds VAO
    vaoPts = gl.createVertexArray();
    gl.bindVertexArray(vaoPts);
    const seeds = new Float32Array(N_PTS * 4);
    let s = 0x2545f491;
    const rnd = () => {
      s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
      return s / 4294967296;
    };
    for (let i = 0; i < seeds.length; i++) seeds[i] = rnd();
    const pb = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, pb);
    gl.bufferData(gl.ARRAY_BUFFER, seeds, gl.STATIC_DRAW);
    const aSeed = gl.getAttribLocation(ptsProg, 'aSeed');
    gl.enableVertexAttribArray(aSeed);
    gl.vertexAttribPointer(aSeed, 4, gl.FLOAT, false, 0, 0);

    // Line strokes VAO
    vaoLine = gl.createVertexArray();
    gl.bindVertexArray(vaoLine);
    lb = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, lb);
    gl.bufferData(gl.ARRAY_BUFFER, 12 * 2048, gl.DYNAMIC_DRAW);
    const aP = gl.getAttribLocation(lineProg, 'aP');
    const aW = gl.getAttribLocation(lineProg, 'aW');
    gl.enableVertexAttribArray(aP);
    gl.vertexAttribPointer(aP, 2, gl.FLOAT, false, 12, 0);
    gl.enableVertexAttribArray(aW);
    gl.vertexAttribPointer(aW, 1, gl.FLOAT, false, 12, 8);
    gl.bindVertexArray(null);

    // Scratch Map FBO
    let scratchTex = null, fbo = null;
    function makeScratchMap(w, h) {
      if (scratchTex) {
        gl.deleteTexture(scratchTex);
        gl.deleteFramebuffer(fbo);
      }
      scratchTex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, scratchTex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      fbo = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, scratchTex, 0);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    }

    // Pointer light scratch tracking
    const segs = [];
    let prev = null;
    cta.addEventListener('pointermove', e => {
      const r = cta.getBoundingClientRect();
      const u = r.width / 758;
      const x = (e.clientX - r.left) / u - 26;
      const y = (e.clientY - r.top) / u - 26;
      if (!prev) { prev = { x, y }; return; }
      const dx = x - prev.x, dy = y - prev.y, len = Math.hypot(dx, dy);
      if (len < 0.8) return;
      const tx = dx / len, ty = dy / len, nx = -ty, ny = tx;
      for (let i = 0; i < 2; i++) {
        const o = (rnd() - 0.5) * 4;
        const w = 0.25 + 0.25 * rnd();
        const j0 = rnd() * 0.25 * len, j1 = rnd() * 0.25 * len;
        segs.push(prev.x + nx * o + tx * j0, prev.y + ny * o + ty * j0, w, x + nx * o - tx * j1, y + ny * o - ty * j1, w);
      }
      if (segs.length > 2000) segs.splice(0, segs.length - 2000);
      prev = { x, y };
    });
    cta.addEventListener('pointerleave', () => { prev = null; });

    // Touch & pointer interaction
    cta.addEventListener('pointerdown', () => {
      if (buttonState !== 'scanning') {
        cta.classList.add('is-pressed');
      }
    });
    const clearPress = () => cta.classList.remove('is-pressed');
    cta.addEventListener('pointerup', clearPress);
    cta.addEventListener('pointercancel', clearPress);

    // Keyboard interaction (Enter / Space)
    cta.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        cta.classList.add('is-pressed');
        if (e.key === 'Enter') {
          cta.click();
        }
      }
    });
    cta.addEventListener('keyup', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        cta.classList.remove('is-pressed');
      }
    });

    // State management
    let buttonState = 'idle'; // 'idle' | 'hover' | 'pressed' | 'scanning' | 'done'
    let doneTimer = null;

    function applyState(newState) {
      buttonState = newState;
      cta.classList.remove('is-hover', 'is-pressed', 'is-scanning', 'is-done');

      if (newState === 'idle') {
        cta.disabled = false;
        cta.removeAttribute('aria-busy');
        if (labelSpan) labelSpan.textContent = 'Scan';
        if (iconSpan) iconSpan.classList.remove('hidden');
      } else if (newState === 'hover') {
        cta.classList.add('is-hover');
      } else if (newState === 'pressed') {
        cta.classList.add('is-pressed');
      } else if (newState === 'scanning') {
        cta.disabled = true;
        cta.setAttribute('aria-busy', 'true');
        cta.classList.add('is-scanning');
        if (labelSpan) labelSpan.textContent = 'Scanning...';
        if (iconSpan) iconSpan.classList.add('hidden');
      } else if (newState === 'done') {
        cta.disabled = false;
        cta.removeAttribute('aria-busy');
        cta.classList.add('is-done');
        if (labelSpan) labelSpan.textContent = 'Done!';
        if (iconSpan) iconSpan.classList.remove('hidden');

        clearTimeout(doneTimer);
        doneTimer = setTimeout(() => {
          applyState('idle');
        }, 600);
      }
      requestRender();
    }

    window.ChromeScanButton = {
      setState: (s) => applyState(s),
      getState: () => buttonState
    };

    // Render loop and performance throttling
    let W = 0, H = 0, raf = 0, isLooping = false;
    let lastRenderTime = 0;
    let isVisible = true;
    let isIntersecting = true;

    function resize() {
      const r = cta.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const u = r.width / 758;
      const w = Math.round(758 * u * dpr), h = Math.round(284 * u * dpr);
      if (w < 4 || h < 4) return false;
      if (w !== W || h !== H) {
        W = w; H = h;
        cv.width = W; cv.height = H;
        makeScratchMap(W, H);
      }
      return true;
    }

    function render(now) {
      if (!resize()) return;

      // Calculate hover amount from CSS or synthetic state
      let hover = parseFloat(getComputedStyle(clock).opacity) || 0;
      if (buttonState === 'scanning') {
        hover = 0.8 + 0.2 * Math.sin(now * 0.005);
      } else if (buttonState === 'done') {
        hover = 1.0;
      } else if (buttonState === 'hover' || buttonState === 'pressed') {
        hover = Math.max(hover, 1.0);
      }

      const t = reducedMotion ? 0 : now / 1000;
      gl.viewport(0, 0, W, H);

      // 1. Scratch map: fade slightly, then add stroke segments
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
      gl.enable(gl.BLEND);
      gl.blendEquation(gl.FUNC_REVERSE_SUBTRACT);
      gl.blendFunc(gl.ONE, gl.ONE);
      gl.useProgram(fadeProg);
      gl.uniform1f(U.fade, 1.25 / 255);
      gl.bindVertexArray(vaoQuad);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      gl.blendEquation(gl.FUNC_ADD);

      if (segs.length) {
        gl.useProgram(lineProg);
        gl.uniform2f(U.l_uRes, W, H);
        gl.uniform1f(U.l_uU, W / 758);
        gl.bindVertexArray(vaoLine);
        gl.bindBuffer(gl.ARRAY_BUFFER, lb);
        gl.bufferSubData(gl.ARRAY_BUFFER, 0, new Float32Array(segs));
        gl.drawArrays(gl.LINES, 0, segs.length / 3);
        segs.length = 0;
      }
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);

      // 2. Button Face + Crystal well
      gl.disable(gl.BLEND);
      gl.useProgram(faceProg);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, scratchTex);
      gl.uniform1i(U.f_uScratch, 0);
      gl.uniform2f(U.f_uRes, W, H);
      gl.uniform1f(U.f_uU, W / 758);
      gl.uniform1f(U.f_uTime, t);
      gl.uniform1f(U.f_uHover, hover);
      gl.bindVertexArray(vaoQuad);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

      // 3. Particles inside crystal knob
      if (!reducedMotion) {
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.ONE, gl.ONE);
        gl.useProgram(ptsProg);
        gl.uniform2f(U.p_uRes, W, H);
        gl.uniform1f(U.p_uU, W / 758);
        gl.uniform1f(U.p_uTime, t);
        gl.uniform1f(U.p_uHover, hover);
        gl.bindVertexArray(vaoPts);
        gl.drawArrays(gl.POINTS, 0, N_PTS);
        gl.bindVertexArray(null);
      }

      lastRenderTime = now;
    }

    function loop(now) {
      if (!isLooping) return;

      const shouldThrottle = (buttonState === 'idle') && !reducedMotion;
      const interval = shouldThrottle ? (1000 / 15) : 0;

      if (now - lastRenderTime >= interval) {
        render(now);
      }

      if (reducedMotion && buttonState === 'idle') {
        isLooping = false;
        return;
      }

      raf = requestAnimationFrame(loop);
    }

    function startLoop() {
      if (isLooping) return;
      if (!isVisible || !isIntersecting) return;
      isLooping = true;
      raf = requestAnimationFrame(loop);
    }

    function stopLoop() {
      isLooping = false;
      cancelAnimationFrame(raf);
    }

    function requestRender() {
      if (!isLooping) {
        startLoop();
      }
    }

    // Visibility and Intersection Observers
    document.addEventListener('visibilitychange', () => {
      isVisible = !document.hidden;
      if (isVisible) {
        render(performance.now());
        startLoop();
      } else {
        stopLoop();
      }
    });

    if (typeof IntersectionObserver !== 'undefined') {
      const observer = new IntersectionObserver(([entry]) => {
        isIntersecting = entry.isIntersecting;
        if (isIntersecting) {
          render(performance.now());
          startLoop();
        } else {
          stopLoop();
        }
      }, { rootMargin: '50px' });
      observer.observe(cta);
    }

    // Context loss handling
    cv.addEventListener('webglcontextlost', e => {
      e.preventDefault();
      stopLoop();
      cta.classList.add('no-gl');
    });

    cv.addEventListener('webglcontextrestored', () => {
      cta.classList.remove('no-gl');
      render(performance.now());
      startLoop();
    });

    // Hover / Focus listeners to wake full 60fps
    cta.addEventListener('mouseenter', () => {
      if (buttonState === 'idle') applyState('hover');
    });
    cta.addEventListener('mouseleave', () => {
      if (buttonState === 'hover') applyState('idle');
    });
    cta.addEventListener('focus', () => {
      if (buttonState === 'idle') applyState('hover');
    });
    cta.addEventListener('blur', () => {
      if (buttonState === 'hover') applyState('idle');
    });

    // Initial render and loop start
    render(performance.now());
    startLoop();
  }

  // DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChromeButton);
  } else {
    initChromeButton();
  }
})();
