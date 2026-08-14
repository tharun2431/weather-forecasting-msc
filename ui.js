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
        io.unobserve(e.target);   // reveal once, do not re-hide on scroll back
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    nodes.forEach(function (n) { io.observe(n); });

    function show(n) {
      if (n.classList.contains('in')) return;
      n.classList.add('in');
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

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
