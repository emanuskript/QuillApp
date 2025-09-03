<template>
  <div class="underlines-layer">
    <!-- Finalized underlines -->
    <div
      v-for="(ul, idx) in underlines"
      :key="'ul-' + idx"
      class="underline-line"
      :style="{
        left: ul.x + 'px',
        top: ul.y + 'px',
        width: ul.width + 'px',
        height: '2px',
      }"
    ></div>

    <!-- Dynamic underline (in-progress) -->
    <div
      v-if="tempUnderline"
      class="underline-line temp"
      :style="{
        left: tempUnderline.x + 'px',
        top: tempUnderline.y + 'px',
        width: tempUnderline.width + 'px',
        height: '2px',
      }"
    ></div>
  </div>
</template>

<script>
export default {
  name: "UnderlinesLayer",
  props: {
    /** Array of finalized underlines: {x,y,width} */
    underlines: {
      type: Array,
      required: true,
      default: () => [],
    },
    /** Temporary underline in-progress: {x,y,width} */
    tempUnderline: {
      type: Object,
      required: false,
      default: null,
    },
  },
};
</script>

<style scoped>
.underlines-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.underline-line {
  position: absolute;
  background-color: red;
  height: 2px;
  pointer-events: none;
  z-index: 1100;
}

.underline-line.temp {
  background-color: blue;
}
</style>
