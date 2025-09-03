/** Basic math/stat helpers used across features */

/** @param {number[]} values */
export function average(values) {
  const xs = (values || []).map(Number).filter((v) => !Number.isNaN(v));
  if (!xs.length) return 0;
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}

/** Population standard deviation */
export function stddev(values) {
  const xs = (values || []).map(Number).filter((v) => !Number.isNaN(v));
  if (!xs.length) return 0;
  const mu = average(xs);
  const varPop = xs.reduce((acc, v) => acc + (v - mu) ** 2, 0) / xs.length;
  return Math.sqrt(varPop);
}

/** Mode (smallest if multimodal). Returns "No mode" if none. */
export function mode(values) {
  const xs = (values || []).map(Number).filter((v) => !Number.isNaN(v));
  if (!xs.length) return "No mode";
  const freq = {};
  xs.forEach((v) => (freq[v] = (freq[v] || 0) + 1));
  const maxF = Math.max(...Object.values(freq));
  if (maxF === 1) return "No mode";
  const modes = Object.keys(freq).filter((k) => freq[k] === maxF).map(Number);
  return Math.min(...modes);
}

export function formatPoints(points) {
  return (points || []).map(({ x, y }) => `${x},${y}`).join(" ");
}

export function calculateAngle(p1, p2, p3) {
  const v1 = { x: p1.x - p2.x, y: p1.y - p2.y };
  const v2 = { x: p3.x - p2.x, y: p3.y - p2.y };
  const dot = v1.x * v2.x + v1.y * v2.y;
  const m1 = Math.sqrt(v1.x ** 2 + v1.y ** 2);
  const m2 = Math.sqrt(v2.x ** 2 + v2.y ** 2);
  if (m1 === 0 || m2 === 0) return 0;
  const cos = Math.min(1, Math.max(-1, dot / (m1 * m2)));
  return ((Math.acos(cos) * 180) / Math.PI);
}
