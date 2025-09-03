<template>
  <div v-if="visible" class="length-popup" @keydown.esc="$emit('cancel')">
    <div class="length-popup-content" role="dialog" aria-modal="true" aria-label="Select horizontal measurement type">
      <h3 class="title">Select Horizontal Measurement Type</h3>

      <!-- Options -->
      <div class="options-grid">
        <button
          v-for="opt in options"
          :key="opt"
          type="button"
          class="type-button"
          :class="{ selected: selected === opt }"
          :aria-pressed="selected === opt ? 'true' : 'false'"
          @click="selected = opt"
        >
          <span class="swatch" :style="{ backgroundColor: colorFor(opt) }" />
          <span class="label">{{ label(opt) }}</span>
        </button>
      </div>

      <!-- Actions -->
      <div class="actions">
        <button type="button" class="confirm" @click="$emit('confirm', selected)">Confirm</button>
        <button type="button" class="cancel" @click="$emit('cancel')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "LengthPopupHorizontal",
  props: {
    visible: { type: Boolean, default: false },
    measurementColors: {
      type: Object,
      required: true,
      default: () => ({}),
    },
    // Optional: let parent preselect something
    initialSelection: {
      type: String,
      default: "ascenders",
    },
  },
  data() {
    return {
      options: [
        "ascenders",
        "descenders",
        "interlinear",
        "upperMargin",
        "lowerMargin",
        "lineHeight",
        "minimumHeight",
      ],
      selected: this.initialSelection || "ascenders",
    };
  },
  watch: {
    initialSelection(v) {
      if (v && this.options.includes(v)) this.selected = v;
    },
    visible(v) {
      // When the popup opens, focus the first selected option for accessibility
      if (v) this.$nextTick(() => this.focusSelected());
    },
  },
  methods: {
    colorFor(k) {
      return this.measurementColors?.[k] || "#ddd";
    },
    label(k) {
      const map = {
        ascenders: "Ascenders",
        descenders: "Descenders",
        interlinear: "Interlinear",
        upperMargin: "Upper Margin",
        lowerMargin: "Lower Margin",
        lineHeight: "Line Height",
        minimumHeight: "Minimum Height",
      };
      return map[k] || k;
    },
    focusSelected() {
      const btn = this.$el.querySelector(".type-button.selected");
      if (btn) btn.focus();
    },
  },
};
</script>

<style scoped>
.length-popup {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1100;
}

.length-popup-content {
  width: min(760px, 92vw);
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.25);
  padding: 28px 28px 22px;
}

.title {
  font-size: 28px;
  text-align: center;
  margin: 0 0 18px;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 18px 16px;
  padding: 6px 6px 4px;
  margin-bottom: 18px;
}

.type-button {
  display: grid;
  justify-items: center;
  align-content: start;
  gap: 8px;
  padding: 10px 8px 12px;
  border: 1px solid #d3d3d3;
  border-radius: 10px;
  background: #fafafa;
  cursor: pointer;
  outline: none;
}
.type-button:hover {
  border-color: #9ec9ff;
  background: #f6fbff;
}
.type-button:focus-visible {
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.35);
}
.type-button.selected {
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.2);
  background: #f4f9ff;
}

.swatch {
  width: 54px;
  height: 54px;
  border-radius: 8px;
  border: 2px solid rgba(0, 0, 0, 0.12);
  display: block;
}
.label {
  font-size: 14px;
  color: #222;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 22px;
  margin-top: 6px;
}
.actions button {
  min-width: 120px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #c8c8c8;
  background: #fff;
  font-size: 16px;
  cursor: pointer;
}
.actions .confirm {
  background: #0d6efd;
  color: #fff;
  border-color: #0d6efd;
}
.actions .confirm:hover {
  filter: brightness(0.95);
}
.actions .cancel:hover {
  background: #f3f3f3;
}
</style>
