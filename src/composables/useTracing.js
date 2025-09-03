import { ref } from "vue";
import { nextColor } from "@/utils/color";
import { formatPoints } from "@/utils/math";

export function useTracing() {
  const penAngles = [0, 25, 30, 50, 80];
  const penWidth = ref(3);
  const penHeight = ref(6);
  const selectedPenAngle = ref(null);
  const showPenSelectionPopup = ref(false);
  const isDrawingTest = ref(false);
  const testTracePath = ref([]);
  const currentStroke = ref(null);

  function selectPen(angle) {
    selectedPenAngle.value = angle;
    switch (angle) {
      case 25: penWidth.value = 3; penHeight.value = 6; break;
      case 30: penWidth.value = 4; penHeight.value = 7; break;
      case 50: penWidth.value = 5; penHeight.value = 8; break;
      case 80: penWidth.value = 6; penHeight.value = 10; break;
      case 0:  penWidth.value = 2; penHeight.value = 2; break;
      default: penWidth.value = 3; penHeight.value = 6;
    }
  }

  function startTraceAt(pos) {
    currentStroke.value = {
      points: [pos],
      color: nextColor(),
      penWidth: penWidth.value,
      penHeight: penHeight.value,
    };
  }

  function continueTrace(pos) {
    if (!currentStroke.value) return;
    currentStroke.value.points.push(pos);
  }

  function endTrace(commit) {
    if (!currentStroke.value) return null;
    const done = currentStroke.value;
    currentStroke.value = null;
    if (commit) return done;
    return null;
  }

  return {
    penAngles, penWidth, penHeight, selectedPenAngle, showPenSelectionPopup,
    isDrawingTest, testTracePath, currentStroke,
    selectPen, startTraceAt, continueTrace, endTrace, formatPoints,
  };
}
