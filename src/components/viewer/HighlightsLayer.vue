<template>
  <div class="highlights-layer">
    <!-- Finalized highlights -->
    <div
      v-for="(hl, idx) in highlights"
      :key="'hl-' + idx"
      class="highlight-rectangle"
      :style="{
        left: hl.x + 'px',
        top: hl.y + 'px',
        width: hl.width + 'px',
        height: hl.height + 'px',
      }"
    ></div>

    <!-- Dynamic highlight (in-progress) -->
    <div
      v-if="tempHighlight"
      class="highlight-rectangle temp"
      :style="{
        left: tempHighlight.x + 'px',
        top: tempHighlight.y + 'px',
        width: tempHighlight.width + 'px',
        height: tempHighlight.height + 'px',
      }"
    ></div>
  </div>
</template>

<script>
export default {
  name: "HighlightsLayer",
  props: {
    /** Array of finalized highlight objects: {x,y,width,height} */
    highlights: {
      type: Array,
      required: true,
      default: () => [],
    },
    /** Temporary highlight in-progress: {x,y,width,height} */
    tempHighlight: {
      type: Object,
      required: false,
      default: null,
    },
  },
};
</script>

<style scoped>
.highlights-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.highlight-rectangle {
  position: absolute;
  border: 2px solid rgba(255, 255, 0, 0.7);
  background-color: rgba(255, 255, 0, 0.3);
  pointer-events: none;
}

.highlight-rectangle.temp {
  border-style: dashed;
}
</style>
