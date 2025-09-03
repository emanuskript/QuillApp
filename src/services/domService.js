export function getMousePosition(viewerEl, event) {
  if (!viewerEl) return { x: 0, y: 0 };
  const rect = viewerEl.getBoundingClientRect();
  return {
    x: event.clientX - rect.left + viewerEl.scrollLeft,
    y: event.clientY - rect.top + viewerEl.scrollTop,
  };
}

export function getRelativeTo(el, event) {
  if (!el) return { x: 0, y: 0 };
  const rect = el.getBoundingClientRect();
  return { x: event.clientX - rect.left, y: event.clientY - rect.top };
}
