import json

with open('/tmp/threeui-intro.json') as f:
    bundle = json.load(f)

for f in bundle['files']:
    if 'creator-studio-intro.html' in f['path']:
        html = f['code']

THREEUI_MARK_SVG = """<svg viewBox="0 0 512 512" aria-hidden="true">
  <defs>
    <mask id="threeui-intro-cut" maskUnits="userSpaceOnUse" x="0" y="0" width="512" height="512">
      <rect width="512" height="512" fill="#000"/>
      <circle cx="256" cy="256" r="208" fill="#fff"/>
      <g fill="none" stroke="#000" stroke-linecap="round" stroke-width="28">
        <path d="M36 178C112 252 184 264 260 196C336 128 404 114 482 180"/>
        <path d="M36 292C112 366 184 378 260 310C336 242 404 228 482 294"/>
      </g>
    </mask>
  </defs>
  <rect width="512" height="512" fill="#f5f5f7" mask="url(#threeui-intro-cut)"/>
</svg>"""

lines = html.splitlines(keepends=True)
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if 'function makeWordmark(){' in line:
        start_idx = i
        break

for i in range(start_idx, start_idx + 30):
    if 'var R=rng(7719)' in lines[i]:
        end_idx = i
        break

replacement = """  function makeWordmark(){
    var s=el('div','scene');
    var wrap=el('div','line',s);
    var tx=el('div','tx',wrap);
    var fs=fitPx('Nothing Goes Unnoticed.',1020);
    tx.style.fontSize=fs.toFixed(2)+'px';
    var mk=el('span','mark',tx,APPLE);
    var chars=[], str='Nothing Goes Unnoticed.';
    for(var i=0;i<str.length;i++){
      if(i===12){
        var br=document.createElement('br');
        br.className='wordmark-break';
        tx.appendChild(br);
      }
      var sp=document.createElement('span');
      if(i===12) sp.className='wordmark-space';
      sp.textContent=str[i]===' '?'\\u00a0':str[i];
      tx.appendChild(sp); chars.push(sp);
    }
"""

new_lines = lines[:start_idx] + [replacement] + lines[end_idx:]
html_mod = ''.join(new_lines)

focus_style = """<!-- ThreeUI Intro Isolation & Focus Style (variant="threeui-intro", mode="dark", hue=0, saturation=1.00, brightness=1.00) -->
<!-- Attribution / License: ThreeUI (https://threeui.com) - Copyright ThreeUI, MIT License -->
<style data-threeui-focus>
html, body { width: 100% !important; height: 100% !important; min-height: 0 !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important; background: #000000 !important; color-scheme: dark !important; }
body { position: relative !important; display: flex !important; align-items: center !important; justify-content: center !important; }
body > * { visibility: hidden !important; }
body[data-threeui-ready] > [data-threeui-role] { visibility: visible !important; }
[data-threeui-residual] { display: none !important; }
[data-threeui-hidden] { display: none !important; }
[data-threeui-role="background"] { position: fixed !important; inset: 0 !important; width: 100% !important; height: 100% !important; max-width: none !important; max-height: none !important; z-index: 0 !important; opacity: 1 !important; pointer-events: none !important; }
#comp .scene:first-child {
  display: block !important;
}
#comp .scene:first-child .tx {
  font-size: 78px !important;
  white-space: nowrap !important;
  line-height: 1.15 !important;
}
.wordmark-break {
  display: none;
}
@media (max-width: 820px) {
  #comp .scene:first-child .tx {
    font-size: 84px !important;
    white-space: normal !important;
    line-height: 1.25 !important;
  }
  .wordmark-break {
    display: block !important;
  }
  .wordmark-space {
    display: none !important;
  }
}
</style>"""

focus_script = f"""<!-- ThreeUI Intro Isolation & Focus Script -->
<script data-threeui-focus>
(function () {{
  document.documentElement.dataset.sfMode = "dark";
  var isolated = false;
  function isolate() {{
    if (isolated) return;
    var specs = [{{"selector":"#stage","role":"background"}}];
    var hiddenSelectors = [\".sr\"];
    var introWordmark = {{
      sceneSelector: \"#comp .scene:first-child\",
      text: \"Nothing Goes Unnoticed.\",
      fontSize: 78,
      endTime: 1.7,
      holdTime: 0.5,
      logoSvg: `{THREEUI_MARK_SVG}`
    }};
    var roots = [];
    hiddenSelectors.forEach(function (selector) {{
      document.querySelectorAll(selector).forEach(function (element) {{
        element.setAttribute('data-threeui-hidden', '');
        element.setAttribute('aria-hidden', 'true');
        if ('inert' in element) element.inert = true;
      }});
    }});
    specs.forEach(function (spec) {{
      var element = document.querySelector(spec.selector);
      if (!element) return;
      element.setAttribute('data-threeui-role', spec.role);
      if (spec.fit) element.setAttribute('data-threeui-fit', spec.fit);
      if (spec.preserveTransform) element.setAttribute('data-threeui-preserve-transform', '');
      if (!roots.some(function (root) {{ return root.contains(element); }})) roots.push(element);
    }});
    if (introWordmark) {{
      var introScene = document.querySelector(introWordmark.sceneSelector);
      var introText = introScene && introScene.querySelector('.tx');
      var introMark = introText && introText.querySelector('.mark');
      if (introText && introMark) {{
        introMark.innerHTML = introWordmark.logoSvg;
      }}
      var introReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var introStartedAt = performance.now();
      var finished = false;
      function notifyDone() {{
        if (finished) return;
        finished = true;
        try {{
          if (window.parent && window.parent !== window) {{
            window.parent.postMessage({{ type: 'THREEUI_INTRO_DONE' }}, '*');
          }}
        }} catch(e) {{}}
      }}
      function renderIntroWordmark(now) {{
        if (typeof window.__seek !== 'function') {{
          requestAnimationFrame(renderIntroWordmark);
          return;
        }}
        if (introReducedMotion) {{
          window.__seek(introWordmark.endTime);
          setTimeout(notifyDone, 300);
          return;
        }}
        var elapsed = (now - introStartedAt) / 1000;
        if (elapsed >= introWordmark.endTime + introWordmark.holdTime) {{
          window.__seek(introWordmark.endTime);
          notifyDone();
          return;
        }}
        window.__seek(Math.min(elapsed, introWordmark.endTime));
        requestAnimationFrame(renderIntroWordmark);
      }}
      requestAnimationFrame(renderIntroWordmark);
    }}
    if (!roots.length) return;
    isolated = true;
    roots.forEach(function (root) {{
      document.body.appendChild(root);
    }});
    Array.from(document.body.children).forEach(function (element) {{
      if (roots.indexOf(element) !== -1) return;
      element.setAttribute('data-threeui-residual', '');
      element.setAttribute('aria-hidden', 'true');
      if ('inert' in element) element.inert = true;
    }});
    document.body.setAttribute('data-threeui-ready', '');
    requestAnimationFrame(function () {{ window.dispatchEvent(new Event('resize')); }});
  }}
  function scheduleIsolation() {{ setTimeout(isolate, 30); }}
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scheduleIsolation, {{ once: true }});
  else scheduleIsolation();
  window.addEventListener('load', isolate, {{ once: true }});
}})();
</script>"""

final_doc = html_mod.replace('</head>', f'{focus_style}\n</head>').replace('</body>', f'{focus_script}\n</body>')

target_path = '/Users/ayushmansharma/.gemini/antigravity/scratch/gods-eye/public/intro.html'
with open(target_path, 'w') as f:
    f.write(final_doc)

print('Generated public/intro.html successfully, size:', len(final_doc))
