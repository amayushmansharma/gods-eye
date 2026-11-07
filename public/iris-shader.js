/**
 * GodsEye Ink-Drawn Iris WebGL Shader Engine
 * 
 * Procedural biological iris generator reproducing the ink-drawn visual target:
 * - Pure black pupil with finely haired edge (32% of iris diameter)
 * - Bright, multi-harmonic jagged collarette ring just outside the pupil
 * - Dark irregular leaf-like crypt voids in the mid band with fibrous rims
 * - Dense, ultra-thin, slightly wavy radial fibers
 * - Darker limbal edge with granular ink dot stippling
 * 
 * Final Tuned Parameters (Hardcoded):
 * - fiberFreq: 520.0
 * - cryptThresh: 0.38
 * - collaretteR: 0.46
 * - pupilSize: 0.32
 * - stippleDensity: 0.82
 * - fiberThinness: 7.2
 * - collaretteBright: 1.9
 * - limbusWidth: 0.16
 */

(function (window, document) {
  'use strict';

  // Final Tuned & Hardcoded Parameters
  var FINAL_TUNED_PARAMS = {
    fiberFreq: 520.0,
    cryptThresh: 0.38,
    collaretteR: 0.46,
    pupilSize: 0.32,
    stippleDensity: 0.82,
    fiberThinness: 7.2,
    collaretteBright: 1.9,
    limbusWidth: 0.16
  };

  // Vertex Shader
  var VS_SOURCE = [
    'attribute vec2 a_position;',
    'varying vec2 v_uv;',
    'void main() {',
    '  v_uv = a_position * 0.5 + 0.5;',
    '  gl_Position = vec4(a_position, 0.0, 1.0);',
    '}'
  ].join('\n');

  // Fragment Shader (Final Converged Ink-Drawn Iris Formulation)
  var FS_SOURCE = [
    'precision highp float;',
    'varying vec2 v_uv;',
    'uniform vec2 u_resolution;',
    'uniform float u_time;',
    'uniform float u_fiber_freq;',
    'uniform float u_crypt_thresh;',
    'uniform float u_collarette_r;',
    'uniform float u_pupil_size;',
    'uniform float u_stipple_density;',
    'uniform float u_fiber_thinness;',
    'uniform float u_collarette_bright;',
    'uniform float u_limbus_width;',

    '#define PI 3.14159265359',

    'float hash21(vec2 p) {',
    '  p = fract(p * vec2(345.34, 678.89));',
    '  p += dot(p, p + 45.32);',
    '  return fract(p.x * p.y);',
    '}',

    'vec2 hash22(vec2 p) {',
    '  float n = sin(dot(p, vec2(127.1, 311.7)));',
    '  return fract(vec2(262144.0, 32768.0) * n);',
    '}',

    'float vnoise(vec2 p) {',
    '  vec2 i = floor(p);',
    '  vec2 f = fract(p);',
    '  vec2 u = f * f * (3.0 - 2.0 * f);',
    '  return mix(mix(hash21(i + vec2(0.0, 0.0)), hash21(i + vec2(1.0, 0.0)), u.x),',
    '             mix(hash21(i + vec2(0.0, 1.0)), hash21(i + vec2(1.0, 1.0)), u.x), u.y);',
    '}',

    'float fbm(vec2 p) {',
    '  float v = 0.0;',
    '  float a = 0.5;',
    '  mat2 rot = mat2(cos(0.52), sin(0.52), -sin(0.52), cos(0.52));',
    '  for (int i = 0; i < 4; i++) {',
    '    v += a * vnoise(p);',
    '    p = rot * p * 2.05 + vec2(100.0);',
    '    a *= 0.5;',
    '  }',
    '  return v;',
    '}',

    'float voronoiCrypts(vec2 p) {',
    '  vec2 n = floor(p);',
    '  vec2 f = fract(p);',
    '  float md = 8.0;',
    '  for (int j = -1; j <= 1; j++) {',
    '    for (int i = -1; i <= 1; i++) {',
    '      vec2 g = vec2(float(i), float(j));',
    '      vec2 o = hash22(n + g);',
    '      vec2 delta = g + o - f;',
    '      delta.x *= 2.4;',
    '      float d = dot(delta, delta);',
    '      if (d < md) md = d;',
    '    }',
    '  }',
    '  return sqrt(md);',
    '}',

    'float calculateStipple(vec2 p, float r, float density, float width) {',
    '  float band = smoothstep(1.0 - width, 1.0, r);',
    '  if (band <= 0.001) return 0.0;',

    '  vec2 g1 = p * 320.0;',
    '  vec2 cell1 = floor(g1);',
    '  vec2 frac1 = fract(g1) - 0.5;',
    '  float h1 = hash21(cell1);',
    '  float d1 = length(frac1);',
    '  float dot1 = smoothstep(0.38, 0.12, d1) * step(1.0 - density * band * 0.95, h1);',

    '  vec2 g2 = p * 190.0 + vec2(12.3, 45.6);',
    '  vec2 cell2 = floor(g2);',
    '  vec2 frac2 = fract(g2) - 0.5;',
    '  float h2 = hash21(cell2);',
    '  float d2 = length(frac2);',
    '  float dot2 = smoothstep(0.42, 0.15, d2) * step(1.0 - density * band * 0.75, h2);',

    '  vec2 g3 = p * 480.0;',
    '  float h3 = hash21(floor(g3));',
    '  float dot3 = step(1.0 - density * band * 0.65, h3) * 0.5;',

    '  return clamp(dot1 * 0.65 + dot2 * 0.45 + dot3 * 0.35, 0.0, 1.0);',
    '}',

    'void main() {',
    '  vec2 p = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / (0.5 * min(u_resolution.x, u_resolution.y));',
    '  float r = length(p);',
    '  float theta = atan(p.y, p.x);',
    '  float phi = (theta + PI) / (2.0 * PI);',

    '  if (r > 1.002) {',
    '    gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);',
    '    return;',
    '  }',

    '  // 1. Pupil & Finely Haired Edge',
    '  float h1 = sin(theta * 360.0) * 0.5 + 0.5;',
    '  float h2 = sin(theta * 780.0 + sin(theta * 80.0) * 1.8) * 0.5 + 0.5;',
    '  float h3 = hash21(vec2(floor(phi * 520.0), 7.0));',
    '  float hairNoise = h1 * 0.45 + h2 * 0.35 + h3 * 0.20;',
    '  float hairLen = 0.023 * hairNoise;',
    '  float pupilRad = u_pupil_size + hairLen;',

    '  if (r < u_pupil_size - 0.007) {',
    '    gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);',
    '    return;',
    '  }',

    '  float pupilMask = smoothstep(pupilRad - 0.004, pupilRad + 0.006, r);',
    '  if (pupilMask <= 0.001) {',
    '    gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);',
    '    return;',
    '  }',

    '  float innerFringe = smoothstep(u_pupil_size + 0.052, u_pupil_size, r);',
    '  float hairSpikes = pow(h2, 2.6) * innerFringe * 0.88;',

    '  // 2. Collarette (Brilliant Jagged Multi-Harmonic Arches)',
    '  float colJag1 = 0.025 * sin(theta * 14.0 + sin(theta * 28.0) * 0.85);',
    '  float colJag2 = 0.015 * sin(theta * 34.0 + 1.6);',
    '  float colJag3 = 0.007 * sin(theta * 68.0 - 0.7);',
    '  float colCenter = u_collarette_r + colJag1 + colJag2 + colJag3;',

    '  float colDist = abs(r - colCenter);',
    '  float colIntensity = exp(-colDist * colDist / (2.0 * 0.024 * 0.024)) * u_collarette_bright;',

    '  float colTendril = smoothstep(u_collarette_r - 0.04, u_collarette_r + 0.10, r) * ',
    '                     smoothstep(u_collarette_r + 0.22, u_collarette_r + 0.08, r);',
    '  colIntensity += colTendril * pow(sin(theta * 48.0) * 0.5 + 0.5, 2.8) * 0.85;',

    '  // 3. Leaf-Like Crypt Voids in Mid Band',
    '  vec2 cCoord = vec2(r * 4.4, phi * 26.0);',
    '  vec2 warp = vec2(fbm(cCoord * 1.5), fbm(cCoord * 1.9 + 5.8));',
    '  cCoord += (warp - 0.5) * 0.55;',

    '  float vDist = voronoiCrypts(cCoord);',
    '  float midBand = smoothstep(u_collarette_r + 0.02, u_collarette_r + 0.13, r) * smoothstep(0.90, 0.66, r);',

    '  float cryptCutoff = u_crypt_thresh * (0.86 + 0.28 * fbm(vec2(phi * 19.0, r * 9.0)));',
    '  float cryptHole = smoothstep(cryptCutoff - 0.075, cryptCutoff + 0.075, vDist);',
    '  float cryptMask = mix(1.0, cryptHole, midBand);',

    '  float rimDist = abs(vDist - cryptCutoff);',
    '  float cryptRim = smoothstep(0.065, 0.0, rimDist) * midBand * 1.6;',

    '  // 4. Dense, Thin, Wavy Radial Fibers',
    '  float flowDeflect = (1.0 - cryptHole) * midBand * (warp.x - 0.5) * 0.09;',
    '  float wave = 0.042 * sin(r * 34.0 + sin(theta * 10.0) * 2.0) + (warp.y - 0.5) * 0.035 + flowDeflect;',
    '  float fAngle = theta + wave;',

    '  float f1 = sin(fAngle * u_fiber_freq);',
    '  float f2 = sin(fAngle * (u_fiber_freq * 1.86) + 2.4);',
    '  float f3 = sin(fAngle * (u_fiber_freq * 0.42) - 1.6);',
    '  float f4 = sin(fAngle * (u_fiber_freq * 2.85) + 0.9);',

    '  float line1 = pow(clamp(f1 * 0.5 + 0.5, 0.0, 1.0), u_fiber_thinness);',
    '  float line2 = pow(clamp(f2 * 0.5 + 0.5, 0.0, 1.0), u_fiber_thinness * 0.92);',
    '  float line3 = pow(clamp(f3 * 0.5 + 0.5, 0.0, 1.0), 2.2);',
    '  float line4 = pow(clamp(f4 * 0.5 + 0.5, 0.0, 1.0), u_fiber_thinness * 1.15);',

    '  float fiberStroma = line1 * 0.65 + line2 * 0.38 + line3 * 0.45 + line4 * 0.28;',

    '  float innerBand = smoothstep(u_collarette_r + 0.03, u_pupil_size + 0.01, r);',
    '  float innerFibers = pow(clamp(sin(theta * (u_fiber_freq * 1.48)) * 0.5 + 0.5, 0.0, 1.0), u_fiber_thinness * 0.78) * innerBand * 1.35;',

    '  // 5. Multi-Scale Granular Limbal Stipple',
    '  float stippleVal = calculateStipple(p, r, u_stipple_density, u_limbus_width);',
    '  float limbusDark = smoothstep(1.0 - u_limbus_width * 1.25, 1.0, r);',

    '  float tone = (fiberStroma * 1.15 + innerFibers * 0.9) * cryptMask;',
    '  tone += colIntensity * 0.95;',
    '  tone += cryptRim * 0.90;',

    '  tone = pow(clamp(tone, 0.0, 1.0), 0.82);',

    '  tone *= (1.0 - limbusDark * 0.84);',
    '  tone = mix(tone, 0.0, stippleVal * 0.88);',

    '  tone = tone * pupilMask - hairSpikes;',
    '  tone = clamp(tone, 0.0, 1.0);',

    '  float edgeAA = smoothstep(1.0, 0.994, r);',
    '  float finalInk = mix(1.0, tone, edgeAA);',

    '  gl_FragColor = vec4(vec3(finalInk), 1.0);',
    '}'
  ].join('\n');

  class IrisWebGLRenderer {
    constructor(canvas, customFs) {
      this.canvas = canvas;
      this.gl = canvas.getContext('webgl', { antialias: true, preserveDrawingBuffer: true });
      if (!this.gl) {
        console.error('WebGL not supported on this context');
        return;
      }
      this.params = Object.assign({}, FINAL_TUNED_PARAMS);
      this.fsSource = customFs || FS_SOURCE;
      this.initGL();
    }

    initGL() {
      var gl = this.gl;
      var vs = this.compileShader(gl.VERTEX_SHADER, VS_SOURCE);
      var fs = this.compileShader(gl.FRAGMENT_SHADER, this.fsSource);
      this.program = gl.createProgram();
      gl.attachShader(this.program, vs);
      gl.attachShader(this.program, fs);
      gl.linkProgram(this.program);

      if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) {
        console.error('Program link error:', gl.getProgramInfoLog(this.program));
        return;
      }

      var vertices = new Float32Array([
        -1.0, -1.0,
         1.0, -1.0,
        -1.0,  1.0,
        -1.0,  1.0,
         1.0, -1.0,
         1.0,  1.0
      ]);
      var buffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

      this.posAttr = gl.getAttribLocation(this.program, 'a_position');
      gl.enableVertexAttribArray(this.posAttr);
      gl.vertexAttribPointer(this.posAttr, 2, gl.FLOAT, false, 0, 0);

      this.uniforms = {
        resolution: gl.getUniformLocation(this.program, 'u_resolution'),
        time: gl.getUniformLocation(this.program, 'u_time'),
        fiberFreq: gl.getUniformLocation(this.program, 'u_fiber_freq'),
        cryptThresh: gl.getUniformLocation(this.program, 'u_crypt_thresh'),
        collaretteR: gl.getUniformLocation(this.program, 'u_collarette_r'),
        pupilSize: gl.getUniformLocation(this.program, 'u_pupil_size'),
        stippleDensity: gl.getUniformLocation(this.program, 'u_stipple_density'),
        fiberThinness: gl.getUniformLocation(this.program, 'u_fiber_thinness'),
        collaretteBright: gl.getUniformLocation(this.program, 'u_collarette_bright'),
        limbusWidth: gl.getUniformLocation(this.program, 'u_limbus_width')
      };
    }

    compileShader(type, src) {
      var gl = this.gl;
      var s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        console.error('Shader compile error:', gl.getShaderInfoLog(s));
      }
      return s;
    }

    setParams(newParams) {
      Object.assign(this.params, newParams);
      this.render();
    }

    render(t) {
      var gl = this.gl;
      if (!gl || !this.program) return;

      var width = this.canvas.width;
      var height = this.canvas.height;
      gl.viewport(0, 0, width, height);
      gl.useProgram(this.program);

      gl.uniform2f(this.uniforms.resolution, width, height);
      gl.uniform1f(this.uniforms.time, t || 0.0);
      gl.uniform1f(this.uniforms.fiberFreq, this.params.fiberFreq);
      gl.uniform1f(this.uniforms.cryptThresh, this.params.cryptThresh);
      gl.uniform1f(this.uniforms.collaretteR, this.params.collaretteR);
      gl.uniform1f(this.uniforms.pupilSize, this.params.pupilSize);
      gl.uniform1f(this.uniforms.stippleDensity, this.params.stippleDensity);
      gl.uniform1f(this.uniforms.fiberThinness, this.params.fiberThinness);
      gl.uniform1f(this.uniforms.collaretteBright, this.params.collaretteBright);
      gl.uniform1f(this.uniforms.limbusWidth, this.params.limbusWidth);

      gl.drawArrays(gl.TRIANGLES, 0, 6);
    }
  }

  // Export globally for project integration
  window.IrisWebGL = {
    Renderer: IrisWebGLRenderer,
    FINAL_PARAMS: FINAL_TUNED_PARAMS,
    createInstance: function (canvas, customParams) {
      var r = new IrisWebGLRenderer(canvas);
      if (customParams) r.setParams(customParams);
      return r;
    }
  };

})(window, document);
