import { ref } from "vue";
import { calculateAngle } from "@/utils/math";

export function useAngles() {
  const measurePoints = ref([]);      // temp 0..3 points
  const draggingPoint = ref(-1);
  const calculatedAngle = ref(0);

  function resetTemp() {
    measurePoints.value = [];
    draggingPoint.value = -1;
    calculatedAngle.value = 0;
  }

  function addPoint(p) {
    if (measurePoints.value.length >= 3) return false;
    measurePoints.value.push(p);
    if (measurePoints.value.length === 3) {
      calculatedAngle.value = +calculateAngle(...measurePoints.value).toFixed(2);
    }
    return true;
  }

  function updatePoint(i, p) {
    if (i < 0 || i >= measurePoints.value.length) return;
    measurePoints.value[i] = p;
    if (measurePoints.value.length === 3) {
      calculatedAngle.value = +calculateAngle(...measurePoints.value).toFixed(2);
    }
  }

  function findNearest(points, x, y, threshold = 10) {
    let idx = -1, min = Infinity;
    points.forEach((pt, i) => {
      const d = Math.hypot(x - pt.x, y - pt.y);
      if (d < threshold && d < min) { min = d; idx = i; }
    });
    return idx;
  }

  return {
    measurePoints, draggingPoint, calculatedAngle,
    resetTemp, addPoint, updatePoint, findNearest,
  };
}
