<template>
  <div class="top-bar">
    <img src="@/assets/logo.png" alt="Logo" class="logo" />
    <div class="toolbar">
      <div class="toolbar-item" @click="$emit('select-tool', 'highlight')">
        <i class="fa-solid fa-highlighter"></i>
        <span>Highlight</span>
      </div>
      <div class="toolbar-item" @click="$emit('select-tool', 'underline')">
        <i class="fa-solid fa-underline"></i>
        <span>Underline</span>
      </div>
      <div class="toolbar-item" @click="$emit('select-tool', 'comment')">
        <i class="fa-regular fa-comment"></i>
        <span>Comment</span>
      </div>
      <div class="toolbar-item" @click="$emit('select-tool', 'trace')" data-tool="trace">
        <i class="fa-solid fa-pencil"></i>
        <span>Trace</span>
      </div>
      <div class="toolbar-item" @click="$emit('select-tool', 'measure')" data-tool="measure">
        <i class="fa-solid fa-angle-up"></i>
        <span>Measure</span>
        <span>Angle</span>
      </div>

      <!-- Horizontal / Vertical length popups -->
      <div class="toolbar-item" @click="$emit('show-length-popup', 'horizontal')">
        <i class="fa-solid fa-ruler-horizontal"></i>
        <span>Horizontal</span>
        <span>Bands</span>
      </div>
      <div class="toolbar-item" @click="$emit('show-length-popup', 'vertical')">
        <i class="fa-solid fa-ruler-vertical"></i>
        <span>Vertical</span>
        <span>Bands</span>
      </div>

      <div class="toolbar-item" @click="$emit('start-crop')">
        <i class="fa-solid fa-scissors"></i>
        <span>Crop</span>
      </div>

      <!-- Calculate menu -->
      <div class="toolbar-item calculate-container" @click.stop="$emit('toggle-calculate-dropdown')">
        <i class="fa-solid fa-calculator"></i>
        <span>Generate</span>
        <span>Statistics</span>
        <div v-if="showCalculateDropdown" class="calculate-dropdown">
          <div @click.stop="$emit('calculate-current-page')">
            Lengths Measurements (Current Page)
          </div>
          <div @click.stop="$emit('calculate-entire-document')">
            Lengths Measurements (Full Document)
          </div>
          <div @click.stop="$emit('calculate-angle-statistics')">
            Angle Measurements
          </div>
        </div>
      </div>

      <div class="toolbar-item" @click="$emit('save-annotations')">
        <i class="fa-solid fa-save"></i>
        <span>Save</span>
      </div>

      <!-- Clear menu -->
      <div class="toolbar-item clear-container" @click.stop="$emit('toggle-clear-dropdown')">
        <i class="fa-regular fa-trash-can"></i>
        <span>Clear</span>
        <div v-if="showClearDropdown" class="clear-dropdown">
          <div @click.stop="$emit('clear-highlights')">Clear Highlights</div>
          <div @click.stop="$emit('clear-underlines')">Clear Underlines</div>
          <div @click.stop="$emit('clear-comments')">Clear Comments</div>
          <div @click.stop="$emit('clear-traces')">Clear Traces</div>
          <div @click.stop="$emit('clear-angles')">Clear Angles</div>
          <div @click.stop="$emit('clear-horizontal-lengths')">Clear Horizontal Lengths</div>
          <div @click.stop="$emit('clear-vertical-lengths')">Clear Vertical Lengths</div>
          <div @click.stop="$emit('clear-all')">Clear All</div>
        </div>
      </div>
    </div>

    <div class="tool-message" v-if="toolMessage">{{ toolMessage }}</div>
  </div>
</template>

<script>
export default {
  name: "ViewerToolbar",
  props: {
    toolStates: { type: Object, default: () => ({}) },
    showCalculateDropdown: { type: Boolean, default: false },
    showClearDropdown: { type: Boolean, default: false },
    toolMessage: { type: String, default: "" },
  },
  emits: [
    "select-tool",
    "show-length-popup",
    "toggle-calculate-dropdown",
    "calculate-current-page",
    "calculate-entire-document",
    "calculate-angle-statistics",
    "save-annotations",
    "toggle-clear-dropdown",
    "clear-highlights",
    "clear-underlines",
    "clear-comments",
    "clear-traces",
    "clear-angles",
    "clear-horizontal-lengths",
    "clear-vertical-lengths",
    "clear-all",
    "start-crop",
  ],
};
</script>

<style scoped>
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f1f1f1;
  border-bottom: 1px solid #ddd;
  padding: 10px 20px;
}
.logo { height: 60px; }
.toolbar {
  display: flex;
  justify-content: center;
  gap: 30px;
  flex: 1;
}
.toolbar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 12px;
  color: #333;
  cursor: pointer;
  padding: 3px;
}
.toolbar-item:hover { color: #007bff; }
.tool-message {
  position: fixed;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  background-color: #007bff; color: white;
  padding: 10px 20px; border-radius: 5px; z-index: 1100;
  font-size: 14px; text-align: center;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
.calculate-container, .clear-container { position: relative; }
.calculate-dropdown, .clear-dropdown {
  position: absolute; top: 100%; left: 0;
  background-color: white; border: 1px solid #ccc; border-radius: 4px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1); z-index: 1100; min-width: 150px;
}
.calculate-dropdown div, .clear-dropdown div { padding: 8px 16px; cursor: pointer; }
.calculate-dropdown div:hover, .clear-dropdown div:hover { background-color: #f1f1f1; }
</style>
