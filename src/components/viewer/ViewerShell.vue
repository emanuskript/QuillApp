<template>
  <div class="viewer-container">
    <!-- Toolbar -->
    <Toolbar
      :activeTool="activeTool"
      @select-tool="selectTool"
      @show-length-popup="showLengthPopup"
      @calculate="handleCalculate"
      @clear="handleClear"
      @save="saveAnnotations"
    />

    <!-- Navigation Bar -->
    <NavigationBar
      :currentPage="currentPage"
      :totalPages="totalPages"
      @prev="prevPage"
      @next="nextPage"
      @go-to="goToPage"
    />

    <!-- Main Image Stage -->
    <ImageStage
      :image="currentImage"
      :cursorMode="cursorMode"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @image-load="handleImageLoad"
    >
      <!-- Overlays -->
      <TracesLayer :annotations="currentPageTraces" :dynamicTrace="dynamicTrace" />
      <AnglesLayer :annotations="currentPageAngles" :measurePoints="measurePoints" />
      <HighlightsLayer :annotations="currentPageHighlights" :current="currentHighlight" />
      <UnderlinesLayer :annotations="currentPageUnderlines" :current="currentUnderline" />
      <LengthsLayer
        :measurements="currentPageLengths"
        :current="currentSquare"
        :labelPositions="labelPositions"
      />
      <CommentsLayer
        :comments="currentPageComments"
        :showInput="showCommentInput"
        :currentText="currentCommentText"
        @add="addComment"
        @cancel="cancelComment"
        @start-drag="startDraggingComment"
        @drag="dragComment"
        @stop-drag="stopDraggingComment"
      />
    </ImageStage>

    <!-- Popups -->
    <PenSelectionPopup
      v-if="showPenSelectionPopup"
      :angles="penAngles"
      :selected="selectedPenAngle"
      @select="selectPen"
      @confirm="confirmPenSelection"
      @cancel="cancelPenSelection"
    />

    <StatisticsPopup
      v-if="showStatistics"
      :horizontal="horizontalStatistics"
      :vertical="verticalStatistics"
      @close="closeStatisticsPopup"
    />

    <AngleStatisticsPopup
      v-if="showAngleStatistics"
      :stats="angleStatistics"
      @close="closeAngleStatisticsPopup"
    />

    <LengthPopupHorizontal
      v-if="showHorizontalPopup"
      :selected="selectedMeasurement"
      :colors="measurementColors"
      @confirm="confirmLengthMeasurement"
      @cancel="hideLengthPopup"
    />

    <LengthPopupVertical
      v-if="showVerticalPopup"
      :selected="selectedMeasurement"
      :colors="measurementColors"
      @confirm="confirmLengthMeasurement"
      @cancel="hideLengthPopup"
    />

    <CroppedPreviewPopup
      v-if="croppedImage"
      :image="croppedImage"
      :annotations="croppedAnnotations"
      @save-png="saveCroppedImageAsPNG"
      @save-svg="saveCroppedImageAsSVG"
      @save-annotated="saveCroppedImage"
      @close="closeCroppedPopup"
    />
  </div>
</template>

<script>
import Toolbar from "./Toolbar.vue";
import NavigationBar from "./NavigationBar.vue";
import ImageStage from "./ImageStage.vue";
import TracesLayer from "./TracesLayer.vue";
import AnglesLayer from "./AnglesLayer.vue";
import HighlightsLayer from "./HighlightsLayer.vue";
import UnderlinesLayer from "./UnderlinesLayer.vue";
import LengthsLayer from "./LengthsLayer.vue";
import CommentsLayer from "./CommentsLayer.vue";

// Popups
import PenSelectionPopup from "../popups/PenSelectionPopup.vue";
import StatisticsPopup from "../popups/StatisticsPopup.vue";
import AngleStatisticsPopup from "../popups/AngleStatisticsPopup.vue";
import LengthPopupHorizontal from "../popups/LengthPopupHorizontal.vue";
import LengthPopupVertical from "../popups/LengthPopupVertical.vue";
import CroppedPreviewPopup from "../popups/CroppedPreviewPopup.vue";

export default {
  name: "ViewerShell",
  props: {
    source: { type: String, required: true },
  },
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
  },
  data() {
    return {
      activeTool: null,
      cursorMode: "default",
      currentPage: 0,
      totalPages: 1,
      images: [],
      // placeholders for state
      measurePoints: [],
      currentSquare: null,
      currentHighlight: null,
      currentUnderline: null,
      dynamicTrace: null,
      labelPositions: {},
      comments: [],
      currentCommentText: "",
      showCommentInput: false,
      croppedImage: null,
      croppedAnnotations: [],
      penAngles: [0, 25, 30, 50, 80],
      selectedPenAngle: null,
      showPenSelectionPopup: false,
      showStatistics: false,
      showAngleStatistics: false,
      angleStatistics: {},
      horizontalStatistics: {},
      verticalStatistics: {},
      showHorizontalPopup: false,
      showVerticalPopup: false,
      selectedMeasurement: "ascenders",
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
    };
  },
  computed: {
    currentImage() {
      return this.images[this.currentPage] || null;
    },
    currentPageTraces() {
      return [];
    },
    currentPageAngles() {
      return [];
    },
    currentPageHighlights() {
      return [];
    },
    currentPageUnderlines() {
      return [];
    },
    currentPageLengths() {
      return [];
    },
    currentPageComments() {
      return this.comments[this.currentPage] || [];
    },
  },
  methods: {
    selectTool(tool) {
      this.activeTool = tool;
      this.cursorMode = ["trace", "highlight", "underline", "measure"].includes(tool)
        ? "crosshair"
        : "default";
    },
    showLengthPopup(type) {
      if (type === "horizontal") this.showHorizontalPopup = true;
      if (type === "vertical") this.showVerticalPopup = true;
    },
    hideLengthPopup() {
      this.showHorizontalPopup = false;
      this.showVerticalPopup = false;
    },
    handleCalculate(action) {
      console.log("Calculate requested:", action);
    },
    handleClear(action) {
      console.log("Clear requested:", action);
    },
    saveAnnotations() {
      console.log("Save requested");
    },
    onMouseDown(e) {
      this.$emit("mousedown", e);
    },
    onMouseMove(e) {
      this.$emit("mousemove", e);
    },
    onMouseUp(e) {
      this.$emit("mouseup", e);
    },
    handleImageLoad(e) {
      console.log("Image loaded", e);
    },
    nextPage() {
      if (this.currentPage < this.totalPages - 1) this.currentPage++;
    },
    prevPage() {
      if (this.currentPage > 0) this.currentPage--;
    },
    goToPage(page) {
      if (page >= 0 && page < this.totalPages) this.currentPage = page;
    },
    confirmPenSelection() {
      this.showPenSelectionPopup = false;
    },
    cancelPenSelection() {
      this.showPenSelectionPopup = false;
    },
    closeStatisticsPopup() {
      this.showStatistics = false;
    },
    closeAngleStatisticsPopup() {
      this.showAngleStatistics = false;
    },
    confirmLengthMeasurement() {
      this.hideLengthPopup();
    },
    closeCroppedPopup() {
      this.croppedImage = null;
    },
    addComment(text) {
      if (!this.comments[this.currentPage]) this.comments[this.currentPage] = [];
      this.comments[this.currentPage].push({ text, x: 100, y: 100 });
    },
    cancelComment() {
      this.showCommentInput = false;
      this.currentCommentText = "";
    },
    startDraggingComment(index, e) {
      console.log("Start dragging comment", index, e);
    },
    dragComment(e) {
      console.log("Dragging comment", e);
    },
    stopDraggingComment() {
      console.log("Stop dragging comment");
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
</style>
