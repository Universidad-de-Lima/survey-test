/**
 * SURVEY TEST FRAMEWORK — Mini-framework de testing para vanilla JS.
 *
 * Cero dependencias. Diseñado para ejecutarse en navegador.
 * Proporciona assert, describe, it y un runner con salida visual.
 *
 * Uso:
 *   describe('formatters', () => {
 *     it('debe formatear decimales', () => {
 *       assert.equal(formatDecimal(3.14159, 2), '3,14');
 *     });
 *   });
 *
 * @module tests/test-framework
 * @version 1.0.0
 */
window.TestFramework = (() => {
  'use strict';

  const results = [];
  let currentDescribe = '';
  let passed = 0;
  let failed = 0;

  const assert = {
    equal(actual, expected, msg) {
      if (actual !== expected) {
        throw new Error(msg || `Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
      }
    },
    deepEqual(actual, expected, msg) {
      const a = JSON.stringify(actual);
      const b = JSON.stringify(expected);
      if (a !== b) {
        throw new Error(msg || `Expected ${b}, got ${a}`);
      }
    },
    isTrue(value, msg) {
      if (!value) throw new Error(msg || `Expected truthy, got ${value}`);
    },
    isFalse(value, msg) {
      if (value) throw new Error(msg || `Expected falsy, got ${value}`);
    },
    throws(fn, msg) {
      try { fn(); } catch (e) { return; }
      throw new Error(msg || 'Expected function to throw');
    },
    isNull(value, msg) {
      if (value !== null) throw new Error(msg || `Expected null, got ${JSON.stringify(value)}`);
    },
    isDefined(value, msg) {
      if (value === undefined) throw new Error(msg || 'Expected defined value');
    },
    typeOf(value, type, msg) {
      if (typeof value !== type) throw new Error(msg || `Expected ${type}, got ${typeof value}`);
    },
  };

  function describe(name, fn) {
    currentDescribe = name;
    results.push({ type: 'describe', name });
    fn();
  }

  function it(name, fn) {
    try {
      fn();
      passed++;
      results.push({ type: 'pass', name: `${currentDescribe} › ${name}` });
    } catch (e) {
      failed++;
      results.push({ type: 'fail', name: `${currentDescribe} › ${name}`, error: e.message });
    }
  }

  function summary() {
    return { passed, failed, total: passed + failed, results };
  }

  function renderTo(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const s = summary();
    const pct = s.total > 0 ? Math.round((s.passed / s.total) * 100) : 100;
    const color = pct === 100 ? '#065F46' : pct >= 80 ? '#92400E' : '#991B1B';

    let html = `<div style="font-family:monospace;font-size:13px;max-width:800px;margin:20px auto;">`;
    html += `<h2 style="color:${color};">${s.passed}/${s.total} passed (${pct}%)</h2>`;

    s.results.forEach((r) => {
      if (r.type === 'describe') {
        html += `<div style="color:#374151;font-weight:700;margin-top:12px;border-bottom:1px solid #E5E7EB;padding-bottom:4px;">${r.name}</div>`;
      } else if (r.type === 'pass') {
        html += `<div style="color:#065F46;padding:2px 0 2px 16px;">✓ ${r.name}</div>`;
      } else if (r.type === 'fail') {
        html += `<div style="color:#991B1B;padding:2px 0 2px 16px;">✗ ${r.name}<br><span style="color:#6B7280;font-size:11px;">${r.error}</span></div>`;
      }
    });

    html += `</div>`;
    el.innerHTML = html;
  }

  return { assert, describe, it, summary, renderTo };
})();
