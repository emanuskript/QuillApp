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
          <i class="fa-solid fa-angle-up"></i>
          <span>Measure</span>
          <span>Angle</span>
        </div>
        <!-- New Length Button -->
        <div class="toolbar-item" @click="showLengthPopup('horizontal')">
          <i class="fa-solid fa-ruler-horizontal"></i>
          <span>Horizontal</span>
          <span>Bands</span>
        </div>

        <div class="toolbar-item" @click="showLengthPopup('vertical')">
          <i class="fa-solid fa-ruler-vertical"></i>
          <span>Vertical</span>
          <span>Bands</span>
        </div>

        <!-- Add the Calculate button -->
        <div
          class="toolbar-item calculate-container"
          @click.stop="toggleCalculateDropdown"
        >
          <i class="fa-solid fa-calculator"></i>
          <span>Calculate</span>
          <!-- Dropdown Menu -->
          <div v-if="showCalculateDropdown" class="calculate-dropdown">
            <div @click.stop="calculateCurrentPage">Calculate Current Page</div>
            <div @click.stop="calculateEntireDocument">
              Calculate Entire Document
            </div>
          </div>
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
    <!-- Horizontal Bands Popup -->
    <div v-if="showHorizontalPopup" class="length-popup">
      <div class="length-popup-content">
        <h3>Select Horizontal Measurement Type</h3>
        <select v-model="selectedMeasurement">
          <option value="ascenders">Ascenders</option>
          <option value="descenders">Descenders</option>
          <option value="interlinear">Interlinear Spaces</option>
          <option value="upperMargin">Upper Margin</option>
          <option value="lowerMargin">Lower Margin</option>
        </select>
        <div class="color-preview">
          <div style="padding: 10px; text-align: center">
            <div style="font-size: 12px; margin-bottom: 10px">Ascenders</div>
            <div
              :style="{ backgroundColor: measurementColors.ascenders }"
              class="color-box"
              style="margin: 0 auto"
            ></div>
          </div>
          <div style="padding: 10px; text-align: center">
            <div style="font-size: 12px; margin-bottom: 10px">Descenders</div>
            <div
              :style="{ backgroundColor: measurementColors.descenders }"
              class="color-box"
              style="margin: 0 auto"
            ></div>
          </div>
          <div style="padding: 10px; text-align: center">
            <div style="font-size: 12px; margin-bottom: 10px">Interlinear</div>
            <div
              :style="{ backgroundColor: measurementColors.interlinear }"
              class="color-box"
              style="margin: 0 auto"
            ></div>
          </div>
          <div style="padding: 10px; text-align: center">
            <div style="font-size: 12px; margin-bottom: 10px">Upper Margin</div>
            <div
              :style="{ backgroundColor: measurementColors.upperMargin }"
              class="color-box"
              style="margin: 0 auto"
            ></div>
          </div>
          <div style="padding: 10px; text-align: center">
            <div style="font-size: 12px; margin-bottom: 10px">Lower Margin</div>
            <div
              :style="{ backgroundColor: measurementColors.lowerMargin }"
              class="color-box"
              style="margin: 0 auto"
            ></div>
          </div>
        </div>
        <button @click="confirmLengthMeasurement">Confirm</button>
        <button @click="hideLengthPopup">Cancel</button>
      </div>
    </div>

    <!-- Vertical Bands Popup -->
    <div v-if="showVerticalPopup" class="length-popup">
      <div class="length-popup-content">
        <h3>Select Vertical Measurement Type</h3>
        <select v-model="selectedMeasurement">
          <option value="internalMargin">Internal Margin</option>
          <option value="intercolumnSpaces">Intercolumn Spaces</option>
        </select>
        <div class="color-preview">
          <div style="padding: 10px; text-align: center">
            <div style="font-size: 12px; margin-bottom: 10px">
              InternalMargin
            </div>
            <div
              :style="{ backgroundColor: measurementColors.internalMargin }"
              class="color-box"
              style="margin: 0 auto"
            ></div>
          </div>
          <div style="padding: 10px; text-align: center">
            <div style="font-size: 12px; margin-bottom: 10px">
              IntercolumnSpaces
            </div>
            <div
              :style="{ backgroundColor: measurementColors.intercolumnSpaces }"
              class="color-box"
              style="margin: 0 auto"
            ></div>
          </div>
        </div>
        <button @click="confirmLengthMeasurement">Confirm</button>
        <button @click="hideLengthPopup">Cancel</button>
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
            traceModeActive ||
            highlightModeActive ||
            underlineModeActive ||
            measureModeActive
              ? 'crosshair'
              : 'default',
        }"
      />

      <!-- Render dynamic length measurement rectangle -->
      <div
        v-if="isMeasuring && currentSquare"
        class="length-measurement"
        :style="{
          left: `${currentSquare.x}px`,
          top: `${currentSquare.y}px`,
          width: `${currentSquare.width}px`,
          height: `${currentSquare.height}px`,
          backgroundColor: currentSquare.color,
          position: 'absolute',
        }"
      >
        <div class="length-label">
          {{ currentSquare.label }}: {{ currentSquare.height }}px
        </div>
      </div>

      <!-- Render finalized length measurements -->
      <div
        v-for="(measurement, index) in currentPageLengthMeasurements"
        :key="'length-' + index"
        class="length-measurement"
        :style="{
          left: `${measurement.x}px`,
          top: `${measurement.y}px`,
          width: `${measurement.width}px`,
          height: `${measurement.height}px`,
          backgroundColor: measurement.color,
          position: 'absolute',
          border: '1px solid black', // Add a border for better visibility
        }"
      >
        <div class="length-label">
          {{ measurement.label }}:
          {{
            measurement.label === "ascenders" ||
            measurement.label === "descenders" ||
            measurement.label === "interlinear" ||
            measurement.label === "upperMargin" ||
            measurement.label === "lowerMargin"
              ? measurement.height
              : measurement.width
          }}px
        </div>
      </div>

      <!-- Statistics Popup -->
      <div v-if="showStatistics" class="statistics-popup">
        <div class="statistics-popup-content">
          <h3>Statistics</h3>

          <!-- Horizontal Lengths -->
          <h4>Horizontal Lengths</h4>
          <table>
            <thead>
              <tr>
                <th>Measurement</th>
                <th>Average</th>
                <th>Standard Deviation</th>
                <th>Mode</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(stats, type) in horizontalStatistics" :key="type">
                <td>{{ type }}</td>
                <td>{{ stats.average.toFixed(2) }}</td>
                <td>{{ stats.standardDeviation.toFixed(2) }}</td>
                <td>
                  {{
                    typeof stats.mode === "number"
                      ? stats.mode.toFixed(2)
                      : stats.mode
                  }}
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Vertical Lengths -->
          <h4>Vertical Lengths</h4>
          <table>
            <thead>
              <tr>
                <th>Measurement</th>
                <th>Average</th>
                <th>Standard Deviation</th>
                <th>Mode</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(stats, type) in verticalStatistics" :key="type">
                <td>{{ type }}</td>
                <td>{{ stats.average.toFixed(2) }}</td>
                <td>{{ stats.standardDeviation.toFixed(2) }}</td>
                <td>
                  {{
                    typeof stats.mode === "number"
                      ? stats.mode.toFixed(2)
                      : stats.mode
                  }}
                </td>
              </tr>
            </tbody>
          </table>

          <button @click="closeStatisticsPopup">Close</button>
        </div>
      </div>

      <!-- Render existing highlights -->
      <div
        v-for="(annotation, index) in currentPageHighlights"
        :key="'highlight-' + index"
        class="highlight-rectangle"
        :style="{
          left: `${annotation.x}px`,
          top: `${annotation.y}px`,
          width: `${annotation.width}px`,
          height: `${annotation.height}px`,
          position: 'absolute',
        }"
      ></div>

      <!-- Render dynamic highlight rectangle -->
      <div
        v-if="highlightModeActive && currentSquare"
        class="highlight-rectangle"
        :style="{
          left: `${currentSquare.x}px`,
          top: `${currentSquare.y}px`,
          width: `${currentSquare.width}px`,
          height: `${currentSquare.height}px`,
          position: 'absolute',
        }"
      ></div>

      <!-- Render existing underlines -->
      <div
        v-for="(annotation, index) in currentPageUnderlines"
        :key="'underline-' + index"
        class="underline-line"
        :style="{
          position: 'absolute',
          left: `${annotation.x}px`,
          top: `${annotation.y}px`,
          width: `${annotation.width}px`,
          height: '2px',
          backgroundColor: 'red',
        }"
      ></div>

      <!-- Render dynamic underline -->
      <div
        v-if="currentImage && underlineModeActive && currentUnderline"
        class="underline-line"
        :style="{
          position: 'absolute',
          left: `${currentUnderline.x}px`,
          top: `${currentUnderline.y}px`,
          width: `${currentUnderline.width}px`,
          height: '2px',
          backgroundColor: 'blue',
        }"
      ></div>

      <!-- Render existing comments -->
      <div
        v-for="(comment, index) in currentPageComments"
        :key="'comment-' + index"
        class="comment-container"
        :style="{
          top: comment.y + 'px',
          left: comment.x + 'px',
          position: 'absolute',
        }"
        @mousedown="startDraggingComment(index, $event)"
        @mouseup="stopDraggingComment"
        @mousemove="dragComment"
      >
        <div class="comment-icon">💬</div>
        <div class="comment-bubble">
          <div class="comment-content">{{ comment.text }}</div>
        </div>
      </div>

      <!-- Comment Input -->
      <div v-if="showCommentInput" class="comment-input-container">
        <textarea
          class="comment-input-box"
          v-model="currentCommentText"
          placeholder="Add your comment..."
        ></textarea>
        <div class="comment-input-actions">
          <button class="btn-save-comment" @click="addComment">Add</button>
          <button class="btn-cancel-comment" @click="cancelComment">
            Cancel
          </button>
        </div>
      </div>

      <!-- Cropping Rectangle -->
      <div
        v-if="croppingStarted && currentSquare"
        class="cropping-rectangle"
        :style="{
          left: `${currentSquare.x}px`,
          top: `${currentSquare.y}px`,
          width: `${currentSquare.width}px`,
          height: `${currentSquare.height}px`,
          position: 'absolute',
        }"
      ></div>

      <!-- Cropped Image Pop-up -->
      <div v-if="croppedImage" class="blurred-background">
        <div class="svg-popup">
          <h3>Interactive Cropped Image</h3>
          <svg
            :width="popupDimensions.width"
            :height="popupDimensions.height"
            @mousedown="startAnnotating"
            @mousemove="annotateImage"
            @mouseup="endAnnotating"
            @mouseleave="endAnnotating"
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

            <!-- Render draggable points for angle measurement -->
            <circle
              v-for="(point, index) in measurePoints"
              :key="'measure-point-' + index"
              :cx="point.x"
              :cy="point.y"
              r="8"
              fill="red"
              style="cursor: pointer"
              @mousedown="startDraggingPoint(index, $event)"
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
            <text
              v-if="measurePoints.length >= 2"
              :x="(measurePoints[0].x + measurePoints[1].x) / 2"
              :y="(measurePoints[0].y + measurePoints[1].y) / 2 - 10"
              font-size="12"
              fill="black"
            >
              {{
                calculateRelativeLength(
                  measurePoints[0],
                  measurePoints[1]
                ).toFixed(2)
              }}
              px
            </text>

            <line
              v-if="measurePoints.length === 3"
              :x1="measurePoints[1].x"
              :y1="measurePoints[1].y"
              :x2="measurePoints[2].x"
              :y2="measurePoints[2].y"
              stroke="blue"
              stroke-width="2"
            ></line>
            <text
              v-if="measurePoints.length === 3"
              :x="(measurePoints[1].x + measurePoints[2].x) / 2"
              :y="(measurePoints[1].y + measurePoints[2].y) / 2 - 10"
              font-size="12"
              fill="black"
            >
              {{
                calculateRelativeLength(
                  measurePoints[1],
                  measurePoints[2]
                ).toFixed(2)
              }}
              px
            </text>

            <!-- Angle Display -->
            <text
              v-if="measurePoints.length === 3"
              :x="measurePoints[1].x + 20"
              :y="measurePoints[1].y - 10"
              font-size="16"
              fill="black"
            >
              {{ calculatedAngle }}°
            </text>
          </svg>
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
import { PDFDocument } from "pdf-lib";
import html2canvas from "html2canvas";
export default {
  props: {
    source: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      showStatistics: false,
      images: [],
      horizontalStatistics: {}, // Stores horizontal statistics
      verticalStatistics: {},
      annotationsByPage: [],
      showCalculateDropdown: false,
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
      showLengthPopupVisible: false,
      showHorizontalPopup: false, // Controls visibility of the horizontal popup
      showVerticalPopup: false, // Controls visibility of the vertical popup
      measurementType: "vertical",
      selectedMeasurement: "ascenders",
      measurementColors: {
        ascenders: "rgba(0, 255, 0, 0.5)", // Transparent green
        descenders: "rgba(0, 0, 255, 0.5)", // Transparent blue
        interlinear: "rgba(255, 165, 0, 0.5)", // Transparent orange
        upperMargin: "rgba(255, 0, 0, 0.5)", // Transparent red
        lowerMargin: "rgba(128, 0, 128, 0.5)", // Transparent purple
        internalMargin: "rgba(0, 255, 255, 0.5)", // Transparent cyan
        intercolumnSpaces: "rgba(255, 0, 255, 0.5)", // Transparent magenta
      },
      statistics: {
        averageVertical: 0,
        standardDeviationVertical: 0,
        modeVertical: 0,
        averageHorizontal: 0,
        standardDeviationHorizontal: 0,
        modeHorizontal: 0,
      },
      lengthMeasurements: {
        ascenders: {},
        descenders: {},
        interlinear: {},
        upperMargin: {},
        lowerMargin: {},
        internalMargin: {},
        intercolumnSpaces: {},
      },
      currentStroke: null,
      dynamicTracePath: "",
      measurePoints: [], // Points for angle measurement
      draggingPoint: -1, // Index of the point being dragged
      calculatedAngle: 0, // Measured angle between the points
      measureModeActive: false,
      traceModeActive: false,
      commentModeActive: false,
      highlightModeActive: false, // Tracks if highlight mode is active
      underlineModeActive: false, // Tracks if underline mode is active
      currentUnderline: null, // Tracks current underline line being drawn
      currentHighlight: null, // Tracks current highlight box being drawn
      showCommentInput: false,
      currentCommentText: "",
      currentCommentPosition: null,
      comments: [],
      isMeasuring: false,
      draggingCommentIndex: null, // Index of the comment being dragged
      dragOffset: { x: 0, y: 0 }, // Offset between the mouse and comment position
      scalingFactor: 1,
    };
  },
  computed: {
    currentPageLengthMeasurements() {
      // Combine all measurements for the current page from all labels
      const measurements = [];
      for (const label in this.lengthMeasurements) {
        if (this.lengthMeasurements[label][this.currentPage]) {
          measurements.push(
            ...this.lengthMeasurements[label][this.currentPage]
          );
        }
      }
      return measurements;
    },
    currentPageHighlights() {
      return (
        this.annotationsByPage[this.currentPage]?.filter(
          (annotation) => annotation.type === "highlight"
        ) || []
      );
    },
    currentPageUnderlines() {
      return (
        this.annotationsByPage[this.currentPage]?.filter(
          (annotation) => annotation.type === "underline"
        ) || []
      );
    },
    currentPageComments() {
      return this.comments[this.currentPage] || [];
    },

    highlightAnnotations() {
      return this.annotations.filter(
        (annotation) => annotation.type === "highlight"
      );
    },
    underlineAnnotations() {
      return this.annotations.filter(
        (annotation) => annotation.type === "underline"
      );
    },
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
        } else {
          // Initialize annotationsByPage with empty arrays for each page
          this.annotationsByPage = new Array(this.images.length)
            .fill()
            .map(() => []);
        }
        this.comments = new Array(this.images.length).fill().map(() => []);
      } catch (error) {
        alert("Error fetching IIIF manifest: " + error.message);
      }
    },

    getMousePosition(event) {
      const viewerElement = this.$refs.viewer;
      if (!viewerElement) {
        console.error("Viewer element not available.");
        return { x: 0, y: 0 };
      }
      const rect = viewerElement.getBoundingClientRect();
      const scrollLeft = viewerElement.scrollLeft;
      const scrollTop = viewerElement.scrollTop;
      return {
        x: event.clientX - rect.left + scrollLeft,
        y: event.clientY - rect.top + scrollTop,
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
    calculateRelativeLength(p1, p2) {
      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      const realLength = Math.sqrt(dx * dx + dy * dy); // Real pixel length
      return realLength * this.scalingFactor; // Relative length
    },

    async generateCroppedSvg() {
      if (!this.currentSquare) {
        console.error("Cannot generate cropped SVG. currentSquare is null.");
        return;
      }

      const { x, y, width, height } = this.currentSquare;
      const imageElement = this.$refs.image;
      const naturalWidth = imageElement.naturalWidth;
      const naturalHeight = imageElement.naturalHeight;
      const rect = imageElement.getBoundingClientRect();
      const scaleX = naturalWidth / rect.width;
      const scaleY = naturalHeight / rect.height;

      const scaledX = (x - rect.left) * scaleX;
      const scaledY = y * scaleY;
      const scaledWidth = width * scaleX;
      const scaledHeight = height * scaleY;

      const popupWidth = (window.innerWidth * 2) / 3;
      const popupHeight = (scaledHeight / scaledWidth) * popupWidth;

      // Save the cropped SVG
      this.croppedSvg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${scaledWidth} ${scaledHeight}" width="${popupWidth}" height="${popupHeight}">
      <image href="${
        this.currentImage
      }" x="${-scaledX}" y="${-scaledY}" width="${naturalWidth}" height="${naturalHeight}" />
    </svg>
  `;

      // Set popup dimensions
      this.popupDimensions = { width: popupWidth, height: popupHeight };

      // Reset cropping state
      this.croppingStarted = false;
      this.currentSquare = null;
      this.startPoint = null;

      // Generate and display the cropped PNG
      await this.generateCroppedPng();
    },

    async generateCroppedPng() {
      if (!this.croppedSvg) {
        console.error("Cannot generate cropped PNG: No SVG available.");
        return;
      }

      // Create an image element from the SVG
      const svgBlob = new Blob([this.croppedSvg], { type: "image/svg+xml" });
      const svgUrl = URL.createObjectURL(svgBlob);

      const img = new Image();
      img.src = svgUrl;

      await new Promise((resolve, reject) => {
        img.onload = () => {
          // Create a canvas to render the PNG
          const canvas = document.createElement("canvas");
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext("2d");

          // Draw the SVG onto the canvas
          ctx.drawImage(img, 0, 0);

          // Convert the canvas to a PNG data URL
          const pngUrl = canvas.toDataURL("image/png");

          // Display the PNG in the popup
          this.croppedImage = pngUrl;

          // Clean up
          URL.revokeObjectURL(svgUrl);
          resolve();
        };

        img.onerror = (error) => {
          console.error("Error loading SVG:", error);
          reject(error);
        };
      });
    },
    discardCroppedImage() {
      this.croppedImage = null;
      this.croppedSvg = null;
      this.strokes = [];
      this.measurePoints = [];
      this.calculatedAngle = 0;
      // Reset cropping state
      this.croppingStarted = false;
      this.currentSquare = null;
      this.startPoint = null;
    },
    nextPage() {
      if (this.currentPage < this.totalPages - 1) {
        this.currentPage++;
        if (!this.comments[this.currentPage]) {
          this.comments[this.currentPage] = [];
        }
      }
    },
    prevPage() {
      if (this.currentPage > 0) {
        this.currentPage--;
        // Ensure commentsByPage is initialized for the new page
        if (!this.comments[this.currentPage]) {
          this.comments[this.currentPage] = [];
        }
      }
    },

    goToPage() {
      const newPage =
        Math.max(1, Math.min(this.pageInput, this.totalPages)) - 1;
      this.currentPage = newPage;
    },
    selectTool(tool) {
      if (!this.currentImage) {
        return;
      }
      this.currentTool = tool;
      if (tool === "trace") {
        this.traceModeActive = true;
        this.measureModeActive = false;
        this.croppedImage = false; // Reset croppedImage when Trace is selected
      } else if (tool === "measure") {
        this.measureModeActive = true;
        this.traceModeActive = false;
        this.croppedImage = false; // Reset croppedImage when Measure is selected
      } else if (tool === "highlight") {
        this.highlightModeActive = true;
      } else if (tool === "underline") {
        this.underlineModeActive = true;
        console.log("Underline mode activated");
      } else if (tool == "comment") {
        this.commentModeActive = true;
        const { x, y } = this.getMousePosition(event);
        this.currentCommentPosition = { x, y };
        this.showCommentInput = true;
      } else {
        this.traceModeActive = false;
        this.measureModeActive = false;
        this.highlightModeActive = false;
        this.underlineModeActive = false;
      }
    },
    handleImageLoad() {
      const imageElement = this.$refs.image;
      if (imageElement) {
        const displayedWidth = imageElement.width;
        const naturalWidth = imageElement.naturalWidth;
        this.scalingFactor = displayedWidth / naturalWidth;
      }
      this.imageLoaded = true;
    },

    startTrace(event) {
      if (
        this.croppedImage == null &&
        !this.highlightModeActive &&
        !this.underlineModeActive &&
        !this.traceModeActive &&
        this.measureModeActive
      ) {
        return; // Exit the function early
      }
      const { x, y } = this.getMousePosition(event);

      if (this.highlightModeActive) {
        if (!this.croppingStarted && event.button === 0) {
          // Start cropping
          const { x, y } = this.getMousePosition(event);
          this.startPoint = { x, y };
          this.currentSquare = { x, y, width: 0, height: 0 };
          this.croppingStarted = true;
        } else {
          // Finish cropping and add the highlight annotation
          this.annotationsByPage[this.currentPage].push({
            type: "highlight",
            ...this.currentSquare,
          });
          this.croppingStarted = false;
          this.highlightModeActive = false;
          this.currentSquare = null;
        }
      } else if (this.underlineModeActive) {
        if (!this.croppingStarted && event.button === 0) {
          console.log("Underline mode started");
          // Start underlining (underline mode)
          const { x, y } = this.getMousePosition(event);
          this.startPoint = { x, y };
          this.currentUnderline = {
            type: "underline",
            x: x,
            y: y,
            width: 0,
            height: 2,
            startX: 0,
            startY: 0,
            endX: 0,
            endY: 0,
          };
          console.log(this.currentUnderline);
          this.croppingStarted = true;
          this.traceModeActive = false;
          this.measureModeActive = false;
        } else {
          console.log(this.currentUnderline);
          this.annotationsByPage[this.currentPage].push(this.currentUnderline);
          this.croppingStarted = false;
          this.underlineModeActive = false;
          this.currentUnderline = null;
        }
      } else if (this.traceModeActive || this.measureModeActive) {
        if (!this.croppingStarted && !this.croppedImage) {
          this.startPoint = { x, y };
          this.currentSquare = { x, y, width: 0, height: 0 };
          this.croppingStarted = true;
        } else if (this.croppingStarted && !this.croppedImage) {
          this.generateCroppedSvg();
          this.croppingStarted = false;
          this.currentSquare = null;
          this.startPoint = null;
        }
      }
    },
    trace(event) {
      if (
        this.croppedImage == null &&
        !this.highlightModeActive &&
        !this.underlineModeActive &&
        !this.traceModeActive &&
        this.measureModeActive
      ) {
        return; // Exit the function early
      }
      const { x, y } = this.getMousePosition(event);

      if (
        this.croppingStarted &&
        (this.highlightModeActive ||
          this.traceModeActive ||
          this.measureModeActive)
      ) {
        const { x, y } = this.getMousePosition(event);

        this.currentSquare = {
          x: Math.min(x, this.startPoint.x),
          y: Math.min(y, this.startPoint.y),
          width: Math.abs(x - this.startPoint.x),
          height: Math.abs(y - this.startPoint.y),
        };
      } else if (this.underlineModeActive && this.currentUnderline) {
        console.log("Underline mode herererer");
        console.log(this.currentUnderline);
        this.currentUnderline.width = Math.abs(x - this.startPoint.x);
        this.currentUnderline.endX = x - this.currentUnderline.x; // Relative to the SVG container
        this.currentUnderline.endY = y - this.currentUnderline.y; // Relative to the SVG container
      }
    },
    endTrace() {
      if (this.highlightModeActive && this.croppingStarted) {
        this.annotations.push({
          type: "highlight",
          ...this.currentSquare,
        });
        this.croppingStarted = false;
        this.highlightModeActive = false;
        this.currentSquare = null;
      } else if (this.underlineModeActive && this.currentUnderline != null) {
        console.log(this.currentUnderline);

        this.annotations.push(this.currentUnderline);
        this.croppingStarted = false;
        this.underlineModeActive = false;
        this.currentUnderline = null;
      }
    },

    startComment(event) {
      const { x, y } = this.getMousePosition(event);
      this.currentCommentPosition = { x, y };
      this.showCommentInput = true;
    },

    addComment() {
      if (!this.currentCommentText) return;

      if (!this.comments[this.currentPage]) {
        this.comments[this.currentPage] = [];
      }

      this.comments[this.currentPage].push({
        text: this.currentCommentText,
        x: this.currentCommentPosition.x,
        y: this.currentCommentPosition.y + 100,
      });

      this.currentCommentText = "";
      this.showCommentInput = false;
    },

    cancelComment() {
      this.currentCommentText = "";
      this.currentCommentPosition = null;
      this.showCommentInput = false;
    },

    removeComment(index) {
      this.comments[this.currentPage].splice(index, 1);
    },

    showComment(comment) {
      this.tooltipContent = comment.text;
      this.tooltipPosition = { x: comment.x + 20, y: comment.y + 20 };
      this.tooltipVisible = true;
    },

    hideComment() {
      this.tooltipVisible = false;
      this.tooltipContent = "";
    },

    startDraggingComment(index, event) {
      this.draggingCommentIndex = index;

      // Calculate the offset between the mouse and comment position
      const comment = this.comments[this.currentPage][index];
      this.dragOffset = {
        x: event.clientX - comment.x,
        y: event.clientY - comment.y,
      };
    },

    dragComment(event) {
      if (this.draggingCommentIndex !== null) {
        const comment =
          this.comments[this.currentPage][this.draggingCommentIndex];
        comment.x = event.clientX - this.dragOffset.x;
        comment.y = event.clientY - this.dragOffset.y;
      }
    },

    // Stop dragging
    stopDraggingComment() {
      this.draggingCommentIndex = null;
    },

    startAnnotating(event) {
      if (this.measureModeActive) {
        this.startAngleMeasurement(event);
      } else if (this.traceModeActive) {
        this.startDrawing(event);
      }
    },
    annotateImage(event) {
      if (this.measureModeActive) {
        this.moveAnglePoint(event);
      } else if (this.traceModeActive) {
        this.dynamicTrace(event);
      }
    },
    endAnnotating() {
      if (this.measureModeActive) {
        this.stopAngleDragging();
      } else if (this.traceModeActive) {
        this.endDrawing();
      }
    },
    startDrawing(event) {
      const { x, y } = this.getPopupMousePosition(event);
      this.currentStroke = {
        points: [{ x, y }],
        color: this.generateRandomColor(),
      };
      this.dynamicTracePath = `M${x},${y}`;
    },
    generateRandomColor() {
      const colorBlindFriendlyPalette = [
        "#E69F00", // Orange
        "#56B4E9", // Sky Blue
        "#009E73", // Green
        "#F0E442", // Yellow
        "#0072B2", // Blue
        "#D55E00", // Vermillion
        "#CC79A7", // Reddish Purple
      ];

      if (!this.lastColor) {
        this.lastColor = null;
      }

      const availableColors = colorBlindFriendlyPalette.filter(
        (color) => color !== this.lastColor
      );

      const randomIndex = Math.floor(Math.random() * availableColors.length);
      const selectedColor = availableColors[randomIndex];

      this.lastColor = selectedColor;
      return selectedColor;
    },
    dynamicTrace(event) {
      if (!this.currentStroke) return;
      const { x, y } = this.getPopupMousePosition(event);
      this.currentStroke.points.push({ x, y });
      this.dynamicTracePath = this.formatPoints(this.currentStroke.points);
    },
    endDrawing() {
      if (this.currentStroke) {
        this.strokes.push(this.currentStroke);
        this.currentStroke = null;
        this.dynamicTracePath = "";
      }
    },
    startAngleMeasurement(event) {
      const { x, y } = this.getPopupMousePosition(event);

      // Check if we're dragging an existing point
      const nearestPointIndex = this.findNearestPoint(x, y, 10); // 10px threshold
      if (nearestPointIndex !== -1) {
        this.draggingPoint = nearestPointIndex;
        return; // Exit early if dragging an existing point
      }

      // Add a new point if we're not dragging
      if (this.measurePoints.length < 3) {
        this.measurePoints.push({ x, y });

        // Calculate the angle if we have 3 points
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

    async saveCroppedImage() {
      if (!this.croppedSvg) {
        console.error("Cannot save: No SVG available.");
        return;
      }
      // Save the SVG alone
      const svgBlob = new Blob([this.croppedSvg], { type: "image/svg+xml" });
      const svgUrl = URL.createObjectURL(svgBlob);
      const svgLink = document.createElement("a");
      svgLink.href = svgUrl;
      svgLink.download = "cropped-image.svg";
      svgLink.click();
      URL.revokeObjectURL(svgUrl);

      // Create a canvas to combine the cropped image and annotations
      const canvas = document.createElement("canvas");
      const { width, height } = this.popupDimensions;
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");

      // Load the cropped image from the SVG
      const img = new Image();
      img.src = this.croppedImage; // Ensure this.croppedImage contains the correct image data (e.g., a data URL or a valid image URL)

      try {
        await new Promise((resolve, reject) => {
          img.onload = () => {
            // Clear the canvas before drawing
            ctx.clearRect(0, 0, width, height);

            // Draw the cropped image onto the canvas
            ctx.drawImage(img, 0, 0, width, height);

            // Draw the annotations (traces and angle measurements)
            this.strokes.forEach((stroke) => {
              ctx.strokeStyle = stroke.color;
              ctx.lineWidth = 2;
              ctx.beginPath();
              stroke.points.forEach((point, index) => {
                if (index === 0) {
                  ctx.moveTo(point.x, point.y);
                } else {
                  ctx.lineTo(point.x, point.y);
                }
              });
              ctx.stroke();
            });

            // Draw angle measurements
            this.measurePoints.forEach((point) => {
              ctx.fillStyle = "red";
              ctx.beginPath();
              ctx.arc(point.x, point.y, 5, 0, 2 * Math.PI);
              ctx.fill();
            });

            if (this.measurePoints.length >= 2) {
              const p1 = this.measurePoints[0];
              const p2 = this.measurePoints[1];
              ctx.strokeStyle = "blue";
              ctx.lineWidth = 2;
              ctx.beginPath();
              ctx.moveTo(p1.x, p1.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.stroke();
            }

            if (this.measurePoints.length === 3) {
              const p2 = this.measurePoints[1];
              const p3 = this.measurePoints[2];
              ctx.strokeStyle = "blue";
              ctx.lineWidth = 2;
              ctx.beginPath();
              ctx.moveTo(p2.x, p2.y);
              ctx.lineTo(p3.x, p3.y);
              ctx.stroke();

              // Display the angle
              ctx.fillStyle = "black";
              ctx.font = "12px Arial";
              ctx.fillText(`${this.calculatedAngle}°`, p2.x + 10, p2.y - 10);
            }

            // Convert the canvas to a PNG and trigger download
            canvas.toBlob((blob) => {
              if (!blob) {
                reject(new Error("Canvas toBlob failed"));
                return;
              }
              const pngUrl = URL.createObjectURL(blob);
              const pngLink = document.createElement("a");
              pngLink.href = pngUrl;
              pngLink.download = "cropped-image-with-annotations.png";
              pngLink.click();
              URL.revokeObjectURL(pngUrl);
              resolve();
            }, "image/png");
          };

          img.onerror = (error) => {
            console.error("Error loading cropped image:", error);
            reject(error);
          };
        });
      } catch (error) {
        console.error("Error in saveCroppedImage:", error);
      }
    },

    async saveAnnotations() {
      try {
        // Hide the top bar and navigation buttons
        const topBar = document.querySelector(".top-bar");
        const navigationBar = document.querySelector(".navigation-bar");
        if (topBar) topBar.style.display = "none";
        if (navigationBar) navigationBar.style.display = "none";

        // Create a new PDF document
        const pdfDoc = await PDFDocument.create();

        for (let i = 0; i < this.images.length; i++) {
          const annotations = this.annotationsByPage[i] || [];
          const comments = this.comments[i] || [];
          const lengthMeasurements = this.currentPageLengthMeasurements || [];

          // Skip pages without annotations, comments, or length measurements
          if (
            annotations.length === 0 &&
            comments.length === 0 &&
            lengthMeasurements.length === 0
          ) {
            console.log(`Skipping empty page ${i + 1}`);
            continue;
          }

          // Go to the current page
          this.currentPage = i;

          // Wait for the page to render
          await this.$nextTick();

          // Capture the content of the pdf-viewer container
          const viewer = this.$refs.viewer;
          const canvas = await html2canvas(viewer, {
            scale: 2, // Increase scale for better quality
            useCORS: true, // Allow cross-origin images
            logging: true, // Enable logging for debugging
            ignoreElements: (element) => {
              // Exclude unnecessary elements (e.g., buttons, toolbars)
              return (
                element.classList.contains("top-bar") ||
                element.classList.contains("navigation-bar")
              );
            },
          });

          // Convert canvas to image
          const imgData = canvas.toDataURL("image/png");

          // Add the image to the PDF
          const image = await pdfDoc.embedPng(imgData);
          const page = pdfDoc.addPage([image.width, image.height]); // Set page size to match image
          page.drawImage(image, {
            x: 0,
            y: 0,
            width: image.width,
            height: image.height,
          });
        }

        // Save the PDF if there is content
        const pdfBytes = await pdfDoc.save();
        const blob = new Blob([pdfBytes], { type: "application/pdf" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "annotated-document.pdf";
        link.click();
        URL.revokeObjectURL(link.href);
        console.log("PDF saved successfully");

        // Restore the top bar and navigation buttons
        if (topBar) topBar.style.display = "flex";
        if (navigationBar) navigationBar.style.display = "flex";
      } catch (error) {
        console.error("Error saving annotations:", error);
      }
    },
    startDraggingPoint(index, event) {
      event.preventDefault();
      this.draggingPoint = index;
    },
    clearAnnotations() {
      this.annotationsByPage[this.currentPage] = [];
      this.comments[this.currentPage] = [];
      this.lengthMeasurements = {
        ascenders: {},
        descenders: {},
        interlinear: {},
        upperMargin: {},
        lowerMargin: {},
        internalMargin: {},
        intercolumnSpaces: {},
      };
      this.strokes = [];
    },

    showLengthPopup(type) {
      if (type === "horizontal") {
        this.selectedMeasurement = "ascenders";
        this.showHorizontalPopup = true;
        this.showVerticalPopup = false;
      } else if (type === "vertical") {
        this.selectedMeasurement = "internalMargin";
        this.showVerticalPopup = true;
        this.showHorizontalPopup = false;
      }
    },
    hideLengthPopup() {
      this.showHorizontalPopup = false;
      this.showVerticalPopup = false;
    },

    confirmLengthMeasurement() {
      this.hideLengthPopup(); // Hide the popup
      this.startLengthMeasurement(); // Start the length measurement process
    },

    startLengthMeasurement() {
      this.lengthMeasurementActive = true; // Activate length measurement mode
      this.$refs.viewer.addEventListener("mousedown", this.startLength);
      this.$refs.viewer.addEventListener("mousemove", this.updateLength);
    },

    startLength(event) {
      if (!this.lengthMeasurementActive) return;

      const { x, y } = this.getMousePosition(event);

      if (!this.croppingStarted) {
        this.startPoint = { x, y };
        this.currentSquare = {
          x: x,
          y: y,
          width: 0,
          height: 0,
          color: this.measurementColors[this.selectedMeasurement], // Set color
          label: this.selectedMeasurement,
        };
        this.croppingStarted = true;
      } else {
        // Second click: Finalize the measurement
        const currentLabel = this.selectedMeasurement;

        // Ensure the nested structure exists
        if (!this.lengthMeasurements[currentLabel]) {
          this.lengthMeasurements[currentLabel] = {};
        }
        if (!this.lengthMeasurements[currentLabel][this.currentPage]) {
          this.lengthMeasurements[currentLabel][this.currentPage] = [];
        }

        // Add the measurement
        this.lengthMeasurements[currentLabel][this.currentPage].push({
          ...this.currentSquare,
          type: "length",
          height: this.currentSquare.height,
          width: this.currentSquare.width,
        });

        // Reset state
        this.startPoint = null;
        this.currentSquare = null;
        this.croppingStarted = false;
        this.lengthMeasurementActive = false;
      }
    },

    updateLength(event) {
      if (
        !this.lengthMeasurementActive ||
        !this.croppingStarted ||
        !this.startPoint
      )
        return;

      const { x, y } = this.getMousePosition(event);

      this.currentSquare = {
        x: Math.min(x, this.startPoint.x), // Use the smaller x value
        y: Math.min(y, this.startPoint.y), // Use the smaller y value
        width: Math.abs(x - this.startPoint.x), // Calculate width
        height: Math.abs(y - this.startPoint.y), // Calculate height
        color: this.measurementColors[this.selectedMeasurement], // Use selected color
        label: this.selectedMeasurement, // Maintain label
      };
    },

    // Calculate statistics for a specific measurement type and page
    calculateStatisticsForType(type, page) {
      const measurements = this.lengthMeasurements[type]?.[page] || [];
      const values =
        type === "ascenders" ||
        type === "descenders" ||
        type === "interlinear" ||
        type === "upperMargin" ||
        type === "lowerMargin"
          ? measurements.map((m) => m.width) // Horizontal measurements use width
          : measurements.map((m) => m.height); // Vertical measurements use height

      console.log("Values for", type, "on page", page, ":", values); // Debugging

      return {
        average: this.calculateAverage(values),
        standardDeviation: this.calculateStandardDeviation(values),
        mode: this.calculateMode(values),
      };
    },

    toggleCalculateDropdown() {
      this.showCalculateDropdown = !this.showCalculateDropdown;
      console.log("Dropdown toggled");
    },
    calculateCurrentPage() {
      this.showCalculateDropdown = false;
      this.showStatisticsPopup(this.getCurrentPageStatistics());
    },
    calculateEntireDocument() {
      this.showCalculateDropdown = false;
      this.showStatisticsPopup(this.getEntireDocumentStatistics());
    },
    getCurrentPageStatistics() {
      const horizontalTypes = [
        "ascenders",
        "descenders",
        "interlinear",
        "upperMargin",
        "lowerMargin",
      ];
      const verticalTypes = ["internalMargin", "intercolumnSpaces"];
      const statistics = {};

      // Calculate horizontal statistics
      horizontalTypes.forEach((type) => {
        if (
          this.lengthMeasurements[type] &&
          this.lengthMeasurements[type][this.currentPage]
        ) {
          const values = this.extractValues(
            this.lengthMeasurements[type][this.currentPage],
            type
          );
          statistics[type] = {
            average: this.calculateAverage(values),
            standardDeviation: this.calculateStandardDeviation(values),
            mode: this.calculateMode(values),
          };
        }
      });

      // Calculate vertical statistics
      verticalTypes.forEach((type) => {
        if (
          this.lengthMeasurements[type] &&
          this.lengthMeasurements[type][this.currentPage]
        ) {
          const values = this.extractValues(
            this.lengthMeasurements[type][this.currentPage],
            type
          );
          statistics[type] = {
            average: this.calculateAverage(values),
            standardDeviation: this.calculateStandardDeviation(values),
            mode: this.calculateMode(values),
          };
        }
      });

      return statistics;
    },
    // Get statistics for the entire document
    getEntireDocumentStatistics() {
      const horizontalTypes = [
        "ascenders",
        "descenders",
        "interlinear",
        "upperMargin",
        "lowerMargin",
      ];
      const verticalTypes = ["internalMargin", "intercolumnSpaces"];
      const statistics = {};

      // Calculate horizontal statistics
      horizontalTypes.forEach((type) => {
        let values = [];
        for (let page = 0; page < this.totalPages; page++) {
          if (
            this.lengthMeasurements[type] &&
            this.lengthMeasurements[type][page]
          ) {
            values = values.concat(
              this.extractValues(this.lengthMeasurements[type][page], type)
            );
          }
        }
        statistics[type] = {
          average: this.calculateAverage(values),
          standardDeviation: this.calculateStandardDeviation(values),
          mode: this.calculateMode(values),
        };
      });

      // Calculate vertical statistics
      verticalTypes.forEach((type) => {
        let values = [];
        for (let page = 0; page < this.totalPages; page++) {
          if (
            this.lengthMeasurements[type] &&
            this.lengthMeasurements[type][page]
          ) {
            values = values.concat(
              this.extractValues(this.lengthMeasurements[type][page], type)
            );
          }
        }
        statistics[type] = {
          average: this.calculateAverage(values),
          standardDeviation: this.calculateStandardDeviation(values),
          mode: this.calculateMode(values),
        };
      });

      return statistics;
    },
    getHorizontalStatistics() {
      const horizontalTypes = [
        "ascenders",
        "descenders",
        "interlinear",
        "upperMargin",
        "lowerMargin",
      ];
      const statistics = {};

      horizontalTypes.forEach((type) => {
        if (
          this.lengthMeasurements[type] &&
          this.lengthMeasurements[type][this.currentPage]
        ) {
          statistics[type] = this.calculateStatisticsForType(
            type,
            this.currentPage
          );
        }
      });

      return statistics;
    },
    getVerticalLengths(page) {
      const verticalTypes = ["internalMargin", "intercolumnSpaces"];
      let verticalLengths = [];

      verticalTypes.forEach((type) => {
        if (
          this.lengthMeasurements[type] &&
          this.lengthMeasurements[type][page]
        ) {
          verticalLengths = verticalLengths.concat(
            this.lengthMeasurements[type][page].map((m) => m.height) // Use height for vertical measurements
          );
        }
      });

      console.log("Vertical Lengths for Page", page, ":", verticalLengths); // Debugging
      return verticalLengths;
    },

    getHorizontalLengths(page) {
      const horizontalTypes = [
        "ascenders",
        "descenders",
        "interlinear",
        "upperMargin",
        "lowerMargin",
      ];
      let horizontalLengths = [];

      horizontalTypes.forEach((type) => {
        if (
          this.lengthMeasurements[type] &&
          this.lengthMeasurements[type][page]
        ) {
          horizontalLengths = horizontalLengths.concat(
            this.lengthMeasurements[type][page].map((m) => m.width) // Use width for horizontal measurements
          );
        }
      });

      console.log("Horizontal Lengths for Page", page, ":", horizontalLengths); // Debugging
      return horizontalLengths;
    },
    // Get all vertical statistics for the current page
    getVerticalStatistics() {
      const verticalTypes = ["internalMargin", "intercolumnSpaces"];
      const statistics = {};

      verticalTypes.forEach((type) => {
        if (
          this.lengthMeasurements[type] &&
          this.lengthMeasurements[type][this.currentPage]
        ) {
          statistics[type] = this.calculateStatisticsForType(
            type,
            this.currentPage
          );
        }
      });

      return statistics;
    },
    extractValues(measurements, type) {
      // Define vertical measurement types
      const verticalTypes = ["internalMargin", "intercolumnSpaces"];

      // Determine if the type is vertical
      const isVertical = verticalTypes.includes(type);

      // Extract "height" for vertical measurements, "width" for horizontal measurements
      return measurements.map((m) => (isVertical ? m.width : m.height));
    },

    // Calculate average
    calculateAverage(values) {
      if (!values || values.length === 0) return 0; // Return 0 for empty arrays

      // Ensure all values are numbers
      const numericValues = values
        .map((val) => parseFloat(val))
        .filter((val) => !isNaN(val));

      if (numericValues.length === 0) return 0; // Return 0 if no valid numbers

      const sum = numericValues.reduce((acc, val) => acc + val, 0);
      return sum / numericValues.length;
    },
    // Calculate standard deviation
    calculateStandardDeviation(values) {
      if (!values || values.length === 0) return 0; // Return 0 for empty arrays

      // Ensure all values are numbers
      const numericValues = values
        .map((val) => parseFloat(val))
        .filter((val) => !isNaN(val));

      if (numericValues.length === 0) return 0; // Return 0 if no valid numbers

      const avg = this.calculateAverage(numericValues);
      const squareDiffs = numericValues.map((val) => (val - avg) ** 2);
      const variance =
        squareDiffs.reduce((acc, val) => acc + val, 0) / numericValues.length; // Population formula
      return Math.sqrt(variance);
    },

    // Calculate mode
    calculateMode(values) {
      if (!values || values.length === 0) return "No mode"; // Return "No mode" for empty arrays

      // Ensure all values are numbers
      const numericValues = values
        .map((val) => parseFloat(val))
        .filter((val) => !isNaN(val));

      if (numericValues.length === 0) return "No mode"; // Return "No mode" if no valid numbers

      const frequency = {};
      numericValues.forEach(
        (val) => (frequency[val] = (frequency[val] || 0) + 1)
      );

      const maxFrequency = Math.max(...Object.values(frequency));

      // If all values appear only once, return "No mode"
      if (maxFrequency === 1) return "No mode";

      const modes = Object.keys(frequency).filter(
        (key) => frequency[key] === maxFrequency
      );

      // Return the smallest mode if there are multiple modes
      return parseFloat(Math.min(...modes));
    },
    showStatisticsPopup(statistics) {
      this.horizontalStatistics = {};
      this.verticalStatistics = {};

      // Separate horizontal and vertical statistics
      for (const [type, stats] of Object.entries(statistics)) {
        if (
          [
            "ascenders",
            "descenders",
            "interlinear",
            "upperMargin",
            "lowerMargin",
          ].includes(type)
        ) {
          this.horizontalStatistics[type] = stats;
        } else if (["internalMargin", "intercolumnSpaces"].includes(type)) {
          this.verticalStatistics[type] = stats;
        }
      }

      this.showStatistics = true;
    },

    closeStatisticsPopup() {
      this.showStatistics = false;
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
  /* margin-left: 300px; */
}

.pdf-viewer img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.underline-line {
  position: absolute;
  background-color: blue; /* Color of the underline */
  height: 2px; /* Height of the underline */
  pointer-events: none; /* Ensure it doesn't block mouse events */
  z-index: 1; /* Ensure it appears above other elements */
}

.cropping-rectangle {
  position: absolute;
  border: 2px dashed #007bff;
  background-color: rgba(0, 123, 255, 0.2);
  pointer-events: none;
  z-index: 100;
}

.blurred-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  backdrop-filter: blur(8px);
  z-index: 1001; /* High z-index to overlay everything */
}

.interactive-svg {
  cursor: crosshair;
  pointer-events: all;
}

.highlight-rectangle {
  position: absolute;
  border: 2px solid rgba(255, 255, 0, 0.7);
  background-color: rgba(255, 255, 0, 0.3);
  pointer-events: none;
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
  z-index: 1002;
}

.comment-container {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: grab;
  z-index: 1;
}
.comment-container:active {
  cursor: grabbing;
}

.comment-icon {
  font-size: 24px;
  cursor: pointer;
  background-color: #ffecb3;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.comment-bubble {
  margin-left: 8px;
  padding: 8px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
}
.comment-bubble::after {
  content: "";
  position: absolute;
  top: 50%;
  left: -8px;
  width: 0;
  height: 0;
  border: 8px solid transparent;
  border-right-color: #fff;
  transform: translateY(-50%);
}

.comment-arrow {
  position: absolute;
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-top: 8px solid #fff;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
}

.comment-content {
  font-size: 14px;
  color: #333;
}

/* Styles for the comment input box */
.comment-input-container {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #fff;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 10px;
  width: 300px;
  z-index: 1000;
}

.comment-input-box {
  width: 100%;
  height: 60px;
  border: 1px solid #ccc;
  border-radius: 5px;
  padding: 8px;
  font-size: 14px;
  margin-bottom: 8px;
  resize: none;
}

.comment-input-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-save-comment,
.btn-cancel-comment {
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 5px 10px;
  font-size: 14px;
  cursor: pointer;
}

.btn-cancel-comment {
  background-color: #6c757d;
  margin-left: 10px;
}

.btn-save-comment:hover {
  background-color: #0056b3;
}

.btn-cancel-comment:hover {
  background-color: #5a6268;
}

.length-popup {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.length-popup-content {
  background-color: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  text-align: center;
}
.color-preview {
  display: flex;
  justify-content: space-around;
  margin: 20px 0;
}

.color-box {
  width: 30px;
  height: 30px;
  border: 1px solid #ccc;
}

button {
  margin: 0px;
  padding: 5px 5px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

button:hover {
  background-color: #007bff;
  color: white;
}

.length-measurement {
  position: absolute;
  border: 2px solid rgba(0, 0, 0, 0.5); /* Add a border for visibility */
  pointer-events: none; /* Ensure it doesn't block mouse events */
}

.length-label {
  position: absolute;
  left: 15px; /* Adjust label position */
  top: 50%;
  transform: translateY(-50%);
  color: black;
  font-size: 12px;
  background-color: white; /* Add background for readability */
  padding: 2px 5px;
  border-radius: 3px;
}

.calculate-container {
  position: relative;
}

.calculate-dropdown {
  position: absolute;
  top: 100%; /* Position below the button */
  left: 0;
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000; /* Ensure it appears above other elements */
  min-width: 150px; /* Set a minimum width */
}

.calculate-dropdown div {
  padding: 8px 16px;
  cursor: pointer;
}

.calculate-dropdown div:hover {
  background-color: #f1f1f1;
}

.statistics-popup {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.statistics-popup-content {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  max-width: 400px;
  width: 100%;
}

.statistics-popup-content table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.statistics-popup-content h3 {
  margin-bottom: 16px;
}

.statistics-popup-content th,
.statistics-popup-content td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
}

.statistics-popup-content th {
  background-color: #f2f2f2;
}

.statistics-popup-content h4 {
  margin-top: 12px;
  margin-bottom: 8px;
}

.statistics-popup-content p {
  margin: 4px 0;
}

.statistics-popup-content button {
  margin-top: 16px;
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.statistics-popup-content button:hover {
  background-color: #0056b3;
}
</style>