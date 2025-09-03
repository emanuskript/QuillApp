<template>
  <!-- SVG overlay that spans the whole stage -->
  <svg class="drawing-layer" xmlns="http://www.w3.org/2000/svg">
    <!-- Saved strokes -->
    <template v-for="(stroke, i) in strokes" :key="'stroke-' + i">
      <polyline
        v-if="stroke?.points?.length"
        :points="formatPoints(stroke.points)"
        :stroke="stroke.color || '#ff0000'"
        :stroke-width="stroke.penWidth || 2"
        fill="none"
        vector-effect="non-scaling-stroke"
      />
    </template>

    <!-- Dynamic (in-progress) stroke -->
    <polyline
      v-if="dynamicStroke && dynamicStroke.points && dynamicStroke.points.length"
      :points="formatPoints(dynamicStroke.points)"
      :stroke="dynamicStroke.color || '#ff0000'"
      :stroke-width="dynamicStroke.penWidth || 2"
      fill="none"
      vector-effect="non-scaling-stroke"
    />
  </svg>
</template>

<script>
export default {
  name: "TracesLayer",
  props: {
    /**
     * Array of strokes:
     * [{ points:[{x,y},...], color:'#hex', penWidth:Number, penHeight:Number }]
     * (penHeight is currently not rendered by SVG; kept for compatibility)
     */
    strokes: {
      type: Array,
      required: true,
      default: () => [],
    },
    /**
     * Current in-progress stroke (or null):
     * { points:[{x,y},...], color:'#hex', penWidth:Number, penHeight:Number }
     */
    dynamicStroke: {
      type: Object,
      required: false,
      default: null,
    },
  },
  methods: {
    formatPoints(points) {
      return (points || []).map(p => `${p.x},${p.y}`).join(" ");
    },
  },
};
</script>

<style scoped>
.drawing-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* don't block mouse interactions with the stage */
}
</style>
