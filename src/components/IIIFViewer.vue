<template>
  <div class="viewer-container">
    <!-- Top Bar -->
    <div class="top-bar">
      <img src="@/assets/logo.png" alt="Logo" class="logo" />
      <div class="toolbar">
        <!-- Highlight -->
        <div class="toolbar-item" @click="selectTool('highlight')">
          <i class="fa-solid fa-highlighter"></i>
          <span>Highlight</span>
        </div>

        <!-- Underline -->
        <div class="toolbar-item" @click="selectTool('underline')">
          <i class="fa-solid fa-underline"></i>
          <span>Underline</span>
        </div>

        <!-- Comment -->
        <div class="toolbar-item" @click="selectTool('comment')">
          <i class="fa-regular fa-comment"></i>
          <span>Comment</span>
        </div>

        <!-- Trace -->
        <div class="toolbar-item" @click="selectTool('trace')">
          <i class="fa-solid fa-pencil"></i>
          <span>Trace</span>
        </div>

        <!-- Measure -->
        <div class="toolbar-item" @click="selectTool('measure')">
          <i class="fa-solid fa-ruler"></i>
          <span>Measure</span>
        </div>

        <!-- Save -->
        <div class="toolbar-item" @click="saveAnnotations">
          <i class="fa-solid fa-save"></i>
          <span>Save</span>
        </div>

        <!-- Clear -->
        <div class="toolbar-item" @click="clearAnnotations">
          <i class="fa-regular fa-trash-can"></i>
          <span>Clear</span>
        </div>

        <!-- Add More -->
        <div class="toolbar-item" @click="addMorePages">
          <i class="fa-solid fa-plus-circle"></i>
          <span>Add more</span>
        </div>

        <!-- Discard Page -->
        <div class="toolbar-item" @click="discardPage">
          <i class="fa-solid fa-ban"></i>
          <span>Discard page</span>
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
      <object
        v-if="currentImage"
        :data="currentImage"
        type="image/jpeg"
        class="pdf-object"
      >
        <p>
          Unable to display the content. Please check the link or upload a valid
          image.
        </p>
      </object>
      <div v-else class="error-message">
        <p>
          Unable to load the image. Please provide a valid IIIF link or file.
        </p>
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
      images: [], // Array to store all image URLs
      currentPage: 0, // Index of the current page being displayed
      pageInput: 1, // Value bound to the text box for page input
    };
  },
  computed: {
    currentImage() {
      return this.images[this.currentPage] || null; // Get the image URL for the current page
    },
    totalPages() {
      return this.images.length;
    },
  },
  watch: {
    currentPage(newValue) {
      this.pageInput = newValue + 1; // Keep the text box value in sync with currentPage
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
      this.images = [this.source]; // If not a manifest, just load the single image
    }
  },
  methods: {
    async fetchIIIFImages(manifestUrl) {
      try {
        const response = await fetch(manifestUrl);
        if (!response.ok) {
          throw new Error("Failed to fetch IIIF manifest.");
        }
        const manifest = await response.json();

        // Extract all canvas images from the manifest
        const canvases = manifest.sequences?.[0]?.canvases || [];
        this.images = canvases
          .map((canvas) => canvas.images?.[0]?.resource?.service?.["@id"])
          .filter((id) => id) // Filter out invalid IDs
          .map((id) => `${id}/full/full/0/default.jpg`); // Generate IIIF image URLs

        if (this.images.length === 0) {
          alert("No images found in IIIF manifest.");
        }
      } catch (error) {
        alert("Error fetching IIIF manifest: " + error.message);
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages - 1) {
        this.currentPage++;
      }
    },
    prevPage() {
      if (this.currentPage > 0) {
        this.currentPage--;
      }
    },
    goToPage() {
      // Validate the page input and update the currentPage
      const newPage =
        Math.max(1, Math.min(this.pageInput, this.totalPages)) - 1;
      this.currentPage = newPage;
    },
    selectTool(tool) {
      console.log(`Selected tool: ${tool}`);
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
  flex: 2;
}

.toolbar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 12px;
  color: #333;
  cursor: pointer;
  text-align: center;
}

.toolbar-item i {
  font-size: 20px;
  margin-bottom: 5px;
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
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.pdf-viewer {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.pdf-object {
  width: 100%;
  height: 100%;
  border: none;
  object-fit: contain;
}
</style>
