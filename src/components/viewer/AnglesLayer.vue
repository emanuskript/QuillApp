<template>
  <svg class="angles-layer" xmlns="http://www.w3.org/2000/svg">
    <!-- Existing / saved angles -->
    <g v-for="(ann, aIdx) in angles" :key="'angle-' + aIdx">
      <!-- first leg -->
      <line
        v-if="ann.points && ann.points.length >= 2"
        :x1="ann.points[0].x"
        :y1="ann.points[0].y"
        :x2="ann.points[1].x"
        :y2="ann.points[1].y"
        class="angle-leg"
      />
      <!-- second leg -->
      <line
        v-if="ann.points && ann.points.length === 3"
        :x1="ann.points[1].x"
        :y1="ann.points[1].y"
        :x2="ann.points[2].x"
        :y2="ann.points[2].y"
        class="angle-leg"
      />
      <!-- label @ vertex (point[1]) -->
      <text
        v-if="ann.points && ann.points.length === 3 && (ann.angle !== undefined && ann.angle !== null)"
        :x="ann.points[1].x + 10"
        :y="ann.points[1].y - 10"
        class="angle-label"
      >
        {{ formatAngle(ann.angle) }}°
      </text>

      <!-- draggable handles -->
      <circle
        v-for="(pt, pIdx) in ann.points"
        :key="'angle-pt-' + aIdx + '-' + pIdx"
        :cx="pt.x"
        :cy="pt.y"
        r="5"
        class="angle-handle"
        @mousedown.stop="$emit('point-mousedown', { annotationIndex: aIdx, pointIndex: pIdx, event: $event })"
      />
    </g>

    <!-- In-progress (temporary) angle construction -->
    <g v-if="tempPoints && tempPoints.length">
      <!-- temp first leg -->
      <line
        v-if="tempPoints.length >= 2"
        :x1="tempPoints[0].x"
        :y1="tempPoints[0].y"
        :x2="tempPoints[1].x"
        :y2="tempPoints[1].y"
        class="angle-leg temp"
      />
      <!-- temp second leg -->
      <line
        v-if="tempPoints.length === 3"
        :x1="tempPoints[1].x"
        :y1="tempPoints[1].y"
        :x2="tempPoints[2].x"
        :y2="tempPoints[2].y"
        class="angle-leg temp"
      />
      <!-- temp label -->
      <text
        v-if="tempPoints.length === 3 && (tempAngle !== undefined && tempAngle !== null)"
        :x="tempPoints[1].x + 10"
        :y="tempPoints[1].y - 10"
        class="angle-label temp"
      >
        {{ formatAngle(tempAngle) }}°
      </text>

      <!-- temp draggable handles -->
      <circle
        v-for="(pt, pIdx) in tempPoints"
        :key="'temp-pt-' + pIdx"
        :cx="pt.x"
        :cy="pt.y"
        r="5"
        class="angle-handle temp"
        @mousedown.stop="$emit('temp-point-mousedown', { pointIndex: pIdx, event: $event })"
      />
    </g>
  </svg>
</template>

<script>
export default {
  name: "AnglesLayer",
  props: {
    /**
     * Array of angle annotations:
     * [{ points:[{x,y},{x,y},{x,y}], angle:Number|String }]
     */
    angles: {
      type: Array,
      required: true,
      default: () => [],
    },
    /** Temporary points while constructing/editing an angle */
    tempPoints: {
      type: Array,
      required: false,
      default: () => [],
    },
    /** Temporary computed angle (if available) */
    tempAngle: {
      type: [Number, String],
      required: false,
      default: null,
    },
  },
  emits: ["point-mousedown", "temp-point-mousedown"],
  methods: {
    formatAngle(a) {
      const n = Number(a);
      if (Number.isFinite(n)) return n.toFixed(2);
      return String(a);
    },
  },
};
</script>

<style scoped>
.angles-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* let the stage receive general interactions */
}

.angle-leg {
  stroke: blue;
  stroke-width: 2;
  fill: none;
  vector-effect: non-scaling-stroke;
  pointer-events: none;
}

.angle-leg.temp {
  stroke-dasharray: 4 4;
}

.angle-label {
  fill: darkblue;
  font-size: 12px;
  user-select: none;
  pointer-events: none;
}

.angle-label.temp {
  opacity: 0.9;
}

.angle-handle {
  fill: red;
  r: 5;
  pointer-events: all; /* enable dragging on points */
  cursor: grab;
}

.angle-handle:active {
  cursor: grabbing;
}

.angle-handle.temp {
  opacity: 0.9;
}
</style>
