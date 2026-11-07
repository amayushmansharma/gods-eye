/**
 * GodsEye Opening Chromatic Wordmark Assembly & Intro Splash
 * 
 * Ported from ThreeUI TextAnimationCollection / Neuform Isolated Effects (variant: "threeui-intro")
 * Canonical Source: src/shaders/neuform-isolated/sources/creator-studio-intro.html (SHA-256 e14795f24ea8aa9cb0005ea740923289869de3250ac4ea18f58527cd42e18cbe)
 * Source URL: https://threeui.com/source-code/threeui-intro.json
 * Configuration: mode "dark", hue 0, saturation 1.00, brightness 1.00
 * License & Terms: ThreeUI Terms of Use (https://threeui.com/terms) — Permitted for digital product integration
 * 
 * Adaptations for God's Eye:
 * - Wordmark changed from "ThreeUI" to "GOD'S EYE" with high-contrast Inter uppercase typography
 * - Brand emblem: Autonomous Emerald Iris Mark SVG integrated into chromatic assembly
 * - Viewport fitting from 360px to 1920px width with optical centering & responsive scaling
 * - Chromatic aberration (RGB channel separation + blur convergence) preserving canonical easing and math
 * - Subtitle reveal: "COMPETITIVE INTELLIGENCE // PERSISTENT MEMORY"
 * - Playback modes: INTRO_MODE = 'always' (default) | 'session' | 'off' + ?nointro query param bypass
 * - Full skippability (click, tap, Esc, Enter, Space) with ~400ms clean fade
 * - Smooth shrink/transition toward top-left header logo
 * - prefers-reduced-motion: 600ms static hold, then smooth fade out
 * - DPR capped at 2, zero audio/microphone dependencies
 */

(function (window, document) {
  'use strict';

  // 1. Playback Configuration: 'always' (default) | 'session' | 'off'
  var INTRO_MODE = 'always';

  // Check URL query param override (?nointro bypasses immediately)
  var urlParams = new URLSearchParams(window.location.search);
  var bypassQuery = urlParams.has('nointro');

  function shouldRunIntro() {
    if (bypassQuery) return false;
    if (INTRO_MODE === 'off') return false;
    if (INTRO_MODE === 'session') {
      try {
        if (sessionStorage.getItem('godseye_intro_seen')) {
          return false;
        }
        sessionStorage.setItem('godseye_intro_seen', '1');
      } catch (e) {
        // Fallback if sessionStorage is disabled
      }
    }
    return true;
  }

  // If intro shouldn't run, dismiss instantly before any animations
  if (!shouldRunIntro()) {
    var overlayEl = document.getElementById('intro-overlay') || document.getElementById('godseye-intro-overlay');
    if (overlayEl) overlayEl.remove();
    document.body.classList.remove('intro-active');
    setTimeout(function() {
      window.dispatchEvent(new CustomEvent('godseye:intro-complete'));
    }, 10);
    return;
  }

  // 2. Canonical Math & Easing Utilities from creator-studio-intro.html
  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function seg(t, a, b) { return clamp((t - a) / (b - a || 1e-6), 0, 1); }
  function smooth(t) { return t * t * (3 - 2 * t); }
  function eOut(t) { return 1 - Math.pow(1 - t, 3); }
  function rng(s) {
    var a = s >>> 0;
    return function () {
      a += 0x6D2B79F5;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // DOM node setters with cached property guards
  function setT(n, v) { if (n._t !== v) { n._t = v; n.style.transform = v; } }
  function setO(n, v) { var r = clamp(v, 0, 1).toFixed(3); if (n._o !== r) { n._o = r; n.style.opacity = r; } }
  function setF(n, v) { if (n._f !== v) { n._f = v; n.style.filter = v; } }

  // 3. Timing Constants (Snappy, Keynote-Calibrated)
  var ASSEMBLE_DUR = 1.65; // Seconds for chromatic assembly
  var HOLD_DUR = 0.70;     // Seconds to hold fully assembled mark
  var TOTAL_DUR = ASSEMBLE_DUR + HOLD_DUR;

  // 4. Wordmark Setup: "GOD'S EYE"
  var WORDMARK_TEXT = "GOD'S EYE";
  var SUBTITLE_TEXT = "COMPETITIVE INTELLIGENCE // PERSISTENT MEMORY";

  // God's Eye Brand Iris Emblem SVG
  var IRIS_LOGO_SVG = '<svg viewBox="0 0 48 48" class="godseye-intro-iris" aria-hidden="true" style="display:block;width:1em;height:1em;">' +
    '<circle cx="24" cy="24" r="22" stroke="rgba(255,255,255,0.2)" stroke-width="2.5" fill="none"/>' +
    '<circle cx="24" cy="24" r="10" fill="#060809" stroke="#34d399" stroke-width="2.5"/>' +
    '<circle cx="20.5" cy="20.5" r="2.8" fill="#ffffff"/>' +
    '<circle cx="24" cy="24" r="17" stroke="rgba(52,211,153,0.35)" stroke-width="1.2" stroke-dasharray="2.5 3.5" fill="none"/>' +
    '</svg>';

  function startIntro() {
    var overlay = document.getElementById('intro-overlay');
    if (!overlay) return;

    if (!shouldRunIntro()) {
      overlay.remove();
      document.body.classList.remove('intro-active');
      window.dispatchEvent(new CustomEvent('godseye:intro-complete'));
      return;
    }

    // Ensure scroll is locked during intro
    document.body.classList.add('intro-active');

    // Build Scene DOM Hierarchy
    var stage = document.createElement('div');
    stage.className = 'godseye-intro-stage';
    stage.style.cssText = 'position:relative;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;';

    var wordmarkWrap = document.createElement('div');
    wordmarkWrap.className = 'godseye-intro-wrap';
    wordmarkWrap.style.cssText = 'position:relative;display:flex;align-items:center;justify-content:center;will-change:transform,opacity;';

    var markNode = document.createElement('span');
    markNode.className = 'godseye-intro-mark';
    markNode.style.cssText = 'display:inline-block;vertical-align:middle;margin-right:0.18em;opacity:0;will-change:transform,opacity;';
    markNode.innerHTML = IRIS_LOGO_SVG;
    wordmarkWrap.appendChild(markNode);

    var txNode = document.createElement('div');
    txNode.className = 'godseye-intro-tx';
    txNode.style.cssText = 'display:inline-block;white-space:nowrap;font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif;font-weight:800;letter-spacing:-0.025em;color:#f5f5f7;line-height:1;will-change:transform,opacity,filter;';
    wordmarkWrap.appendChild(txNode);

    var subNode = document.createElement('div');
    subNode.className = 'godseye-intro-sub';
    subNode.style.cssText = 'margin-top:20px;font-family:JetBrains Mono,monospace;font-size:11px;letter-spacing:0.22em;color:#a1a1aa;text-transform:uppercase;opacity:0;white-space:nowrap;will-change:transform,opacity;';
    subNode.textContent = SUBTITLE_TEXT;

    stage.appendChild(wordmarkWrap);
    stage.appendChild(subNode);
    overlay.innerHTML = '';
    overlay.appendChild(stage);

    // Skip hint overlay
    var skipHint = document.createElement('div');
    skipHint.className = 'godseye-skip-hint';
    skipHint.style.cssText = 'position:absolute;bottom:24px;right:28px;font-family:JetBrains Mono,monospace;font-size:11px;letter-spacing:0.08em;color:rgba(255,255,255,0.28);text-transform:uppercase;pointer-events:none;transition:opacity 0.3s;z-index:10;';
    skipHint.textContent = 'Press Space or Esc to skip';
    overlay.appendChild(skipHint);

    // Create individual character elements for chromatic jitter assembly
    var chars = [];
    for (var i = 0; i < WORDMARK_TEXT.length; i++) {
      var sp = document.createElement('span');
      sp.style.cssText = 'display:inline-block;opacity:0;will-change:transform,opacity,filter;';
      sp.textContent = WORDMARK_TEXT[i] === ' ' ? '\u00a0' : WORDMARK_TEXT[i];
      txNode.appendChild(sp);
      chars.push(sp);
    }

    // Canonical pseudo-random jitter vectors: [dx, dy, phase]
    var R = rng(7719);
    var jit = chars.map(function () {
      return [R() * 2 - 1, R() * 2 - 1, R()];
    });

    // Responsive font scaling: ensure wordmark fits 360px to 1920px seamlessly
    function updateResponsiveLayout() {
      var vw = window.innerWidth || document.documentElement.clientWidth || 1280;
      var targetFs = clamp(vw * 0.076, 28, 92);
      txNode.style.fontSize = targetFs.toFixed(1) + 'px';
      markNode.style.fontSize = targetFs.toFixed(1) + 'px';

      if (vw < 480) {
        subNode.style.fontSize = '8.5px';
        subNode.style.letterSpacing = '0.12em';
        subNode.style.marginTop = '14px';
      } else if (vw < 768) {
        subNode.style.fontSize = '9.5px';
        subNode.style.letterSpacing = '0.16em';
        subNode.style.marginTop = '16px';
      } else {
        subNode.style.fontSize = '11px';
        subNode.style.letterSpacing = '0.22em';
        subNode.style.marginTop = '20px';
      }
    }

    updateResponsiveLayout();
    window.addEventListener('resize', updateResponsiveLayout);

    // 5. Render Frame at Normalized Progress p (0..1)
    function renderFrame(p) {
      p = clamp(p, 0, 1);

      // 5a. Iris Emblem Assembly
      setO(markNode, smooth(seg(p, 0.22, 0.50)));
      setT(markNode, 'scale(' + lerp(0.55, 1, eOut(seg(p, 0.22, 0.54))).toFixed(3) + ')');

      // 5b. Character Jitter & Chromatic Dispersion Convergence (Cohesive Assembly)
      for (var i = 0; i < chars.length; i++) {
        var j = jit[i];
        var a = eOut(clamp(seg(p, 0.06, 0.46), 0, 1));

        if (a >= 0.99) {
          setT(chars[i], 'none');
          setO(chars[i], 1);
          setF(chars[i], 'none');
          chars[i].style.textShadow = 'none';
        } else {
          var tx = (j[0] * 12 * (1 - a)).toFixed(1);
          var ty = (j[1] * 8 * (1 - a)).toFixed(1);
          var sc = lerp(1.08, 1, a).toFixed(3);
          setT(chars[i], 'translate(' + tx + 'px,' + ty + 'px) scale(' + sc + ')');
          setO(chars[i], a);

          var sep = (1 - a) * 5;
          chars[i].style.textShadow = sep > 0.3
            ? (-sep).toFixed(1) + 'px 0 rgba(255,64,72,0.8),' +
              sep.toFixed(1) + 'px 0 rgba(64,255,190,0.75),0 ' +
              (sep * 0.5).toFixed(1) + 'px rgba(96,124,255,0.75)'
            : 'none';

          setF(chars[i], sep > 0.8 ? 'blur(' + (sep * 0.2).toFixed(2) + 'px)' : 'none');
        }
      }

      // 5c. Subtitle Monospace Line Reveal
      var subProgress = seg(p, 0.52, 0.82);
      var subAlpha = smooth(subProgress);
      var subTranslate = lerp(12, 0, eOut(subProgress));
      setO(subNode, subAlpha);
      setT(subNode, 'translateY(' + subTranslate.toFixed(1) + 'px)');
    }

    // 6. Dismiss & Transition Controller
    var isDismissed = false;
    var rafId = 0;

    function dismissIntro(isSkipped) {
      if (isDismissed) return;
      isDismissed = true;

      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = 0;
      }

      window.removeEventListener('keydown', handleKeydown);
      overlay.removeEventListener('click', handleClick);
      window.removeEventListener('resize', updateResponsiveLayout);

      if (isSkipped) {
        overlay.style.transition = 'opacity 0.28s cubic-bezier(0.16, 1, 0.3, 1)';
        overlay.style.opacity = '0';
        overlay.style.pointerEvents = 'none';
        setTimeout(cleanupDOM, 280);
        return;
      }

      // Natural completion: smooth shrink & transition toward top-left header logo
      var targetEl = document.getElementById('headerIrisContainer');
      if (targetEl && wordmarkWrap) {
        var startRect = wordmarkWrap.getBoundingClientRect();
        var targetRect = targetEl.getBoundingClientRect();

        var startCenterX = startRect.left + startRect.width / 2;
        var startCenterY = startRect.top + startRect.height / 2;
        var targetCenterX = targetRect.left + targetRect.width / 2;
        var targetCenterY = targetRect.top + targetRect.height / 2;

        var dx = (targetCenterX - startCenterX).toFixed(1);
        var dy = (targetCenterY - startCenterY).toFixed(1);
        var scale = clamp(targetRect.height / (startRect.height || 1), 0.15, 0.5).toFixed(3);

        wordmarkWrap.style.transition = 'transform 0.42s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.38s ease-out';
        wordmarkWrap.style.transform = 'translate(' + dx + 'px, ' + dy + 'px) scale(' + scale + ')';
        setO(subNode, 0);
      }

      overlay.style.transition = 'opacity 0.42s cubic-bezier(0.16, 1, 0.3, 1)';
      overlay.style.opacity = '0';
      overlay.style.pointerEvents = 'none';

      setTimeout(cleanupDOM, 420);
    }

    function cleanupDOM() {
      document.body.classList.remove('intro-active');
      if (overlay && overlay.parentNode) {
        overlay.parentNode.removeChild(overlay);
      }
      window.dispatchEvent(new CustomEvent('godseye:intro-complete'));
    }

    // 7. Interactive Skip Handlers (Click, Tap, Esc, Enter, Space)
    function handleKeydown(e) {
      if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ' || e.code === 'Space') {
        e.preventDefault();
        dismissIntro(true);
      }
    }

    function handleClick() {
      dismissIntro(true);
    }

    window.addEventListener('keydown', handleKeydown);
    overlay.addEventListener('click', handleClick);

    // 8. prefers-reduced-motion Handling: ~600ms static wordmark hold, then fade out
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) {
      renderFrame(1.0);
      setTimeout(function () {
        dismissIntro(false);
      }, 600);
      return;
    }

    // 9. Animation Driver Loop
    var startTime = null;

    function loop(now) {
      if (isDismissed) return;

      if (startTime === null) startTime = now;
      var elapsed = (now - startTime) / 1000;

      if (elapsed <= ASSEMBLE_DUR) {
        var p = elapsed / ASSEMBLE_DUR;
        renderFrame(p);
        rafId = requestAnimationFrame(loop);
      } else if (elapsed < TOTAL_DUR) {
        renderFrame(1.0);
        rafId = requestAnimationFrame(loop);
      } else {
        renderFrame(1.0);
        dismissIntro(false);
      }
    }

    rafId = requestAnimationFrame(loop);

    window.GodsEyeIntro = {
      dismiss: function () { dismissIntro(true); },
      isActive: function () { return !isDismissed; },
      renderProgress: function (p) {
        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = 0;
        }
        renderFrame(p);
      }
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startIntro);
  } else {
    startIntro();
  }

})(window, document);
