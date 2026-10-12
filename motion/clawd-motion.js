/* Zero-dependency helper. Inline the SVG, then ClawdMotion.play(element). */
(function (root) {
  const running = new WeakMap();
  const reduced = root.matchMedia('(prefers-reduced-motion: reduce)');
  const find = el => el?.matches?.('svg.cr') ? el : el?.querySelector?.('svg.cr');
  function play(el, motion = "trick") {
    const svg = find(el);
    if (!svg) return Promise.resolve();
    if (reduced.matches) { svg.classList.remove('is-asleep', 'is-waking'); return Promise.resolve(); }
    if (running.has(svg)) return running.get(svg); // Finish the gesture before accepting another.
    svg.classList.remove('is-asleep', 'is-waking');
    svg.dataset.motion = ['trick','blink','happy'].includes(motion) ? motion : 'trick';
    svg.classList.add('is-playing');
    const animations = svg.getAnimations({ subtree: true });
    const done = Promise.allSettled(animations.map(a => a.finished)).then(() => {
      // A cancelled older gesture must not stop a newer one.
      if (running.get(svg) === done) {
        svg.classList.remove('is-playing');
        running.delete(svg);
      }
    });
    running.set(svg, done);
    return done;
  }
  function stop(el) {
    const svg = find(el);
    if (!svg) return;
    const animations = svg.getAnimations({ subtree: true });
    running.delete(svg);
    svg.classList.remove('is-playing', 'is-waking');
    animations.filter(animation => !/^cr-(idle-blink|breathe|i-coupled-breathe)$/.test(animation.animationName)).forEach(animation => animation.cancel());
    // Resolve CSS cancellation before a synchronous replay.
    svg.getAnimations({ subtree: true });
  }
  function asleep(el, on = true) {
    const svg = find(el);
    if (!svg) return;
    stop(svg);
    svg.classList.toggle('is-asleep', on);
    if (!on && !reduced.matches) svg.classList.add('is-waking');
  }
  function idle(el, on = true) { find(el)?.classList.toggle('is-idle', on); }
  root.ClawdMotion = { play, stop, asleep, idle };
})(window);
