/**
 * GodsEye Iris Mark — Autonomous Logo & Scanner Visualizer
 * 
 * Ported from ThreeUI TextAnimationCollection / Neuform Isolated Effects (variant: "audio-wordmark")
 * Canonical Source: src/shaders/neuform-isolated/sources/audio-wordmark.html (SHA-256 26f0d8d0449483ce146183c7fbeed26e93f9aaa90bccf327c0140f679da23480)
 * Source URL: https://threeui.com/source-code/audio-wordmark.json
 * Configuration: mode "dark", hue -14, saturation 1.00, brightness 1.14
 * License & Terms: ThreeUI Terms of Use (https://threeui.com/terms) — Permitted for personal and commercial integration
 * 
 * Adaptations for God's Eye:
 * - Wordmark DOM and ThreeUI icons omitted; pure Canvas 2D radial iris mark
 * - Preserves canonical bar-field trigonometric wave math, easing curves, and devicePixelRatio scaling
 * - Audio API replaced with simulated procedural waveforms (zero microphone permissions)
 * - Tuned for high-legibility ~36-40px header mark (28 radial bars around center pupil)
 * - Multi-state machine: 'idle' (30fps breathing), 'scanning' (high-amplitude wave), 'done' (settling pulse), 'hover'
 */

(function (window) {
  'use strict';

  // Canonical Easing & Math Utilities from audio-wordmark.html
  function sat(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function easeOut(t) { t = sat(t); return 1 - Math.pow(1 - t, 3); }
  function easeInOut(t) { t = sat(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }

  class IrisMark {
    constructor(canvas, options = {}) {
      if (!canvas) return;
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.size = options.size || 38;
      this.barCount = options.barCount || 28;
      this.isLarge = Boolean(options.isLarge);

      // State Management
      this.state = 'idle'; // 'idle' | 'scanning' | 'done'
      this.progress = 0; // 0..1
      this.hover = false;
      this.hoverFactor = 0;
      this.doneStart = null;
      this.doneDuration = 1400; // ms

      // Time tracking
      this.t = 0;
      this.lastTime = performance.now();
      this.lastFrameTime = 0;
      this.running = false;
      this.isVisible = true;

      // Color Palette: Canonical Dark Mode with Emerald Accent
      // Original config: mode "dark", hue -14, saturation 1.00, brightness 1.14
      // Near-white base (#E8EEE9) with faint emerald (#34d399) matching the Hindsight indicator
      this.colorBase = options.colorBase || '#E8EEE9';
      this.colorAccent = options.colorAccent || '#34d399';
      this.pupilColor = options.pupilColor || '#060809';

      // Setup DOM & Dimensions
      this.canvas.setAttribute('aria-hidden', 'true');
      this.setupDpr();
      this.setupObservers();
      this.setupHover();

      // Check prefers-reduced-motion
      this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (this.reducedMotion) {
        this.renderFrame(0);
        return;
      }

      this.start();
    }

    setupDpr() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      this.dpr = dpr;
      this.canvas.width = Math.round(this.size * dpr);
      this.canvas.height = Math.round(this.size * dpr);
      this.canvas.style.width = `${this.size}px`;
      this.canvas.style.height = `${this.size}px`;
      this.ctx.setTransform(1, 0, 0, 1, 0, 0);
      this.ctx.scale(dpr, dpr);
    }

    setupObservers() {
      // Pause loop when off-screen
      if ('IntersectionObserver' in window) {
        this.observer = new IntersectionObserver((entries) => {
          this.isVisible = entries[0].isIntersecting;
          if (this.isVisible && !this.running && !this.reducedMotion) {
            this.lastTime = performance.now();
            this.start();
          }
        }, { threshold: 0.05 });
        this.observer.observe(this.canvas);
      }

      // Pause loop when tab is backgrounded
      document.addEventListener('visibilitychange', () => {
        if (!document.hidden && this.isVisible && !this.running && !this.reducedMotion) {
          this.lastTime = performance.now();
          this.start();
        }
      });

      // Handle screen resize/DPR change
      window.addEventListener('resize', () => {
        this.setupDpr();
        if (this.reducedMotion) this.renderFrame(this.t);
      });
    }

    setupHover() {
      const target = this.canvas.closest('.cursor-pointer') || this.canvas.parentElement || this.canvas;
      target.addEventListener('mouseenter', () => { this.hover = true; });
      target.addEventListener('mouseleave', () => { this.hover = false; });
    }

    setState(newState) {
      if (this.state === newState) return;
      if (newState === 'done') {
        this.doneStart = performance.now();
      }
      this.state = newState;
      if (!this.running && !this.reducedMotion) {
        this.lastTime = performance.now();
        this.start();
      }
    }

    setProgress(p) {
      this.progress = sat(p);
    }

    start() {
      if (this.running || this.reducedMotion) return;
      this.running = true;
      const loop = (now) => {
        if (!this.running) return;

        // Stop animating if tab is hidden or element is off-screen
        if (document.hidden || !this.isVisible) {
          this.running = false;
          return;
        }

        const delta = Math.min((now - this.lastTime) / 1000, 0.1);
        this.lastTime = now;

        // Throttling for 'idle' state to ~30fps for CPU efficiency
        if (this.state === 'idle') {
          if (now - this.lastFrameTime < 32) {
            requestAnimationFrame(loop);
            return;
          }
        }
        this.lastFrameTime = now;

        this.update(delta);
        this.renderFrame(this.t);

        requestAnimationFrame(loop);
      };
      requestAnimationFrame(loop);
    }

    stop() {
      this.running = false;
    }

    update(dt) {
      // Smooth hover interpolation
      const targetHover = this.hover ? 1 : 0;
      this.hoverFactor = lerp(this.hoverFactor, targetHover, sat(dt * 8));

      // Handle 'done' settling state
      if (this.state === 'done') {
        const elapsed = performance.now() - this.doneStart;
        if (elapsed > this.doneDuration) {
          this.state = 'idle';
          this.doneStart = null;
        }
      }

      // Simulation Speed modulation based on state
      let speed = 1.6; // Base idle
      if (this.state === 'scanning') {
        speed = 3.6;
      } else if (this.state === 'done') {
        speed = 2.4;
      }
      this.t += dt * speed;
    }

    renderFrame(t) {
      const ctx = this.ctx;
      const size = this.size;
      const cx = size / 2;
      const cy = size / 2;

      ctx.clearRect(0, 0, size, size);

      // Geometry calculation tuned for high-legibility ~36-40px iris
      const rPupil = this.isLarge ? size * 0.15 : size * 0.16;   // Center pupil
      const rInner = this.isLarge ? size * 0.22 : size * 0.25;   // Inner bar baseline
      const rOuterMax = size * 0.48;                             // Outer bar boundary
      const span = rOuterMax - rInner;
      const n = this.barCount;

      // Amplitude & Wave modulation based on state
      let baseAmp = 0.52;
      let speedA = 6.4;
      let freqA = 0.62;
      let speedB = 2.4;
      let freqB = 0.17;

      if (this.state === 'scanning') {
        baseAmp = 1.15;
        speedA = 8.2;
        speedB = 3.8;
      } else if (this.state === 'done') {
        const doneProgress = sat((performance.now() - (this.doneStart || 0)) / this.doneDuration);
        const pulseDecay = easeOut(1 - doneProgress);
        baseAmp = lerp(0.52, 1.45, pulseDecay);
      }

      // Apply hover boost (~25%)
      const amp = baseAmp * (1 + 0.25 * this.hoverFactor);

      // Bar thickness: crisp and clean
      const barThickness = this.isLarge ? Math.max(3.2, size * 0.018) : Math.max(1.75, size * 0.046);

      // 1. Draw Ring of Radial Bars
      for (let i = 0; i < n; i++) {
        const theta = (i / n) * Math.PI * 2;

        // Canonical wave field math from audio-wordmark.html
        // var pulse = 0.78 + 0.22*Math.sin(t*6.4 + i*0.62)*Math.sin(t*2.4 + i*0.17);
        const wave = Math.sin(t * speedA + i * freqA) * Math.sin(t * speedB + i * freqB);
        let pulse = 0.78 + 0.22 * wave;

        // Scanning wave sweep enhancement
        if (this.state === 'scanning') {
          const sweep = Math.sin(theta - this.t * 3.2 + this.progress * Math.PI * 2);
          pulse = pulse * (0.82 + 0.28 * sweep);
        }

        const minLen = this.isLarge ? size * 0.04 : size * 0.06;
        const barLen = Math.max(minLen, span * (0.28 + 0.72 * pulse * amp));
        const rBarOuter = rInner + Math.min(barLen, span);

        // Color interpolation: near-white with faint emerald accent (#34d399)
        const isPeak = pulse > 0.86 || (this.state === 'scanning' && (i % 3 === 0));
        let barColor = this.colorBase;
        if (this.state === 'scanning') {
          barColor = isPeak ? this.colorAccent : 'rgba(232, 238, 233, 0.88)';
        } else if (this.state === 'done') {
          barColor = this.colorAccent;
        } else if (isPeak) {
          barColor = 'rgba(52, 211, 153, 0.9)';
        }

        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(theta);

        ctx.beginPath();
        ctx.lineCap = 'round';
        ctx.lineWidth = barThickness;
        ctx.strokeStyle = barColor;

        ctx.moveTo(rInner, 0);
        ctx.lineTo(rBarOuter, 0);
        ctx.stroke();

        ctx.restore();
      }

      // 2. Draw Center Pupil with Emerald Rim & Specular Glint
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, rPupil, 0, Math.PI * 2);
      ctx.fillStyle = this.pupilColor;
      ctx.fill();

      // Pupil Rim (Emerald Accent)
      ctx.lineWidth = this.isLarge ? 2.2 : 1.2;
      ctx.strokeStyle = (this.state === 'scanning' || this.state === 'done')
        ? 'rgba(52, 211, 153, 0.95)' 
        : 'rgba(52, 211, 153, 0.45)';
      ctx.stroke();

      // Specular Glint
      const glintDist = rPupil * 0.35;
      const glintSize = Math.max(0.9, rPupil * 0.24);
      ctx.beginPath();
      ctx.arc(cx - glintDist, cy - glintDist, glintSize, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fill();

      ctx.restore();
    }
  }

  // Global Singleton & Factory Controller
  let headerMarkInstance = null;
  let scannerMarkInstance = null;

  function initHeaderMark() {
    const canvas = document.getElementById('irisMarkCanvas');
    if (!canvas) return;
    headerMarkInstance = new IrisMark(canvas, { size: 38, barCount: 26 });
  }

  function initScannerMark() {
    // Optional large scanner mark behind clear flag
    const isEnabled = window.GODS_EYE_ENABLE_SCANNER_IRIS !== false;
    const canvas = document.getElementById('scannerIrisCanvas');
    if (!canvas || !isEnabled) return;
    const size = parseInt(canvas.getAttribute('width'), 10) || 200;
    scannerMarkInstance = new IrisMark(canvas, { size: size, barCount: 36, isLarge: true });
  }

  window.GodsEyeMark = {
    setState: function (state) {
      if (headerMarkInstance) headerMarkInstance.setState(state);
      if (scannerMarkInstance) scannerMarkInstance.setState(state);
    },
    setProgress: function (progress) {
      if (headerMarkInstance) headerMarkInstance.setProgress(progress);
      if (scannerMarkInstance) scannerMarkInstance.setProgress(progress);
    },
    getState: function () {
      return headerMarkInstance ? headerMarkInstance.state : 'idle';
    },
    getHeaderMark: function () {
      return headerMarkInstance;
    },
    getScannerMark: function () {
      return scannerMarkInstance;
    },
    createInstance: function (canvas, options) {
      return new IrisMark(canvas, options);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initHeaderMark();
      initScannerMark();
    });
  } else {
    initHeaderMark();
    initScannerMark();
  }

})(window);
