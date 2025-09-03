<template>
  <div v-if="visible" class="length-popup" @keydown.esc="$emit('cancel')">
    <div class="length-popup-content" role="dialog" aria-modal="true" aria-label="Choose angle statistics scope">
      <h3 class="title">Angle Statistics</h3>

      <div class="section-title">Scope</div>
      <div class="options-grid wide">
        <button type="button" class="type-button" @click="$emit('confirm', { scope: 'current', label: null })">
          <span class="swatch big"></span>
          <span class="label">Current Page (All Labels)</span>
        </button>
        <button type="button" class="type-button" @click="$emit('confirm', { scope: 'entire', label: null })">
          <span class="swatch big"></span>
          <span class="label">Entire Document (All Labels)</span>
        </button>
      </div>

      <div class="section-title">By Label</div>
      <div v-if="labels && labels.length" class="options-grid">
        <button
          v-for="l in labels"
          :key="l"
          type="button"
          class="type-button"
          @click="$emit('confirm', { scope: 'byLabel', label: l })"
        >
          <span class="swatch"></span>
          <span class="label">{{ l }}</span>
        </button>
      </div>
      <div v-else class="empty">No labels yet — create one by measuring with a new label.</div>

      <div class="actions">
        <button class="cancel" type="button" @click="$emit('cancel')">Close</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "AngleStatsPickerPopup",
  props: {
    visible: { type: Boolean, default: false },
    labels: { type: Array, default: () => [] },
  },
};
</script>

<style scoped>
.length-popup { position: fixed; inset: 0; display: grid; place-items: center; background: rgba(0,0,0,.5); z-index: 1100; }
.length-popup-content { width: min(760px, 92vw); background: #fff; border-radius: 12px; box-shadow: 0 8px 28px rgba(0,0,0,.25); padding: 28px; }
.title { font-size: 28px; text-align: center; margin: 0 0 12px; }
.section-title { margin: 14px 4px 8px; font-weight: 600; color: #222; }
.options-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 10px; }
.options-grid.wide { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
.type-button { display: grid; justify-items: center; gap: 8px; padding: 12px 10px; border: 1px solid #d3d3d3; border-radius: 10px; background: #fafafa; cursor: pointer; }
.type-button:hover { border-color: #9ec9ff; background: #f6fbff; }
.swatch { width: 44px; height: 44px; border-radius: 8px; background: #e9ecef; border: 2px solid rgba(0,0,0,.08); }
.swatch.big { width: 58px; height: 58px; }
.label { font-size: 14px; color: #222; text-align: center; }
.empty { font-size: 14px; color: #666; margin: 6px 0 12px; }
.actions { display: flex; justify-content: center; margin-top: 10px; }
.actions .cancel { min-width: 120px; padding: 10px 14px; border-radius: 8px; border: 1px solid #c8c8c8; background: #fff; font-size: 16px; cursor: pointer; }
.actions .cancel:hover { background: #f3f3f3; }
</style>
