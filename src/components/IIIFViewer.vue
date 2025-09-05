<!-- /src/components/IIIFViewer.vue -->
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

        <!-- Measure Angle -->
        <div class="toolbar-item" @click="selectTool('measure')">
          <i class="fa-solid fa-angle-up"></i>
          <span>Measure</span>
          <span>Angle</span>
        </div>

        <!-- Horizontal Bands -->
        <div class="toolbar-item" @click="openHorizontalPopup">
          <i class="fa-solid fa-ruler-horizontal"></i>
          <span>Horizontal</span>
          <span>Bands</span>
        </div>

        <!-- Vertical Bands -->
        <div class="toolbar-item" @click="openVerticalPopup">
          <i class="fa-solid fa-ruler-vertical"></i>
          <span>Vertical</span>
          <span>Bands</span>
        </div>

        <!-- Crop -->
        <div class="toolbar-item" @click="startCrop">
          <i class="fa-solid fa-scissors"></i>
          <span>Crop</span>
        </div>

        <!-- Generate Statistics -->
        <div class="toolbar-item" @click="showStatsPanel = !showStatsPanel">
          <i class="fa-solid fa-calculator"></i>
          <span>Generate</span>
          <span>Statistics</span>
        </div>

        <!-- Save -->
        <div class="toolbar-item" @click="saveAnnotations">
          <i class="fa-solid fa-save"></i>
          <span>Save</span>
        </div>

        <!-- Clear -->
        <div class="toolbar-item" @click="toggleClearDropdown">
          <i class="fa-regular fa-trash-can"></i>
          <span>Clear</span>
          <div v-if="showClearDropdown" class="clear-dropdown">
            <div @click.stop="clearHighlights">Clear Highlights</div>
            <div @click.stop="clearUnderlines">Clear Underlines</div>
            <div @click.stop="clearComments">Clear Comments</div>
            <div @click.stop="clearTraces">Clear Traces</div>
            <div @click.stop="clearAngles">Clear Angles</div>
            <div @click.stop="clearHorizontalLengths">Clear Horizontal Lengths</div>
            <div @click.stop="clearVerticalLengths">Clear Vertical Lengths</div>
            <div @click.stop="clearAll">Clear All</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Page Navigation (now right under the toolbar, at the top) -->
    <NavigationBar
      :currentPage="currentPage"
      :totalPages="totalPages"
      :pageInput="pageInput"
      @prev="prevPage"
      @next="nextPage"
      @go-to="goToPage"
    />

    <!-- Tool tip message -->
    <div class="tool-message" v-if="toolMessage">{{ toolMessage }}</div>

    <!-- Workspace: stage + annotations bank -->
    <div class="workspace">
      <!-- Image Stage -->
      <div
        class="pdf-viewer stage"
        ref="viewer"
        :style="{ cursor: (traceModeActive || highlightModeActive || underlineModeActive || measureModeActive || isMeasuring || moveModeActive) ? 'crosshair' : 'default' }"
        @mousedown="startTrace($event)"
        @mousemove="trace($event)"
        @mouseup="endTrace($event)"
      >
        <img
          v-if="croppedImage || currentImage"
          :src="croppedImage || currentImage"
          ref="image"
          class="image-viewer"
          @load="handleImageLoad"
          draggable="false"
        />

        <!-- SVG drawing layer -->
        <svg
          v-if="showTraces"
          class="drawing-layer"
          :width="viewerWidth"
          :height="viewerHeight"
        >
          <!-- existing traces -->
          <polyline
            v-for="(stroke, index) in currentPageStrokes"
            :key="'stroke-' + index"
            :points="formatPoints(stroke.points)"
            :stroke="stroke.color"
            :stroke-width="stroke.penWidth"
            :stroke-height="stroke.penHeight"
            fill="none"
          />
          <!-- measure points (temp) -->
          <circle
            v-for="(point, index) in measurePoints"
            :key="'measure-point-' + index"
            :cx="point.x"
            :cy="point.y"
            r="5"
            fill="red"
          />
          <!-- saved angles -->
          <g
            v-for="(annotation, index) in currentPageAngles"
            :key="'angle-' + index"
          >
            <line
              v-if="annotation.type === 'measure' && annotation.points.length >= 2"
              :x1="annotation.points[0].x"
              :y1="annotation.points[0].y"
              :x2="annotation.points[1].x"
              :y2="annotation.points[1].y"
              stroke="blue"
              stroke-width="2"
            />
            <line
              v-if="annotation.type === 'measure' && annotation.points.length === 3"
              :x1="annotation.points[1].x"
              :y1="annotation.points[1].y"
              :x2="annotation.points[2].x"
              :y2="annotation.points[2].y"
              stroke="blue"
              stroke-width="2"
            />
            <text
              v-if="annotation.type === 'measure' && annotation.points.length === 3"
              :x="annotation.points[1].x + 10"
              :y="annotation.points[1].y - 10"
              font-size="12"
              fill="darkblue"
            >
              {{ annotation.angle }}°{{ annotation.label ? ' • ' + annotation.label : '' }}
            </text>
          </g>
          <!-- dynamic freehand trace -->
          <polyline
            v-if="currentStroke"
            :points="formatPoints(currentStroke.points)"
            :stroke="currentStroke.color"
            :stroke-width="currentStroke.penWidth"
            :stroke-height="currentStroke.penHeight"
            fill="none"
          />
        </svg>

        <!-- Dynamic Crop / Highlight / Length rectangles -->
        <div
          v-if="(isMeasuring && currentSquare) || (highlightModeActive && currentSquare) || (croppingStarted && currentSquare)"
          class="length-measurement"
          :style="{
            left: `${currentSquare.x}px`,
            top: `${currentSquare.y}px`,
            width: `${currentSquare.width}px`,
            height: `${currentSquare.height}px`,
            backgroundColor: currentSquare.color || 'rgba(0,0,0,0.1)',
            position: 'absolute',
          }"
        >
          <div
            v-if="isMeasuring"
            class="length-label draggable-label"
            :style="{
              left: (labelPositions['dynamic']?.x ?? 15) + 'px',
              top: (labelPositions['dynamic']?.y ?? 15) + 'px',
              position: 'absolute',
              cursor: draggedLabelIndex === 'dynamic' ? 'grabbing' : 'grab',
              backgroundColor: 'white',
              zIndex: 400,
              userSelect: 'none',
              pointerEvents: 'auto',
            }"
            @mousedown.stop="startLabelDrag('dynamic', $event)"
          >
            {{ currentSquare.label }}:
            {{
              isHorizontalLabel(currentSquare.label)
                ? currentSquare.height
                : currentSquare.width
            }}px
          </div>
        </div>

        <!-- Finalized Lengths -->
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
            border: '1px solid #000',
          }"
        >
          <div
            class="length-label draggable-label"
            :style="{
              left: (labelPositions[measurement.id]?.x ?? 15) + 'px',
              top: (labelPositions[measurement.id]?.y ?? 15) + 'px',
              position: 'absolute',
              cursor: draggedLabelIndex === measurement.id ? 'grabbing' : 'grab',
              backgroundColor: 'white',
              zIndex: 400,
              userSelect: 'none',
              pointerEvents: 'auto',
            }"
            @mousedown.stop="startLabelDrag(measurement.id, $event)"
          >
            {{ measurement.label }}:
            {{
              isHorizontalLabel(measurement.label)
                ? measurement.height
                : measurement.width
            }}px
          </div>
        </div>

        <!-- Highlights -->
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

        <!-- Dynamic Underline -->
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

        <!-- Saved Underlines -->
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

        <!-- Comments -->
        <div
          v-for="(comment, index) in currentPageComments"
          :key="'comment-' + index"
          class="comment-container"
          :style="{ top: comment.y + 'px', left: comment.x + 'px', position: 'absolute' }"
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
            <button class="btn-cancel-comment" @click="cancelComment">Cancel</button>
          </div>
        </div>

        <!-- Cropping rectangle -->
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

<!-- Compact Bank Panel (anchored, not affecting layout) -->
   <AnnotationsBank
    :page="currentPage"
     :items="bankItems"
     :selectedKeys="bankSelectedKeys"
     :multiSelect="bankMultiSelect"
     :moveActive="moveModeActive"
     @update:selected="(keys) => bankSelectedKeys = keys"
     @toggle-multi="bankMultiSelect = !bankMultiSelect"
     @request-move="enableMoveMode"
     @cancel-move="disableMoveMode"
     @request-delete="deleteSelectedFromBank"
   />
    </div>

    <!-- Angle Label Picker Popup -->
    <div v-if="showAngleLabelPopup" class="length-popup" @click.self="showAngleLabelPopup = false">
      <div class="length-popup-content">
        <h3>Select or Create Angle Label</h3>

        <div class="label-grid">
          <button
            v-for="label in angleLabels"
            :key="label"
            class="grid-btn"
            :class="{ active: activeAngleLabel === label }"
            @click="activeAngleLabel = label"
          >
            {{ label }}
          </button>
        </div>

        <div class="new-label-row">
          <input v-model="newAngleLabel" placeholder="New label…" />
          <button class="grid-btn" @click="confirmNewAngleLabel">Add</button>
        </div>

        <div class="popup-actions">
          <button class="grid-btn" @click="confirmAngleLabel">Use Label</button>
          <button class="grid-btn" @click="cancelAngleLabel">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Angle Statistics Filter Popup -->
    <div v-if="showAngleFilterPopup" class="length-popup" @click.self="showAngleFilterPopup = false">
      <div class="length-popup-content">
        <h3>Angle Measurements</h3>
        <div class="row">
          <label>Scope:</label>
          <div class="label-grid">
            <button class="grid-btn" :class="{active: angleScope==='page'}" @click="angleScope='page'">Current Page</button>
            <button class="grid-btn" :class="{active: angleScope==='doc'}" @click="angleScope='doc'">Entire Document</button>
          </div>
        </div>
        <div class="row">
          <label>Label:</label>
          <div class="label-grid">
            <button class="grid-btn" :class="{active: angleFilterLabel==='__ALL__'}" @click="angleFilterLabel='__ALL__'">All labels</button>
            <button
              v-for="label in angleLabels"
              :key="'f-'+label"
              class="grid-btn"
              :class="{active: angleFilterLabel===label}"
              @click="angleFilterLabel=label"
            >
              {{ label }}
            </button>
          </div>
        </div>

        <div class="popup-actions">
          <button class="grid-btn" @click="runAngleStatistics">Generate</button>
          <button class="grid-btn" @click="showAngleFilterPopup=false">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Trace Pen Popup -->
    <div v-if="showTracePopup" class="length-popup" @click.self="showTracePopup = false">
      <div class="length-popup-content">
        <h3>Choose Pen & Angle</h3>

        <div class="row" style="text-align:center">
          <label style="width:auto;margin-right:8px">Angle:</label>
          <div class="label-grid">
            <button
              v-for="ang in penAngles"
              :key="'ang-'+ang"
              class="grid-btn"
              :class="{ active: selectedPenAngle === ang }"
              @click="selectedPenAngle = ang"
            >
              {{ ang }}°
            </button>
          </div>
        </div>

        <div class="row" style="text-align:center">
          <label style="width:auto;margin-right:8px">Nib size:</label>
          <div class="label-grid">
            <button
              v-for="p in penSizes"
              :key="'size-'+p.key"
              class="grid-btn"
              :class="{ active: selectedPenSize === p.key }"
              @click="selectedPenSize = p.key"
            >
              {{ p.label }}
            </button>
          </div>
        </div>

        <div class="popup-actions">
          <button class="grid-btn" @click="confirmPenSelection">Start Tracing</button>
          <button class="grid-btn" @click="cancelPenSelection">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Stats quick panel (Lengths + Angles entry) -->
    <div
      v-if="showStatsPanel"
      class="stats-panel"
      @click.self="showStatsPanel = false"
    >
      <div class="panel-card stats-card">
        <h4>Statistics</h4>

        <div class="panel-actions">
          <button class="grid-btn" @click="calculateCurrentPage">Lengths: Current Page</button>
          <button class="grid-btn" @click="calculateEntireDocument">Lengths: Entire Document</button>
          <button class="grid-btn" @click="openAnglesFilterFromStats">Angle Measurements…</button>
          <button class="grid-btn" @click="showStatsPanel=false">Close</button>
        </div>
      </div>
    </div>

    <!-- Horizontal Bands Popup (as buttons) -->
    <div v-if="showHorizontalPopup" class="length-popup" @click.self="showHorizontalPopup = false">
      <div class="length-popup-content">
        <h3>Select Horizontal Measurement</h3>
        <div class="btn-grid">
          <button class="grid-btn" @click="beginLength('ascenders')">
            <span class="swatch" :style="{ background: measurementColors.ascenders }"></span>
            <span>Ascenders</span>
          </button>
          <button class="grid-btn" @click="beginLength('descenders')">
            <span class="swatch" :style="{ background: measurementColors.descenders }"></span>
            <span>Descenders</span>
          </button>
          <button class="grid-btn" @click="beginLength('interlinear')">
            <span class="swatch" :style="{ background: measurementColors.interlinear }"></span>
            <span>Interlinear Spaces</span>
          </button>
          <button class="grid-btn" @click="beginLength('upperMargin')">
            <span class="swatch" :style="{ background: measurementColors.upperMargin }"></span>
            <span>Upper Margin</span>
          </button>
          <button class="grid-btn" @click="beginLength('lowerMargin')">
            <span class="swatch" :style="{ background: measurementColors.lowerMargin }"></span>
            <span>Lower Margin</span>
          </button>
          <button class="grid-btn" @click="beginLength('lineHeight')">
            <span class="swatch" :style="{ background: measurementColors.lineHeight }"></span>
            <span>Line Height</span>
          </button>
          <button class="grid-btn" @click="beginLength('minimumHeight')">
            <span class="swatch" :style="{ background: measurementColors.minimumHeight }"></span>
            <span>Minimum Height</span>
          </button>
        </div>
        <div class="popup-actions">
          <button class="grid-btn" @click="hideLengthPopup">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Vertical Bands Popup (as buttons) -->
    <div v-if="showVerticalPopup" class="length-popup" @click.self="showVerticalPopup = false">
      <div class="length-popup-content">
        <h3>Select Vertical Measurement</h3>
        <div class="btn-grid">
          <button class="grid-btn" @click="beginLength('internalMargin')">
            <span class="swatch" :style="{ background: measurementColors.internalMargin }"></span>
            <span>Internal Margin</span>
          </button>
          <button class="grid-btn" @click="beginLength('intercolumnSpaces')">
            <span class="swatch" :style="{ background: measurementColors.intercolumnSpaces }"></span>
            <span>Intercolumn Spaces</span>
          </button>
          <button class="grid-btn" @click="beginLength('externalMargin')">
            <span class="swatch" :style="{ background: measurementColors.externalMargin }"></span>
            <span>External Margin</span>
          </button>
        </div>
        <div class="popup-actions">
          <button class="grid-btn" @click="hideLengthPopup">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Angle Statistics Result Popup -->
    <div v-if="showAngleStatistics" class="statistics-popup" @click.self="showAngleStatistics = false">
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
                {{ typeof angleStatistics.mode === "number" ? angleStatistics.mode.toFixed(2) : angleStatistics.mode }}
              </td>
            </tr>
          </tbody>
        </table>
        <button class="grid-btn" @click="closeAngleStatisticsPopup">Close</button>
      </div>
    </div>

    <!-- Lengths Statistics Result Popup -->
    <div v-if="showStatistics" class="statistics-popup" @click.self="showStatistics = false">
      <div class="statistics-popup-content">
        <h3>Statistics</h3>

        <!-- Horizontal -->
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
              <td>{{ typeof stats.mode === 'number' ? stats.mode.toFixed(2) : stats.mode }}</td>
            </tr>
          </tbody>
        </table>

        <!-- Vertical -->
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
              <td>{{ typeof stats.mode === 'number' ? stats.mode.toFixed(2) : stats.mode }}</td>
            </tr>
          </tbody>
        </table>

        <button class="grid-btn" @click="closeStatisticsPopup">Close</button>
      </div>
    </div>

    <!-- Cropped Image Popup -->
    <div v-if="croppedImage" class="blurred-background" style="top: 90px" @click="croppedImage = null"></div>
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

          <!-- Cropped Highlights -->
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

          <!-- Cropped Underlines -->
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

          <!-- Cropped Traces & Angles -->
          <svg
            class="drawing-layer"
            :width="popupDimensions.width"
            :height="popupDimensions.height"
            style="position:absolute;top:0;left:0;width:100%;height:100%;z-index:2;"
          >
            <polyline
              v-for="(stroke, index) in croppedStrokes"
              :key="'cstroke-' + index"
              :points="formatPoints(stroke.points)"
              :stroke="stroke.color"
              stroke-width="2"
              fill="none"
            />
            <polyline
              v-if="croppedCurrentStroke && croppedCurrentStroke.points && croppedCurrentStroke.points.length"
              :points="formatPoints(croppedCurrentStroke.points)"
              :stroke="croppedCurrentStroke.color"
              stroke-width="2"
              fill="none"
            />
            <!-- temp cropped angle points -->
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
                v-if="croppedMeasurePoints.length === 3 && croppedCalculatedAngle"
                :x="croppedMeasurePoints[1].x + 10"
                :y="croppedMeasurePoints[1].y - 10"
                fill="darkblue"
                font-size="12"
              >
                {{ croppedCalculatedAngle }}°
              </text>
            </g>

            <!-- finalized cropped angles -->
            <g v-for="(measure, index) in croppedMeasures" :key="'cmeasure-' + index">
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
              />
            </g>
          </svg>
        </div>

        <div class="popup-actions">
          <button class="grid-btn" @click="saveCroppedImageAsPNG">Save as PNG</button>
          <button class="grid-btn" @click="saveCroppedImageAsSVG">Save as SVG</button>
          <button class="grid-btn" @click="saveCroppedImage">Save with Annotations</button>
          <button class="grid-btn" @click="closeCroppedPopup">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/* eslint-disable */
import { PDFDocument } from "pdf-lib";
import html2canvas from "html2canvas";
import AnnotationsBank from "@/components/viewer/AnnotationsBank.vue";
import NavigationBar from "@/components/viewer/NavigationBar.vue";

export default {
  name: "IIIFViewer",
  components: { AnnotationsBank, NavigationBar },
  props: {
    source: { type: String, required: true },
  },
  data() {
    return {
      annotationsByPage: [],
      // Pen config
      penWidth: 3,
      penHeight: 6,
      // Trace popup & pen options
      showTracePopup: false,
      penAngles: [0, 15, 30, 45, 60, 75],
      penSizes: [
        { key: 'thin',   label: 'Thin'   , w: 2, h: 3 },
        { key: 'medium', label: 'Medium' , w: 3, h: 5 },
        { key: 'broad',  label: 'Broad'  , w: 5, h: 8 },
      ],
      selectedPenAngle: 45,
      selectedPenSize: 'medium',
      currentNibAngle: 45,
      // Toggles / modes
      showTraces: true,
      measureModeActive: false,
      traceModeActive: false,
      commentModeActive: false,
      highlightModeActive: false,
      underlineModeActive: false,
      isMeasuring: false, // length-bands creation
      croppingStarted: false,
      cropButtonClicked: false,

      // Stage state
      images: [],
      currentPage: 0,
      pageInput: 1,
      imageLoaded: false,
      scalingFactor: 1,

      // Drawing state
      startPoint: null,
      currentSquare: null, // for crop / highlight / bands
      currentUnderline: null,
      currentStroke: null,
      strokes: [],
      dynamicTracePath: "",

      // Angles
      measurePoints: [],      // temp points for new angle OR during drag
      draggingPoint: -1,      // index within measurePoints
      editingAnnotationIndex: -1,
      calculatedAngle: 0,

      // Angle labels
      showAngleLabelPopup: false,
      activeAngleLabel: null,
      angleLabels: [],           // list of strings (persist within session)
      newAngleLabel: "",

      // Angle stats filter
      showAngleFilterPopup: false,
      angleScope: "page",        // 'page' | 'doc'
      angleFilterLabel: "__ALL__", // "__ALL__" or a label
      angleStatistics: { average: 0, standardDeviation: 0, mode: "No mode" },
      showAngleStatistics: false,

      // Bands
      showHorizontalPopup: false,
      showVerticalPopup: false,
      selectedMeasurement: "ascenders",
      lengthMeasurementActive: false,
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
        externalMargin: "rgba(0, 128, 128, 0.5)",
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
        externalMargin: {},
      },
      labelPositions: {}, // for length labels drag
      draggedLabelIndex: null,
      labelDragOffset: { x: 0, y: 0 },

      // Popups and stats
      showStatistics: false,
      horizontalStatistics: {},
      verticalStatistics: {},
      showStatsPanel: false,

      // Cropped popup state
      croppedSvg: null,
      croppedImage: null,
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
      popupDimensions: { width: 0, height: 0 },

      // Comments
      comments: [],
      showCommentInput: false,
      currentCommentText: "",
      currentCommentPosition: null,
      draggingCommentIndex: null,
      dragOffset: { x: 0, y: 0 },

      // UI
      showClearDropdown: false,
      toolMessage: "",

      // Bank
      bankSelectedKeys: [],
      bankMultiSelect: true,
      moveModeActive: false,
      moveStartPos: null,
      currentMoveDelta: { x: 0, y: 0 },
    };
  },
  computed: {
    viewerWidth() {
      const viewer = this.$refs.viewer;
      return viewer ? viewer.clientWidth : 0;
    },
    viewerHeight() {
      const viewer = this.$refs.viewer;
      return viewer ? viewer.clientHeight : 0;
    },
    currentImage() {
      return this.images[this.currentPage] || null;
    },
    totalPages() {
      return this.images.length;
    },
    currentPageHighlights() {
      return (this.annotationsByPage[this.currentPage] || []).filter(a => a.type === "highlight");
    },
    currentPageUnderlines() {
      return (this.annotationsByPage[this.currentPage] || []).filter(a => a.type === "underline");
    },
    currentPageStrokes() {
      const strokes = (this.annotationsByPage[this.currentPage] || []).filter(a => a.type === "trace");
      
      // Apply movement delta if in move mode and annotations are selected
      if (this.moveModeActive && this.currentMoveDelta.x !== 0 || this.currentMoveDelta.y !== 0) {
        return strokes.map((stroke, index) => {
          const key = `trace-${index}`;
          if (this.bankSelectedKeys.includes(key)) {
            return {
              ...stroke,
              points: stroke.points.map(point => ({
                x: point.x + this.currentMoveDelta.x,
                y: point.y + this.currentMoveDelta.y
              }))
            };
          }
          return stroke;
        });
      }
      
      return strokes;
    },
    currentPageAngles() {
      const angles = (this.annotationsByPage[this.currentPage] || []).filter(a => a.type === "measure");
      
      // Apply movement delta if in move mode and annotations are selected
      if (this.moveModeActive && (this.currentMoveDelta.x !== 0 || this.currentMoveDelta.y !== 0)) {
        return angles.map((angle, index) => {
          const key = `measure-${index}`;
          if (this.bankSelectedKeys.includes(key)) {
            return {
              ...angle,
              points: angle.points.map(point => ({
                x: point.x + this.currentMoveDelta.x,
                y: point.y + this.currentMoveDelta.y
              }))
            };
          }
          return angle;
        });
      }
      
      return angles;
    },
    currentPageLengthMeasurements() {
      const measurements = [];
      for (const label in this.lengthMeasurements) {
        if (this.lengthMeasurements[label][this.currentPage]) {
          measurements.push(...this.lengthMeasurements[label][this.currentPage]);
        }
      }
      return measurements;
    },
    currentPageComments() {
      return this.comments[this.currentPage] || [];
    },
    bankItems() {
      const items = [];
      const ann = this.annotationsByPage[this.currentPage] || [];

      // Annotations
      ann.forEach((a, i) => {
        if (!a) return;

        if (a.type === "measure") {
          // Angle(Label)(number)
          const label = a.label ? String(a.label) : "Unlabeled";
          const num = typeof a.angle === "number" || typeof a.angle === "string"
            ? String(a.angle)
            : "";
          items.push({
            key: `a:${i}`,
            category: "angle",
            title: `Angle (${label}) (${num})`,
            subtitle: "",
            color: "#0d6efd", // blue accent for angles
          });
          return;
        }

        if (a.type === "trace") {
          // Trace(Color)
          const colorName = this.colorToName(a.color);
          items.push({
            key: `a:${i}`,
            category: "trace",
            title: `Trace (${colorName})`,
            subtitle: `${a.points?.length || 0} pts`,
            color: a.color || "#0d6efd",
          });
          return;
        }

        if (a.type === "highlight") {
          items.push({
            key: `a:${i}`,
            category: "highlight",
            title: "Highlight",
            subtitle: `${Math.round(a.width)}×${Math.round(a.height)} px`,
            color: "rgba(255, 255, 0, 0.8)",
          });
          return;
        }

        if (a.type === "underline") {
          items.push({
            key: `a:${i}`,
            category: "underline",
            title: "Underline",
            subtitle: `${Math.round(a.width)} px`,
            color: "red",
          });
          return;
        }
      });

      // Length bands (name according to actual type)
      const pageLengths = this.currentPageLengthMeasurements || [];
      pageLengths.forEach((m) => {
        items.push({
          key: `l:${m.id}`,
          category: "length",
          title: this.camelToTitle(m.label || "Length"),
          subtitle: `${Math.round(m.width)}×${Math.round(m.height)} px`,
          color: m.color || this.measurementColors[m.label] || "#6ea8fe",
        });
      });

      // Comments
      const cmts = this.comments[this.currentPage] || [];
      cmts.forEach((c, i) => {
        items.push({
          key: `c:${i}`,
          category: "comment",
          title: "Comment",
          subtitle: (c.text || "").slice(0, 60),
          color: "#6ea8fe",
        });
      });

      return items;
    },
  },
  watch: {
    currentPage(n) {
      this.pageInput = n + 1;
    },
  },
  async created() {
    if (!this.source) {
      alert("Invalid source. Returning to input.");
      this.$router.push({ name: "IIIFInput" });
      return;
    }
    this.annotationsByPage = []; // init
    if (this.source.endsWith("manifest.json")) {
      await this.fetchIIIFImages(this.source);
    } else {
      this.images = [this.source];
      this.annotationsByPage = [ [] ];
      this.comments = [ [] ];
    }
  },
  mounted() {
    this._onLabelDragMove = (e) => {
      if (this.draggedLabelIndex !== null) {
        let measurement = null;
        if (this.draggedLabelIndex === "dynamic") {
          measurement = this.currentSquare;
        } else {
          measurement = this.currentPageLengthMeasurements.find((m) => m.id === this.draggedLabelIndex);
        }
        if (measurement) this.dragLabel(this.draggedLabelIndex, e);
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
          return;
        }
        this.annotationsByPage = new Array(this.images.length).fill().map(() => []);
        this.comments = new Array(this.images.length).fill().map(() => []);
      } catch (e) {
        alert("Error fetching IIIF manifest: " + e.message);
      }
    },

    /* ---------- Helpers ---------- */
    getMousePosition(event) {
      const viewerElement = this.$refs.viewer;
      const rect = viewerElement.getBoundingClientRect();
      const scrollLeft = viewerElement.scrollLeft || 0;
      const scrollTop = viewerElement.scrollTop || 0;
      return {
        x: event.clientX - rect.left + scrollLeft,
        y: event.clientY - rect.top + scrollTop,
      };
    },
    formatPoints(points) {
      return points.map(({ x, y }) => `${x},${y}`).join(" ");
    },
    calculateAngle(pt1, pt2, pt3) {
      const v1 = { x: pt1.x - pt2.x, y: pt1.y - pt2.y };
      const v2 = { x: pt3.x - pt2.x, y: pt3.y - pt2.y };
      const dot = v1.x * v2.x + v1.y * v2.y;
      const mag1 = Math.hypot(v1.x, v1.y);
      const mag2 = Math.hypot(v2.x, v2.y);
      const angleRad = Math.acos(Math.max(-1, Math.min(1, dot / (mag1 * mag2))));
      return ((angleRad * 180) / Math.PI).toFixed(2);
    },
    isHorizontalLabel(label) {
      return ["ascenders","descenders","interlinear","upperMargin","lowerMargin","lineHeight","minimumHeight"].includes(label);
    },
    generateRandomColor() {
      const palette = ["#E69F00","#56B4E9","#009E73","#F0E442","#0072B2","#D55E00","#CC79A7"];
      this._lastColor = this._lastColor || null;
      const pool = palette.filter(c => c !== this._lastColor);
      const selected = pool[Math.floor(Math.random()*pool.length)];
      this._lastColor = selected;
      return selected;
    },
    parseBankKey(key) {
      const [kind, ref] = String(key).split(":");
      return { kind, ref };
    },

    /* ----- Bank helpers ----- */
    camelToTitle(key) {
      if (!key) return "";
      return key
        .replace(/([a-z])([A-Z])/g, "$1 $2")
        .replace(/^./, (s) => s.toUpperCase());
    },
    colorToName(color) {
      if (!color) return "Color";
      const c = color.toLowerCase();

      // common trace palette (from generateRandomColor)
      const map = {
        "#e69f00": "Orange",
        "#56b4e9": "Sky",
        "#009e73": "Green",
        "#f0e442": "Yellow",
        "#0072b2": "Blue",
        "#d55e00": "Rust",
        "#cc79a7": "Magenta",
      };

      // try exact hex first
      if (map[c]) return map[c];

      // try rgba swatches used for bands (just rough labels)
      if (c.includes("0, 255, 0")) return "Green";
      if (c.includes("0, 0, 255")) return "Blue";
      if (c.includes("255, 165, 0")) return "Orange";
      if (c.includes("255, 0, 0")) return "Red";
      if (c.includes("128, 0, 128")) return "Purple";
      if (c.includes("0, 255, 255")) return "Cyan";
      if (c.includes("255, 0, 255")) return "Pink";
      if (c.includes("100, 100, 255")) return "Indigo";
      if (c.includes("255, 100, 100")) return "Coral";

      return "Color";
    },

    /* ---------- Toolbar ---------- */
    selectTool(tool) {
      if (!this.currentImage) return;

      // reset non-related modes
      const resetAll = () => {
        this.traceModeActive = false;
        this.measureModeActive = false;
        this.highlightModeActive = false;
        this.underlineModeActive = false;
        this.commentModeActive = false;
        this.lengthMeasurementActive = false;
        this.isMeasuring = false;
        this.croppingStarted = false;
        this.cropButtonClicked = false;
        this.showStatsPanel = false;
      };

      if (tool === "trace") {
        if (this.traceModeActive) {
          // Toggle OFF
          this.traceModeActive = false;
          this.showTracePopup = false;
          this.showToolMessage("Trace mode off.");
          return;
        }
        resetAll();
        // Open pen picker first
        this.showTracePopup = true;
        return;
      }

      if (tool === "measure") {
        resetAll();
        // open label chooser first
        this.showAngleLabelPopup = true;
        return;
      }

      if (tool === "highlight") {
        resetAll();
        this.highlightModeActive = true;
        this.showToolMessage("Highlight: click-start then click-end.");
        return;
      }

      if (tool === "underline") {
        resetAll();
        this.underlineModeActive = true;
        this.showToolMessage("Underline: click-start then click-end.");
        return;
      }

      if (tool === "comment") {
        resetAll();
        this.commentModeActive = true;
        this.showToolMessage("Click anywhere to add a comment.");
        // comment is placed on next click-down within stage via startTrace
        return;
      }
    },

    showPenSelection() {
      // Keep UI minimal: set trace active immediately (we already have angles/labels UI elsewhere)
      this.traceModeActive = true;
      this.showToolMessage("Trace mode active. Draw freehand on the page.");
    },

    openHorizontalPopup() {
      this.showStatsPanel = false;
      this.showHorizontalPopup = true;
      this.showVerticalPopup = false;
    },
    openVerticalPopup() {
      this.showStatsPanel = false;
      this.showVerticalPopup = true;
      this.showHorizontalPopup = false;
    },
    hideLengthPopup() {
      this.showHorizontalPopup = false;
      this.showVerticalPopup = false;
    },
    beginLength(type) {
      this.selectedMeasurement = type;
      this.hideLengthPopup();
      this.startLengthMeasurement();
    },

    /* ---------- Angle label popup ---------- */
    confirmNewAngleLabel() {
      const label = (this.newAngleLabel || "").trim();
      if (!label) return;
      if (!this.angleLabels.includes(label)) this.angleLabels.push(label);
      this.activeAngleLabel = label;
      this.newAngleLabel = "";
    },
    confirmAngleLabel() {
      if (!this.activeAngleLabel) {
        this.showToolMessage("Choose or create a label first.");
        return;
      }
      this.showAngleLabelPopup = false;
      this.measureModeActive = true;
      this.showToolMessage(`Angle measure: label "${this.activeAngleLabel}". Click 3 points (A, vertex, B).`);
    },
    cancelAngleLabel() {
      this.activeAngleLabel = null;
      this.showAngleLabelPopup = false;
      this.measureModeActive = false;
    },

    confirmPenSelection() {
  const size = this.penSizes.find(s => s.key === this.selectedPenSize) || this.penSizes[1];
  this.penWidth  = size.w;
  this.penHeight = size.h;
  this.currentNibAngle = this.selectedPenAngle;

  this.showTracePopup = false;
  this.traceModeActive = true;
  this.showToolMessage(`Trace: ${size.label} nib at ${this.currentNibAngle}°`);
},
cancelPenSelection() {
  this.showTracePopup = false;
  this.traceModeActive = false;
},

    /* ---------- Stats panel ---------- */
    calculateCurrentPage() {
      this.showStatsPanel = false;
      this.showStatisticsPopup(this.getCurrentPageStatistics());
    },
    calculateEntireDocument() {
      this.showStatsPanel = false;
      this.showStatisticsPopup(this.getEntireDocumentStatistics());
    },

    openAnglesFilterFromStats() {
      this.showStatsPanel = false;          // ensure the stats panel closes
      this.showAngleFilterPopup = true;     // then open the angles filter
    },

    runAngleStatistics() {
      // collect angles by label + scope
      const gather = [];
      const pages = this.angleScope === "page" ? [this.currentPage] : Array.from({length:this.totalPages}, (_,i)=>i);
      pages.forEach(p => {
        (this.annotationsByPage[p] || []).forEach(a => {
          if (a.type !== "measure") return;
          if (this.angleFilterLabel !== "__ALL__" && a.label !== this.angleFilterLabel) return;
          if (typeof a.angle === "number" || typeof a.angle === "string") {
            gather.push(parseFloat(a.angle));
          }
        });
      });

      this.angleStatistics = {
        average: this.calculateAverage(gather),
        standardDeviation: this.calculateStandardDeviation(gather),
        mode: this.calculateMode(gather),
      };
      this.showAngleFilterPopup = false;
      this.showAngleStatistics = true;
    },

    closeAngleStatisticsPopup() {
      this.showAngleStatistics = false;
    },

    /* ---------- Length measurement ---------- */
    startLengthMeasurement() {
      this.lengthMeasurementActive = true;
      this.isMeasuring = true;
      this.showToolMessage(`Measuring "${this.selectedMeasurement}": click-start then click-end.`);
    },

    /* ---------- Comments ---------- */
    startComment(event) {
      const { x, y } = this.getMousePosition(event);
      this.currentCommentPosition = { x, y };
      this.showCommentInput = true;
    },
    addComment() {
      if (!this.currentCommentText) return;
      if (!this.comments[this.currentPage]) this.comments[this.currentPage] = [];
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
    startDraggingComment(index, event) {
      this.draggingCommentIndex = index;
      const comment = this.comments[this.currentPage][index];
      this.dragOffset = { x: event.clientX - comment.x, y: event.clientY - comment.y };
    },
    dragComment(event) {
      if (this.draggingCommentIndex !== null) {
        const comment = this.comments[this.currentPage][this.draggingCommentIndex];
        comment.x = event.clientX - this.dragOffset.x;
        comment.y = event.clientY - this.dragOffset.y;
      }
    },
    stopDraggingComment() {
      this.draggingCommentIndex = null;
    },

    /* ---------- Clear dropdown ---------- */
    toggleClearDropdown() {
      this.showClearDropdown = !this.showClearDropdown;
    },
    clearHighlights() {
      this.annotationsByPage[this.currentPage] = (this.annotationsByPage[this.currentPage] || [])
        .filter(a => a.type !== "highlight");
      this.showToolMessage("Highlights cleared.");
      this.showClearDropdown = false;
    },
    clearUnderlines() {
      this.annotationsByPage[this.currentPage] = (this.annotationsByPage[this.currentPage] || [])
        .filter(a => a.type !== "underline");
      this.showToolMessage("Underlines cleared.");
      this.showClearDropdown = false;
    },
    clearComments() {
      this.comments[this.currentPage] = [];
      this.showToolMessage("Comments cleared.");
      this.showClearDropdown = false;
    },
    clearTraces() {
      this.annotationsByPage[this.currentPage] = (this.annotationsByPage[this.currentPage] || [])
        .filter(a => a.type !== "trace");
      this.showToolMessage("Traces cleared.");
      this.showClearDropdown = false;
    },
    clearAngles() {
      this.annotationsByPage[this.currentPage] = (this.annotationsByPage[this.currentPage] || [])
        .filter(a => a.type !== "measure");
      this.showToolMessage("Angles cleared.");
      this.showClearDropdown = false;
    },
    clearHorizontalLengths() {
      ["ascenders","descenders","interlinear","upperMargin","lowerMargin","lineHeight","minimumHeight"].forEach((t)=>{
        if (this.lengthMeasurements[t]) delete this.lengthMeasurements[t][this.currentPage];
      });
      this.showToolMessage("Horizontal lengths cleared.");
      this.showClearDropdown = false;
    },
    clearVerticalLengths() {
      ["internalMargin","intercolumnSpaces"].forEach((t)=>{
        if (this.lengthMeasurements[t]) delete this.lengthMeasurements[t][this.currentPage];
      });
      this.showToolMessage("Vertical lengths cleared.");
      this.showClearDropdown = false;
    },
    clearAll() {
      this.annotationsByPage[this.currentPage] = [];
      this.comments[this.currentPage] = [];
      const all = ["ascenders","descenders","interlinear","upperMargin","lowerMargin","internalMargin","intercolumnSpaces","lineHeight","minimumHeight"];
      all.forEach(t => { if (this.lengthMeasurements[t]) delete this.lengthMeasurements[t][this.currentPage]; });
      this.strokes = [];
      this.measurePoints = [];
      this.calculatedAngle = 0;
      this.showToolMessage("All annotations cleared.");
      this.showClearDropdown = false;
    },

    /* ---------- Label drag for length badges ---------- */
    startLabelDrag(id, event) {
      this.draggedLabelIndex = id;
      const pos = this.labelPositions[id] || { x: 15, y: 15 };
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

    /* ---------- Paging ---------- */
    nextPage() {
      if (this.currentPage < this.totalPages - 1) {
        this.currentPage++;
        if (!this.comments[this.currentPage]) this.comments[this.currentPage] = [];
      }
    },
    prevPage() {
      if (this.currentPage > 0) {
        this.currentPage--;
        if (!this.comments[this.currentPage]) this.comments[this.currentPage] = [];
      }
    },
    goToPage(pageNumber = null) {
      const targetPage = pageNumber !== null ? pageNumber : this.pageInput;
      const newPage = Math.max(1, Math.min(targetPage, this.totalPages)) - 1;
      this.currentPage = newPage;
      this.pageInput = newPage + 1; // keep pageInput in sync
    },

    /* ---------- Stage interactions (DROP-IN versions) ---------- */
    startTrace(event) {
      // MOVE MODE
      if (this.moveModeActive && this.bankSelectedKeys.length > 0) {
        this.moveStartPos = this.getMousePosition(event);
        return;
      }

      // COMMENT PLACEMENT
      if (this.commentModeActive) {
        this.startComment(event);
        return;
      }

      // LENGTH BANDS
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

      // CROP START
      if (this.croppingStarted && this.cropButtonClicked && !this.croppedImage) {
        const { x, y } = this.getMousePosition(event);
        this.startPoint = { x, y };
        this.currentSquare = { x, y, width: 0, height: 0 };
        return;
      }

      // HIGHLIGHT / UNDERLINE
      if (this.highlightModeActive || this.underlineModeActive) {
        if (!this.startPoint) {
          const { x, y } = this.getMousePosition(event);
          this.startPoint = { x, y };
          if (this.highlightModeActive) this.currentSquare = { x, y, width: 0, height: 0 };
          else this.currentUnderline = { x, y, width: 0, height: 2 };
          return;
        } else {
          if (this.highlightModeActive && this.currentSquare) {
            this.annotationsByPage[this.currentPage].push({ type: "highlight", ...this.currentSquare });
            this.currentSquare = null;
          } else if (this.underlineModeActive && this.currentUnderline) {
            this.annotationsByPage[this.currentPage].push({ type: "underline", ...this.currentUnderline });
            this.currentUnderline = null;
          }
          this.startPoint = null;
          this.highlightModeActive = false;
          this.underlineModeActive = false;
          return;
        }
      }

      // TRACE
      if (this.traceModeActive) {
        const { x, y } = this.getMousePosition(event);
        this.currentStroke = {
          points: [{ x, y }],
          color: this.generateRandomColor(),
          penWidth: this.penWidth,
          penHeight: this.penHeight,
          nibAngle: this.currentNibAngle,
        };
        return;
      }

      // MEASURE ANGLE
      if (this.measureModeActive) {
        const { x, y } = this.getMousePosition(event);
        const nearest = this.findNearestPoint(x, y, 10);
        if (nearest.annotationIndex !== -1) {
          this.editingAnnotationIndex = nearest.annotationIndex;
          this.draggingPoint = nearest.pointIndex;
          const ann = this.annotationsByPage[this.currentPage][this.editingAnnotationIndex];
          this.measurePoints = [...ann.points];
          return;
        }
        if (this.measurePoints.length >= 3) return;
        this.measurePoints.push({ x, y });
        if (this.measurePoints.length === 3) {
          this.calculatedAngle = this.calculateAngle(this.measurePoints[0], this.measurePoints[1], this.measurePoints[2]);
          this.annotationsByPage[this.currentPage].push({
            type: "measure",
            points: [...this.measurePoints],
            angle: this.calculatedAngle,
            label: this.activeAngleLabel || "Unlabeled",
          });
          // add label to list if new
          if (this.activeAngleLabel && !this.angleLabels.includes(this.activeAngleLabel)) {
            this.angleLabels.push(this.activeAngleLabel);
          }
          this.measurePoints = [];
        }
        return;
      }
    },

    trace(event) {
      // MOVE MODE: show live movement preview
      if (this.moveModeActive && this.bankSelectedKeys.length > 0 && this.moveStartPos) {
        const currentPos = this.getMousePosition(event);
        this.currentMoveDelta = {
          x: currentPos.x - this.moveStartPos.x,
          y: currentPos.y - this.moveStartPos.y,
        };
        return;
      }

      // CROP dynamic
      if (this.startPoint && this.cropButtonClicked && this.croppingStarted && !this.croppedImage) {
        const { x, y } = this.getMousePosition(event);
        this.currentSquare = {
          x: Math.min(x, this.startPoint.x),
          y: Math.min(y, this.startPoint.y),
          width: Math.abs(x - this.startPoint.x),
          height: Math.abs(y - this.startPoint.y),
        };
      }

      // HIGHLIGHT dynamic
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

      // UNDERLINE dynamic
      if (this.underlineModeActive && this.currentUnderline) {
        const { x } = this.getMousePosition(event);
        this.currentUnderline = {
          ...this.currentUnderline,
          x: Math.min(x, this.startPoint.x),
          width: Math.abs(x - this.startPoint.x),
        };
      }

      // BANDS dynamic
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

      // TRACE dynamic
      if (this.traceModeActive && this.currentStroke) {
        const { x, y } = this.getMousePosition(event);
        this.currentStroke.points.push({ x, y });
      }

      // ANGLE drag existing vertex
      if (this.measureModeActive && this.draggingPoint !== -1) {
        const { x, y } = this.getMousePosition(event);
        this.measurePoints[this.draggingPoint] = { x, y };
        if (this.editingAnnotationIndex !== -1) {
          const ann = this.annotationsByPage[this.currentPage][this.editingAnnotationIndex];
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

    endTrace(event) {
      // MOVE MODE: apply delta
      if (this.moveModeActive && this.bankSelectedKeys.length > 0 && this.moveStartPos) {
        const endPos = this.getMousePosition(event);
        const dx = endPos.x - this.moveStartPos.x;
        const dy = endPos.y - this.moveStartPos.y;
        this.applyMoveDelta(dx, dy);
        this.moveStartPos = null;
        this.currentMoveDelta = { x: 0, y: 0 };
        this.disableMoveMode();
        return;
      }

      // TRACE finalize
      if (this.traceModeActive && this.currentStroke) {
        this.annotationsByPage[this.currentPage].push({
          type: "trace",
          points: this.currentStroke.points,
          color: this.currentStroke.color,
          penWidth: this.currentStroke.penWidth,
          penHeight: this.currentStroke.penHeight,
          nibAngle: this.currentStroke.nibAngle,
        });
        this.currentStroke = null;
      }

      // ANGLE drag end
      if (this.measureModeActive && this.draggingPoint !== -1) {
        this.draggingPoint = -1;
        this.editingAnnotationIndex = -1;
        this.measurePoints = [];
      }

      // CROP finalize
      if ((this.croppingStarted || this.currentSquare) && this.cropButtonClicked && !this.croppedImage) {
        this.generateCroppedFromCurrentSquare();
        this.croppingStarted = false;
        this.cropButtonClicked = false;
        this.currentSquare = null;
        this.startPoint = null;
      }
    },

    /* ---------- Angle helpers ---------- */
    findNearestPoint(x, y, threshold = 10) {
      const all = (this.annotationsByPage[this.currentPage] || [])
        .map((a, i) => ({ a, i }))
        .filter(({ a }) => a && a.type === "measure");

      let best = { annotationIndex: -1, pointIndex: -1, dist: Infinity };
      all.forEach(({ a, i }) => {
        a.points.forEach((p, pi) => {
          const d = Math.hypot(x - p.x, y - p.y);
          if (d < threshold && d < best.dist) best = { annotationIndex: i, pointIndex: pi, dist: d };
        });
      });
      return { annotationIndex: best.annotationIndex, pointIndex: best.pointIndex };
    },

    /* ---------- Move selected ---------- */
    enableMoveMode() {
      if (this.bankSelectedKeys.length === 0) return;
      this.moveModeActive = true;
      this.showToolMessage("Move mode: drag on the image to reposition selected items.");
    },
    disableMoveMode() {
      this.moveModeActive = false;
      this.moveStartPos = null;
    },
    applyMoveDelta(dx, dy) {
      const page = this.currentPage;
      this.bankSelectedKeys.forEach((k) => {
        const { kind, ref } = this.parseBankKey(k);
        if (kind === "a") {
          const i = +ref;
          const a = this.annotationsByPage[page]?.[i];
          if (!a) return;
          if (a.type === "highlight" || a.type === "underline") {
            a.x += dx; a.y += dy;
          } else if (a.type === "trace" || a.type === "measure") {
            a.points = a.points.map((p) => ({ x: p.x + dx, y: p.y + dy }));
          }
        }
        if (kind === "c") {
          const i = +ref;
          const c = this.comments[page]?.[i];
          if (!c) return;
          c.x += dx; c.y += dy;
        }
        if (kind === "l") {
          const id = ref;
          for (const label in this.lengthMeasurements) {
            const arr = this.lengthMeasurements[label]?.[page];
            if (!Array.isArray(arr)) continue;
            const m = arr.find((mm) => String(mm.id) === String(id));
            if (m) {
              m.x += dx; m.y += dy;
              if (this.labelPositions[id]) {
                this.labelPositions[id] = {
                  x: (this.labelPositions[id].x || 0) + dx,
                  y: (this.labelPositions[id].y || 0) + dy,
                };
              }
              break;
            }
          }
        }
      });
    },
    deleteSelectedFromBank() {
      if (this.bankSelectedKeys.length === 0) return;
      const page = this.currentPage;

      const annIdxs = [];
      const cmtIdxs = [];
      const lengthIds = [];

      this.bankSelectedKeys.forEach((k) => {
        const { kind, ref } = this.parseBankKey(k);
        if (kind === "a") annIdxs.push(+ref);
        if (kind === "c") cmtIdxs.push(+ref);
        if (kind === "l") lengthIds.push(ref);
      });

      if (annIdxs.length) {
        const sorted = [...annIdxs].sort((a,b)=>b-a);
        sorted.forEach((i) => {
          if (this.annotationsByPage[page]?.[i] != null) {
            this.annotationsByPage[page].splice(i, 1);
          }
        });
      }
      if (cmtIdxs.length) {
        const sorted = [...cmtIdxs].sort((a,b)=>b-a);
        sorted.forEach((i) => {
          if (this.comments[page]?.[i] != null) {
            this.comments[page].splice(i, 1);
          }
        });
      }
      if (lengthIds.length) {
        for (const label in this.lengthMeasurements) {
          const pageArr = this.lengthMeasurements[label]?.[page];
          if (Array.isArray(pageArr)) {
            this.lengthMeasurements[label][page] = pageArr.filter((m) => !lengthIds.includes(String(m.id)));
          }
        }
        lengthIds.forEach((id) => { if (this.labelPositions[id]) delete this.labelPositions[id]; });
      }

      this.bankSelectedKeys = [];
    },

    /* ---------- Image & crop ---------- */
    handleImageLoad() {
      const imageElement = this.$refs.image;
      if (imageElement) {
        const displayedWidth = imageElement.width;
        const naturalWidth = imageElement.naturalWidth;
        this.scalingFactor = displayedWidth / naturalWidth;
      }
      this.imageLoaded = true;
    },
    startCrop() {
      this.croppingStarted = true;
      this.cropButtonClicked = true;
      this.currentSquare = null;
      this.startPoint = null;
      this.showToolMessage("Click and drag to crop.");
    },
    async generateCroppedFromCurrentSquare() {
      const { x, y, width, height } = this.currentSquare;
      const imageElement = this.$refs.image;
      const naturalWidth = imageElement.naturalWidth;
      const naturalHeight = imageElement.naturalHeight;
      const rect = imageElement.getBoundingClientRect();
      const scaleX = naturalWidth / rect.width;
      const scaleY = naturalHeight / rect.height;

      const scaledX = (x - 0) * scaleX; // since x,y already relative to viewer
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
      await new Promise((resolve, reject) => {
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
          resolve();
        };
        img.onerror = reject;
      });
    },
    saveCroppedImageAsPNG() {
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
    closeCroppedPopup() {
      this.croppedImage = null;
    },

    /* ---------- Save to PDF ---------- */
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
          const hasLengths = Object.values(this.lengthMeasurements).some(obj => (obj[i] || []).length > 0);

          if (annotations.length === 0 && comments.length === 0 && !hasLengths) continue;

          this.currentPage = i;
          await this.$nextTick();

          const viewer = this.$refs.viewer;
          const canvas = await html2canvas(viewer, {
            scale: 2,
            useCORS: true,
            logging: false,
            ignoreElements: (el) =>
              el.classList?.contains("top-bar") ||
              el.classList?.contains("navigation-bar")
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

    /* ---------- Stats helpers ---------- */
    extractValues(measurements, type) {
      const vertical = ["internalMargin", "intercolumnSpaces"];
      const isVertical = vertical.includes(type);
      // In our rectangles: for horizontal labels we report height; for vertical we report width
      return measurements.map((m) => (isVertical ? m.width : m.height));
    },
    calculateAverage(values) {
      if (!values || values.length === 0) return 0;
      const nums = values.map(Number).filter(v => !isNaN(v));
      if (!nums.length) return 0;
      return nums.reduce((a,b)=>a+b,0) / nums.length;
    },
    calculateStandardDeviation(values) {
      if (!values || values.length === 0) return 0;
      const nums = values.map(Number).filter(v => !isNaN(v));
      if (!nums.length) return 0;
      const avg = this.calculateAverage(nums);
      const variance = nums.reduce((acc,v)=>acc + (v-avg)*(v-avg), 0) / nums.length;
      return Math.sqrt(variance);
    },
    calculateMode(values) {
      if (!values || values.length === 0) return "No mode";
      const nums = values.map(Number).filter(v => !isNaN(v));
      if (!nums.length) return "No mode";
      const freq = {};
      nums.forEach(v => { freq[v] = (freq[v] || 0) + 1; });
      const maxF = Math.max(...Object.values(freq));
      if (maxF === 1) return "No mode";
      const modes = Object.keys(freq).filter(k => freq[k] === maxF).map(Number);
      return Math.min(...modes);
    },
    showStatisticsPopup(statistics) {
      this.horizontalStatistics = {};
      this.verticalStatistics = {};
      for (const [type, stats] of Object.entries(statistics)) {
        if (["ascenders","descenders","interlinear","upperMargin","lowerMargin","lineHeight","minimumHeight"].includes(type)) {
          this.horizontalStatistics[type] = stats;
        } else if (["internalMargin","intercolumnSpaces"].includes(type)) {
          this.verticalStatistics[type] = stats;
        }
      }
      this.showStatistics = true;
    },
    closeStatisticsPopup() {
      this.showStatistics = false;
    },
    getCurrentPageStatistics() {
      const horizontal = ["ascenders","descenders","interlinear","upperMargin","lowerMargin","lineHeight","minimumHeight"];
      const vertical = ["internalMargin","intercolumnSpaces"];
      const stats = {};
      horizontal.forEach((t) => {
        const arr = this.lengthMeasurements[t]?.[this.currentPage];
        if (arr?.length) {
          const vals = this.extractValues(arr, t);
          stats[t] = {
            average: this.calculateAverage(vals),
            standardDeviation: this.calculateStandardDeviation(vals),
            mode: this.calculateMode(vals),
          };
        }
      });
      vertical.forEach((t) => {
        const arr = this.lengthMeasurements[t]?.[this.currentPage];
        if (arr?.length) {
          const vals = this.extractValues(arr, t);
          stats[t] = {
            average: this.calculateAverage(vals),
            standardDeviation: this.calculateStandardDeviation(vals),
            mode: this.calculateMode(vals),
          };
        }
      });
      return stats;
    },
    getEntireDocumentStatistics() {
      const horizontal = ["ascenders","descenders","interlinear","upperMargin","lowerMargin","lineHeight","minimumHeight"];
      const vertical = ["internalMargin","intercolumnSpaces"];
      const stats = {};
      horizontal.forEach((t) => {
        let vals = [];
        for (let p = 0; p < this.totalPages; p++) {
          const arr = this.lengthMeasurements[t]?.[p];
          if (arr?.length) vals = vals.concat(this.extractValues(arr, t));
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
          const arr = this.lengthMeasurements[t]?.[p];
          if (arr?.length) vals = vals.concat(this.extractValues(arr, t));
        }
        stats[t] = {
          average: this.calculateAverage(vals),
          standardDeviation: this.calculateStandardDeviation(vals),
          mode: this.calculateMode(vals),
        };
      });
      return stats;
    },

    /* ---------- Tool message ---------- */
    showToolMessage(message) {
      this.toolMessage = message;
      setTimeout(() => { this.toolMessage = ""; }, 3000);
    },
  },
};
</script>

<style scoped>
* { font-family: "Arial", "Helvetica", sans-serif !important; }
.viewer-container { display: flex; flex-direction: column; height: 100vh; background-color: #f1f1f1; }
.top-bar { display: flex; justify-content: space-between; align-items: center; background: #f1f1f1; border-bottom: 1px solid #ddd; padding: 10px 20px; }
.logo { height: 60px; }

.toolbar { display: flex; justify-content: center; gap: 30px; flex: 1; position: relative; }
.toolbar-item { display: flex; flex-direction: column; align-items: center; font-size: 12px; color: #333; cursor: pointer; padding: 3px; }
.toolbar-item:hover { color: #007bff; }

.tool-message {
  position: fixed; top: 60px; left: 50%; transform: translateX(-50%);
  background-color: #007bff; color: white; padding: 8px 14px; border-radius: 6px; z-index: 1200; font-size: 12px;
}

.workspace { display: block; height: calc(100vh - 110px); }
.stage {    position: relative;   background: #f1f1f1; }
.bank { width: 300px; min-width: 300px; border-left: 1px solid #e5e7eb; }

.navigation-bar { display: flex; justify-content: center; align-items: center; margin: 0; padding: 6px 0; gap: 8px; background: #f1f1f1; border-bottom: 1px solid #ddd; }
.page-input-container { display: flex; align-items: center; gap: 4px; }
.page-input-container input { width: 45px; text-align: center; }

/* === Base stacking for stage and annotations === */
.stage,
.pdf-viewer {
  position: relative;
  z-index: 0;
}

.drawing-layer,            /* SVG traces/angles */
.highlight-rectangle,
.underline-line,
.length-measurement,       /* the colored band rectangles */
.comment-container,
.cropping-rectangle {
  z-index: 200;            /* safely below overlays/panels */
}

/* Bank panel still floats above the stage but below popups */
.bank-panel {
  z-index: 1500;
}

/* === Popups / overlays must always be on top === */
.length-popup,             /* Horizontal/Vertical selectors */
.statistics-popup,         /* results tables */
.stats-panel,              /* the 'Statistics' quick panel */
.cropped-popup,            /* cropped image dialog */
.blurred-background {
  z-index: 5000;           /* top-most */
}

/* Just to be safe, their internal cards sit above their own backdrop */
.length-popup-content,
.statistics-popup-content,
.panel-card.stats-card,
.cropped-popup-content {
  position: relative;
  z-index: 1;
}

.pdf-viewer { margin: 0; position: relative; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; overflow: hidden; max-height: 100%; }
.pdf-viewer img { max-width: 100%; max-height: 100%; object-fit: contain; display: block; }

.drawing-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }

.underline-line { position: absolute; background-color: blue; height: 2px; pointer-events: none; z-index: 1100; }

.length-measurement { position: absolute; border: 2px solid rgba(0, 0, 0, 0.5); pointer-events: none; }
.length-label {
  position: absolute; left: 15px; top: 15px; transform: translateY(0);
  color: black; font-size: 12px; background-color: white; padding: 2px 5px; border-radius: 3px;
}
.draggable-label { cursor: grab; user-select: none; }
.draggable-label:active { cursor: grabbing; }

.highlight-rectangle { position: absolute; border: 2px solid rgba(255, 255, 0, 0.7); background-color: rgba(255, 255, 0, 0.3); pointer-events: none; }

.cropping-rectangle { position: absolute; border: 2px dashed #007bff; background-color: rgba(0, 123, 255, 0.2); pointer-events: none; z-index: 100; }

.blurred-background { position: fixed; top: 0; left: 0; width: 100%; height: 100%; backdrop-filter: blur(8px); background-color: rgba(0,0,0,0.3); z-index: 999; }
.cropped-popup { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #fff; border: 1px solid #ccc; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); z-index: 1000; padding: 20px; text-align: center; }
.cropped-popup-content img { max-width: 100%; max-height: 300px; margin-bottom: 20px; }
.cropped-popup-content button { margin-top: 10px; padding: 8px 16px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
.cropped-popup-content button:hover { background-color: #0056b3; }

.comment-container { position: absolute; display: flex; flex-direction: column; align-items: center; cursor: grab; z-index: 1; }
.comment-container:active { cursor: grabbing; }
.comment-icon { font-size: 24px; background-color: #ffecb3; border-radius: 50%; width: 30px; height: 30px; display: flex; justify-content: center; align-items: center; }
.comment-bubble { margin-left: 8px; padding: 8px; background: #fff; border: 1px solid #ccc; border-radius: 4px; box-shadow: 0px 2px 4px rgba(0,0,0,0.1); position: relative; }
.comment-bubble::after { content: ""; position: absolute; top: 50%; left: -8px; width: 0; height: 0; border: 8px solid transparent; border-right-color: #fff; transform: translateY(-50%); }
.comment-content { font-size: 14px; color: #333; }
.comment-input-container { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #fff; border: 1px solid #ccc; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 10px; width: 300px; z-index: 1000; }
.comment-input-box { width: 100%; height: 60px; border: 1px solid #ccc; border-radius: 5px; padding: 8px; font-size: 14px; margin-bottom: 8px; resize: none; }
.btn-save-comment, .btn-cancel-comment { background-color: #007bff; color: white; border: none; border-radius: 5px; padding: 5px 10px; font-size: 14px; cursor: pointer; }
.btn-cancel-comment { background-color: #6c757d; margin-left: 10px; }

.clear-dropdown {
  position: absolute; top: 100%; left: 0; background: white; border: 1px solid #ccc; border-radius: 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); z-index: 1100; min-width: 160px;
}
.clear-dropdown div { padding: 8px 12px; cursor: pointer; }
.clear-dropdown div:hover { background: #f5f5f5; }

.length-popup {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  display: flex; justify-content: center; align-items: center;
  background-color: rgba(0,0,0,0.5); z-index: 1200;
}
.length-popup-content {
  background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); text-align: center; width: 520px; max-width: calc(100% - 24px);
}
.btn-grid, .label-grid { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 14px 0; }
.grid-btn {
  border: 1px solid #2563eb;
  background: #3b82f6;         /* primary blue */
  color: #fff;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: filter .15s, transform .02s;
}
.grid-btn:hover { filter: brightness(0.95); }
.grid-btn:active { transform: translateY(1px); }
.grid-btn.active {
  background: #2563eb;
  border-color: #1d4ed8;
}
.swatch {
  display:inline-block;
  width:16px;
  height:16px;
  border-radius:4px;
  margin-right:8px;
  border:1px solid rgba(0,0,0,.1);
  vertical-align: -2px;
}
.popup-actions { display: flex; justify-content: center; gap: 10px; }

.row { margin: 12px 0; text-align: left; }
.row label { display: inline-block; width: 80px; font-size: 13px; color: #333; }
.new-label-row { display: flex; gap: 8px; justify-content: center; margin: 8px 0 0; }
.new-label-row input { flex: 1; min-width: 240px; border: 1px solid #ddd; border-radius: 6px; padding: 6px 8px; }

/* Overlay for stats panel */
.stats-panel {
  position: fixed;
  inset: 0;                           /* top/left/right/bottom: 0 */
  background: rgba(0, 0, 0, 0.30);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Card look & feel */
.panel-card.stats-card {
  background: #ffffff;
  border-radius: 14px;
  box-shadow: 0 12px 28px rgba(0,0,0,0.18);
  width: min(680px, calc(100% - 32px));
  padding: 22px 24px 24px;
  text-align: center;
}

/* Title */
.panel-card.stats-card h4 {
  margin: 0 0 14px;
  font-size: 26px;
  font-weight: 700;
}

/* Button layout inside the stats card */
.panel-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  margin-top: 6px;
}

/* Reuse the blue 'grid-btn' look but add a little breathing room */
.panel-actions .grid-btn {
  min-width: 230px;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid #2f60e3;
  background: #3f6eea;
  color: #fff;
  font-weight: 600;
  box-shadow: 0 2px 0 rgba(0,0,0,0.06) inset;
}
.panel-actions .grid-btn:hover {
  filter: brightness(0.97);
}
.panel-actions .grid-btn:active {
  transform: translateY(1px);
}

.statistics-popup {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  display: flex; justify-content: center; align-items: center; background: rgba(0,0,0,0.5); z-index: 1200;
}
.statistics-popup-content {
  background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  max-width: 600px; width: 100%;
}
.statistics-popup-content table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
.statistics-popup-content th, .statistics-popup-content td { border: 1px solid #ddd; padding: 8px; text-align: center; }
.statistics-popup-content th { background: #f2f2f2; }
.statistics-popup-content h4 { margin-top: 12px; margin-bottom: 8px; }
</style>
