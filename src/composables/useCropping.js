import { ref } from "vue";

export function useCropping() {
  const croppingStarted = ref(false);
  const startPoint = ref(null);
  const currentSquare = ref(null);
  const croppedSvg = ref(null);
  const croppedImage = ref(null); // dataURL

  function start() {
    croppingStarted.value = true;
    startPoint.value = null;
    currentSquare.value = null;
  }

  function beginAt(pos) {
    startPoint.value = pos;
    currentSquare.value = { x: pos.x, y: pos.y, width: 0, height: 0 };
  }

  function updateTo(pos) {
    if (!startPoint.value) return;
    currentSquare.value = {
      x: Math.min(pos.x, startPoint.value.x),
      y: Math.min(pos.y, startPoint.value.y),
      width: Math.abs(pos.x - startPoint.value.x),
      height: Math.abs(pos.y - startPoint.value.y),
    };
  }

  function reset() {
    croppingStarted.value = false;
    startPoint.value = null;
    currentSquare.value = null;
    croppedSvg.value = null;
    croppedImage.value = null;
  }

  return {
    croppingStarted, startPoint, currentSquare, croppedSvg, croppedImage,
    start, beginAt, updateTo, reset,
  };
}
