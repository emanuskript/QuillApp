<template>
  <div v-if="visible" class="length-popup" @keydown.esc="$emit('cancel')">
    <div class="length-popup-content" role="dialog" aria-modal="true" aria-label="Select angle label">
      <h3 class="title">Choose Angle Label</h3>

      <div v-if="labels && labels.length" class="section-title">Existing Labels</div>
      <div v-if="labels && labels.length" class="options-grid">
        <button
          v-for="l in labels"
          :key="l"
          type="button"
          class="type-button"
          :class="{ selected: selected === l }"
          :aria-pressed="selected === l ? 'true' : 'false'"
          @click="selected = l"
        >
          <span class="swatch" />
          <span class="label">{{ l }}</span>
        </button>
      </div>

      <div class="section-title">Create New Label</div>
      <div class="new-row">
        <input
          v-model.trim="newLabel"
          type="text"
          placeholder="e.g., Main Hand, Corrector A, Line-end flourish"
          @keyup.enter="confirmNew"
        />
        <button class="make-btn" type="button" @click="confirmNew">Create & Use</button>
      </div>

      <div class="actions">
        <button type="button" class="confirm" :disabled="!selected" @click="$emit('confirm', selected)">Use Selected</button>
        <button type="button" class="cancel" @click="$emit('cancel')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "AngleLabelPopup",
  props: {
    visible: { type: Boolean, default: false },
    labels: { type: Array, default: () => [] },
    initialLabel: { type: String, default: "" },
  },
  data() {
    return {
      selected: this.initialLabel || "",
      newLabel: "",
    };
  },
  watch: {
    visible(v) {
      if (v) this.$nextTick(() => this.focusFirst());
    },
    initialLabel(v) {
      this.selected = v || "";
    },
  },
  methods: {
    confirmNew() {
      if (!this.newLabel) return;
      this.$emit("confirm", this.newLabel);
      this.newLabel = "";
    },
    focusFirst() {
      const el =
        this.$el.querySelector(".type-button") ||
        this.$el.querySelector("input");
      if (el) el.focus();
    },
  },
};
</script>

<style scoped>
.length-popup { position: fixed; inset: 0; display: grid; place-items: center; background: rgba(0,0,0,.5); z-index: 1100; }
.length-popup-content { width: min(720px, 92vw); background: #fff; border-radius: 12px; box-shadow: 0 8px 28px rgba(0,0,0,.25); padding: 28px; }
.title { font-size: 28px; text-align: center; margin: 0 0 16px; }
.section-title { margin: 14px 4px 8px; font-weight: 600; color: #222; }
.options-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 10px; }
.type-button { display: grid; justify-items: center; gap: 8px; padding: 10px; border: 1px solid #d3d3d3; border-radius: 10px; background: #fafafa; cursor: pointer; }
.type-button:hover { border-color: #9ec9ff; background: #f6fbff; }
.type-button.selected { border-color: #007bff; box-shadow: 0 0 0 3px rgba(0,123,255,.2); background: #f4f9ff; }
.swatch { width: 40px; height: 40px; border-radius: 8px; background: #e9ecef; border: 2px solid rgba(0,0,0,.08); }
.label { font-size: 14px; color: #222; text-align: center; }
.new-row { display: grid; grid-template-columns: 1fr auto; gap: 10px; margin: 8px 0 4px; }
.new-row input { border: 1px solid #cfd4da; border-radius: 8px; padding: 10px 12px; font-size: 15px; }
.make-btn { border: 1px solid #0d6efd; color: #fff; background: #0d6efd; border-radius: 8px; padding: 10px 14px; cursor: pointer; }
.actions { display: flex; justify-content: center; gap: 16px; margin-top: 16px; }
.actions button { min-width: 130px; padding: 10px 14px; border-radius: 8px; border: 1px solid #c8c8c8; background: #fff; font-size: 16px; cursor: pointer; }
.actions .confirm { background: #0d6efd; color: #fff; border-color: #0d6efd; }
.actions .confirm:disabled { opacity: .5; cursor: not-allowed; }
.actions .cancel:hover { background: #f3f3f3; }
</style>
