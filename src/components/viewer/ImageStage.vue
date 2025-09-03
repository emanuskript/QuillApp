<template>
  <div
    class="image-stage"
    :style="{ cursor: cursorMode }"
    @mousedown="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup="onMouseUp"
  >
    <img
      v-if="image"
      :src="image"
      class="stage-image"
      draggable="false"
      @load="$emit('image-load')"
    />

    <!-- Overlay layers come from the parent via slot -->
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: "ImageStage",
  props: {
    image: { type: String, default: null },
    cursorMode: { type: String, default: "default" },
  },
  emits: ["image-load", "mousedown", "mousemove", "mouseup"],
  methods: {
    onMouseDown(e) {
      // forward DOM events upward so IIIFViewer can handle tools
      this.$emit("mousedown", e);
    },
    onMouseMove(e) {
      this.$emit("mousemove", e);
    },
    onMouseUp(e) {
      this.$emit("mouseup", e);
    },
  },
};
</script>

<style scoped>
.image-stage {
  position: relative;
  width: 100vw;
  height: 90vh;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}
.stage-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
}
</style>
