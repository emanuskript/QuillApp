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

    <!-- PDF-Style Viewer Section -->
    <div class="pdf-viewer">
      <object
        v-if="imageSrc"
        :data="imageSrc"
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
      imageSrc: "",
      annotating: false,
    };
  },
  async created() {
    if (!this.source) {
      console.error("No source provided for IIIFViewer.");
      alert("Invalid source provided. Returning to input page.");
      this.$router.push({ name: "IIIFInput" });
      return;
    }

    console.log("Source received:", this.source);

    if (this.source.endsWith("manifest.json")) {
      await this.fetchIIIFImage(this.source);
    } else {
      this.imageSrc = this.source;
      this.annotating = true;
    }
  },
  methods: {
    async fetchIIIFImage(manifestUrl) {
      try {
        const response = await fetch(manifestUrl);
        if (!response.ok) {
          throw new Error("Failed to fetch IIIF manifest.");
        }
        const manifest = await response.json();
        console.log("IIIF manifest fetched:", manifest);

        const firstCanvas = manifest.sequences?.[0]?.canvases?.[0];
        if (
          firstCanvas &&
          firstCanvas.images?.[0]?.resource?.service?.["@id"]
        ) {
          const iiifImageApiUrl = firstCanvas.images[0].resource.service["@id"];
          this.imageSrc = `${iiifImageApiUrl}/full/full/0/default.jpg`;
          this.annotating = true;
        } else {
          alert("No image found in IIIF manifest.");
        }
      } catch (error) {
        alert("Error fetching IIIF manifest: " + error.message);
      }
    },
    selectTool(tool) {
      console.log(`Selected tool: ${tool}`);
    },
    saveAnnotations() {
      console.log("Annotations saved.");
    },
    clearAnnotations() {
      console.log("Annotations cleared.");
    },
    addMorePages() {
      console.log("Add more pages.");
    },
    discardPage() {
      console.log("Discard current page.");
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
  justify-content: center;
  align-items: center;
  background-color: #f1f1f1;
  border-bottom: 1px solid #ddd;
  padding: 10px 0;
}

.logo {
  margin-right: 20px;
  height: 40px;
}

.toolbar {
  display: flex;
  gap: 20px;
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
