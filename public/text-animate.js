/**
 * God's Eye — TextAnimate Helper
 * 
 * Conceptual port of Magic UI's TextAnimate component
 * Reference & Docs: https://magicui.design/docs/components/text-animate
 * License: MIT License (c) 2024 Dillion Verma (https://github.com/magicuidesign/magicui)
 *
 * Lightweight vanilla JS text-reveal helper using CSS keyframes and IntersectionObserver.
 * Splits text nodes while preserving existing DOM markup, whitespace, nested elements,
 * full screen-reader accessibility, and prefers-reduced-motion.
 */

(() => {
  'use strict';

  // 1. Inject Keyframe Styles
  const STYLE_ID = 'text-animate-styles';
  if (!document.getElementById(STYLE_ID)) {
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      @keyframes ta-blurInUp {
        0% { opacity: 0; filter: blur(10px); transform: translateY(20px); }
        100% { opacity: 1; filter: blur(0px); transform: translateY(0); }
      }
      @keyframes ta-blurIn {
        0% { opacity: 0; filter: blur(10px); }
        100% { opacity: 1; filter: blur(0px); }
      }
      @keyframes ta-fadeIn {
        0% { opacity: 0; }
        100% { opacity: 1; }
      }
      @keyframes ta-slideUp {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
      }
      @keyframes ta-scaleUp {
        0% { opacity: 0; transform: scale(0.8); }
        100% { opacity: 1; transform: scale(1); }
      }

      .text-animate-segment {
        display: inline-block;
        vertical-align: baseline;
      }

      .text-animating .text-animate-segment {
        opacity: 0;
      }

      .text-animate-instant .text-animate-segment,
      .text-animate-reduced .text-animate-segment,
      .text-animate-complete .text-animate-segment {
        opacity: 1 !important;
        filter: none !important;
        transform: none !important;
        animation: none !important;
      }

      @media (prefers-reduced-motion: reduce) {
        .text-animate-segment {
          opacity: 1 !important;
          filter: none !important;
          transform: none !important;
          animation: none !important;
        }
      }
    `;
    document.head.appendChild(style);
  }

  // Animation variants map
  const VARIANTS = {
    blurInUp: 'ta-blurInUp',
    blurIn: 'ta-blurIn',
    fadeIn: 'ta-fadeIn',
    slideUp: 'ta-slideUp',
    scaleUp: 'ta-scaleUp'
  };

  const prefersReduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function parseTime(val, defaultSec = 0) {
    if (!val) return defaultSec;
    val = String(val).trim();
    if (val.endsWith('ms')) return parseFloat(val) / 1000;
    if (val.endsWith('s')) return parseFloat(val);
    const n = parseFloat(val);
    return isNaN(n) ? defaultSec : n;
  }

  // Recursively collect text nodes, preserving DOM structure and skipping ignored tags
  function collectTextNodes(node, list = []) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (node.textContent.trim().length > 0) {
        list.push(node);
      }
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.classList?.contains('sr-only') || node.tagName === 'SCRIPT' || node.tagName === 'STYLE') {
        return list;
      }
      for (const child of Array.from(node.childNodes)) {
        collectTextNodes(child, list);
      }
    }
    return list;
  }

  // Split text nodes into segments based on data-by (word | character | line)
  function prepareElement(el) {
    if (el.hasAttribute('data-text-animated')) {
      return el._taSegments || [];
    }
    el.setAttribute('data-text-animated', 'true');

    // Accessibility: store complete text in aria-label so screen readers read smoothly
    if (!el.getAttribute('aria-label')) {
      const fullText = el.textContent.trim().replace(/\s+/g, ' ');
      el.setAttribute('aria-label', fullText);
    }

    if (prefersReduced()) {
      el.classList.add('text-animate-reduced');
      return [];
    }

    const by = el.getAttribute('data-by') || 'word';
    const textNodes = collectTextNodes(el);
    const segments = [];

    textNodes.forEach(tn => {
      const text = tn.textContent;
      const parentEl = tn.parentElement;
      const extraDelay = parseTime(parentEl?.getAttribute('data-delay'), 0);

      const matchLeading = text.match(/^\s+/);
      const matchTrailing = text.match(/\s+$/);
      const leading = matchLeading ? matchLeading[0] : '';
      const trailing = matchTrailing ? matchTrailing[0] : '';
      const trimmed = text.trim();

      const frag = document.createDocumentFragment();
      if (leading) frag.appendChild(document.createTextNode(leading));

      let units = [];
      if (by === 'character') {
        units = trimmed.split('');
      } else if (by === 'line') {
        units = [trimmed];
      } else {
        // default: word
        units = trimmed.split(/\s+/);
      }

      units.forEach((unit, idx) => {
        const span = document.createElement('span');
        span.className = 'text-animate-segment';
        span.setAttribute('aria-hidden', 'true');
        span.textContent = unit;
        span._extraDelay = extraDelay;
        segments.push(span);
        frag.appendChild(span);

        if (idx < units.length - 1) {
          frag.appendChild(document.createTextNode(' '));
        }
      });

      if (trailing) frag.appendChild(document.createTextNode(trailing));
      tn.parentNode.replaceChild(frag, tn);
    });

    el._taSegments = segments;
    return segments;
  }

  function playAnimation(el, segments) {
    if (!segments || segments.length === 0) return;
    if (prefersReduced()) {
      el.classList.add('text-animate-complete');
      return;
    }

    el.classList.add('text-animating');

    let animateType = el.getAttribute('data-animate') || 'blurInUp';
    if (!VARIANTS[animateType]) animateType = 'blurInUp';

    // Segment count threshold (> 40 segments): fallback to plain fadeIn
    if (segments.length > 40 && animateType !== 'fadeIn') {
      animateType = 'fadeIn';
    }

    const animKeyframe = VARIANTS[animateType];
    const baseDelay = parseTime(el.getAttribute('data-delay'), 0);
    const totalDurationAttr = el.getAttribute('data-duration');
    const by = el.getAttribute('data-by') || 'word';

    const segDuration = 0.35; // ~0.35s per segment
    let staggerStep = (by === 'character') ? 0.02 : 0.05;

    if (totalDurationAttr) {
      const totalDur = parseTime(totalDurationAttr, 0.6);
      staggerStep = segments.length > 1 ? Math.max(0.01, (totalDur - segDuration) / (segments.length - 1)) : 0;
    }

    const totalExpectedMs = (baseDelay + segDuration + (segments.length * staggerStep) + 0.15) * 1000;

    let completedCount = 0;
    const finalize = () => {
      el.classList.remove('text-animating');
      el.classList.add('text-animate-complete');
      segments.forEach(seg => {
        seg.style.willChange = 'auto';
        seg.style.filter = '';
        seg.style.transform = '';
        seg.style.opacity = '1';
        seg.style.animation = 'none';
      });
    };

    segments.forEach((seg, idx) => {
      const segDelay = baseDelay + (seg._extraDelay || 0) + (idx * staggerStep);

      // Apply will-change only during active animation
      seg.style.willChange = 'transform, opacity, filter';
      seg.style.animation = `${animKeyframe} ${segDuration}s cubic-bezier(0.16, 1, 0.3, 1) ${segDelay.toFixed(3)}s forwards`;

      const onEnd = () => {
        seg.removeEventListener('animationend', onEnd);
        seg.style.willChange = 'auto';
        seg.style.filter = '';
        seg.style.transform = '';
        seg.style.opacity = '1';
        completedCount++;
        if (completedCount >= segments.length) {
          finalize();
        }
      };
      seg.addEventListener('animationend', onEnd);
    });

    // Hard safety timer: absolutely guarantees text is 100% visible and unblurred
    setTimeout(finalize, Math.max(700, totalExpectedMs));
  }

  // IntersectionObserver for view-triggered elements
  let observer = null;
  function getObserver() {
    if (!observer) {
      observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const el = entry.target;
            const once = el.getAttribute('data-once') !== 'false';
            if (once) observer.unobserve(el);

            triggerElement(el);
          }
        });
      }, { rootMargin: '0px 0px -40px 0px', threshold: 0.1 });
    }
    return observer;
  }

  function isIntroRunning() {
    return document.body.classList.contains('intro-active') ||
           (window.GodsEyeIntro && typeof window.GodsEyeIntro.isActive === 'function' && window.GodsEyeIntro.isActive()) ||
           !!document.getElementById('godseye-intro-overlay');
  }

  function triggerElement(el) {
    const isHero = el.hasAttribute('data-hero') || el.id === 'heroTitle' || el.closest('.hero-section');
    if (isHero && isIntroRunning()) {
      let triggered = false;
      const execute = () => {
        if (triggered) return;
        triggered = true;
        window.removeEventListener('godseye:intro-complete', execute);
        const segs = el._taSegments || prepareElement(el);
        playAnimation(el, segs);
      };
      window.addEventListener('godseye:intro-complete', execute);
      setTimeout(execute, 2200); // safety fallback
      return;
    }

    const segs = el._taSegments || prepareElement(el);
    playAnimation(el, segs);
  }

  // Public API
  const TextAnimate = {
    scan(root = document) {
      if (!root) return;
      const elements = root.querySelectorAll ? root.querySelectorAll('[data-animate]') : [];
      const obs = getObserver();

      Array.from(elements).forEach(el => {
        if (el.hasAttribute('data-text-animated')) return;

        // Prepare segments in advance to prevent any FOUC or layout shift
        const segs = prepareElement(el);
        el._taSegments = segs;
        obs.observe(el);
      });
    },

    animate(el) {
      if (!el) return;
      const segs = el._taSegments || prepareElement(el);
      playAnimation(el, segs);
    }
  };

  window.TextAnimate = TextAnimate;

  // Auto-scan on page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => TextAnimate.scan());
  } else {
    TextAnimate.scan();
  }
})();
