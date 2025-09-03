<template>
  <div class="lengths-layer">
    <!-- Dynamic rectangle while measuring -->
    <div
      v-if="dynamic"
      class="length-measurement"
      :style="boxStyle(dynamic)"
    >
      <div
        class="length-label draggable-label"
        :style="labelStyle('dynamic')"
        @mousedown.stop="onLabelMouseDown('dynamic', $event, dynamic)"
      >
        {{ dynamic.label }}:
        {{
          isHorizontal(dynamic.label) ? dynamic.height : dynamic.width
        }}px
      </div>
    </div>

    <!-- Finalized measurements -->
    <div
      v-for="m in measurements"
      :key="m.id"
      class="length-measurement"
      :style="boxStyle(m, true)"
    >
      <div
        class="length-label draggable-label"
        :style="labelStyle(m.id)"
        @mousedown.stop="onLabelMouseDown(m.id, $event, m)"
      >
        {{ m.label }}:
        {{
          isHorizontal(m.label) ? m.height : m.width
        }}px
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "LengthsLayer",
  props: {
    measurements: { type: Array, default: () => [] },
    dynamic: { type: Object, default: null },
    labelPositions: { type: Object, default: () => ({}) },
  },
  emits: ["label-mousedown"],
  methods: {
    isHorizontal(label) {
      return [
        "ascenders",
        "descenders",
        "interlinear",
        "upperMargin",
        "lowerMargin",
        "minimumHeight",
        "lineHeight",
      ].includes(label);
    },
    boxStyle(m, solid = false) {
      return {
        left: `${m.x}px`,
        top: `${m.y}px`,
        width: `${m.width}px`,
        height: `${m.height}px`,
        backgroundColor: m.color,
        position: "absolute",
        border: solid ? "1px solid black" : undefined,
      };
    },
    labelStyle(id) {
      const pos = this.labelPositions?.[id] || { x: 15, y: 0 };
      return {
        left: `${pos.x}px`,
        top: pos.y ? `${pos.y}px` : "50%",
        position: "absolute",
        cursor: "grab",
        backgroundColor: "white",
        zIndex: 2000,
        userSelect: "none",
        pointerEvents: "auto",
      };
    },
    onLabelMouseDown(id, _event, measurement) {
      // eslint-disable-next-line vue/custom-event-name-casing
      this.$emit("label-mousedown", { id, event: _event, measurement });
    },
  },
};
</script>

<style scoped>
.lengths-layer {
  position: absolute;
  inset: 0;
}

.length-measurement {
  position: absolute;
  border: 2px solid rgba(0, 0, 0, 0.5);
  pointer-events: none;
}

.length-label {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: black;
  font-size: 12px;
  background-color: white;
  padding: 2px 5px;
  border-radius: 3px;
}

.draggable-label {
  cursor: grab;
  user-select: none;
}
.draggable-label:active {
  cursor: grabbing;
}
</style>
