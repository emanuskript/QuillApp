<template>
  <div v-if="visible" class="pen-selection-popup">
    <div class="pen-selection-content">
      <h3>Select a Pen</h3>

      <!-- Pen options -->
      <div class="pen-options">
        <div
          v-for="angle in penAngles"
          :key="angle"
          class="pen-option"
          :class="{ selected: selectedAngle === angle }"
          @click="$emit('select', angle)"
        >
          <div
            class="pen-preview"
            :style="{ transform: `rotate(${-angle}deg)` }"
          >
            <svg width="40" height="20">
              <ellipse
                cx="20"
                cy="10"
                rx="12"
                ry="4"
                :fill="selectedAngle === angle ? '#007bff' : '#555'"
                :stroke="selectedAngle === angle ? '#007bff' : '#333'"
                stroke-width="2"
                :transform="`rotate(${-angle}, 20, 10)`"
              />
            </svg>
          </div>
          <span class="pen-angle-text">{{ angle }}°</span>
        </div>
      </div>

      <!-- Test area -->
      <div class="test-box">
        <h4>Test Your Pen</h4>
        <div
          class="test-area"
          @mousedown="$emit('test-start', $event)"
          @mousemove="$emit('test-move', $event)"
          @mouseup="$emit('test-end')"
          @mouseleave="$emit('test-end')"
        >
          <svg class="test-svg">
            <polyline
              v-if="testPath.length > 0"
              :points="formatPoints(testPath)"
              stroke="black"
              :stroke-width="penWidth"
              :stroke-height="penHeight"
              fill="none"
            />
          </svg>
        </div>
      </div>

      <!-- Actions -->
      <div class="pen-selection-actions">
        <button @click="$emit('confirm')">Confirm</button>
        <button @click="$emit('cancel')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "PenSelectionPopup",
  props: {
    visible: { type: Boolean, default: false },
    penAngles: { type: Array, default: () => [0, 25, 30, 50, 80] },
    selectedAngle: { type: Number, default: null },
    testPath: { type: Array, default: () => [] },
    penWidth: { type: Number, default: 3 },
    penHeight: { type: Number, default: 6 },
  },
  methods: {
    formatPoints(points) {
      return points.map(({ x, y }) => `${x},${y}`).join(" ");
    },
  },
};
</script>

<style scoped>
.pen-selection-popup {
  position: fixed;
  inset: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1100;
}

.pen-selection-content {
  background-color: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  text-align: center;
  width: 400px;
}

.pen-options {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.pen-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}
.pen-option.selected {
  border: 2px solid #007bff;
  border-radius: 5px;
  padding: 5px;
}

.pen-preview {
  width: 40px;
  height: 20px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pen-option:hover {
  background-color: #f0f8ff;
  border-color: #007bff;
}

.test-box {
  margin-top: 20px;
}

.test-area {
  width: 100%;
  height: 100px;
  border: 1px solid #ccc;
  background-color: white;
  position: relative;
}

.test-svg {
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.pen-selection-actions {
  margin-top: 20px;
  display: flex;
  justify-content: space-around;
}
</style>
