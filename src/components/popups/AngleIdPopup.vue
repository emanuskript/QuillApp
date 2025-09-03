<template>
  <div v-if="visible" class="length-popup" @keydown.esc="$emit('cancel')">
    <div class="length-popup-content small" role="dialog" aria-modal="true" aria-label="Assign angle ID">
      <h3 class="title small">Assign Classification / ID</h3>
      <p class="hint">This ID helps group and reference specific angles in statistics.</p>
      <input
        v-model.trim="value"
        type="text"
        placeholder="e.g., A1, C-Angle-07, unique code"
        @keyup.enter="$emit('confirm', value || '')"
      />
      <div class="actions">
        <button class="confirm" type="button" @click="$emit('confirm', value || '')">Save</button>
        <button class="cancel" type="button" @click="$emit('cancel')">Skip</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "AngleIdPopup",
  props: {
    visible: { type: Boolean, default: false },
    initialValue: { type: String, default: "" },
  },
  data() {
    return { value: this.initialValue || "" };
  },
  watch: {
    initialValue(v) { this.value = v || ""; },
    visible(v) { if (v) this.$nextTick(() => this.$el.querySelector("input")?.focus()); },
  },
};
</script>

<style scoped>
.length-popup { position: fixed; inset: 0; display: grid; place-items: center; background: rgba(0,0,0,.5); z-index: 1100; }
.length-popup-content.small { width: min(520px, 88vw); padding: 22px; background: #fff; border-radius: 12px; box-shadow: 0 8px 28px rgba(0,0,0,.25); }
.title.small { font-size: 22px; margin: 0 0 10px; text-align: center; }
.hint { font-size: 13px; color: #555; margin: 0 0 10px; text-align: center; }
input { width: 100%; border: 1px solid #cfd4da; border-radius: 8px; padding: 10px 12px; font-size: 15px; }
.actions { display: flex; justify-content: center; gap: 12px; margin-top: 12px; }
.actions button { min-width: 110px; padding: 8px 12px; border-radius: 8px; border: 1px solid #c8c8c8; background: #fff; cursor: pointer; }
.actions .confirm { background: #0d6efd; color: #fff; border-color: #0d6efd; }
.actions .cancel:hover { background: #f3f3f3; }
</style>
