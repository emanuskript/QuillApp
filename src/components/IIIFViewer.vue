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
        <div
          class="toolbar-item"
          @click="selectTool('trace')"
          data-tool="trace"
        >
          <i class="fa-solid fa-pencil"></i>
          <span>Trace</span>
        </div>
        <div
          class="toolbar-item"
          @click="selectTool('measure')"
          data-tool="measure"
        >
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

        <div class="toolbar-item" @click="startCrop">
          <i class="fa-solid fa-scissors"></i>
          <span>Crop</span>
        </div>

        <div class="tool-message" v-if="toolMessage">{{ toolMessage }}</div>

        <!-- Add the Calculate button -->
        <div
          class="toolbar-item calculate-container"
          @click.stop="toggleCalculateDropdown"
        >
          <i class="fa-solid fa-calculator"></i>
          <span>Generate</span>
          <span>Statistics</span>
          <!-- Dropdown Menu -->
          <div v-if="showCalculateDropdown" class="calculate-dropdown">
            <div @click.stop="calculateCurrentPage">
              Lengths Measurements (Current Page)
            </div>
            <div @click.stop="calculateEntireDocument">
              Lengths Measurements (Full Document)
            </div>
            <div @click.stop="calculateAngleStatistics">Angle Measurements</div>
          </div>
        </div>
        <div class="toolbar-item" @click="saveAnnotations">
          <i class="fa-solid fa-save"></i>
          <span>Save</span>
        </div>
        <div
          class="toolbar-item clear-container"
          @click.stop="toggleClearDropdown"
        >
          <i class="fa-regular fa-trash-can"></i>
          <span>Clear</span>
          <!-- Dropdown Menu -->
          <div v-if="showClearDropdown" class="clear-dropdown">
            <div @click.stop="clearHighlights">Clear Highlights</div>
            <div @click.stop="clearUnderlines">Clear Underlines</div>
            <div @click.stop="clearComments">Clear Comments</div>
            <div @click.stop="clearTraces">Clear Traces</div>
            <div @click.stop="clearAngles">Clear Angles</div>
            <div @click.stop="clearHorizontalLengths">
              Clear Horizontal Lengths
            </div>
            <div @click.stop="clearVerticalLengths">Clear Vertical Lengths</div>
            <div @click.stop="clearAll">Clear All</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Trace Pen Selection Popup -->
    <div v-if="showPenSelectionPopup" class="pen-selection-popup">
      <div class="pen-selection-content">
        <h3 style="margin-top: 20px">Select a Pen</h3>
        <div class="pen-options">
          <div
            v-for="angle in penAngles"
            :key="angle"
            class="pen-option"
            @click="selectPen(angle)"
            :class="{ selected: selectedPenAngle === angle }"
          >
            <div
              class="pen-preview"
              :style="{ transform: `rotate(${-angle}deg)` }"
            >
              <!-- Simulate the pen nib -->
              <div class="pen-nib"></div>
            </div>
            <span class="pen-angle-text">{{ angle }}°</span>
          </div>
        </div>
        <div class="test-box">
          <h4>Test Your Pen</h4>
          <div
            class="test-area"
            @mousedown="startTestTrace"
            @mousemove="testTrace"
            @mouseup="endTestTrace"
            @mouseleave="endTestTrace"
          >
            <svg class="test-svg">
              <polyline
                v-if="testTracePath.length > 0"
                :points="formatPoints(testTracePath)"
                stroke="black"
                :stroke-width="penWidth"
                :stroke-height="penHeight"
                fill="none"
              />
            </svg>
          </div>
        </div>
        <div class="pen-selection-actions">
          <button @click="confirmPenSelection">Confirm</button>
          <button @click="cancelPenSelection">Cancel</button>
        </div>
      </div>
    </div>
    <!-- Angle Statistics Popup -->
    <div v-if="showAngleStatistics" class="statistics-popup">
      <div class="statistics-popup-content">
        <h3>Angle Statistics</h3>
        <table>
          <thead>
            <tr>
              <th>Average</th>
              <th>Standard Deviation</th>
              <th>Mode</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ angleStatistics.average.toFixed(2) }}</td>
              <td>{{ angleStatistics.standardDeviation.toFixed(2) }}</td>
              <td>
                {{
                  typeof angleStatistics.mode === "number"
                    ? angleStatistics.mode.toFixed(2)
                    : angleStatistics.mode
                }}
              </td>
            </tr>
          </tbody>
        </table>
        <button @click="closeAngleStatisticsPopup">Close</button>
      </div>
    </div>

    <!-- Blurred Background -->
    <div v-if="croppedImage" class="blurred-background" style="top: 90px"></div>

    <!-- Cropped Image Popup -->
    <div v-if="croppedImage" class="cropped-popup">
      <div class="cropped-popup-content">
        <h3>Cropped Image</h3>
        <hr class="popup-divider" />
        <div
          class="cropped-image-container"
          ref="croppedContainer"
          @mousedown="startCroppedAnnotation"
          @mousemove="handleCroppedAnnotation"
          @mouseup="endCroppedAnnotation"
          @mouseleave="endCroppedAnnotation"
        >
          <img
            :src="croppedImage"
            alt="Cropped"
            class="cropped-image"
            draggable="false"
            style="display: block; width: 100%; height: auto"
          />

          <!-- Annotation Layers -->
          <!-- Highlights -->
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

          <!-- Underlines -->
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

          <!-- Dynamic Trace (while drawing) -->
          <svg
            class="drawing-layer"
            :width="popupDimensions.width"
            :height="popupDimensions.height"
            style="
              position: absolute;
              top: 0;
              left: 0;
              width: 100%;
              height: 100%;
              z-index: 2;
            "
          >
            <!-- Cropped Traces -->
            <polyline
              v-for="(stroke, index) in croppedStrokes"
              :key="'cstroke-' + index"
              :points="formatPoints(stroke.points)"
              :stroke="stroke.color"
              stroke-width="2"
              fill="none"
            />
            <!-- Dynamic trace while drawing -->
            <polyline
              v-if="
                croppedCurrentStroke &&
                croppedCurrentStroke.points &&
                croppedCurrentStroke.points.length
              "
              :points="formatPoints(croppedCurrentStroke.points)"
              :stroke="croppedCurrentStroke.color"
              stroke-width="2"
              fill="none"
            />
            <!-- Cropped Angles -->
            <!-- Finalized cropped angles -->
            <g v-if="croppedMeasurePoints.length">
              <circle
                v-for="(point, index) in croppedMeasurePoints"
                :key="'cmeasure-point-' + index"
                :cx="point.x"
                :cy="point.y"
                r="5"
                fill="red"
                @mousedown.stop="croppedDraggingPoint = index"
              />
              <line
                v-if="croppedMeasurePoints.length >= 2"
                :x1="croppedMeasurePoints[0].x"
                :y1="croppedMeasurePoints[0].y"
                :x2="croppedMeasurePoints[1].x"
                :y2="croppedMeasurePoints[1].y"
                stroke="blue"
                stroke-width="2"
              />
              <line
                v-if="croppedMeasurePoints.length === 3"
                :x1="croppedMeasurePoints[1].x"
                :y1="croppedMeasurePoints[1].y"
                :x2="croppedMeasurePoints[2].x"
                :y2="croppedMeasurePoints[2].y"
                stroke="blue"
                stroke-width="2"
              />
              <text
                v-if="
                  croppedMeasurePoints.length === 3 && croppedCalculatedAngle
                "
                :x="croppedMeasurePoints[1].x + 10"
                :y="croppedMeasurePoints[1].y - 10"
                fill="darkblue"
                font-size="12"
              >
                {{ croppedCalculatedAngle }}°
              </text>
            </g>
            <!-- Finalized angles -->
            <g
              v-for="(measure, index) in croppedMeasures"
              :key="'cmeasure-' + index"
            >
              <line
                v-if="measure.points.length >= 2"
                :x1="measure.points[0].x"
                :y1="measure.points[0].y"
                :x2="measure.points[1].x"
                :y2="measure.points[1].y"
                stroke="blue"
                stroke-width="2"
              />
              <line
                v-if="measure.points.length === 3"
                :x1="measure.points[1].x"
                :y1="measure.points[1].y"
                :x2="measure.points[2].x"
                :y2="measure.points[2].y"
                stroke="blue"
                stroke-width="2"
              />
              <text
                v-if="measure.points.length === 3 && measure.angle"
                :x="measure.points[1].x + 10"
                :y="measure.points[1].y - 10"
                fill="darkblue"
                font-size="12"
              >
                {{ measure.angle }}°
              </text>
              <circle
                v-for="(point, pi) in measure.points"
                :key="'cmeasure-final-point-' + pi"
                :cx="point.x"
                :cy="point.y"
                r="5"
                fill="red"
                pointer-events:
                all
              />
            </g>
          </svg>
        </div>
        <div class="popup-actions">
          <button @click="saveCroppedImageAsPNG">Save as PNG</button>
          <button @click="saveCroppedImageAsSVG">Save as SVG</button>
          <button @click="saveCroppedImage">Save with Annotations</button>
          <button @click="closeCroppedPopup">Close</button>
        </div>
      </div>
    </div>

    <!-- Horizontal Bands Popup -->
    <!-- filepath: /Users/mohamedbasuony/quill_1.0/src/components/IIIFViewer.vue -->
    <div v-if="showHorizontalPopup" class="length-popup">
      <div class="length-popup-content">
        <h3>Select Horizontal Measurement Type</h3>
        <select v-model="selectedMeasurement">
          <option value="ascenders">Ascenders</option>
          <option value="descenders">Descenders</option>
          <option value="interlinear">Interlinear Spaces</option>
          <option value="upperMargin">Upper Margin</option>
          <option value="lowerMargin">Lower Margin</option>
          <option value="lineHeight">Line Height</option>
          <!-- New -->
          <option value="minimumHeight">Minimum Height</option>
          <!-- New -->
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
          <div style="padding: 10px; text-align: center">
            <div style="font-size: 12px; margin-bottom: 10px">Line Height</div>
            <div
              :style="{ backgroundColor: measurementColors.lineHeight }"
              class="color-box"
              style="margin: 0 auto"
            ></div>
          </div>
          <div style="padding: 10px; text-align: center">
            <div style="font-size: 12px; margin-bottom: 10px">
              Minimum Height
            </div>
            <div
              :style="{ backgroundColor: measurementColors.minimumHeight }"
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
    <!-- filepath: /Users/mohamedbasuony/quill_1.0/src/components/IIIFViewer.vue -->
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
              Internal Margin
            </div>
            <div
              :style="{ backgroundColor: measurementColors.internalMargin }"
              class="color-box"
              style="margin: 0 auto"
            ></div>
          </div>
          <div style="padding: 10px; text-align: center">
            <div style="font-size: 12px; margin-bottom: 10px">
              Intercolumn Spaces
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
      @mouseup="endTrace"
      ref="viewer"
    >
      <img
        v-if="croppedImage || currentImage"
        :src="croppedImage || currentImage"
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
        draggable="false"
      />

      <svg
        v-if="showTraces"
        class="drawing-layer"
        :width="viewerWidth"
        :height="viewerHeight"
      >
        <!-- Render existing traces -->
        <polyline
          v-for="(stroke, index) in currentPageStrokes"
          :key="'stroke-' + index"
          :points="formatPoints(stroke.points)"
          :stroke="stroke.color"
          :stroke-width="stroke.penWidth"
          :stroke-height="stroke.penHeight"
          fill="none"
        />

        <circle
          v-for="(point, index) in measurePoints"
          :key="'measure-point-' + index"
          :cx="point.x"
          :cy="point.y"
          r="5"
          fill="red"
          @mousedown.stop="startDraggingPoint(index, $event)"
        />
        <!-- Render existing angles -->
        <g
          v-for="(annotation, index) in annotationsByPage[currentPage]"
          :key="'angle-' + index"
        >
          <line
            v-if="
              annotation.type === 'measure' && annotation.points.length >= 2
            "
            :x1="annotation.points[0].x"
            :y1="annotation.points[0].y"
            :x2="annotation.points[1].x"
            :y2="annotation.points[1].y"
            stroke="blue"
            stroke-width="2"
          />
          <line
            v-if="
              annotation.type === 'measure' && annotation.points.length === 3
            "
            :x1="annotation.points[1].x"
            :y1="annotation.points[1].y"
            :x2="annotation.points[2].x"
            :y2="annotation.points[2].y"
            stroke="blue"
            stroke-width="2"
          />
          <text
            v-if="
              annotation.type === 'measure' && annotation.points.length === 3
            "
            :x="annotation.points[1].x + 10"
            :y="annotation.points[1].y - 10"
            font-size="12"
            fill="darkblue"
            style="background-color: black; padding: 10px"
          >
            {{ annotation.angle }}°
          </text>
        </g>

        <!-- Render dynamic trace -->
        <polyline
          v-if="dynamicTracePath"
          :points="dynamicTracePath"
          stroke="red"
          stroke-width="2"
          fill="none"
        />
      </svg>
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
            measurement.label === "lowerMargin" ||
            measurement.label === "minimumHeight" ||
            measurement.label === "lineHeight"
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
        v-if="underlineModeActive && currentUnderline"
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
      penWidth: 3, // Default pen width
      penHeight: 6, // Default pen height
      showTraces: false,
      showStatistics: false,
      showAngleStatistics: false,
      isCreatingAngle: false, // Track if a new angle is being created
      activeAngleIndex: -1,
      showPenSelectionPopup: false,
      showClearDropdown: false,
      penAngles: [0, 25, 30, 50, 80], // Available pen angles
      selectedPenAngle: null, // Currently selected pen angle
      testTracePath: "", // Path for testing the pen
      images: [],
      angleStatistics: {},
      croppedAnnotations: [],
      croppedStrokes: [],
      croppedMeasures: [],
      croppedHighlights: [],
      croppedUnderlines: [],
      croppedMeasurePoints: [],
      croppedCalculatedAngle: null,
      croppedDraggingPoint: -1,
      croppedCurrentStroke: null,
      croppedCurrentMeasure: null,
      croppedCurrentHighlight: null,
      croppedCurrentUnderline: null,
      isFirstClick: true,
      horizontalStatistics: {}, // Stores horizontal statistics
      verticalStatistics: {},
      annotationsByPage: [],
      showCalculateDropdown: false,
      toolMessage: "",
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
        lineHeight: "rgba(100, 100, 255, 0.5)", // New: Transparent blue-purple
        minimumHeight: "rgba(255, 100, 100, 0.5)", // New: Transparent red-pink
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
        lineHeight: {}, // New
        minimumHeight: {}, // New
      },
      currentStroke: null,
      dynamicTracePath: "",
      measurePoints: [], // Points for angle measurement
      draggingPoint: -1, // Index of the point being dragged
      calculatedAngle: 0, // Measured angle between the points
      measureModeActive: false,
      traceModeActive: false,
      cropButtonClicked: false,
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
      editingAnnotationIndex: -1,
      draggingCommentIndex: null, // Index of the comment being dragged
      dragOffset: { x: 0, y: 0 }, // Offset between the mouse and comment position
      scalingFactor: 1,
    };
  },
  computed: {
    viewerWidth() {
      const viewer = this.$refs.viewer;
      return viewer ? viewer.clientWidth : 0;
    },
    currentPageAngleMeasurements() {
      return (
        this.annotationsByPage[this.currentPage]?.filter(
          (annotation) => annotation.type === "measure"
        ) || []
      );
    },
    viewerHeight() {
      const viewer = this.$refs.viewer;
      return viewer ? viewer.clientHeight : 0;
    },

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
    currentPageStrokes() {
      return (
        this.annotationsByPage[this.currentPage]?.filter(
          (annotation) => annotation.type === "trace"
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

    // Show the pen selection popup
    showPenSelection() {
      this.showPenSelectionPopup = true;
      this.selectedPenAngle = null;
      this.testTracePath = "";
    },

    // Select a pen angle
    selectPen(angle) {
      this.selectedPenAngle = angle;

      switch (angle) {
        case 25:
          this.penWidth = 3;
          this.penHeight = 6; // Wider on one axis
          break;
        case 30:
          this.penWidth = 4;
          this.penHeight = 7;
          break;
        case 50:
          this.penWidth = 5;
          this.penHeight = 8;
          break;
        case 80:
          this.penWidth = 6;
          this.penHeight = 10;
          break;
        case 0:
          this.penWidth = 2;
          this.penHeight = 2; // Round dot
          break;
        default:
          this.penWidth = 3;
          this.penHeight = 6;
      }
    },

    // Start testing the pen in the test area
    startTestTrace(event) {
      const { x, y } = this.getTestBoxMousePosition(event);
      this.testTracePath = [{ x, y }];
      this.isDrawingTest = true; // Flag to indicate drawing is active
    },

    // Continue testing the pen in the test area
    testTrace(event) {
      if (!this.isDrawingTest) return; // Only draw if the mouse is pressed
      const { x, y } = this.getTestBoxMousePosition(event);
      this.testTracePath.push({ x, y });
    },

    // End testing the pen in the test area
    endTestTrace() {
      this.isDrawingTest = false; // Stop drawing
    },

    getTestBoxMousePosition(event) {
      const testArea = event.target.closest(".test-area");
      if (!testArea) return { x: 0, y: 0 };
      const rect = testArea.getBoundingClientRect();
      return {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
    },

    // Confirm the pen selection and activate trace mode
    confirmPenSelection() {
      if (
        this.selectedPenAngle === null ||
        this.selectedPenAngle === undefined
      ) {
        alert("Please select a pen angle before confirming.");
        return;
      }
      this.showPenSelectionPopup = false;
      this.traceModeActive = true; // Activate trace mode
      this.testTracePath = ""; // Clear the test trace
      this.showToolMessage(
        `Trace mode activated with ${this.selectedPenAngle}° pen.`
      );
    },

    // Cancel the pen selection
    cancelPenSelection() {
      this.showPenSelectionPopup = false;
      this.selectedPenAngle = null;
      this.testTracePath = "";
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
    calculateAngleStatistics() {
      // Fetch all "measure" annotations for the current page
      const angleAnnotations =
        this.annotationsByPage[this.currentPage]?.filter(
          (annotation) => annotation.type === "measure"
        ) || [];

      // Extract the angles
      const angles = angleAnnotations.map((annotation) => annotation.angle);

      // Calculate statistics
      this.angleStatistics = {
        average: this.calculateAverage(angles),
        standardDeviation: this.calculateStandardDeviation(angles),
        mode: this.calculateMode(angles),
      };

      // Show the angle statistics popup
      this.showAngleStatistics = true;
    },

    closeAngleStatisticsPopup() {
      this.showAngleStatistics = false;
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
        this.traceModeActive = !this.traceModeActive; // Toggle trace mode
        if (this.traceModeActive) {
          this.showPenSelection();
        }
        this.showTraces = true;
        this.measureModeActive = false;
        this.showToolMessage(
          this.traceModeActive
            ? "Trace mode active. Click again to deactivate."
            : "Trace mode deactivated."
        );
      } else if (tool === "measure") {
        this.measureModeActive = !this.measureModeActive; // Toggle measure mode
        this.showTraces = true;
        this.measurePoints = []; // Clear existing points
        this.draggingPoint = -1; // Reset dragging state
        this.isCreatingAngle = false; // Reset angle creation state
        this.activeAngleIndex = -1; // Reset active angle index
        this.traceModeActive = false;
        this.showToolMessage(
          this.measureModeActive
            ? "Angle measurement active. Click again to deactivate."
            : "Angle measurement deactivated."
        );
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

    showToolMessage(message) {
      this.toolMessage = message;
      setTimeout(() => {
        this.toolMessage = "";
      }, 3000);
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
        !this.measureModeActive &&
        !this.croppingStarted
      ) {
        return; // Exit the function early if no relevant tool is active
      }

      if (this.croppingStarted && this.cropButtonClicked) {
        const { x, y } = this.getMousePosition(event);
        this.startPoint = { x, y };
        this.currentSquare = { x, y, width: 0, height: 0 };
      }

      // Highlight Mode
      if (this.highlightModeActive || this.underlineModeActive) {
        if (this.isFirstClick) {
          // First click: Start the annotation
          if (this.highlightModeActive) {
            const { x, y } = this.getMousePosition(event);
            this.startPoint = { x, y };
            this.currentSquare = { x, y, width: 0, height: 0 };
          }
          if (this.underlineModeActive) {
            const { x, y } = this.getMousePosition(event);

            if (!this.currentUnderline) {
              // First click: Initialize the underline
              this.startPoint = { x, y };
              this.currentUnderline = {
                x: x,
                y: y,
                width: 0,
                height: 2, // Height of the underline
              };
            }

            console.log(this.currentUnderline);
          }
          this.isFirstClick = false; // Next click will finalize the annotation
        } else {
          // Second click: Finalize the annotation
          if (this.highlightModeActive) {
            this.annotationsByPage[this.currentPage].push({
              type: "highlight",
              ...this.currentSquare,
            });
            this.currentSquare = null;
          } else if (this.underlineModeActive) {
            this.annotationsByPage[this.currentPage].push({
              type: "underline",
              ...this.currentUnderline,
            });
            this.currentUnderline = null;
          }
          this.isFirstClick = true; // Reset for the next annotation
          this.highlightModeActive = false;
          this.underlineModeActive = false;
        }
      }

      // Trace Mode
      if (this.traceModeActive) {
        // Start a new trace
        const { x, y } = this.getMousePosition(event);
        this.startPoint = { x, y };
        this.currentStroke = {
          points: [{ x, y }],
          color: this.generateRandomColor(),
          penWidth: this.penWidth, // Use the selected pen width
          penHeight: this.penHeight, // Use the selected pen height
        };
        this.dynamicTracePath = `M${x},${y}`;
      } else if (this.measureModeActive) {
        const { x, y } = this.getMousePosition(event);
        const nearest = this.findNearestPoint(x, y, 10);
        if (nearest.pointIndex !== -1) {
          const annotation =
            this.annotationsByPage[this.currentPage][nearest.annotationIndex];
          this.measurePoints = [...annotation.points];
          this.editingAnnotationIndex = nearest.annotationIndex;
          this.draggingPoint = nearest.pointIndex;
          return;
        }

        if (this.measurePoints.length >= 3) return;
        this.measurePoints.push({ x, y });

        if (this.measurePoints.length === 3) {
          this.calculatedAngle = this.calculateAngle(...this.measurePoints);
          this.annotationsByPage[this.currentPage].push({
            type: "measure",
            points: [...this.measurePoints],
            angle: this.calculatedAngle,
          });
          this.measurePoints = []; // Reset after creating
        }
      }
    },
    trace(event) {
      if (
        this.croppedImage == null &&
        !this.highlightModeActive &&
        !this.underlineModeActive &&
        !this.traceModeActive &&
        !this.measureModeActive &&
        !this.croppingStarted &&
        !this.startPoint
      ) {
        return; // Exit the function early if no relevant tool is active
      }

      if (this.startPoint && this.cropButtonClicked) {
        const { x, y } = this.getMousePosition(event);
        console.log("Mouse position:", this.startPoint);
        this.currentSquare = {
          x: Math.min(x, this.startPoint.x),
          y: Math.min(y, this.startPoint.y),
          width: Math.abs(x - this.startPoint.x),
          height: Math.abs(y - this.startPoint.y),
        };
      }
      // Highlight Mode
      if (this.highlightModeActive && this.currentSquare) {
        // Update the highlight rectangle dimensions as the mouse moves
        const { x, y } = this.getMousePosition(event);
        this.currentSquare.width = Math.abs(x - this.startPoint.x);
        this.currentSquare.height = Math.abs(y - this.startPoint.y);
        this.currentSquare.x = Math.min(x, this.startPoint.x);
        this.currentSquare.y = Math.min(y, this.startPoint.y);
      } else if (this.underlineModeActive && this.currentUnderline) {
        // Update the underline width as the mouse moves
        const { x } = this.getMousePosition(event);
        this.currentUnderline.width = Math.abs(x - this.startPoint.x);
        this.currentUnderline.x = Math.min(x, this.startPoint.x);
      }

      // Trace Mode
      else if (this.traceModeActive && this.currentStroke) {
        // Continue drawing the trace
        const { x, y } = this.getMousePosition(event);
        this.currentStroke.points.push({ x, y });
        this.dynamicTracePath = this.formatPoints(this.currentStroke.points);
      } else if (this.measureModeActive && this.draggingPoint !== -1) {
        const { x, y } = this.getMousePosition(event);
        this.measurePoints[this.draggingPoint] = { x, y };

        if (this.editingAnnotationIndex !== -1) {
          const annotation =
            this.annotationsByPage[this.currentPage][
              this.editingAnnotationIndex
            ];
          const newAngle =
            this.measurePoints.length === 3
              ? this.calculateAngle(...this.measurePoints)
              : 0;

          this.annotationsByPage[this.currentPage][
            this.editingAnnotationIndex
          ] = {
            ...annotation,
            points: [...this.measurePoints],
            angle: newAngle,
          };
        }
      }
    },
    endTrace() {
      if (this.traceModeActive && this.currentStroke) {
        // Save the current trace and reset
        this.annotationsByPage[this.currentPage].push({
          type: "trace",
          points: this.currentStroke.points,
          color: this.currentStroke.color,
          penWidth: this.currentStroke.penWidth, // Save pen width
          penHeight: this.currentStroke.penHeight, // Save pen height
        });
        this.currentStroke = null;
        this.dynamicTracePath = "";
      } else if (this.measureModeActive) {
        this.draggingPoint = -1;
        this.editingAnnotationIndex = -1;
        if (
          this.measurePoints.length === 3 &&
          this.editingAnnotationIndex === -1
        ) {
          this.measurePoints = []; // Clear points after saving new annotation
        }
      } else if (
        (this.croppingStarted || this.currentSquare) &&
        this.cropButtonClicked
      ) {
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

        const canvas = document.createElement("canvas");
        canvas.width = scaledWidth;
        canvas.height = scaledHeight;
        const ctx = canvas.getContext("2d");

        const img = new Image();
        img.crossOrigin = "anonymous"; // Allow cross-origin requests
        img.src = this.currentImage;
        img.onload = () => {
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
          this.croppedImage = canvas.toDataURL("image/png");
        };

        img.onerror = (error) => {
          console.error("Error loading image:", error);
        };
        this.croppedSvg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${scaledWidth} ${scaledHeight}" width="${scaledWidth}" height="${scaledHeight}">
        <image href="${
          this.currentImage
        }" x="${-scaledX}" y="${-scaledY}" width="${naturalWidth}" height="${naturalHeight}" />
      </svg>
    `;
        this.croppingStarted = false;
        this.currentSquare = null;
        this.startPoint = null;
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

    startCrop() {
      this.croppingStarted = true;
      this.cropButtonClicked = true;
      this.currentSquare = null;
      this.startPoint = null;
      this.showToolMessage("Click and drag to crop.");
    },

    saveCroppedImageAsPNG() {
      const link = document.createElement("a");
      link.href = this.croppedImage; // The PNG data URL
      link.download = "cropped-image.png";
      link.click();
    },
    saveCroppedImageAsSVG() {
      if (!this.croppedSvg) {
        console.error("No SVG data available to save.");
        return;
      }
      const svgBlob = new Blob([this.croppedSvg], { type: "image/svg+xml" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(svgBlob);
      link.download = "cropped-image.svg";
      link.click();
      URL.revokeObjectURL(link.href);
    },

    closeCroppedPopup() {
      this.croppedImage = null;
    },

    getCroppedMousePosition(event) {
      const container = this.$refs.croppedContainer;
      const img = container.querySelector(".cropped-image");
      if (!img) return { x: 0, y: 0 };
      const imgRect = img.getBoundingClientRect();

      // Calculate mouse position relative to the displayed image
      const x = event.clientX - imgRect.left;
      const y = event.clientY - imgRect.top;

      return { x, y };
    },

    startCroppedAnnotation(event) {
      if (!this.croppedImage) return;

      const pos = this.getCroppedMousePosition(event);

      // Highlight Mode
      if (this.highlightModeActive || this.underlineModeActive) {
        if (this.isFirstClick) {
          // First click: Store start position
          this.startPoint = pos;
          this.isFirstClick = false;

          if (this.highlightModeActive) {
            this.croppedCurrentHighlight = {
              start: pos,
              current: pos,
              style: this.getHighlightStyle(pos, pos),
            };
          } else if (this.underlineModeActive) {
            this.croppedCurrentUnderline = {
              start: pos,
              current: pos.x,
              style: this.getUnderlineStyle(pos, pos.x),
            };
          }
        } else {
          // Second click: Finalize annotation
          const finalPos = this.getCroppedMousePosition(event);

          if (this.highlightModeActive) {
            this.croppedHighlights.push({
              style: this.getHighlightStyle(this.startPoint, finalPos),
            });
            this.croppedCurrentHighlight = null;
          } else if (this.underlineModeActive) {
            this.croppedUnderlines.push({
              style: this.getUnderlineStyle(this.startPoint, finalPos.x),
            });
            this.croppedCurrentUnderline = null;
          }

          this.isFirstClick = true;
          this.highlightModeActive = false;
          this.underlineModeActive = false;
        }
      }
      // Trace Mode (keep existing trace logic)
      else if (this.traceModeActive) {
        this.croppedCurrentStroke = {
          points: [pos],
          color: this.generateRandomColor(),
        };
      }

      // Measure Mode (keep existing measure logic)
      // Measure Mode
      else if (this.measureModeActive) {
        // If dragging a point, don't add a new one
        if (this.croppedDraggingPoint !== -1) return;

        // If already 3 points, clicking starts a new angle
        if (this.croppedMeasurePoints.length === 3) {
          // Save the finished angle
          this.croppedMeasures.push({
            points: [...this.croppedMeasurePoints],
            angle: this.croppedCalculatedAngle,
          });
          // Start new angle
          this.croppedMeasurePoints = [];
          this.croppedCalculatedAngle = null;
        }

        // Add a new point
        this.croppedMeasurePoints.push({ x: pos.x, y: pos.y });

        // If 3 points, calculate angle
        if (this.croppedMeasurePoints.length === 3) {
          this.croppedCalculatedAngle = this.calculateAngle(
            this.croppedMeasurePoints[0],
            this.croppedMeasurePoints[1],
            this.croppedMeasurePoints[2]
          );
        }
      }
    },

    handleCroppedAnnotation(event) {
      if (!this.croppedImage) return;
      const pos = this.getCroppedMousePosition(event);

      // Dynamic highlight rectangle
      if (
        this.highlightModeActive &&
        this.croppedCurrentHighlight &&
        this.startPoint
      ) {
        this.croppedCurrentHighlight.style = this.getHighlightStyle(
          this.startPoint,
          pos
        );
      }
      // Dynamic underline
      else if (
        this.underlineModeActive &&
        this.croppedCurrentUnderline &&
        this.startPoint
      ) {
        this.croppedCurrentUnderline.style = this.getUnderlineStyle(
          this.startPoint,
          pos.x
        );
      }

      // Only handle drag operations for trace and measure tools
      if (this.croppedCurrentStroke) {
        this.croppedCurrentStroke.points.push(pos);
      } // Dragging a cropped angle point
      if (
        this.measureModeActive &&
        this.croppedDraggingPoint !== -1 &&
        this.croppedMeasurePoints.length === 3
      ) {
        const pos = this.getCroppedMousePosition(event);
        if (this.croppedMeasurePoints[this.croppedDraggingPoint]) {
          this.croppedMeasurePoints[this.croppedDraggingPoint] = {
            x: pos.x,
            y: pos.y,
          };
          if (this.croppedMeasurePoints.length === 3) {
            this.croppedCalculatedAngle = this.calculateAngle(
              this.croppedMeasurePoints[0],
              this.croppedMeasurePoints[1],
              this.croppedMeasurePoints[2]
            );
          }
        }
      }
    },

    endCroppedAnnotation() {
      // Only handle trace and measure tools
      if (this.croppedCurrentStroke) {
        this.croppedStrokes.push(this.croppedCurrentStroke);
        this.croppedCurrentStroke = null;
      }
      if (this.measureModeActive && this.croppedDraggingPoint !== -1) {
        this.croppedDraggingPoint = -1;
      }

      if (
        this.measureModeActive &&
        this.croppedMeasurePoints.length === 3 &&
        this.croppedDraggingPoint === -1
      ) {
        // Wait for a new click to start a new angle
        this.croppedMeasurePoints = [];
        this.croppedCalculatedAngle = null;
      }
    },
    findNearestCroppedPoint(x, y, threshold = 10) {
      let nearestIdx = -1;
      let minDist = Infinity;
      this.croppedMeasurePoints.forEach((pt, idx) => {
        const dist = Math.hypot(x - pt.x, y - pt.y);
        if (dist < threshold && dist < minDist) {
          minDist = dist;
          nearestIdx = idx;
        }
      });
      return nearestIdx;
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
      const measureAnnotations = this.annotationsByPage[
        this.currentPage
      ].filter((annotation) => annotation.type === "measure");

      let nearestDistance = Infinity;
      let nearestAnnotationIndex = -1;
      let nearestPointIndex = -1;

      measureAnnotations.forEach((annotation, annIndex) => {
        annotation.points.forEach((point, ptIndex) => {
          const distance = Math.hypot(x - point.x, y - point.y);
          if (distance < threshold && distance < nearestDistance) {
            nearestDistance = distance;
            nearestAnnotationIndex = annIndex;
            nearestPointIndex = ptIndex;
          }
        });
      });

      return {
        annotationIndex: nearestAnnotationIndex,
        pointIndex: nearestPointIndex,
      };
    },
    async saveCroppedImage() {
      const container = this.$refs.croppedContainer;
      if (!container) {
        console.error("Cropped container not found.");
        return;
      }

      try {
        // Use html2canvas to capture the container with annotations
        const canvas = await html2canvas(container, {
          useCORS: true, // Handle cross-origin images
          logging: true, // Debugging logs
          backgroundColor: null, // Transparent background
          scale: 2, // Higher resolution
        });

        // Convert canvas to PNG and trigger download
        const dataUrl = canvas.toDataURL("image/png");
        const link = document.createElement("a");
        link.href = dataUrl;
        link.download = "cropped-with-annotations.png";
        link.click();
      } catch (error) {
        console.error("Error saving cropped image with annotations:", error);
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
      event.stopPropagation();
      this.draggingPoint = index;
    },
    toggleClearDropdown() {
      this.showClearDropdown = !this.showClearDropdown;
    },

    clearHighlights() {
      this.annotationsByPage[this.currentPage] = this.annotationsByPage[
        this.currentPage
      ].filter((annotation) => annotation.type !== "highlight");
      this.showToolMessage("Highlights cleared.");
      this.showClearDropdown = false;
    },

    clearUnderlines() {
      this.annotationsByPage[this.currentPage] = this.annotationsByPage[
        this.currentPage
      ].filter((annotation) => annotation.type !== "underline");
      this.showToolMessage("Underlines cleared.");
      this.showClearDropdown = false;
    },

    clearComments() {
      this.comments[this.currentPage] = [];
      this.showToolMessage("Comments cleared.");
      this.showClearDropdown = false;
    },

    clearTraces() {
      this.annotationsByPage[this.currentPage] = this.annotationsByPage[
        this.currentPage
      ].filter((annotation) => annotation.type !== "trace");
      this.showToolMessage("Traces cleared.");
      this.showClearDropdown = false;
    },

    clearAngles() {
      this.annotationsByPage[this.currentPage] = this.annotationsByPage[
        this.currentPage
      ].filter((annotation) => annotation.type !== "measure");
      this.showToolMessage("Angles cleared.");
      this.showClearDropdown = false;
    },

    clearHorizontalLengths() {
      const horizontalTypes = [
        "ascenders",
        "descenders",
        "interlinear",
        "upperMargin",
        "lowerMargin",
        "lineHeight", // New
        "minimumHeight", // New
      ];
      horizontalTypes.forEach((type) => {
        if (this.lengthMeasurements[type]) {
          delete this.lengthMeasurements[type][this.currentPage];
        }
      });
      this.showToolMessage("Horizontal lengths cleared.");
      this.showClearDropdown = false;
    },

    clearVerticalLengths() {
      const verticalTypes = ["internalMargin", "intercolumnSpaces"];
      verticalTypes.forEach((type) => {
        if (this.lengthMeasurements[type]) {
          delete this.lengthMeasurements[type][this.currentPage];
        }
      });
      this.showToolMessage("Vertical lengths cleared.");
      this.showClearDropdown = false;
    },

    clearAll() {
      this.annotationsByPage[this.currentPage] = [];
      this.comments[this.currentPage] = [];
      const allTypes = [
        "ascenders",
        "descenders",
        "interlinear",
        "upperMargin",
        "lowerMargin",
        "internalMargin",
        "intercolumnSpaces",
      ];
      allTypes.forEach((type) => {
        if (this.lengthMeasurements[type]) {
          delete this.lengthMeasurements[type][this.currentPage];
        }
      });
      this.strokes = [];
      this.measurePoints = [];
      this.calculatedAngle = 0;
      this.showToolMessage("All annotations cleared.");
      this.showClearDropdown = false;
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
        "lineHeight", // New
        "minimumHeight", // New
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
        "lineHeight", // New
        "minimumHeight", // New
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
        "lineHeight", // New
        "minimumHeight", // New
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
        "lineHeight", // New
        "minimumHeight", // New
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
            "lineHeight", // New
            "minimumHeight", // New
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
  font-family: "Arial", "Helvetica", sans-serif;
}

body {
  font-family: "Arial", "Helvetica", sans-serif; /* Use Sans-serif fonts */
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
  padding: 3px;
  font-family: "Arial", "Helvetica", sans-serif;
}
.toolbar-item.active {
  color: #007bff;
  background-color: #e0f7ff;
}

.drawing-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.tool-message {
  position: fixed;
  top: 50%; /* Center vertically */
  left: 50%; /* Center horizontally */
  transform: translate(-50%, -50%); /* Adjust for exact centering */
  background-color: #007bff;
  color: white;
  padding: 10px 20px;
  border-radius: 5px;
  z-index: 1100;
  font-size: 14px;
  text-align: center;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Optional: Add a subtle shadow */
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
  z-index: 1100; /* Ensure it appears above other elements */
  pointer-events: none;
}

.cropped-image-container {
  position: relative;
  display: inline-block;
}

.cropped-annotation-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
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
  font-family: "Arial", "Helvetica", sans-serif;
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
.cropping-rectangle {
  position: absolute;
  border: 2px dashed blue;
  background-color: rgba(0, 0, 255, 0.2);
  pointer-events: none;
  z-index: 100;
}

.blurred-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  backdrop-filter: blur(8px); /* Apply blur effect */
  background-color: rgba(0, 0, 0, 0.3); /* Add a semi-transparent overlay */
  z-index: 999; /* Ensure it appears below the cropped popup */
}

.cropped-popup {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  z-index: 1000; /* Ensure it appears above the blurred background */
  padding: 20px;
  text-align: center;
}

.cropped-popup-content img {
  max-width: 100%;
  max-height: 300px;
  margin-bottom: 20px;
}

.cropped-popup-content button {
  margin-top: 10px;
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.cropped-popup-content button:hover {
  background-color: #0056b3;
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
  font-family: "Arial", "Helvetica", sans-serif;
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
  z-index: 1100; /* Ensure it appears above other elements */
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
  z-index: 1100;
}

.statistics-popup-content {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  max-width: 400px;
  width: 100%;
  font-family: "Arial", "Helvetica", sans-serif;
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

.pen-selection-popup {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1100;
}

.pen-selection-content {
  background-color: white;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  text-align: center;
  width: 400px;
}

.pen-options {
  display: flex;
  justify-content: space-between; /* Align items from left to right */
  margin-bottom: 20px;
}

.pen-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.pen-option.selected {
  border: 2px solid #007bff;
  border-radius: 5px;
  padding: 5px;
}

.pen-preview {
  width: 30px;
  height: 10px;
  background-color: grey; /* Pen color */
  margin-bottom: 20px; /* Add margin between the pen and the angle text */
  transform-origin: left center; /* Rotate around the left edge */
  position: relative;
}

.pen-nib {
  width: 10px;
  height: 10px;
  background-color: black;
  border-radius: 50%; /* Make the nib circular */
  position: absolute;
  top: 0;
  left: 0;
}

.pen-option:hover {
  background-color: #f0f8ff; /* Light blue background */
  border-color: #007bff; /* Blue border */
}
.test-box {
  margin-top: 20px;
}

.test-area {
  width: 100%;
  height: 100px;
  border: 1px solid #ccc;
  background-color: white;
  position: relative;
}

.test-svg {
  width: 100%;
  height: 100%;
  z-index: 10000;
  pointer-events: none;
}

.clear-container {
  position: relative;
}

.clear-dropdown {
  position: absolute;
  top: 100%; /* Position below the button */
  left: 0;
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  z-index: 1100; /* Ensure it appears above other elements */
  min-width: 150px; /* Set a minimum width */
}

.clear-dropdown div {
  padding: 8px 16px;
  cursor: pointer;
}

.clear-dropdown div:hover {
  background-color: #f1f1f1;
}
</style>