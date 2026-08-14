// presentation only. this file adds scroll-reveal and stagger to the static
// parts of the page. it does not touch the model, the data, or anything app.js
// owns. the elements app.js animates itself (hero, generated grids) are left
// alone here so the two do not fight over the same nodes.

(function () {
  var reduce = window.matchMedia &&
               window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return;

  // static blocks worth revealing. anything app.js builds at runtime is excluded.
  var SEL = [
    '.sec-head',
    '.chart-card',
    '.insight',
    '.disclosure',
    '.finding',
    '.foot'
  ].join(',');

  function stagger(nodes) {
    // group siblings so a row of cards comes in one after another rather than
    // all at once, which reads as a single blur of motion
    var byParent = new Map();
    nodes.forEach(function (n) {
      var p = n.parentElement;
      if (!byParent.has(p)) byParent.set(p, []);
      byParent.get(p).push(n);
    });
    byParent.forEach(function (group) {
      group.forEach(function (n, i) {
        n.style.setProperty('--d', Math.min(i * 70, 280) + 'ms');
      });
    });
  }

  function init() {
    var nodes = Array.prototype.slice.call(document.querySelectorAll(SEL));
    if (!nodes.length) return;

    nodes.forEach(function (n) { n.classList.add('reveal'); });
    stagger(nodes);

    if (!('IntersectionObserver' in window)) {
      // old browser, just show everything rather than leaving it invisible
      nodes.forEach(function (n) { n.classList.add('in'); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('in');
        animateFigures(e.target);
        io.unobserve(e.target);   // reveal once, do not re-hide on scroll back
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    nodes.forEach(function (n) { io.observe(n); });

    function show(n) {
      if (n.classList.contains('in')) return;
      n.classList.add('in');
      animateFigures(n);
      io.unobserve(n);
    }

    // anything already on screen at load should not wait for a scroll event.
    // this runs on a timer rather than requestAnimationFrame on purpose: rAF
    // does not fire while the page is not compositing (background tab), which
    // would leave the content stuck at opacity 0 until the tab was focused.
    setTimeout(function () {
      nodes.forEach(function (n) {
        if (n.getBoundingClientRect().top < window.innerHeight * 0.92) show(n);
      });
    }, 60);

    // hard safety net. whatever happens with the observer, nothing on this page
    // is allowed to stay invisible. a missed animation is fine, a blank page is not.
    setTimeout(function () { nodes.forEach(show); }, 2500);
  }

  // ── count-up on the headline figures ────────────────────────────────
  // the finding values are static text in index.html, e.g. "1.268 vs 1.272".
  // this animates each number it finds while leaving the markup around it
  // (the "vs" and unit spans) untouched, and keeps the original decimal places.
  function countUpNode(node) {
    var text = node.nodeValue;
    if (!/\d/.test(text)) return;

    var parts = [];                       // [{raw, value, decimals}]
    text.replace(/\d+(?:\.\d+)?/g, function (m) {
      var dot = m.indexOf('.');
      parts.push({ raw: m, value: parseFloat(m), decimals: dot < 0 ? 0 : m.length - dot - 1 });
      return m;
    });
    if (!parts.length) return;

    var t0 = null, DUR = 900;
    function frame(now) {
      if (t0 === null) t0 = now;
      var k = Math.min(1, (now - t0) / DUR);
      var e = 1 - Math.pow(1 - k, 3);     // ease out, settles rather than stops
      var i = 0;
      node.nodeValue = text.replace(/\d+(?:\.\d+)?/g, function () {
        var p = parts[i++];
        return (p.value * e).toFixed(p.decimals);
      });
      if (k < 1) requestAnimationFrame(frame);
      else node.nodeValue = text;         // land exactly on the real figure
    }
    requestAnimationFrame(frame);
    // rAF does not run in a background tab. make sure the true value is there
    // regardless, so nobody is ever shown a half-counted number.
    setTimeout(function () { node.nodeValue = text; }, DUR + 250);
  }

  function animateFigures(root) {
    var vals = root.matches && root.matches('.finding')
      ? [root.querySelector('.f-value')]
      : Array.prototype.slice.call(root.querySelectorAll('.f-value'));
    vals.forEach(function (v) {
      if (!v || v.dataset.counted) return;
      v.dataset.counted = '1';
      Array.prototype.slice.call(v.childNodes).forEach(function (n) {
        if (n.nodeType === 3) countUpNode(n);
      });
    });
  }

  // ── section transition when the bottom nav is used ──────────────────
  function wireNav() {
    document.querySelectorAll('.nav-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var id = btn.getAttribute('data-target');
        var sec = id && document.getElementById(id);
        if (!sec) return;
        sec.classList.remove('pop');
        void sec.offsetWidth;              // restart the animation
        sec.classList.add('pop');
        setTimeout(function () { sec.classList.remove('pop'); }, 900);
      });
      // app.js owns the scrolling. this only adds the arrival animation.
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { init(); wireNav(); });
  } else {
    init(); wireNav();
  }
})();
