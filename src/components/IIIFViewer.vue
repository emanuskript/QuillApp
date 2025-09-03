<template>
  <div class="viewer-container">
    <!-- Top Bar / Toolbar -->
    <Toolbar
      :toolStates="{
        highlight: highlightModeActive,
        underline: underlineModeActive,
        comment: commentModeActive,
        trace: traceModeActive,
        measure: measureModeActive
      }"
      :showCalculateDropdown="showCalculateDropdown"
      :showClearDropdown="showClearDropdown"
      :toolMessage="toolMessage"
      @select-tool="selectTool"
      @show-length-popup="showLengthPopup"
      @toggle-calculate-dropdown="toggleCalculateDropdown"
      @calculate-current-page="calculateCurrentPage"
      @calculate-entire-document="calculateEntireDocument"
      @calculate-angle-statistics="openAngleStatsPicker"
      @save-annotations="saveAnnotations"
      @toggle-clear-dropdown="toggleClearDropdown"
      @clear-highlights="clearHighlights"
      @clear-underlines="clearUnderlines"
      @clear-comments="clearComments"
      @clear-traces="clearTraces"
      @clear-angles="clearAngles"
      @clear-horizontal-lengths="clearHorizontalLengths"
      @clear-vertical-lengths="clearVerticalLengths"
      @clear-all="clearAll"
      @start-crop="startCrop"
    />

    <!-- Navigation -->
    <NavigationBar
      :currentPage="currentPage"
      :totalPages="totalPages"
      :pageInput="pageInput"
      @prev="prevPage"
      @next="nextPage"
      @go-to="(p1) => { pageInput = p1; goToPage(); }"
    />

    <!-- Main stage (image + overlays) -->
    <ImageStage
      ref="viewer"
      :image="croppedImage || currentImage"
      :cursorMode="(traceModeActive || highlightModeActive || underlineModeActive || measureModeActive || isMeasuring) ? 'crosshair' : 'default'"
      @image-load="handleImageLoad"
      @mousedown="startTrace"
      @mousemove="trace"
      @mouseup="endTrace"
    >
      <!-- Traces -->
      <TracesLayer
        :strokes="currentPageStrokes"
        :dynamicStroke="currentStroke"
      />

      <!-- Angles -->
      <AnglesLayer
        :angles="currentPageAngleMeasurements"
        :tempPoints="measurePoints"
        :tempAngle="measurePoints.length === 3 ? calculatedAngle : null"
        @point-mousedown="({ pointIndex, event }) => startDraggingPoint(pointIndex, event)"
        @temp-point-mousedown="({ pointIndex, event }) => { draggingPoint = pointIndex; }"
      />

      <!-- Highlights -->
      <HighlightsLayer
        :highlights="currentPageHighlights"
        :tempHighlight="highlightModeActive && currentSquare ? currentSquare : null"
      />

      <!-- Underlines -->
      <UnderlinesLayer
        :underlines="currentPageUnderlines"
        :tempUnderline="underlineModeActive && currentUnderline ? currentUnderline : null"
      />

      <!-- Lengths / Bands -->
      <LengthsLayer
        :measurements="currentPageLengthMeasurements"
        :dynamic="isMeasuring && currentSquare ? currentSquare : null"
        :labelPositions="labelPositions"
        @label-mousedown="({ id, event, measurement }) => startLabelDrag(id, event, measurement)"
      />

      <!-- Comments -->
      <CommentsLayer
        :comments="currentPageComments"
        :showInput="showCommentInput"
        :draft="{ text: currentCommentText, x: currentCommentPosition?.x || 0, y: (currentCommentPosition?.y || 0) + 100 }"
        @add="onAddComment"
        @cancel="cancelComment"
        @drag-start="startDraggingComment"
        @drag-move="dragComment"
        @drag-stop="stopDraggingComment"
      />

      <!-- Cropping Rectangle (dynamic while dragging) -->
      <div
        v-if="(croppingStarted || cropButtonClicked) && currentSquare"
        class="cropping-rectangle"
        :style="{
          left: currentSquare.x + 'px',
          top: currentSquare.y + 'px',
          width: currentSquare.width + 'px',
          height: currentSquare.height + 'px'
        }"
      />
    </ImageStage>

    <!-- Pen Selection -->
    <PenSelectionPopup
      :visible="showPenSelectionPopup"
      :penAngles="penAngles"
      :selectedAngle="selectedPenAngle"
      :testPath="testTracePath"
      :penWidth="penWidth"
      :penHeight="penHeight"
      @select="selectPen"
      @test-start="startTestTrace"
      @test-move="testTrace"
      @test-end="endTestTrace"
      @confirm="confirmPenSelection"
      @cancel="cancelPenSelection"
    />

    <!-- Statistics -->
    <StatisticsPopup
      :visible="showStatistics"
      :horizontal="horizontalStatistics"
      :vertical="verticalStatistics"
      @close="closeStatisticsPopup"
    />

    <AngleStatisticsPopup
      :visible="showAngleStatistics"
      :stats="angleStatistics"
      @close="closeAngleStatisticsPopup"
    />

    <!-- Length popups -->
    <LengthPopupHorizontal
      :visible="showHorizontalPopup"
      :measurementColors="measurementColors"
      @confirm="(sel) => { selectedMeasurement = sel; hideLengthPopup(); startLengthMeasurement(); }"
      @cancel="hideLengthPopup"
    />
    <LengthPopupVertical
      :visible="showVerticalPopup"
      :measurementColors="measurementColors"
      @confirm="(sel) => { selectedMeasurement = sel; hideLengthPopup(); startLengthMeasurement(); }"
      @cancel="hideLengthPopup"
    />

    <!-- Angle: choose label (label == ID) -->
    <AngleLabelPopup
      :visible="showAngleLabelPopup"
      :labels="angleLabels"
      :initialLabel="activeAngleLabel"
      @confirm="onConfirmAngleLabel"
      @cancel="onCancelAngleLabel"
    />

    <!-- Angle stats scope picker -->
    <AngleStatsPickerPopup
      :visible="showAngleStatsPicker"
      :labels="angleLabels"
      @confirm="onConfirmAngleStats"
      @cancel="onCancelAngleStats"
    />

    <!-- Cropped preview popup -->
    <CroppedPreviewPopup
      :croppedImage="croppedImage"
      @start-annotation="startCroppedAnnotation"
      @move-annotation="handleCroppedAnnotation"
      @end-annotation="endCroppedAnnotation"
      @save-png="saveCroppedImageAsPNG"
      @save-svg="saveCroppedImageAsSVG"
      @save-annotated="saveCroppedImage"
      @close="closeCroppedPopup"
    >
      <!-- Render cropped overlays inside popup via the slot -->
      <svg
        v-if="croppedImage"
        class="drawing-layer"
        :width="popupDimensions.width"
        :height="popupDimensions.height"
        style="position:absolute; inset:0; width:100%; height:100%; z-index:2; pointer-events:none;"
      >
        <!-- Cropped traces -->
        <polyline
          v-for="(stroke, index) in croppedStrokes"
          :key="'cstroke-' + index"
          :points="formatPoints(stroke.points)"
          :stroke="stroke.color"
          stroke-width="2"
          fill="none"
        />
        <!-- Dynamic cropped trace -->
        <polyline
          v-if="croppedCurrentStroke && croppedCurrentStroke.points && croppedCurrentStroke.points.length"
          :points="formatPoints(croppedCurrentStroke.points)"
          :stroke="croppedCurrentStroke.color"
          stroke-width="2"
          fill="none"
        />
        <!-- Cropped angles points/lines/labels -->
        <g v-if="croppedMeasurePoints.length">
          <circle
            v-for="(point, index) in croppedMeasurePoints"
            :key="'cmeasure-point-' + index"
            :cx="point.x" :cy="point.y" r="5" fill="red"
          />
          <line
            v-if="croppedMeasurePoints.length >= 2"
            :x1="croppedMeasurePoints[0].x" :y1="croppedMeasurePoints[0].y"
            :x2="croppedMeasurePoints[1].x" :y2="croppedMeasurePoints[1].y"
            stroke="blue" stroke-width="2"
          />
          <line
            v-if="croppedMeasurePoints.length === 3"
            :x1="croppedMeasurePoints[1].x" :y1="croppedMeasurePoints[1].y"
            :x2="croppedMeasurePoints[2].x" :y2="croppedMeasurePoints[2].y"
            stroke="blue" stroke-width="2"
          />
          <text
            v-if="croppedMeasurePoints.length === 3 && croppedCalculatedAngle"
            :x="croppedMeasurePoints[1].x + 10"
            :y="croppedMeasurePoints[1].y - 10"
            fill="darkblue" font-size="12"
          >
            {{ croppedCalculatedAngle }}°
          </text>
        </g>
        <g v-for="(measure, index) in croppedMeasures" :key="'cmeasure-' + index">
          <line
            v-if="measure.points.length >= 2"
            :x1="measure.points[0].x" :y1="measure.points[0].y"
            :x2="measure.points[1].x" :y2="measure.points[1].y"
            stroke="blue" stroke-width="2"
          />
          <line
            v-if="measure.points.length === 3"
            :x1="measure.points[1].x" :y1="measure.points[1].y"
            :x2="measure.points[2].x" :y2="measure.points[2].y"
            stroke="blue" stroke-width="2"
          />
          <text
            v-if="measure.points.length === 3 && measure.angle"
            :x="measure.points[1].x + 10"
            :y="measure.points[1].y - 10"
            fill="darkblue" font-size="12"
          >
            {{ measure.angle }}°
          </text>
          <circle
            v-for="(point, pi) in measure.points"
            :key="'cmeasure-final-point-' + pi"
            :cx="point.x" :cy="point.y" r="5" fill="red"
          />
        </g>
      </svg>

      <!-- Cropped highlight + underline rectangles -->
      <div
        v-if="croppedCurrentHighlight"
        class="highlight-rectangle"
        :style="croppedCurrentHighlight.style"
      ></div>
      <div
        v-for="(hl, index) in croppedHighlights"
        :key="'chl-' + index"
        class="highlight-rectangle"
        :style="hl.style"
      ></div>

      <div
        v-if="croppedCurrentUnderline"
        class="underline-line"
        :style="croppedCurrentUnderline.style"
      ></div>
      <div
        v-for="(ul, index) in croppedUnderlines"
        :key="'cul-' + index"
        class="underline-line"
        :style="ul.style"
      ></div>
    </CroppedPreviewPopup>
  </div>
</template>

<script>
/* eslint-disable */
import { PDFDocument } from "pdf-lib";
import html2canvas from "html2canvas";

// Viewer pieces
import Toolbar from "@/components/viewer/Toolbar.vue";
import NavigationBar from "@/components/viewer/NavigationBar.vue";
import ImageStage from "@/components/viewer/ImageStage.vue";
import TracesLayer from "@/components/viewer/TracesLayer.vue";
import AnglesLayer from "@/components/viewer/AnglesLayer.vue";
import HighlightsLayer from "@/components/viewer/HighlightsLayer.vue";
import UnderlinesLayer from "@/components/viewer/UnderlinesLayer.vue";
import LengthsLayer from "@/components/viewer/LengthsLayer.vue";
import CommentsLayer from "@/components/viewer/CommentsLayer.vue";

// Popups
import PenSelectionPopup from "@/components/popups/PenSelectionPopup.vue";
import StatisticsPopup from "@/components/popups/StatisticsPopup.vue";
import AngleStatisticsPopup from "@/components/popups/AngleStatisticsPopup.vue";
import LengthPopupHorizontal from "@/components/popups/LengthPopupHorizontal.vue";
import LengthPopupVertical from "@/components/popups/LengthPopupVertical.vue";
import CroppedPreviewPopup from "@/components/popups/CroppedPreviewPopup.vue";

import AngleLabelPopup from "@/components/popups/AngleLabelPopup.vue";
import AngleStatsPickerPopup from "@/components/popups/AngleStatsPickerPopup.vue";

export default {
  name: "IIIFViewer",
  components: {
    Toolbar,
    NavigationBar,
    ImageStage,
    TracesLayer,
    AnglesLayer,
    HighlightsLayer,
    UnderlinesLayer,
    LengthsLayer,
    CommentsLayer,
    PenSelectionPopup,
    StatisticsPopup,
    AngleStatisticsPopup,
    LengthPopupHorizontal,
    LengthPopupVertical,
    CroppedPreviewPopup,
    AngleLabelPopup,
    AngleStatsPickerPopup,
  },
  props: {
    source: { type: String, required: true },
  },
  data() {
    return {
      // images / pages
      images: [],
      currentPage: 0,
      pageInput: 1,

      // viewer metrics
      scalingFactor: 1,

      // tool state
      showTraces: false,
      measureModeActive: false,
      traceModeActive: false,
      commentModeActive: false,
      highlightModeActive: false,
      underlineModeActive: false,

      // tool UI
      toolMessage: "",
      showCalculateDropdown: false,
      showClearDropdown: false,

      // pen
      penAngles: [0, 25, 30, 50, 80],
      selectedPenAngle: null,
      showPenSelectionPopup: false,
      penWidth: 3,
      penHeight: 6,
      testTracePath: "",

      // trace data
      currentStroke: null,

      // measure angles
      measurePoints: [],
      draggingPoint: -1,
      calculatedAngle: 0,
      editingAnnotationIndex: -1,

      // angle labeling (label == ID)
      angleLabels: [],
      activeAngleLabel: "",
      showAngleLabelPopup: false,
      showAngleStatsPicker: false,

      // bands / lengths
      showHorizontalPopup: false,
      showVerticalPopup: false,
      selectedMeasurement: "ascenders",
      isMeasuring: false,
      lengthMeasurementActive: false,
      labelPositions: {},
      draggedLabelIndex: null,
      labelDragOffset: { x: 0, y: 0 },

      measurementColors: {
        ascenders: "rgba(0, 255, 0, 0.5)",
        descenders: "rgba(0, 0, 255, 0.5)",
        interlinear: "rgba(255, 165, 0, 0.5)",
        upperMargin: "rgba(255, 0, 0, 0.5)",
        lowerMargin: "rgba(128, 0, 128, 0.5)",
        internalMargin: "rgba(0, 255, 255, 0.5)",
        intercolumnSpaces: "rgba(255, 0, 255, 0.5)",
        lineHeight: "rgba(100, 100, 255, 0.5)",
        minimumHeight: "rgba(255, 100, 100, 0.5)",
      },
      lengthMeasurements: {
        ascenders: {},
        descenders: {},
        interlinear: {},
        upperMargin: {},
        lowerMargin: {},
        internalMargin: {},
        intercolumnSpaces: {},
        lineHeight: {},
        minimumHeight: {},
      },

      // rectangles / dragging
      startPoint: null,
      currentSquare: null,

      // annotations storage
      annotationsByPage: [],
      comments: [],

      // highlights/underlines dynamic
      currentUnderline: null,
      isFirstClick: true,

      // crop
      croppingStarted: false,
      cropButtonClicked: false,
      croppedImage: null,
      croppedSvg: null,
      popupDimensions: { width: 0, height: 0 },

      // cropped overlays
      croppedStrokes: [],
      croppedMeasures: [],
      croppedHighlights: [],
      croppedUnderlines: [],
      croppedMeasurePoints: [],
      croppedCalculatedAngle: null,
      croppedDraggingPoint: -1,
      croppedCurrentStroke: null,
      croppedCurrentHighlight: null,
      croppedCurrentUnderline: null,

      // statistics popups
      showStatistics: false,
      horizontalStatistics: {},
      verticalStatistics: {},
      showAngleStatistics: false,
      angleStatistics: {},

      // comments input
      showCommentInput: false,
      currentCommentText: "",
      currentCommentPosition: null,

      // misc
      imageLoaded: false,
    };
  },
  computed: {
    currentImage() {
      return this.images[this.currentPage] || null;
    },
    totalPages() {
      return this.images.length;
    },
    currentPageStrokes() {
      return (
        this.annotationsByPage[this.currentPage]?.filter((a) => a.type === "trace") || []
      );
    },
    currentPageAngleMeasurements() {
      return (
        this.annotationsByPage[this.currentPage]?.filter((a) => a.type === "measure") || []
      );
    },
    currentPageHighlights() {
      return (
        this.annotationsByPage[this.currentPage]?.filter((a) => a.type === "highlight") || []
      );
    },
    currentPageUnderlines() {
      return (
        this.annotationsByPage[this.currentPage]?.filter((a) => a.type === "underline") || []
      );
    },
    currentPageComments() {
      return this.comments[this.currentPage] || [];
    },
    currentPageLengthMeasurements() {
      const arr = [];
      for (const label in this.lengthMeasurements) {
        if (this.lengthMeasurements[label][this.currentPage]) {
          arr.push(...this.lengthMeasurements[label][this.currentPage]);
        }
      }
      return arr;
    },
  },
  watch: {
    currentPage(n) {
      this.pageInput = n + 1;
      if (!this.comments[this.currentPage]) this.comments[this.currentPage] = [];
    },
  },
  async created() {
    if (!this.source) {
      alert("Invalid source provided. Returning to input page.");
      this.$router.push({ name: "IIIFInput" });
      return;
    }

    if (this.source.endsWith("manifest.json")) {
      await this.fetchIIIFImages(this.source);
    } else {
      this.images = [this.source];
      this.annotationsByPage = new Array(this.images.length)
        .fill()
        .map(() => []);
      this.comments = new Array(this.images.length).fill().map(() => []);
    }
  },
  mounted() {
    // global move for label dragging
    this._onLabelDragMove = (e) => {
      if (this.draggedLabelIndex !== null) {
        let measurement = null;
        if (this.draggedLabelIndex === "dynamic") {
          measurement = this.currentSquare;
        } else {
          measurement = this.currentPageLengthMeasurements.find(
            (m) => m.id === this.draggedLabelIndex
          );
        }
        if (measurement) this.dragLabel(this.draggedLabelIndex, e, measurement);
      }
    };
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
          .filter(Boolean)
          .map((id) => `${id}/full/full/0/default.jpg`);

        if (this.images.length === 0) {
          alert("No images found in IIIF manifest.");
        } else {
          this.annotationsByPage = new Array(this.images.length)
            .fill()
            .map(() => []);
          this.comments = new Array(this.images.length).fill().map(() => []);
        }
      } catch (e) {
        alert("Error fetching IIIF manifest: " + e.message);
      }
    },

    // geometry helpers
    getMousePosition(event) {
      const el = this.$refs.viewer?.$el;
      if (!el) return { x: 0, y: 0 };
      const rect = el.getBoundingClientRect();
      return {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
    },
    formatPoints(points) {
      return points.map(({ x, y }) => `${x},${y}`).join(" ");
    },
    calculateAngle(pt1, pt2, pt3) {
      const v1 = { x: pt1.x - pt2.x, y: pt1.y - pt2.y };
      const v2 = { x: pt3.x - pt2.x, y: pt3.y - pt2.y };
      const dot = v1.x * v2.x + v1.y * v2.y;
      const m1 = Math.sqrt(v1.x ** 2 + v1.y ** 2);
      const m2 = Math.sqrt(v2.x ** 2 + v2.y ** 2);
      const rad = Math.acos(dot / (m1 * m2));
      return ((rad * 180) / Math.PI).toFixed(2);
    },

    // toolbar + tools
    selectTool(tool, event) {
      if (!this.currentImage) return;
      this.currentTool = tool;

      if (tool === "trace") {
        const next = !this.traceModeActive;
        this.traceModeActive = next;
        if (next) this.showPenSelection();
        this.showTraces = true;
        this.measureModeActive = false;
        this.showToolMessage(
          next ? "Trace mode active. Click again to deactivate."
               : "Trace mode deactivated."
        );
        return;
      }

      if (tool === "measure") {
        const becomingActive = !this.measureModeActive;
        this.measureModeActive = !this.measureModeActive;
        this.showTraces = true;
        this.measurePoints = [];
        this.draggingPoint = -1;
        this.traceModeActive = false;
        if (becomingActive) {
          this.showAngleLabelPopup = true; // choose or create the label (which is the ID)
        } else {
          this.activeAngleLabel = ""; // cleared when turning off
        }
        this.showToolMessage(
          this.measureModeActive ? "Angle measurement active."
                                 : "Angle measurement deactivated."
        );
        return;
      }

      if (tool === "highlight") {
        this.highlightModeActive = true;
        this.underlineModeActive = false;
        return;
      }

      if (tool === "underline") {
        this.underlineModeActive = true;
        this.highlightModeActive = false;
        return;
      }

      if (tool === "comment") {
        this.commentModeActive = true;
        const { x, y } = this.getMousePosition(event || { clientX: 0, clientY: 0 });
        this.currentCommentPosition = { x, y };
        this.showCommentInput = true;
        return;
      }

      // default: turn off
      this.traceModeActive = false;
      this.measureModeActive = false;
      this.highlightModeActive = false;
      this.underlineModeActive = false;
    },

    showToolMessage(msg) {
      this.toolMessage = msg;
      setTimeout(() => (this.toolMessage = ""), 2600);
    },

    // pen selection
    showPenSelection() {
      this.showPenSelectionPopup = true;
      this.selectedPenAngle = null;
      this.testTracePath = "";
    },
    selectPen(angle) {
      this.selectedPenAngle = angle;
      switch (angle) {
        case 25: this.penWidth = 3; this.penHeight = 6; break;
        case 30: this.penWidth = 4; this.penHeight = 7; break;
        case 50: this.penWidth = 5; this.penHeight = 8; break;
        case 80: this.penWidth = 6; this.penHeight = 10; break;
        case 0:  this.penWidth = 2; this.penHeight = 2; break;
        default: this.penWidth = 3; this.penHeight = 6;
      }
    },
    startTestTrace(e) {
      const rect = e.currentTarget.getBoundingClientRect();
      this.testTracePath = [{ x: e.clientX - rect.left, y: e.clientY - rect.top }];
      this.isDrawingTest = true;
    },
    testTrace(e) {
      if (!this.isDrawingTest) return;
      const rect = e.currentTarget.getBoundingClientRect();
      this.testTracePath.push({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    },
    endTestTrace() { this.isDrawingTest = false; },
    confirmPenSelection() {
      if (this.selectedPenAngle === null || this.selectedPenAngle === undefined) {
        alert("Please select a pen angle before confirming.");
        return;
      }
      this.showPenSelectionPopup = false;
      this.traceModeActive = true;
      this.testTracePath = "";
      this.showToolMessage(`Trace mode with ${this.selectedPenAngle}° pen.`);
    },
    cancelPenSelection() {
      this.showPenSelectionPopup = false;
      this.selectedPenAngle = null;
      this.testTracePath = "";
    },

    // image load
    handleImageLoad() {
      const imgEl = this.$refs.viewer?.$el?.querySelector("img");
      if (imgEl) {
        const displayedWidth = imgEl.width;
        const naturalWidth = imgEl.naturalWidth;
        this.scalingFactor = displayedWidth / naturalWidth;
      }
      this.imageLoaded = true;
    },

    // NAV
    nextPage() {
      if (this.currentPage < this.totalPages - 1) this.currentPage++;
    },
    prevPage() {
      if (this.currentPage > 0) this.currentPage--;
    },
    goToPage() {
      const newPage = Math.max(1, Math.min(this.pageInput, this.totalPages)) - 1;
      this.currentPage = newPage;
    },

    // POPUPS: lengths
    showLengthPopup(type) {
      if (type === "horizontal") {
        this.selectedMeasurement = "ascenders";
        this.showHorizontalPopup = true;
        this.showVerticalPopup = false;
      } else {
        this.selectedMeasurement = "internalMargin";
        this.showVerticalPopup = true;
        this.showHorizontalPopup = false;
      }
    },
    hideLengthPopup() {
      this.showHorizontalPopup = false;
      this.showVerticalPopup = false;
    },
    startLengthMeasurement() {
      this.lengthMeasurementActive = true;
      this.isMeasuring = true;
    },

    // POPUPS: angles label + stats
    onConfirmAngleLabel(label) {
      this.activeAngleLabel = label;
      if (label && !this.angleLabels.includes(label)) this.angleLabels.push(label);
      this.showAngleLabelPopup = false;
    },
    onCancelAngleLabel() {
      this.measureModeActive = false;
      this.activeAngleLabel = "";
      this.showAngleLabelPopup = false;
    },
    openAngleStatsPicker() {
      this.showAngleStatsPicker = true;
    },
    onConfirmAngleStats(sel) {
      this.showAngleStatsPicker = false;
      const { scope, label } = sel;
      let angles = [];
      if (scope === "current") {
        angles = (this.annotationsByPage[this.currentPage] || []).filter(a => a.type === "measure");
      } else if (scope === "entire") {
        angles = this.annotationsByPage.flat().filter(a => a && a.type === "measure");
      } else if (scope === "byLabel" && label) {
        angles = this.annotationsByPage.flat().filter(a => a && a.type === "measure" && a.label === label);
      }
      const values = angles.map(a => parseFloat(a.angle)).filter(n => !isNaN(n));
      this.angleStatistics = {
        average: this.calculateAverage(values),
        standardDeviation: this.calculateStandardDeviation(values),
        mode: this.calculateMode(values),
      };
      this.showAngleStatistics = true;
    },
    onCancelAngleStats() { this.showAngleStatsPicker = false; },

    // Drawing handlers (stage-level)
startTrace(event) {
  // 1) Length bands: two-click create rectangle
  if (this.lengthMeasurementActive) {
    const { x, y } = this.getMousePosition(event);
    if (!this.startPoint) {
      this.startPoint = { x, y };
      this.currentSquare = {
        x, y, width: 0, height: 0,
        color: this.measurementColors[this.selectedMeasurement],
        label: this.selectedMeasurement,
      };
      return;
    } else {
      const label = this.selectedMeasurement;
      if (!this.lengthMeasurements[label]) this.lengthMeasurements[label] = {};
      if (!this.lengthMeasurements[label][this.currentPage]) this.lengthMeasurements[label][this.currentPage] = [];
      this.lengthMeasurements[label][this.currentPage].push({
        ...this.currentSquare,
        type: "length",
        id: Date.now() + Math.random(),
      });
      this.startPoint = null;
      this.currentSquare = null;
      this.lengthMeasurementActive = false;
      this.isMeasuring = false;
      return;
    }
  }

  // 2) Crop start
  if (this.croppingStarted && this.cropButtonClicked && !this.croppedImage) {
    const { x, y } = this.getMousePosition(event);
    this.startPoint = { x, y };
    this.currentSquare = { x, y, width: 0, height: 0 };
    return;
  }

  // 3) Highlight / Underline: two-click flow
  if (this.highlightModeActive || this.underlineModeActive) {
    if (this.isFirstClick) {
      const { x, y } = this.getMousePosition(event);
      this.startPoint = { x, y };
      if (this.highlightModeActive) {
        this.currentSquare = { x, y, width: 0, height: 0 };
      } else {
        this.currentUnderline = { x, y, width: 0, height: 2 };
      }
      this.isFirstClick = false;
      return;
    } else {
      if (this.highlightModeActive && this.currentSquare) {
        this.annotationsByPage[this.currentPage].push({ type: "highlight", ...this.currentSquare });
        this.currentSquare = null;
      } else if (this.underlineModeActive && this.currentUnderline) {
        this.annotationsByPage[this.currentPage].push({ type: "underline", ...this.currentUnderline });
        this.currentUnderline = null;
      }
      this.isFirstClick = true;
      this.highlightModeActive = false;
      this.underlineModeActive = false;
      return;
    }
  }

  // 4) Trace start (freehand)
  if (this.traceModeActive) {
    const { x, y } = this.getMousePosition(event);
    this.currentStroke = {
      points: [{ x, y }],
      color: this.generateRandomColor(),
      penWidth: this.penWidth,
      penHeight: this.penHeight,
    };
    return;
  }

  // 5) Measure Angle: start drag on existing point OR add new point
  if (this.measureModeActive) {
    const { x, y } = this.getMousePosition(event);

    // Try to grab an existing vertex first
    const nearest = this.findNearestPoint(x, y, 10);
    if (nearest.annotationIndex !== -1) {
      this.editingAnnotationIndex = nearest.annotationIndex;
      this.draggingPoint = nearest.pointIndex;

      const ann = this.annotationsByPage[this.currentPage][this.editingAnnotationIndex];
      this.measurePoints = [...ann.points]; // work on local copy while dragging
      return;
    }

    // Otherwise: create a new angle (collect up to 3 points)
    if (this.measurePoints.length >= 3) return;
    this.measurePoints.push({ x, y });

    if (this.measurePoints.length === 3) {
      this.calculatedAngle = this.calculateAngle(
        this.measurePoints[0],
        this.measurePoints[1],
        this.measurePoints[2]
      );
      this.annotationsByPage[this.currentPage].push({
        type: "measure",
        points: [...this.measurePoints],
        angle: this.calculatedAngle,
        label: this.activeAngleLabel || "Unlabeled",
      });
      this.measurePoints = [];
    }
    return;
  }
},


trace(event) {
  // 1) Crop: dynamic rectangle sizing
  if (this.startPoint && this.cropButtonClicked && this.croppingStarted && !this.croppedImage) {
    const { x, y } = this.getMousePosition(event);
    this.currentSquare = {
      x: Math.min(x, this.startPoint.x),
      y: Math.min(y, this.startPoint.y),
      width: Math.abs(x - this.startPoint.x),
      height: Math.abs(y - this.startPoint.y),
    };
  }

  // 2) Highlight dynamic box
  if (this.highlightModeActive && this.currentSquare) {
    const { x, y } = this.getMousePosition(event);
    this.currentSquare = {
      ...this.currentSquare,
      x: Math.min(x, this.startPoint.x),
      y: Math.min(y, this.startPoint.y),
      width: Math.abs(x - this.startPoint.x),
      height: Math.abs(y - this.startPoint.y),
    };
  }

  // 3) Underline dynamic width
  if (this.underlineModeActive && this.currentUnderline) {
    const { x } = this.getMousePosition(event);
    this.currentUnderline = {
      ...this.currentUnderline,
      x: Math.min(x, this.startPoint.x),
      width: Math.abs(x - this.startPoint.x),
    };
  }

  // 4) Length bands: dynamic rectangle
  if (this.lengthMeasurementActive && this.startPoint) {
    const { x, y } = this.getMousePosition(event);
    this.currentSquare = {
      x: Math.min(x, this.startPoint.x),
      y: Math.min(y, this.startPoint.y),
      width: Math.abs(x - this.startPoint.x),
      height: Math.abs(y - this.startPoint.y),
      color: this.measurementColors[this.selectedMeasurement],
      label: this.selectedMeasurement,
    };
  }

  // 5) Trace freehand path
  if (this.traceModeActive && this.currentStroke) {
    const { x, y } = this.getMousePosition(event);
    this.currentStroke.points.push({ x, y });
  }

  // 6) Drag existing angle vertex (live update)
  if (this.measureModeActive && this.draggingPoint !== -1) {
    const { x, y } = this.getMousePosition(event);
    // Update temp copy
    this.measurePoints[this.draggingPoint] = { x, y };

    // If editing an existing annotation, update it live
    if (this.editingAnnotationIndex !== -1) {
      const ann = this.annotationsByPage[this.currentPage][this.editingAnnotationIndex];

      // Ensure measurePoints has 3 vertices
      if (this.measurePoints.length !== 3) {
        this.measurePoints = [...ann.points];
        this.measurePoints[this.draggingPoint] = { x, y };
      }

      const newAngle =
        this.measurePoints.length === 3
          ? this.calculateAngle(this.measurePoints[0], this.measurePoints[1], this.measurePoints[2])
          : ann.angle;

      this.annotationsByPage[this.currentPage][this.editingAnnotationIndex] = {
        ...ann,
        points: [...this.measurePoints],
        angle: newAngle,
      };
    }
  }
},


endTrace() {
  // 1) Finish trace stroke
  if (this.traceModeActive && this.currentStroke) {
    this.annotationsByPage[this.currentPage].push({
      type: "trace",
      points: this.currentStroke.points,
      color: this.currentStroke.color,
      penWidth: this.currentStroke.penWidth,
      penHeight: this.currentStroke.penHeight,
    });
    this.currentStroke = null;
  }

  // 2) Finish angle vertex drag
  if (this.measureModeActive && this.draggingPoint !== -1) {
    this.draggingPoint = -1;
    this.editingAnnotationIndex = -1;
    this.measurePoints = []; // clear temp after finishing drag
  }

  // 3) Finalize crop, generate preview popup
  if ((this.croppingStarted || this.currentSquare) && this.cropButtonClicked && !this.croppedImage) {
    this.generateCroppedFromCurrentSquare();
    this.croppingStarted = false;
    this.cropButtonClicked = false;
    this.currentSquare = null;
    this.startPoint = null;
  }
},

    startCrop() {
      this.croppingStarted = true;
      this.cropButtonClicked = true;
      this.currentSquare = null;
      this.startPoint = null;
      this.showToolMessage("Click and drag to crop.");
    },

    async generateCroppedFromCurrentSquare() {
      if (!this.currentSquare) return;
      const { x, y, width, height } = this.currentSquare;
      const imgEl = this.$refs.viewer?.$el?.querySelector("img");
      if (!imgEl) return;

      const naturalWidth = imgEl.naturalWidth;
      const naturalHeight = imgEl.naturalHeight;
      const rect = this.$refs.viewer.$el.getBoundingClientRect();
      const scaleX = naturalWidth / rect.width;
      const scaleY = naturalHeight / rect.height;

      const sx = x * scaleX;
      const sy = y * scaleY;
      const sw = width * scaleX;
      const sh = height * scaleY;

      const canvas = document.createElement("canvas");
      canvas.width = sw;
      canvas.height = sh;
      const ctx = canvas.getContext("2d");

      const srcImg = new Image();
      srcImg.crossOrigin = "anonymous";
      srcImg.src = this.currentImage;

      await new Promise((resolve, reject) => {
        srcImg.onload = () => {
          ctx.drawImage(srcImg, sx, sy, sw, sh, 0, 0, sw, sh);
          this.croppedImage = canvas.toDataURL("image/png");
          resolve();
        };
        srcImg.onerror = reject;
      });

      // keep SVG version for export
      this.croppedSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${sw} ${sh}" width="${sw}" height="${sh}">
          <image href="${this.currentImage}" x="${-sx}" y="${-sy}" width="${naturalWidth}" height="${naturalHeight}" />
        </svg>
      `;
      // popup sizing
      const popupWidth = (window.innerWidth * 2) / 3;
      const popupHeight = (sh / sw) * popupWidth;
      this.popupDimensions = { width: popupWidth, height: popupHeight };
    },

    // Save / export
    async saveCroppedImageAsPNG() {
      const link = document.createElement("a");
      link.href = this.croppedImage;
      link.download = "cropped-image.png";
      link.click();
    },
    saveCroppedImageAsSVG() {
      if (!this.croppedSvg) return;
      const svgBlob = new Blob([this.croppedSvg], { type: "image/svg+xml" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(svgBlob);
      link.download = "cropped-image.svg";
      link.click();
      URL.revokeObjectURL(link.href);
    },
    async saveCroppedImage() {
      const container = document.querySelector(".cropped-image-container");
      if (!container) return;
      const canvas = await html2canvas(container, {
        useCORS: true,
        backgroundColor: null,
        scale: 2,
      });
      const dataUrl = canvas.toDataURL("image/png");
      const link = document.createElement("a");
      link.href = dataUrl;
      link.download = "cropped-with-annotations.png";
      link.click();
    },
    closeCroppedPopup() { this.croppedImage = null; },

    async saveAnnotations() {
      try {
        const topBar = document.querySelector(".top-bar");
        const navigationBar = document.querySelector(".navigation-bar");
        if (topBar) topBar.style.display = "none";
        if (navigationBar) navigationBar.style.display = "none";

        const pdfDoc = await PDFDocument.create();

        for (let i = 0; i < this.images.length; i++) {
          const annotations = this.annotationsByPage[i] || [];
          const comments = this.comments[i] || [];
          const hasLengths =
            Object.values(this.lengthMeasurements).some(obj => obj[i] && obj[i].length);

          if (annotations.length === 0 && comments.length === 0 && !hasLengths) continue;

          this.currentPage = i;
          await this.$nextTick();

          const viewerEl = this.$refs.viewer?.$el;
          const canvas = await html2canvas(viewerEl, {
            scale: 2,
            useCORS: true,
            ignoreElements: (el) =>
              el.classList?.contains("top-bar") ||
              el.classList?.contains("navigation-bar"),
          });

          const imgData = canvas.toDataURL("image/png");
          const image = await pdfDoc.embedPng(imgData);
          const page = pdfDoc.addPage([image.width, image.height]);
          page.drawImage(image, { x: 0, y: 0, width: image.width, height: image.height });
        }

        const pdfBytes = await pdfDoc.save();
        const blob = new Blob([pdfBytes], { type: "application/pdf" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "annotated-document.pdf";
        link.click();
        URL.revokeObjectURL(link.href);

        if (topBar) topBar.style.display = "flex";
        if (navigationBar) navigationBar.style.display = "flex";
      } catch (e) {
        console.error("Error saving annotations:", e);
      }
    },

    // Clear menus
    toggleClearDropdown() { this.showClearDropdown = !this.showClearDropdown; },
    clearHighlights() {
      this.annotationsByPage[this.currentPage] =
        this.annotationsByPage[this.currentPage].filter(a => a.type !== "highlight");
      this.showToolMessage("Highlights cleared.");
      this.showClearDropdown = false;
    },
    clearUnderlines() {
      this.annotationsByPage[this.currentPage] =
        this.annotationsByPage[this.currentPage].filter(a => a.type !== "underline");
      this.showToolMessage("Underlines cleared.");
      this.showClearDropdown = false;
    },
    clearComments() {
      this.comments[this.currentPage] = [];
      this.showToolMessage("Comments cleared.");
      this.showClearDropdown = false;
    },
    clearTraces() {
      this.annotationsByPage[this.currentPage] =
        this.annotationsByPage[this.currentPage].filter(a => a.type !== "trace");
      this.showToolMessage("Traces cleared.");
      this.showClearDropdown = false;
    },
    clearAngles() {
      this.annotationsByPage[this.currentPage] =
        this.annotationsByPage[this.currentPage].filter(a => a.type !== "measure");
      this.showToolMessage("Angles cleared.");
      this.showClearDropdown = false;
    },
    clearHorizontalLengths() {
      const list = ["ascenders","descenders","interlinear","upperMargin","lowerMargin","lineHeight","minimumHeight"];
      list.forEach(t => { if (this.lengthMeasurements[t]) delete this.lengthMeasurements[t][this.currentPage]; });
      this.showToolMessage("Horizontal lengths cleared.");
      this.showClearDropdown = false;
    },
    clearVerticalLengths() {
      ["internalMargin","intercolumnSpaces"].forEach(t => {
        if (this.lengthMeasurements[t]) delete this.lengthMeasurements[t][this.currentPage];
      });
      this.showToolMessage("Vertical lengths cleared.");
      this.showClearDropdown = false;
    },
    clearAll() {
      this.annotationsByPage[this.currentPage] = [];
      this.comments[this.currentPage] = [];
      ["ascenders","descenders","interlinear","upperMargin","lowerMargin","internalMargin","intercolumnSpaces","lineHeight","minimumHeight"].forEach(t => {
        if (this.lengthMeasurements[t]) delete this.lengthMeasurements[t][this.currentPage];
      });
      this.measurePoints = [];
      this.calculatedAngle = 0;
      this.showToolMessage("All annotations cleared.");
      this.showClearDropdown = false;
    },

    // Calculate statistics (bands)
    toggleCalculateDropdown() { this.showCalculateDropdown = !this.showCalculateDropdown; },
    calculateCurrentPage() {
      this.showCalculateDropdown = false;
      this.showStatisticsPopup(this.getCurrentPageStatistics());
    },
    calculateEntireDocument() {
      this.showCalculateDropdown = false;
      this.showStatisticsPopup(this.getEntireDocumentStatistics());
    },
    extractValues(measurements, type) {
      const vertical = ["internalMargin", "intercolumnSpaces"].includes(type);
      return measurements.map((m) => (vertical ? m.width : m.height));
    },
    getCurrentPageStatistics() {
      const horizontal = ["ascenders","descenders","interlinear","upperMargin","lowerMargin","lineHeight","minimumHeight"];
      const vertical = ["internalMargin", "intercolumnSpaces"];
      const stats = {};
      horizontal.forEach((t) => {
        if (this.lengthMeasurements[t]?.[this.currentPage]) {
          const vals = this.extractValues(this.lengthMeasurements[t][this.currentPage], t);
          stats[t] = {
            average: this.calculateAverage(vals),
            standardDeviation: this.calculateStandardDeviation(vals),
            mode: this.calculateMode(vals),
          };
        }
      });
      vertical.forEach((t) => {
        if (this.lengthMeasurements[t]?.[this.currentPage]) {
          const vals = this.extractValues(this.lengthMeasurements[t][this.currentPage], t);
          stats[t] = {
            average: this.calculateAverage(vals),
            standardDeviation: this.calculateStandardDeviation(vals),
            mode: this.calculateMode(vals),
          };
        }
      });
      return stats;
    },

      findNearestPoint(x, y, threshold = 10) {
    const measures = (this.annotationsByPage[this.currentPage] || [])
      .map((a, i) => ({ a, i }))
      .filter(({ a }) => a && a.type === "measure");

    let best = { annotationIndex: -1, pointIndex: -1, dist: Infinity };

    measures.forEach(({ a, i }) => {
      a.points.forEach((p, pi) => {
        const d = Math.hypot(x - p.x, y - p.y);
        if (d < threshold && d < best.dist) {
          best = { annotationIndex: i, pointIndex: pi, dist: d };
        }
      });
    });

    return { annotationIndex: best.annotationIndex, pointIndex: best.pointIndex };
  },
    getEntireDocumentStatistics() {
      const horizontal = ["ascenders","descenders","interlinear","upperMargin","lowerMargin","lineHeight","minimumHeight"];
      const vertical = ["internalMargin", "intercolumnSpaces"];
      const stats = {};
      horizontal.forEach((t) => {
        let vals = [];
        for (let p = 0; p < this.totalPages; p++) {
          if (this.lengthMeasurements[t]?.[p]) {
            vals = vals.concat(this.extractValues(this.lengthMeasurements[t][p], t));
          }
        }
        stats[t] = {
          average: this.calculateAverage(vals),
          standardDeviation: this.calculateStandardDeviation(vals),
          mode: this.calculateMode(vals),
        };
      });
      vertical.forEach((t) => {
        let vals = [];
        for (let p = 0; p < this.totalPages; p++) {
          if (this.lengthMeasurements[t]?.[p]) {
            vals = vals.concat(this.extractValues(this.lengthMeasurements[t][p], t));
          }
        }
        stats[t] = {
          average: this.calculateAverage(vals),
          standardDeviation: this.calculateStandardDeviation(vals),
          mode: this.calculateMode(vals),
        };
      });
      return stats;
    },
    showStatisticsPopup(statistics) {
      this.horizontalStatistics = {};
      this.verticalStatistics = {};
      for (const [type, s] of Object.entries(statistics)) {
        if (["ascenders","descenders","interlinear","upperMargin","lowerMargin","lineHeight","minimumHeight"].includes(type)) {
          this.horizontalStatistics[type] = s;
        } else if (["internalMargin","intercolumnSpaces"].includes(type)) {
          this.verticalStatistics[type] = s;
        }
      }
      this.showStatistics = true;
    },
    closeStatisticsPopup() { this.showStatistics = false; },

    // labels drag for bands
    startLabelDrag(id, event) {
      this.draggedLabelIndex = id;
      const pos = this.labelPositions[id] || { x: 15, y: 0 };
      this.labelDragOffset = { x: event.clientX - pos.x, y: event.clientY - pos.y };
      window.addEventListener("mousemove", this._onLabelDragMove);
      window.addEventListener("mouseup", this.stopLabelDrag);
    },
    dragLabel(id, event) {
      if (this.draggedLabelIndex !== id) return;
      const x = event.clientX - this.labelDragOffset.x;
      const y = event.clientY - this.labelDragOffset.y;
      this.labelPositions[id] = { x, y };
    },
    stopLabelDrag() {
      this.draggedLabelIndex = null;
      window.removeEventListener("mousemove", this._onLabelDragMove);
      window.removeEventListener("mouseup", this.stopLabelDrag);
    },

    // comments
    onAddComment(payload) {
      if (!this.comments[this.currentPage]) this.comments[this.currentPage] = [];
      this.comments[this.currentPage].push({
        text: payload.text || "",
        x: payload.x,
        y: payload.y,
      });
      this.currentCommentText = "";
      this.showCommentInput = false;
    },
    cancelComment() {
      this.currentCommentText = "";
      this.currentCommentPosition = null;
      this.showCommentInput = false;
    },
    startDraggingComment({ index, event }) {
      this.draggingCommentIndex = index;
      const c = this.comments[this.currentPage][index];
      this.dragOffset = { x: event.clientX - c.x, y: event.clientY - c.y };
    },
    dragComment(event) {
      if (this.draggingCommentIndex == null) return;
      const c = this.comments[this.currentPage][this.draggingCommentIndex];
      c.x = event.clientX - this.dragOffset.x;
      c.y = event.clientY - this.dragOffset.y;
    },
    stopDraggingComment() {
      this.draggingCommentIndex = null;
    },

    // cropped popup interactions (highlights / underline / trace / angles)
    getCroppedMousePosition(event) {
      const container = document.querySelector(".cropped-image-container");
      const img = container?.querySelector(".cropped-image");
      if (!img) return { x: 0, y: 0 };
      const r = img.getBoundingClientRect();
      return { x: event.clientX - r.left, y: event.clientY - r.top };
    },
    startCroppedAnnotation(event) {
      if (!this.croppedImage) return;
      const pos = this.getCroppedMousePosition(event);

      if (this.highlightModeActive || this.underlineModeActive) {
        if (this.isFirstClick) {
          this.startPoint = pos;
          this.isFirstClick = false;
          if (this.highlightModeActive) {
            this.croppedCurrentHighlight = { start: pos, current: pos, style: this.getHighlightStyle(pos, pos) };
          } else {
            this.croppedCurrentUnderline = { start: pos, current: pos.x, style: this.getUnderlineStyle(pos, pos.x) };
          }
        } else {
          const finalPos = this.getCroppedMousePosition(event);
          if (this.highlightModeActive) {
            this.croppedHighlights.push({ style: this.getHighlightStyle(this.startPoint, finalPos) });
            this.croppedCurrentHighlight = null;
          } else {
            this.croppedUnderlines.push({ style: this.getUnderlineStyle(this.startPoint, finalPos.x) });
            this.croppedCurrentUnderline = null;
          }
          this.isFirstClick = true;
          this.highlightModeActive = false;
          this.underlineModeActive = false;
        }
        return;
      }

      if (this.traceModeActive) {
        this.croppedCurrentStroke = { points: [pos], color: this.generateRandomColor() };
        return;
      }

      if (this.measureModeActive) {
        if (this.croppedDraggingPoint !== -1) return;
        if (this.croppedMeasurePoints.length === 3) {
          this.croppedMeasures.push({ points: [...this.croppedMeasurePoints], angle: this.croppedCalculatedAngle });
          this.croppedMeasurePoints = [];
          this.croppedCalculatedAngle = null;
        }
        this.croppedMeasurePoints.push({ x: pos.x, y: pos.y });
        if (this.croppedMeasurePoints.length === 3) {
          this.croppedCalculatedAngle = this.calculateAngle(
            this.croppedMeasurePoints[0], this.croppedMeasurePoints[1], this.croppedMeasurePoints[2]
          );
        }
      }
    },
    handleCroppedAnnotation(event) {
      if (!this.croppedImage) return;
      const pos = this.getCroppedMousePosition(event);

      if (this.highlightModeActive && this.croppedCurrentHighlight && this.startPoint) {
        this.croppedCurrentHighlight.style = this.getHighlightStyle(this.startPoint, pos);
      } else if (this.underlineModeActive && this.croppedCurrentUnderline && this.startPoint) {
        this.croppedCurrentUnderline.style = this.getUnderlineStyle(this.startPoint, pos.x);
      }

      if (this.croppedCurrentStroke) this.croppedCurrentStroke.points.push(pos);

      if (this.measureModeActive && this.croppedDraggingPoint !== -1 && this.croppedMeasurePoints.length === 3) {
        if (this.croppedMeasurePoints[this.croppedDraggingPoint]) {
          this.croppedMeasurePoints[this.croppedDraggingPoint] = { x: pos.x, y: pos.y };
          if (this.croppedMeasurePoints.length === 3) {
            this.croppedCalculatedAngle = this.calculateAngle(
              this.croppedMeasurePoints[0], this.croppedMeasurePoints[1], this.croppedMeasurePoints[2]
            );
          }
        }
      }
    },
    endCroppedAnnotation() {
      if (this.croppedCurrentStroke) {
        this.croppedStrokes.push(this.croppedCurrentStroke);
        this.croppedCurrentStroke = null;
      }
      if (this.measureModeActive && this.croppedDraggingPoint !== -1) this.croppedDraggingPoint = -1;

      if (this.measureModeActive && this.croppedMeasurePoints.length === 3 && this.croppedDraggingPoint === -1) {
        this.croppedMeasurePoints = [];
        this.croppedCalculatedAngle = null;
      }
    },
    getHighlightStyle(start, end) {
      return {
        left: `${Math.min(start.x, end.x)}px`,
        top: `${Math.min(start.y, end.y)}px`,
        width: `${Math.abs(end.x - start.x)}px`,
        height: `${Math.abs(end.y - start.y)}px`,
      };
    },
    getUnderlineStyle(start, currentX) {
      return {
        left: `${Math.min(start.x, currentX)}px`,
        top: `${start.y}px`,
        width: `${Math.abs(currentX - start.x)}px`,
      };
    },

    // angle editing
    startDraggingPoint(index, event) {
      event.preventDefault();
      event.stopPropagation();
      this.draggingPoint = index;
    },

    // colors
    generateRandomColor() {
      const palette = ["#E69F00","#56B4E9","#009E73","#F0E442","#0072B2","#D55E00","#CC79A7"];
      if (!this.lastColor) this.lastColor = null;
      const avail = palette.filter(c => c !== this.lastColor);
      const selected = avail[Math.floor(Math.random() * avail.length)];
      this.lastColor = selected;
      return selected;
    },

    // math helpers
    calculateAverage(values) {
      if (!values?.length) return 0;
      const nums = values.map(v => +v).filter(v => !isNaN(v));
      if (!nums.length) return 0;
      return nums.reduce((a,b)=>a+b,0) / nums.length;
    },
    calculateStandardDeviation(values) {
      if (!values?.length) return 0;
      const nums = values.map(v => +v).filter(v => !isNaN(v));
      if (!nums.length) return 0;
      const avg = this.calculateAverage(nums);
      const variance = nums.reduce((acc,v)=>acc + (v-avg)**2, 0) / nums.length;
      return Math.sqrt(variance);
    },
    calculateMode(values) {
      if (!values?.length) return "No mode";
      const nums = values.map(v => +v).filter(v => !isNaN(v));
      if (!nums.length) return "No mode";
      const freq = {};
      nums.forEach(v => freq[v] = (freq[v]||0)+1);
      const max = Math.max(...Object.values(freq));
      if (max === 1) return "No mode";
      const modes = Object.keys(freq).filter(k => freq[k] === max);
      return parseFloat(Math.min(...modes));
    },
  },
};
</script>

<style scoped>
* { font-family: "Arial","Helvetica",sans-serif !important; }
.viewer-container { display: flex; flex-direction: column; height: 100vh; background-color: #f1f1f1; }

/* Toolbar / Nav shared classes used by saveAnnotations() */
.top-bar {
  display: flex; justify-content: space-between; align-items: center;
  background-color: #f1f1f1; border-bottom: 1px solid #ddd; padding: 10px 20px;
}
.navigation-bar { display: flex; justify-content: center; align-items: center; margin: 10px 0; gap: 10px; }

/* Stage */
.drawing-layer { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; }

/* Cropping overlay */
.cropping-rectangle {
  position: absolute;
  border: 2px dashed #007bff;
  background-color: rgba(0,123,255,0.2);
  pointer-events: none;
  z-index: 100;
}

/* Highlight / underline */
.highlight-rectangle {
  position: absolute;
  border: 2px solid rgba(255, 255, 0, 0.7);
  background-color: rgba(255, 255, 0, 0.3);
  pointer-events: none;
}
.underline-line {
  position: absolute;
  background-color: blue;
  height: 2px;
  pointer-events: none;
  z-index: 1100;
}

/* Tool message toast */
.tool-message {
  position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
  background-color: #007bff; color: #fff; padding: 10px 20px; border-radius: 5px;
  z-index: 1100; font-size: 14px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
</style>
