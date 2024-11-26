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
    <div class="pdf-viewer">
      <img
        v-if="currentImage"
        :src="currentImage"
        ref="image"
        @mousedown="startTrace"
        @mousemove="trace"
        @mouseup="endTrace"
        @load="handleImageLoad"
        class="image-viewer"
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
          <h3>Cropped Image</h3>
          <img :src="croppedImage" alt="Cropped Image" />
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
      images: [], // Store all image URLs
      currentPage: 0, // Current page index
      pageInput: 1, // Input for page navigation
      traceModeActive: false, // Trace Mode status
      showTraceMessage: true, // Show trace message initially
      startPoint: null, // Starting point for the crop
      currentSquare: null, // The square being drawn
      croppedImage: null, // Cropped image to display in the pop-up
      squareVisible: false, // Control square visibility
      imageLoaded: false, // Check if image has loaded
      annotations: [], // Store annotations like highlights or comments
    };
  },
  computed: {
    currentImage() {
      return this.images[this.currentPage] || null; // Get current image URL
    },
    totalPages() {
      return this.images.length;
    },
  },
  watch: {
    currentPage(newValue) {
      this.pageInput = newValue + 1; // Sync page number
    },
    traceModeActive(active) {
      if (active) {
        this.showTraceMessage = true;
        setTimeout(() => {
          this.showTraceMessage = false;
        }, 3000);
      }
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
      this.images = [this.source]; // Load a single image
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
      this.croppedImage = null; // Clear previous crop
    },
    startTrace(event) {
      if (!this.traceModeActive || !this.imageLoaded) return;

      const imageElement = this.$refs.image;
      const rect = imageElement.getBoundingClientRect();

      // Ensure click is within bounds of the image
      if (
        event.clientX < rect.left ||
        event.clientX > rect.right ||
        event.clientY < rect.top ||
        event.clientY > rect.bottom
      ) {
        return;
      }

      // Calculate relative coordinates
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      this.startPoint = { x, y };
      this.currentSquare = { x, y, width: 0, height: 0 };
      this.squareVisible = true;
    },
    trace(event) {
      if (!this.traceModeActive || !this.startPoint) return;

      const imageElement = this.$refs.image;
      const rect = imageElement.getBoundingClientRect();

      // Ensure movement is within bounds of the image
      const x = Math.min(Math.max(event.clientX - rect.left, 0), rect.width);
      const y = Math.min(Math.max(event.clientY - rect.top, 0), rect.height);

      const width = Math.abs(x - this.startPoint.x);
      const height = Math.abs(y - this.startPoint.y);

      this.currentSquare = {
        x: Math.min(this.startPoint.x, x),
        y: Math.min(this.startPoint.y, y),
        width,
        height,
      };
    },
    endTrace() {
      if (!this.traceModeActive || !this.currentSquare) return;

      this.cropImage();
      this.squareVisible = false;
    },
    cropImage() {
      const imageElement = this.$refs.image;
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");

      // Scale factor for natural image size
      const naturalWidth = imageElement.naturalWidth;
      const naturalHeight = imageElement.naturalHeight;
      const displayWidth = imageElement.width;
      const displayHeight = imageElement.height;

      const scaleX = naturalWidth / displayWidth;
      const scaleY = naturalHeight / displayHeight;

      // Set canvas size
      canvas.width = this.currentSquare.width * scaleX;
      canvas.height = this.currentSquare.height * scaleY;

      // Draw cropped area on canvas
      context.drawImage(
        imageElement,
        this.currentSquare.x * scaleX,
        this.currentSquare.y * scaleY,
        this.currentSquare.width * scaleX,
        this.currentSquare.height * scaleY,
        0,
        0,
        canvas.width,
        canvas.height
      );

      // Convert canvas to image data
      this.croppedImage = canvas.toDataURL();
    },
    saveCroppedImage() {
      console.log("Image saved.");
      this.croppedImage = null; // Clear after save
    },
    discardCroppedImage() {
      this.croppedImage = null; // Clear pop-up
    },
    saveAnnotations() {
      console.log("Annotations saved:", this.annotations);
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
    handleImageLoad() {
      this.imageLoaded = true; // Image is fully loaded
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
  overflow: hidden;
}

.pdf-viewer img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.drawing-square {
  position: absolute;
  border: 2px dashed #007bff;
  background-color: rgba(0, 123, 255, 0.2); /* Light blue overlay */
}

.pdf-object {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.trace-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
}

.trace-message {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
}

/* Blurred background for when the SVG square is shown */
.blurred-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  backdrop-filter: blur(8px); /* Blur */
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Popup for the drawn square (SVG) */
.svg-popup {
  background-color: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.svg-popup img {
  max-width: 100%;
  max-height: 100%;
  border: 1px solid #ddd;
}

.popup-buttons {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}

.popup-buttons button {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 5px;
  cursor: pointer;
}

.popup-buttons button:hover {
  background-color: #0056b3;
}

.popup-buttons button:active {
  background-color: #004085; /* Even darker on click */
}

.image-viewer {
  position: relative;
  max-width: 100%;
  max-height: 100%;
}

.cropped-image-popup {
  position: fixed;
  top: 10%;
  left: 10%;
  background: white;
  padding: 20px;
  border: 1px solid #ddd;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
}
</style>
