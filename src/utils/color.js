const palette = [
  "#E69F00", // Orange
  "#56B4E9", // Sky Blue
  "#009E73", // Green
  "#F0E442", // Yellow
  "#0072B2", // Blue
  "#D55E00", // Vermillion
  "#CC79A7", // Reddish Purple
];

let lastColor = null;

export function nextColor() {
  const pool = palette.filter((c) => c !== lastColor);
  const pick = pool[Math.floor(Math.random() * pool.length)];
  lastColor = pick;
  return pick;
}

export const measurementColors = {
  ascenders: "rgba(0, 255, 0, 0.5)",
  descenders: "rgba(0, 0, 255, 0.5)",
  interlinear: "rgba(255, 165, 0, 0.5)",
  upperMargin: "rgba(255, 0, 0, 0.5)",
  lowerMargin: "rgba(128, 0, 128, 0.5)",
  internalMargin: "rgba(0, 255, 255, 0.5)",
  intercolumnSpaces: "rgba(255, 0, 255, 0.5)",
  lineHeight: "rgba(100, 100, 255, 0.5)",
  minimumHeight: "rgba(255, 100, 100, 0.5)",
};
