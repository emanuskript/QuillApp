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
        :style="{
          cursor:
            traceModeActive || measureModeActive ? 'crosshair' : 'default',
        }"
      />

      <!-- Cropped Image Pop-up -->
      <div
        v-if="croppedImage && !measurePopupVisible"
        class="blurred-background"
      >
        <div class="svg-popup">
          <h3>Interactive Cropped Image</h3>
          <svg
            :width="popupDimensions.width"
            :height="popupDimensions.height"
            @mousedown="startDrawing"
            @mousemove="dynamicTrace"
            @mouseup="endDrawing"
            @mouseleave="endDrawing"
            xmlns="http://www.w3.org/2000/svg"
            class="interactive-svg"
          >
            <!-- Render cropped image -->
            <foreignObject
              :width="popupDimensions.width"
              :height="popupDimensions.height"
            >
              <div v-html="croppedSvg"></div>
            </foreignObject>

            <!-- Render existing strokes -->
            <polyline
              v-for="(stroke, index) in strokes"
              :key="'stroke-' + index"
              :points="formatPoints(stroke.points)"
              :stroke="stroke.color"
              stroke-width="2"
              fill="none"
            ></polyline>

            <!-- Render dynamic path while drawing -->
            <polyline
              v-if="dynamicTracePath"
              :points="dynamicTracePath"
              stroke="red"
              stroke-width="2"
              fill="none"
            ></polyline>
          </svg>
          <div class="popup-buttons">
            <button @click="saveCroppedImage">Save</button>
            <button @click="discardCroppedImage">Discard</button>
          </div>
        </div>
      </div>

      <!-- Measurement Pop-up -->
      <div v-if="measurePopupVisible" class="blurred-background">
        <div class="svg-popup">
          <h3>Interactive Angle Measurement</h3>
          <svg
            :width="popupDimensions.width"
            :height="popupDimensions.height"
            xmlns="http://www.w3.org/2000/svg"
            class="interactive-svg"
            @mousedown="startAngleMeasurement"
            @mousemove="moveAnglePoint"
            @mouseup="stopAngleDragging"
            @mouseleave="stopAngleDragging"
          >
            <!-- Render cropped image -->
            <foreignObject
              :width="popupDimensions.width"
              :height="popupDimensions.height"
            >
              <div v-html="croppedSvg"></div>
            </foreignObject>

            <!-- Render draggable points -->
            <circle
              v-for="(point, index) in measurePoints"
              :key="'measure-point-' + index"
              :cx="point.x"
              :cy="point.y"
              r="8"
              fill="red"
              style="cursor: pointer"
            ></circle>

            <!-- Draw lines between points -->
            <line
              v-if="measurePoints.length >= 2"
              :x1="measurePoints[0].x"
              :y1="measurePoints[0].y"
              :x2="measurePoints[1].x"
              :y2="measurePoints[1].y"
              stroke="blue"
              stroke-width="2"
            ></line>
            <line
              v-if="measurePoints.length === 3"
              :x1="measurePoints[1].x"
              :y1="measurePoints[1].y"
              :x2="measurePoints[2].x"
              :y2="measurePoints[2].y"
              stroke="blue"
              stroke-width="2"
            ></line>

            <!-- Angle Display -->
            <text
              v-if="measurePoints.length === 3"
              :x="measurePoints[1].x + 10"
              :y="measurePoints[1].y - 10"
              font-size="16"
              fill="white"
            >
              {{ calculatedAngle.toFixed(2) }}°
            </text>
          </svg>
          <div class="popup-buttons">
            <button @click="closeMeasurePopup">Close</button>
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
      startPoint: null,
      currentSquare: null,
      croppedSvg: null,
      croppedImage: null,
      squareVisible: false,
      imageLoaded: false,
      croppingStarted: false,
      annotations: [],
      popupDimensions: { width: 0, height: 0 },
      strokes: [],
      currentStroke: null,
      dynamicTracePath: "",
      measurePoints: [], // Points for angle measurement
      draggingPoint: -1, // Index of the point being dragged
      calculatedAngle: 0, // Measured angle between the points
      measureModeActive: false,
      traceModeActive: false,
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
    formatPoints(points) {
      return points.map(({ x, y }) => `${x},${y}`).join(" ");
    },

    calculateAngle(pt1, pt2, pt3) {
      const v1 = { x: pt1.x - pt2.x, y: pt1.y - pt2.y };
      const v2 = { x: pt3.x - pt2.x, y: pt3.y - pt2.y };

      const dotProduct = v1.x * v2.x + v1.y * v2.y;
      const magnitude1 = Math.sqrt(v1.x ** 2 + v1.y ** 2);
      const magnitude2 = Math.sqrt(v2.x ** 2 + v2.y ** 2);

      const angleRad = Math.acos(dotProduct / (magnitude1 * magnitude2));
      let angleDeg = (angleRad * 180) / Math.PI;

      return angleDeg.toFixed(2); // Return as fixed decimal
    },

    discardCroppedImage() {
      this.croppedImage = null;
      this.croppedSvg = null;
      this.strokes = [];
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
      if (tool === "trace") {
        this.traceModeActive = true;
        this.measureModeActive = false;
      } else if (tool === "measure") {
        this.measureModeActive = true;
        this.traceModeActive = false;
        this.croppingStarted = false; // Prepare for cropping
        this.startPoint = null; // Reset cropping points
      } else {
        this.traceModeActive = false;
        this.measureModeActive = false;
      }
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
        this.croppingStarted = true;
      } else {
        this.generateCroppedSvg();
        this.croppingStarted = false;
        this.traceModeActive = false;
      }
    },
    trace(event) {
      if (!this.croppingStarted || !this.startPoint) return;
      const { x, y } = this.getMousePosition(event);

      this.currentSquare = {
        x: Math.min(x, this.startPoint.x),
        y: Math.min(y, this.startPoint.y),
        width: Math.abs(x - this.startPoint.x),
        height: Math.abs(y - this.startPoint.y),
      };
    },
    getMousePosition(event) {
      const imageElement = this.$refs.image;
      const rect = imageElement.getBoundingClientRect();
      return { x: event.clientX - rect.left, y: event.clientY - rect.top };
    },
    generateCroppedSvg() {
      const { x, y, width, height } = this.currentSquare;
      const imageElement = this.$refs.image;
      const naturalWidth = imageElement.naturalWidth;
      const naturalHeight = imageElement.naturalHeight;
      const rect = imageElement.getBoundingClientRect();
      const scaleX = naturalWidth / rect.width;
      const scaleY = naturalHeight / rect.height;

      const scaledX = x * scaleX;
      const scaledY = y * scaleY;
      const scaledWidth = width * scaleX;
      const scaledHeight = height * scaleY;

      const popupWidth = (window.innerWidth * 2) / 3;
      const popupHeight = (scaledHeight / scaledWidth) * popupWidth;

      this.croppedSvg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${scaledWidth} ${scaledHeight}" width="${popupWidth}" height="${popupHeight}">
        <image href="${
          this.currentImage
        }" x="${-scaledX}" y="${-scaledY}" width="${naturalWidth}" height="${naturalHeight}" />
      </svg>
      `;
      this.popupDimensions = { width: popupWidth, height: popupHeight };
      this.croppedImage = true;
    },
    startDrawing(event) {
      const { x, y } = this.getPopupMousePosition(event);
      this.currentStroke = {
        points: [{ x, y }],
        color: this.generateRandomColor(),
      };
      this.dynamicTracePath = `M${x},${y}`; // Initialize dynamic path
    },
    generateRandomColor() {
      const hue = Math.floor(Math.random() * 360);
      const saturation = 70 + Math.random() * 30;
      const lightness = 50 + Math.random() * 10;
      return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    },
    draw(event) {
      if (!this.currentStroke) return;
      const { x, y } = this.getPopupMousePosition(event);
      this.currentStroke.points.push({ x, y });
      this.dynamicTracePath += ` L${x},${y}`; // Update dynamic path
    },
    dynamicTrace(event) {
      if (!this.currentStroke) return; // Ensure a stroke is in progress
      const { x, y } = this.getPopupMousePosition(event);

      // Add the current point to the stroke
      this.currentStroke.points.push({ x, y });

      // Dynamically format the points to update the path
      this.dynamicTracePath = this.formatPoints(this.currentStroke.points);
    },
    endDrawing() {
      if (this.currentStroke) {
        this.strokes.push(this.currentStroke);
        this.currentStroke = null;
        this.dynamicTracePath = ""; // Reset dynamic path
      }
    },

    startAngleMeasurement(event) {
      if (this.measurePopupVisible) {
        const { x, y } = this.getPopupMousePosition(event);

        // Prevent adding duplicate points
        if (this.measurePoints.some((p) => Math.hypot(p.x - x, p.y - y) < 10)) {
          alert("Point too close to an existing one.");
          return;
        }

        if (this.measurePoints.length < 3) {
          this.measurePoints.push({ x, y });

          if (this.measurePoints.length === 3) {
            this.calculatedAngle = this.calculateAngle(
              this.measurePoints[0],
              this.measurePoints[1],
              this.measurePoints[2]
            );
          }
        } else {
          alert("Three points already selected. Drag to adjust.");
        }
      }
    },

    startDraggingAnglePoint(event) {
      const { x, y } = this.getPopupMousePosition(event);
      this.draggingPoint = this.findNearestPoint(x, y);
    },

    moveAnglePoint(event) {
      if (this.draggingPoint !== -1) {
        const { x, y } = this.getPopupMousePosition(event);
        this.measurePoints[this.draggingPoint] = { x, y };

        if (this.measurePoints.length === 3) {
          this.calculatedAngle = this.calculateAngle(
            this.measurePoints[0],
            this.measurePoints[1],
            this.measurePoints[2]
          );
        }
      }
    },

    stopAngleDragging() {
      if (this.draggingPoint !== -1) {
        this.draggingPoint = -1;

        if (this.measurePoints.length === 3) {
          this.calculatedAngle = this.calculateAngle(
            this.measurePoints[0],
            this.measurePoints[1],
            this.measurePoints[2]
          );
        }
      }
    },

    findNearestPoint(x, y, threshold = 10) {
      return this.measurePoints.findIndex(
        (point) =>
          Math.abs(point.x - x) < threshold && Math.abs(point.y - y) < threshold
      );
    },
    saveCroppedImage() {
      const { x, y, width, height } = this.currentSquare;
      const imageElement = this.$refs.image; // Reference to the image element
      const naturalWidth = imageElement.naturalWidth;
      const naturalHeight = imageElement.naturalHeight;
      const rect = imageElement.getBoundingClientRect();
      const scaleX = naturalWidth / rect.width;
      const scaleY = naturalHeight / rect.height;

      const scaledX = x * scaleX;
      const scaledY = y * scaleY;
      const scaledWidth = width * scaleX;
      const scaledHeight = height * scaleY;

      const canvas = document.createElement("canvas");
      canvas.width = scaledWidth;
      canvas.height = scaledHeight;
      const ctx = canvas.getContext("2d");

      const img = new Image();
      img.crossOrigin = "anonymous";
      img.src = this.currentImage;

      img.onload = () => {
        try {
          ctx.drawImage(
            img,
            scaledX,
            scaledY,
            scaledWidth,
            scaledHeight,
            0,
            0,
            scaledWidth,
            scaledHeight
          );

          this.strokes.forEach((stroke) => {
            ctx.strokeStyle = stroke.color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            stroke.points.forEach((point, index) => {
              const transformedX =
                (point.x - scaledX) * (canvas.width / scaledWidth);
              const transformedY =
                (point.y - scaledY) * (canvas.height / scaledHeight);

              if (index === 0) {
                ctx.moveTo(transformedX, transformedY);
              } else {
                ctx.lineTo(transformedX, transformedY);
              }
            });
            ctx.stroke();
          });

          canvas.toBlob((blob) => {
            const imageUrl = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = imageUrl;
            link.download = "cropped-image-with-drawings.png";
            link.click();
            URL.revokeObjectURL(imageUrl);
          });
        } catch (error) {
          console.error("Error saving image with drawings:", error);
        }
      };

      img.onerror = (error) => {
        console.error("Error loading the image:", error);
      };
    },

    getPopupMousePosition(event) {
      const svgElement = event.target.closest("svg");
      if (!svgElement) {
        console.error("SVG element not found.");
        return { x: 0, y: 0 };
      }
      const rect = svgElement.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      return { x, y };
    },
    clearAnnotations() {
      this.strokes = [];
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

.cropping-rectangle {
  position: absolute;
  border: 2px dashed #007bff;
  background-color: rgba(0, 123, 255, 0.2);
  pointer-events: none;
  z-index: 100;
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

.interactive-svg {
  cursor: crosshair;
  pointer-events: all;
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