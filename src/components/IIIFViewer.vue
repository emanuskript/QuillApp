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

      <!-- Render existing highlights -->
      <div
        v-for="(annotation, index) in highlightAnnotations"
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

      <!-- Render existing underlines -->
      <svg class="underline-svg" style="position: absolute">
        <line
          v-for="(annotation, index) in underlineAnnotations"
          :key="'underline-' + index"
          :x1="annotation.startX"
          :y1="annotation.startY"
          :x2="annotation.endX"
          :y2="annotation.endY"
          stroke="blue"
          stroke-width="2"
        ></line>
      </svg>

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

      <!-- Render dynamic underline -->
      <svg class="underline-svg" style="position: absolute">
        <line
          v-if="underlineModeActive && currentUnderline"
          :x1="currentUnderline.startX"
          :y1="currentUnderline.startY"
          :x2="currentUnderline.endX"
          :y2="currentUnderline.endY"
          stroke="blue"
          stroke-width="2"
        ></line>
      </svg>

      <!-- Comments -->
      <!-- Comments -->
      <div
        v-for="(comment, index) in comments"
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

        <div
          class="comment-icon"
          @mouseenter="showComment(comment)"
          @mouseleave="hideComment"
        >
          💬
        </div>
        <div
          v-if="tooltipVisible && activeComment === comment"
          class="comment-bubble"
        >
          <div class="comment-content">{{ comment.text }}</div>
          <div class="comment-arrow"></div>
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
      commentModeActive: false,
      highlightModeActive: false, // Tracks if highlight mode is active
      underlineModeActive: false, // Tracks if underline mode is active
      currentUnderline: null, // Tracks current underline line being drawn
      currentHighlight: null, // Tracks current highlight box being drawn
      showCommentInput: false,
      currentCommentText: "",
      currentCommentPosition: null,
      comments: [],
      draggingCommentIndex: null, // Index of the comment being dragged
      dragOffset: { x: 0, y: 0 }, // Offset between the mouse and comment position
    };
  },
  computed: {
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
        }
      } catch (error) {
        alert("Error fetching IIIF manifest: " + error.message);
      }
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
        this.clearAnnotations();
      }
    },
    prevPage() {
      if (this.currentPage > 0) this.currentPage--;
      this.clearAnnotations();
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
      this.imageLoaded = true;
    },
    startTrace(event) {
      if (this.croppedImage == null && !this.highlightModeActive) {
        return; // Exit the function early
      }
      const { x, y } = this.getMousePosition(event);

      if (this.highlightModeActive) {
        if (!this.croppingStarted && event.button === 0) {
          // Start cropping
          this.startPoint = { x, y };
          this.currentSquare = { x, y, width: 0, height: 0 };
          this.croppingStarted = true;
        } else {
          // Finish cropping and add the highlight annotation
          this.annotations.push({
            type: "highlight",
            ...this.currentSquare,
          });
          this.croppingStarted = false;
          this.highlightModeActive = false;
          this.currentSquare = null;
        }
      } else if (this.underlineModeActive) {
        if (!this.currentUnderline) {
          // Start underlining
          const rect = this.$refs.image.getBoundingClientRect();
          this.startPoint = { x, y };
          this.currentUnderline = {
            startX: x,
            startY: y - rect.top,
            endX: x,
            endY: y - rect.top,
          };
        } else {
          // Finish underlining and add the underline annotation
          this.annotations.push({
            type: "underline",
            ...this.currentUnderline,
          });
          this.currentUnderline = null;
          this.underlineModeActive = false;
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
      if (this.croppedImage == null && !this.highlightModeActive) {
        return; // Exit the function early
      }

      if (this.croppingStarted || this.startPoint) {
        const { x, y } = this.getMousePosition(event);

        this.currentSquare = {
          x:
            Math.min(x, this.startPoint.x) +
            this.$refs.image.getBoundingClientRect().left,
          y: Math.min(y, this.startPoint.y),
          width: Math.abs(x - this.startPoint.x),
          height: Math.abs(y - this.startPoint.y),
        };
      } else if (this.underlineModeActive && this.currentUnderline) {
        // Update the end position of the underline
        const rect = this.$refs.image.getBoundingClientRect();
        const { x, y } = this.getMousePosition(event);
        this.currentUnderline.endX = x;
        this.currentUnderline.endY = y - rect.top;
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
      } else if (this.underlineModeActive && this.currentUnderline) {
        this.annotations.push({
          type: "underline",
          ...this.currentUnderline,
        });
        this.currentUnderline = null;
        this.underlineModeActive = false;
      }
    },

    startComment(event) {
      const { x, y } = this.getMousePosition(event);
      this.currentCommentPosition = { x, y };
      this.showCommentInput = true;
    },

    addComment() {
      if (!this.currentCommentText) return;

      this.comments.push({
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
      this.comments.splice(index, 1);
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
      const comment = this.comments[index];
      this.dragOffset = {
        x: event.clientX - comment.x,
        y: event.clientY - comment.y,
      };
    },

    dragComment(event) {
      if (this.draggingCommentIndex !== null) {
        const comment = this.comments[this.draggingCommentIndex];
        comment.x = event.clientX - this.dragOffset.x;
        comment.y = event.clientY - this.dragOffset.y;
      }
    },

    // Stop dragging
    stopDraggingComment() {
      this.draggingCommentIndex = null;
    },

    getMousePosition(event) {
      const imageElement = this.$refs.image;
      if (!imageElement) {
        console.error("Image element not available.");
        return { x: 0, y: 0 };
      }
      const rect = imageElement.getBoundingClientRect();
      return { x: event.clientX - rect.left, y: event.clientY - rect.top };
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
    startDraggingPoint(index, event) {
      event.preventDefault();
      this.draggingPoint = index;
    },
    clearAnnotations() {
      this.annotations = [];
      this.comments = [];
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
  overflow: hidden;
  /* margin-left: 300px; */
}

.pdf-viewer img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.underline-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* Ensure it doesn't block mouse events */
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
}

.comment-container {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: grab;
  z-index: 10;
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
</style>