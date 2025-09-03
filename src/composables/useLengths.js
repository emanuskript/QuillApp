import { reactive, ref } from "vue";
import { measurementColors as defaultColors } from "@/utils/color";
import { average, stddev, mode } from "@/utils/math";
import { uid } from "@/utils/id";

const HORIZONTAL = [
  "ascenders", "descenders", "interlinear",
  "upperMargin", "lowerMargin", "lineHeight", "minimumHeight",
];
const VERTICAL = ["internalMargin", "intercolumnSpaces"];

export function useLengths() {
  const colors = reactive({ ...defaultColors });
  const selectedMeasurement = ref("ascenders");
  const labelPositions = reactive({}); // { [measurementId]: {x,y} }
  // lengthMeasurements[label][page] = [{x,y,width,height,color,label,id}]
  const lengthMeasurements = reactive({});

  function addMeasurement(label, page, rect) {
    if (!lengthMeasurements[label]) lengthMeasurements[label] = {};
    if (!lengthMeasurements[label][page]) lengthMeasurements[label][page] = [];
    lengthMeasurements[label][page].push({
      ...rect,
      color: colors[label],
      label,
      id: uid("len"),
    });
  }

  function clearHorizontal(page) {
    HORIZONTAL.forEach((t) => lengthMeasurements[t] && delete lengthMeasurements[t][page]);
  }
  function clearVertical(page) {
    VERTICAL.forEach((t) => lengthMeasurements[t] && delete lengthMeasurements[t][page]);
  }
  function clearAll(page) {
    [...HORIZONTAL, ...VERTICAL].forEach((t) => lengthMeasurements[t] && delete lengthMeasurements[t][page]);
  }

  function extractValues(arr, type) {
    // NOTE: original code uses height for horizontal and width for vertical in places,
    // but the final UI labels show expected dimensions. To preserve behavior, mirror logic:
    const isVertical = VERTICAL.includes(type);
    return (arr || []).map((m) => (isVertical ? m.width : m.height));
  }

  function statsForType(type, page) {
    const arr = lengthMeasurements[type]?.[page] || [];
    const vals = extractValues(arr, type);
    return {
      average: average(vals),
      standardDeviation: stddev(vals),
      mode: mode(vals),
    };
  }

  function statsForPage(page) {
    const stats = {};
    [...HORIZONTAL, ...VERTICAL].forEach((t) => {
      if (lengthMeasurements[t]?.[page]?.length) stats[t] = statsForType(t, page);
    });
    return stats;
  }

  function statsForDocument(totalPages) {
    const stats = {};
    [...HORIZONTAL, ...VERTICAL].forEach((t) => {
      let vals = [];
      for (let p = 0; p < totalPages; p++) {
        if (lengthMeasurements[t]?.[p]?.length) {
          vals = vals.concat(extractValues(lengthMeasurements[t][p], t));
        }
      }
      stats[t] = {
        average: average(vals),
        standardDeviation: stddev(vals),
        mode: mode(vals),
      };
    });
    return stats;
  }

  return {
    colors, selectedMeasurement, labelPositions, lengthMeasurements,
    addMeasurement, clearHorizontal, clearVertical, clearAll,
    statsForType, statsForPage, statsForDocument,
    HORIZONTAL, VERTICAL,
  };
}
