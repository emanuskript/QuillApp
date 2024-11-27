<template>
  <div class="viewer-container">
    <!-- Top Bar -->
    <div class="top-bar">
      <img src="@/assets/logo.png" alt="Logo" class="logo" />
      <div class="toolbar">
        <div class="toolbar-item" @click="selectTool('highlight')">
          <i class="fa-solid fa-highlighter"></i>
          <span>Highlight</span>
        </div>
        <div class="toolbar-item" @click="selectTool('underline')">
          <i class="fa-solid fa-underline"></i>
          <span>Underline</span>
        </div>
        <div class="toolbar-item" @click="selectTool('comment')">
          <i class="fa-regular fa-comment"></i>
          <span>Comment</span>
        </div>
        <div class="toolbar-item" @click="selectTool('trace')">
          <i class="fa-solid fa-pencil"></i>
          <span>Trace</span>
        </div>
        <div class="toolbar-item" @click="selectTool('measure')">
          <i class="fa-solid fa-ruler"></i>
          <span>Measure</span>
        </div>
        <div class="toolbar-item" @click="saveAnnotations">
          <i class="fa-solid fa-save"></i>
          <span>Save</span>
        </div>
        <div class="toolbar-item" @click="clearAnnotations">
          <i class="fa-regular fa-trash-can"></i>
          <span>Clear</span>
        </div>
        <div class="toolbar-item" @click="addMorePages">
          <i class="fa-solid fa-plus-circle"></i>
          <span>Add more</span>
        </div>
        <div class="toolbar-item" @click="discardPage">
          <i class="fa-solid fa-ban"></i>
          <span>Discard Page</span>
        </div>
      </div>
    </div>

    <!-- Page Navigation -->
    <div class="navigation-bar">
      <button :disabled="currentPage === 0" @click="prevPage">⬅️ Prev</button>
      <div class="page-input-container">
        <label for="pageInput">Page:</label>
        <input
          id="pageInput"
          type="number"
          v-model.number="pageInput"
          @blur="goToPage()"
          @keyup.enter="goToPage()"
          :max="totalPages"
          :min="1"
        />
        <span>/ {{ totalPages }}</span>
      </div>
      <button :disabled="currentPage === totalPages - 1" @click="nextPage">
        Next ➡️
      </button>
    </div>

    <!-- Viewer Section -->
    <div
      class="pdf-viewer"
      @mousedown="startTrace"
      @mousemove="trace"
      @mouseup="endTrace"
      @mouseleave="endTrace"
      ref="viewer"
    >
      <img
        v-if="currentImage"
        :src="currentImage"
        ref="image"
        class="image-viewer"
        @load="handleImageLoad"
        :style="{ cursor: traceModeActive ? 'crosshair' : 'default' }"
      />

      <!-- Visualize square during draw -->
      <div
        v-if="squareVisible && currentSquare"
        class="drawing-square"
        :style="{
          top: currentSquare.y + 'px',
          left: currentSquare.x + 'px',
          width: currentSquare.width + 'px',
          height: currentSquare.height + 'px',
        }"
      ></div>

      <!-- Cropped Image Pop-up -->
      <div v-if="croppedImage" class="blurred-background">
        <div class="svg-popup">
          <h3>Cropped SVG Area</h3>
          <div v-html="croppedSvg"></div>
          <div class="popup-buttons">
            <button @click="saveCroppedImage">Save</button>
            <button @click="discardCroppedImage">Discard</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    source: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      images: [],
      currentPage: 0,
      pageInput: 1,
      traceModeActive: false,
      startPoint: null,
      currentSquare: null,
      croppedSvg: null,
      croppedImage: null,
      squareVisible: false,
      imageLoaded: false,
      croppingStarted: false,
      annotations: [],
      popupDimensions: { width: 0, height: 0 }, // Popup dimensions for SVG
    };
  },
  computed: {
    currentImage() {
      return this.images[this.currentPage] || null;
    },
    totalPages() {
      return this.images.length;
    },
  },
  watch: {
    currentPage(newValue) {
      this.pageInput = newValue + 1;
    },
  },
  async created() {
    if (!this.source) {
      console.error("No source provided for IIIFViewer.");
      alert("Invalid source provided. Returning to input page.");
      this.$router.push({ name: "IIIFInput" });
      return;
    }

    if (this.source.endsWith("manifest.json")) {
      await this.fetchIIIFImages(this.source);
    } else {
      this.images = [this.source];
    }
  },
  methods: {
    async fetchIIIFImages(manifestUrl) {
      try {
        const response = await fetch(manifestUrl);
        if (!response.ok) throw new Error("Failed to fetch IIIF manifest.");
        const manifest = await response.json();

        const canvases = manifest.sequences?.[0]?.canvases || [];
        this.images = canvases
          .map((canvas) => canvas.images?.[0]?.resource?.service?.["@id"])
          .filter((id) => id)
          .map((id) => `${id}/full/full/0/default.jpg`);

        if (this.images.length === 0) {
          alert("No images found in IIIF manifest.");
        }
      } catch (error) {
        alert("Error fetching IIIF manifest: " + error.message);
      }
    },

    nextPage() {
      if (this.currentPage < this.totalPages - 1) this.currentPage++;
    },
    prevPage() {
      if (this.currentPage > 0) this.currentPage--;
    },
    goToPage() {
      const newPage =
        Math.max(1, Math.min(this.pageInput, this.totalPages)) - 1;
      this.currentPage = newPage;
    },
    selectTool(tool) {
      this.traceModeActive = tool === "trace";
      this.croppedImage = null;
    },

    handleImageLoad() {
      this.imageLoaded = true;
    },

    startTrace(event) {
      if (!this.traceModeActive || !this.imageLoaded) return;

      const { x, y } = this.getMousePosition(event);

      if (!this.croppingStarted) {
        this.startPoint = { x, y };
        this.currentSquare = { x, y, width: 0, height: 0 };
        this.squareVisible = true;
        this.croppingStarted = true;
      } else {
        this.generateCroppedSvg();
        this.squareVisible = false;
        this.croppingStarted = false;
        this.traceModeActive = false; // Disable trace mode after cropping
        console.log("Mouse Position:", { x, y });
        console.log("Square Position:", this.currentSquare);
      }
    },

    trace(event) {
      if (!this.croppingStarted || !this.startPoint) return;

      const { x, y } = this.getMousePosition(event);

      this.currentSquare = {
        x: this.startPoint.x,
        y: this.startPoint.y,
        width: Math.abs(x - this.startPoint.x),
        height: Math.abs(y - this.startPoint.y),
      };
    },

    getMousePosition(event) {
      const imageElement = this.$refs.image;
      const rect = imageElement.getBoundingClientRect();

      return {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
    },

    generateCroppedSvg() {
      const { x, y, width, height } = this.currentSquare;

      const imageElement = this.$refs.image;
      const naturalWidth = imageElement.naturalWidth;
      const naturalHeight = imageElement.naturalHeight;
      const rect = imageElement.getBoundingClientRect();

      // Scale the coordinates to the natural dimensions
      const scaleX = naturalWidth / rect.width;
      const scaleY = naturalHeight / rect.height;

      const scaledX = x * scaleX;
      const scaledY = y * scaleY;
      const scaledWidth = width * scaleX;
      const scaledHeight = height * scaleY;

      // Ensure the SVG is 2/3 the size of the PDF viewer
      const viewerWidth = this.$refs.viewer.clientWidth;
      const viewerHeight = this.$refs.viewer.clientHeight;
      const svgWidth = viewerWidth * 0.66;
      const svgHeight = viewerHeight * 0.66;

      this.croppedSvg = `
      <svg width="${svgWidth}" height="${svgHeight}" viewBox="0 0 ${scaledWidth} ${scaledHeight}" xmlns="http://www.w3.org/2000/svg">
      <image href="${
        this.currentImage
      }" x="${-scaledX}" y="${-scaledY}" width="${naturalWidth}" height="${naturalHeight}" />
      </svg>
      `;

      this.popupDimensions = { width: svgWidth, height: svgHeight };
      this.croppedImage = true;
    },

    saveCroppedImage() {
      console.log("SVG image saved.");
      this.croppedImage = null;
    },

    discardCroppedImage() {
      this.croppedImage = null;
    },

    clearAnnotations() {
      if (confirm("Are you sure you want to clear all annotations?")) {
        this.annotations = [];
        console.log("Annotations cleared.");
      }
    },
    addMorePages() {
      console.log("Adding more pages.");
      alert("Feature not yet implemented.");
    },
    discardPage() {
      if (confirm("Are you sure you want to discard this page?")) {
        this.images.splice(this.currentPage, 1);
        this.currentPage = Math.min(this.currentPage, this.images.length - 1);
      }
    },
  },
};
</script>

<style scoped>
.viewer-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f1f1f1;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f1f1f1;
  border-bottom: 1px solid #ddd;
  padding: 10px 20px;
}

.logo {
  height: 60px;
}

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
}

.toolbar-item:hover {
  color: #007bff;
}

.navigation-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 10px 0;
  gap: 10px;
}

.page-input-container {
  display: flex;
  align-items: center;
  gap: 5px;
}

.page-input-container input {
  width: 50px;
  text-align: center;
}

.pdf-viewer {
  position: relative;
  width: 100vw;
  height: 90vh;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pdf-viewer img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.drawing-square {
  position: absolute;
  border: 2px dashed #007bff;
  background-color: rgba(0, 123, 255, 0.2);
  pointer-events: none;
}

.blurred-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  backdrop-filter: blur(8px);
}

.svg-popup {
  background-color: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  max-width: 66%;
  max-height: 66%;
}
</style>