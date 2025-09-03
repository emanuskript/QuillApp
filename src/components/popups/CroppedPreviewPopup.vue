<template>
  <div v-if="croppedImage" class="cropped-popup">
    <div class="cropped-popup-content">
      <h3>Cropped Image</h3>
      <hr class="popup-divider" />

      <div
        class="cropped-image-container"
        ref="croppedContainer"
        @mousedown="$emit('start-annotation', $event)"
        @mousemove="$emit('move-annotation', $event)"
        @mouseup="$emit('end-annotation')"
        @mouseleave="$emit('end-annotation')"
      >
        <img
          :src="croppedImage"
          alt="Cropped"
          class="cropped-image"
          draggable="false"
        />

        <!-- Default slot for annotation overlays -->
        <slot></slot>
      </div>

      <div class="popup-actions">
        <button @click="$emit('save-png')">Save as PNG</button>
        <button @click="$emit('save-svg')">Save as SVG</button>
        <button @click="$emit('save-annotated')">Save with Annotations</button>
        <button @click="$emit('close')">Close</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "CroppedPreviewPopup",
  props: {
    croppedImage: { type: String, default: null },
  },
};
</script>

<style scoped>
.cropped-popup {
  position: fixed;
  inset: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.3);
  z-index: 1000;
}

.cropped-popup-content {
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  padding: 20px;
  width: 80%;
  max-width: 900px;
  text-align: center;
}

.cropped-image-container {
  position: relative;
  display: inline-block;
  width: 100%;
}

.cropped-image {
  display: block;
  width: 100%;
  height: auto;
}

.popup-actions {
  margin-top: 20px;
  display: flex;
  justify-content: space-evenly;
}

.popup-actions button {
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.popup-actions button:hover {
  background-color: #0056b3;
}
</style>
