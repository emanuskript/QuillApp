<!-- /src/components/IIIFViewer.vue -->
<template>
  <div class="viewer-container">
    <!-- Top Bar -->
    <div class="top-bar">
      <img
        src="@/assets/logo.png"
        alt="Logo"
        class="logo"
        @click="goHome"
      />

      <div class="toolbar">
        <!-- Comment -->
        <div class="toolbar-item" @click="selectTool('comment')">
          <i class="fa-regular fa-comment"></i>
          <span>Comment</span>
        </div>

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

        <!-- Trace -->
        <div class="toolbar-item" @click="selectTool('trace')">
          <i class="fa-solid fa-pencil"></i>
          <span>Trace</span>
        </div>

        <!-- Crop -->
        <div class="toolbar-item" @click="startCrop">
          <i class="fa-solid fa-scissors"></i>
          <span>Crop</span>
        </div>

        <!-- divider -->
        <div class="toolbar-divider" aria-hidden="true"></div>

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

        <!-- Generate Statistics -->
        <div class="toolbar-item" @click="showStatsPanel = !showStatsPanel">
          <i class="fa-solid fa-calculator"></i>
          <span>Generate</span>
          <span>Statistics</span>
        </div>

        <!-- divider -->
        <div class="toolbar-divider" aria-hidden="true"></div>

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
      :imageReady="imageReady"
      :zoomLevel="zoomLevel"
      :minZoom="minZoom"
      @prev="prevPage"
      @next="nextPage"
      @go-to="goToPage"
      @zoom-in="zoomIn"
      @zoom-out="zoomOut"
      @start-hold-reset="startHoldReset"
      @cancel-hold-reset="cancelHoldReset"
    />

    <!-- Tool tip message -->
    <div class="tool-message" v-if="toolMessage">{{ toolMessage }}</div>

    <!-- Workspace: stage + annotations bank -->
    <div class="workspace">
      <!-- Image Stage -->
      <div
        class="pdf-viewer stage"
        ref="viewer"
        :style="{ cursor: stageCursor }"
        @mousedown="startTrace($event)"
        @mousemove="trace($event)"
        @mouseup="endTrace($event)"
        @selectstart.prevent.stop
        @dragstart.prevent.stop
        @contextmenu.prevent.stop
        ondragstart="return false"
        onselectstart="return false"
        oncontextmenu="return false"
        unselectable="on"
      >
        <!-- NEW: zoom anchor -->
        <div v-show="imageReady" class="zoom-anchor" :style="anchorStyle">
          <!-- ⬇️ keep your existing <img>, <svg>, rectangles, comments, etc. here ⬇️ -->
        
        <!-- NUCLEAR OPTION: Replace img with div background -->
        <div
          v-if="croppedImage || currentImage"
          class="image-viewer-background"
          :style="{
            backgroundImage: `url(${croppedImage || currentImage})`,
            backgroundSize: 'contain',
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'center',
            width: '100%',
            height: '100%'
          }"
          draggable="false"
          unselectable="on"
          @selectstart.prevent.stop
          @dragstart.prevent.stop
          @mousedown.prevent.stop="handleMainImageMouseDown"
          @contextmenu.prevent.stop
          ondragstart="return false"
          onselectstart="return false"
          oncontextmenu="return false"
          onmousedown="return false"
          onmouseup="return false"
          onmousemove="return false"
          onclick="return false"
        ></div>
        
        <!-- Invisible image for size calculations positioned correctly -->
        <img
          v-if="croppedImage || currentImage"
          :src="croppedImage || currentImage"
          ref="image"
          class="calculation-image"
          @load="handleImageLoad"
          style="width: 100% !important; height: 100% !important; object-fit: contain !important; opacity: 0 !important; pointer-events: none !important; user-select: none !important; position: absolute !important; top: 0 !important; left: 0 !important; z-index: -1 !important;"
        />

        <!-- SVG drawing layer -->
        <svg
          v-if="showTraces"
          class="drawing-layer"
          :width="baseFitWidth"
          :height="baseFitHeight"
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

        <!-- Comments (attached to page edge; positioned in viewer space, not scaled) -->
        <div
          v-for="(c, i) in currentPageComments"
          :key="'comment-'+i"
          class="comment-card"
          :style="commentStyle(c)"
          @mousedown.stop="startDraggingComment(i, $event)"
          @mouseup.stop="stopDraggingComment"
          @mousemove.stop="dragComment"
          @click.stop
        >
          <div class="comment-pin">💬</div>
          <div class="comment-bubble">
            <div class="comment-text">{{ c.text }}</div>
          </div>
        </div>

        <!-- Inline composer near target Y on chosen side -->
        <div
          v-if="showCommentInput"
          class="comment-composer"
          :style="composerStyle"
          @mousedown.stop
          @click.stop
        >
          <textarea
            class="composer-textarea"
            v-model="currentCommentText"
            placeholder="Add your comment…"
            @keydown.enter.exact.prevent="addComment"
          ></textarea>

          <div class="composer-actions">
            <button class="btn-blue" @click.stop="addComment">Add</button>
            <button class="btn-gray" @click.stop="cancelComment">Cancel</button>
          </div>
        </div>

      </div>

<!-- Compact Bank Panel (anchored, not affecting layout) -->
   <AnnotationsBank
    :page="currentPage"
     :items="bankItems"
     :selectedKeys="bankSelectedKeys"
     :multiSelect="bankMultiSelect"
     :moveActive="moveModeActive"
     :zoomLevel="zoomLevel"
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
            <span>Minim Height</span>
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
        <h3>Angle Statistics ({{ angleStatistics.count }} angles)</h3>
        <table>
          <thead>
            <tr>
              <th>Mean</th>
              <th>Median</th>
              <th>Std Dev</th>
              <th>Min</th>
              <th>Max</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ angleStatistics.mean }}°</td>
              <td>{{ angleStatistics.median }}°</td>
              <td>{{ angleStatistics.stdDev }}°</td>
              <td>{{ angleStatistics.min }}°</td>
              <td>{{ angleStatistics.max }}°</td>
            </tr>
          </tbody>
        </table>
        <button class="grid-btn" @click="showAngleStatistics = false">Close</button>
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

    <!-- Clear Confirmation Popup -->
    <div v-if="showClearConfirmation" class="length-popup" @click.self="showClearConfirmation = false">
      <div class="length-popup-content">
        <h3>Clear All Annotations</h3>
        <p>Are you sure you want to clear all annotations on this page?</p>
        <div class="popup-actions">
          <button class="grid-btn confirm-btn" @click="confirmClearAll">Yes</button>
          <button class="grid-btn cancel-btn" @click="cancelClearAll">No</button>
        </div>
      </div>
    </div>

    <!-- ========= CROPPED IMAGE MODAL (drop-in replacement) ========= -->
    <div v-if="croppedImage" class="blurred-background" @click="closeCroppedPopup"></div>

    <div v-if="croppedImage" class="cropped-popup" @click.stop>
      <div class="cropped-popup-content">

        <!-- Header row with centered zoom controls -->
        <div class="crop-header">
          <div class="left-spacer"></div>

          <div class="zoom-cluster">
            <button class="zoom-pill" :disabled="cropZoom<=1" @click.stop="cropZoomOut">−</button>
            <button class="zoom-pill" @click.stop="cropZoomIn">+</button>
            <span class="zoom-readout">{{ Math.round(cropZoom*100) }}%</span>
          </div>

          <div class="crop-actions">
            <button class="grid-btn" @click.stop="saveCroppedImageAsPNG">Save PNG</button>
            <button class="grid-btn" @click.stop="saveCroppedImageAsSVG" :disabled="!croppedSvg">Save SVG</button>
            <button class="grid-btn" @click.stop="saveCroppedImage">Save w/ Annotations</button>
            <button class="grid-btn cancel-btn" @click.stop="closeCroppedPopup">Close</button>
          </div>
        </div>

        <!-- Mini Toolbar for cropped popup -->
        <div class="crop-toolbar">
          <div class="crop-tool" 
               :class="{ active: highlightModeActive }"
               @click="selectTool('highlight')"
               title="Highlight">
            <i class="fas fa-highlighter"></i>
            <span>Highlight</span>
          </div>
          
          <div class="crop-tool" 
               :class="{ active: underlineModeActive }"
               @click="selectTool('underline')"
               title="Underline">
            <i class="fas fa-minus"></i>
            <span>Underline</span>
          </div>
          
          <div class="crop-tool" 
               :class="{ active: traceModeActive }"
               @click="selectTool('trace')"
               title="Draw">
            <i class="fas fa-pencil-alt"></i>
            <span>Draw</span>
          </div>
          
          <div class="crop-tool" 
               :class="{ active: measureModeActive }"
               @click="selectTool('measure')"
               title="Measure Angle">
            <i class="fas fa-drafting-compass"></i>
            <span>Angle</span>
          </div>
          
          <div class="crop-tool" 
               @click="calculateCroppedAngleStatistics"
               title="Angle Statistics">
            <i class="fas fa-calculator"></i>
            <span>Stats</span>
          </div>
          
          <div class="crop-tool-divider"></div>
          
          <div class="crop-tool" 
               @click="selectTool('')"
               title="Pan/Zoom">
            <i class="fas fa-hand-paper"></i>
            <span>Pan</span>
          </div>
        </div>

        <!-- Stage -->
        <div
          class="crop-stage"
          ref="croppedStage"
          :style="{ cursor: croppedStageCursor }"
          @mousedown="cropStageDown"
          @mousemove="cropStageMove"
          @mouseup="cropStageUp"
          @mouseleave="cropStageUp"
          @selectstart.prevent.stop
          @dragstart.prevent.stop
          @contextmenu.prevent.stop
          @dblclick.prevent.stop
          ondragstart="return false"
          onselectstart="return false"
          oncontextmenu="return false"
          unselectable="on"
        >
          <div class="crop-anchor" :style="croppedAnchorStyle">
            <!-- Base image (fit-to-anchor coordinates) -->
            <img
              :src="croppedImage"
              ref="croppedImg"
              class="cropped-image"
              alt=""
              draggable="false"
              unselectable="on"
              @load="onCroppedImgLoad"
              style="pointer-events: none !important; user-select: none !important;"
              ondragstart="return false"
              onselectstart="return false"
              oncontextmenu="return false"
              onmousedown="return false"
              onmouseup="return false"
              onmousemove="return false"
              onclick="return false"
            />

            <!-- Transparent overlay to capture mouse events -->
            <div class="image-overlay" 
                 style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; background: transparent; cursor: inherit;"></div>

            <!-- ABS layer (rects/lines) -->
            <div
              v-for="(a, i) in croppedAnnotationsAbs"
              :key="'ca-'+i"
              v-show="a.type==='highlight' || a.type==='underline'"
              :class="a.type==='highlight' ? 'highlight-rectangle' : 'underline-line'"
              :style="a.style"
            ></div>

            <!-- Live rectangles/lines -->
            <div
              v-if="croppedLive.highlight"
              class="highlight-rectangle"
              :style="croppedLive.highlight.style"
            ></div>
            <div
              v-if="croppedLive.underline"
              class="underline-line"
              :style="croppedLive.underline.style"
            ></div>

            <!-- SVG layer (traces & angles) -->
            <svg class="drawing-layer" :width="croppedBaseW" :height="croppedBaseH"
                 style="position:absolute;inset:0;z-index:2;">
              <!-- traces -->
              <polyline
                v-for="(a, i) in croppedTraces"
                :key="'ct-'+i"
                :points="formatPoints(a.points)"
                :stroke="a.color"
                :stroke-width="a.penWidth || 2"
                fill="none"
              />
              <!-- live stroke -->
              <polyline
                v-if="croppedLive.trace"
                :points="formatPoints(croppedLive.trace.points)"
                :stroke="croppedLive.trace.color"
                :stroke-width="croppedLive.trace.penWidth || 2"
                fill="none"
              />

              <!-- angles -->
              <g v-for="(a, i) in croppedMeasures" :key="'cm-'+i">
                <line v-if="a.points.length>=2"
                  :x1="a.points[0].x" :y1="a.points[0].y"
                  :x2="a.points[1].x" :y2="a.points[1].y"
                  stroke="blue" stroke-width="2" />
                <line v-if="a.points.length===3"
                  :x1="a.points[1].x" :y1="a.points[1].y"
                  :x2="a.points[2].x" :y2="a.points[2].y"
                  stroke="blue" stroke-width="2" />
                <text v-if="a.points.length===3"
                  :x="a.points[1].x + 10" :y="a.points[1].y - 10"
                  fill="darkblue" font-size="12">
                  {{ a.angle }}°{{ a.label ? ' • '+a.label : '' }}
                </text>
              </g>

              <!-- live angle points/lines -->
              <g v-if="croppedLive.measure && croppedLive.measure.points.length">
                <circle
                  v-for="(p, idx) in croppedLive.measure.points"
                  :key="'livep-'+idx"
                  :cx="p.x" :cy="p.y" r="5" fill="red" />
                <line v-if="croppedLive.measure.points.length>=2"
                  :x1="croppedLive.measure.points[0].x" :y1="croppedLive.measure.points[0].y"
                  :x2="croppedLive.measure.points[1].x" :y2="croppedLive.measure.points[1].y"
                  stroke="blue" stroke-width="2" />
                <line v-if="croppedLive.measure.points.length===3"
                  :x1="croppedLive.measure.points[1].x" :y1="croppedLive.measure.points[1].y"
                  :x2="croppedLive.measure.points[2].x" :y2="croppedLive.measure.points[2].y"
                  stroke="blue" stroke-width="2" />
              </g>
            </svg>
          </div>
        </div>

        <!-- Mini bank (re-uses same UX: multi-select, move, delete) -->
        <AnnotationsBank
          class="mini-bank"
          :page="0"
          :items="croppedBankItems"
          :selectedKeys="croppedBankSelected"
          :multiSelect="croppedBankMulti"
          :moveActive="croppedMoveActive"
          @update:selected="(keys)=>croppedBankSelected = keys"
          @toggle-multi="croppedBankMulti = !croppedBankMulti"
          @request-move="enableCroppedMove"
          @cancel-move="disableCroppedMove"
          @request-delete="deleteSelectedCropped"
        />
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

      // Bands sticky-mode
      activeBandGroup: null,   // 'horizontal' | 'vertical' | null
      pendingBandGroup: null,  // which popup opened last ('horizontal'|'vertical')

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
      angleStatistics: { count: 0, mean: 0, median: 0, stdDev: 0, min: 0, max: 0, angles: [] },
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
      croppedStartPoint: null,
      croppedPendingAngle: null,
      croppedEditingAnnotationIndex: -1,
      popupDimensions: { width: 0, height: 0 },

      // Comments
      comments: [],                   // per page (array of arrays)
      showCommentInput: false,
      currentCommentText: "",
      // Where the composer should appear:
      composerTarget: { side: 'right', t: 0.5 }, // side: 'left'|'right', t in [0..1] vertical relative
      draggingCommentIndex: null,
      dragOffset: { x: 0, y: 0 },
      suppressNextComment: false,

      // UI
      showClearDropdown: false,
      showClearConfirmation: false,
      toolMessage: "",

      // Bank
      bankSelectedKeys: [],
      bankMultiSelect: false,
      moveModeActive: false,
      moveStartPos: null,
      currentMoveDelta: { x: 0, y: 0 },

      // Zoom & Pan
      zoomLevel: 1,
      zoomStep: 0.10,
      minZoom: 1,
      maxZoom: 3,
      _holdTimer: null,      // for long-press reset
      panX: 0,
      panY: 0,
      isPanning: false,
      baseFitWidth: 0,       // image fitted width at 100% zoom
      baseFitHeight: 0,      // image fitted height at 100% zoom

      // Cropped zoom/pan
      cropZoom: 1,
      cropZoomStep: 0.10,
      cropPanX: 0,
      cropPanY: 0,
      isCropPanning: false,
      _cPanStart: null,
      croppedBaseW: 0,
      croppedBaseH: 0,

      // Unified cropped state
      croppedLive: {
        trace: null,
        highlight: null,
        underline: null,
        measure: null
      },
      croppedAnnotations: [],
      croppedBankSelected: [],
      croppedBankMulti: false,
      croppedMoveActive: false,
    };
  },
  computed: {
    anchorStyle() {
      // A fixed box centered in the stage; zoom/pan transform is applied here
      return {
        position: 'absolute',
        left: '50%',
        top: '50%',
        width: `${this.baseFitWidth || 0}px`,
        height: `${this.baseFitHeight || 0}px`,
        transform: `translate(-50%, -50%) translate(${this.panX}px, ${this.panY}px) scale(${this.zoomLevel})`,
        transformOrigin: 'center center',
        zIndex: 100, // below buttons/bank/panels
      };
    },

    zoomedWidth() { return this.baseFitWidth  * (this.zoomLevel || 1); },
    zoomedHeight(){ return this.baseFitHeight * (this.zoomLevel || 1); },

    // Stage cursor: when zoomed, show grab/grabbing; otherwise use your existing logic
    stageCursor() {
      if (this.isPanning) return 'grabbing';
      if (this.zoomLevel > 1) return 'grab';
      // Fallback to tool cursors
      return (this.traceModeActive || this.highlightModeActive || this.underlineModeActive || this.measureModeActive || this.isMeasuring || this.moveModeActive)
        ? 'crosshair'
        : 'default';
    },

    imageReady() {
      return this.imageLoaded && this.baseFitWidth > 0 && this.baseFitHeight > 0;
    },

    anchorBoxInViewer() {
      // Page rect in viewer-coordinates after zoom/pan (NOT the image's natural size)
      const w = this.zoomedWidth;
      const h = this.zoomedHeight;
      const left = (this.viewerWidth / 2) - (w / 2) + this.panX;
      const top  = (this.viewerHeight / 2) - (h / 2) + this.panY;
      return { left, top, width: w, height: h, right: left + w, bottom: top + h };
    },

    composerStyle() {
      if (!this.imageReady) return {};
      const box = this.anchorBoxInViewer;
      const pad = 12;             // gap outside page
      const width = 260;          // composer width
      const y = box.top + this.composerTarget.t * box.height;
      const x = this.composerTarget.side === 'left'
        ? (box.left - pad - width)
        : (box.right + pad);

      return {
        position: 'absolute',
        top: `${Math.round(y)}px`,
        left: `${Math.round(x)}px`,
        transform: 'translateY(-50%)',
        zIndex: 1600
      };
    },

    commentStyle() {
      // returns a function to style each card
      return (c) => {
        const box = this.anchorBoxInViewer;
        const pad = 12;     // gap from page edge
        const width = 240;  // visual width of comment card
        const y = box.top + c.t * box.height;
        const x = c.side === 'left'
          ? (box.left - pad - width)
          : (box.right + pad);

        return {
          position: 'absolute',
          top: `${Math.round(y)}px`,
          left: `${Math.round(x)}px`,
          transform: 'translateY(-50%)',
          zIndex: 1400,
          width: `${width}px`
        };
      };
    },

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

    // Cropped popup computed properties
    croppedAnchorStyle() {
      return {
        position: 'absolute',
        left: '50%',
        top: '50%',
        width: this.croppedBaseW + 'px',
        height: this.croppedBaseH + 'px',
        transform: `translate(-50%,-50%) translate(${this.cropPanX}px, ${this.cropPanY}px) scale(${this.cropZoom})`,
        transformOrigin: 'center center',
      };
    },
    croppedStageCursor() {
      if (this.isCropPanning) return 'grabbing';
      if (this.cropZoom > 1) return 'grab';
      return 'crosshair';
    },
    cropZoomLeftStyle() {
      const el = this.$refs.croppedStage;
      if (!el) return {};
      const y = el.clientHeight/2;
      const x = el.clientWidth/2 - (this.croppedBaseW*this.cropZoom)/2 + this.cropPanX - 44;
      return { left: `${Math.round(x)}px`, top: `${Math.round(y)}px`, transform: 'translateY(-50%)' };
    },
    cropZoomRightStyle() {
      const el = this.$refs.croppedStage;
      if (!el) return {};
      const y = el.clientHeight/2;
      const x = el.clientWidth/2 + (this.croppedBaseW*this.cropZoom)/2 + this.cropPanX + 8;
      return { left: `${Math.round(x)}px`, top: `${Math.round(y)}px`, transform: 'translateY(-50%)' };
    },
    // Unified cropped annotations system
    croppedAnnotationsAbs() {
      return this.croppedAnnotations.filter(a => a.type === 'highlight' || a.type === 'underline').map(a => ({
        ...a,
        style: a.type === 'highlight' ? {
          position: 'absolute',
          left: `${a.rect.left}px`,
          top: `${a.rect.top}px`,
          width: `${a.rect.width}px`,
          height: `${a.rect.height}px`,
          backgroundColor: a.color,
          opacity: 0.3,
          pointerEvents: 'none'
        } : {
          position: 'absolute',
          left: `${a.line.x1}px`,
          top: `${a.line.y1}px`,
          width: `${Math.abs(a.line.x2 - a.line.x1)}px`,
          height: `${Math.abs(a.line.y2 - a.line.y1) || 2}px`,
          backgroundColor: a.color,
          pointerEvents: 'none'
        }
      }));
    },
    croppedAnnotationsSvg() {
      return this.croppedAnnotations.filter(a => a.type === 'trace' || a.type === 'measure');
    },
    croppedTraces() {
      return this.croppedAnnotations.filter(a => a.type === 'trace');
    },
    croppedMeasures() {
      return this.croppedAnnotations.filter(a => a.type === 'measure');
    },
    croppedBankItems() {
      return this.croppedAnnotations.map((a, i) => ({
        key: `c${i}`,
        category: a.type,
        title: a.type === 'trace' ? 'Trace' : 
               a.type === 'measure' ? `Angle (${a.angle || ''}°)` :
               a.type === 'highlight' ? 'Highlight' : 'Underline',
        subtitle: a.type === 'trace' ? `${a.points?.length || 0} pts` : '',
        color: a.color || (a.type === 'measure' ? 'blue' : a.type === 'highlight' ? 'rgba(255,255,0,0.8)' : '#3b82f6')
      }));
    },
  },
  watch: {
    currentPage(n) {
      this.pageInput = n + 1;
      // Clear bank selections when page changes
      this.bankSelectedKeys = [];
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
    
    // Initialize fit computation
    this.$nextTick(() => {
      this.computeBaseFit();  // in case the image is cached and loads instantly
    });
    window.addEventListener('resize', this.computeBaseFit);
    
    // Global selection prevention for cropped popup
    this._preventSelection = (e) => {
      if (this.croppedImage && (e.target.closest('.cropped-popup') || e.target.closest('.crop-stage'))) {
        e.preventDefault();
        e.stopPropagation();
        return false;
      }
    };
    
    document.addEventListener('selectstart', this._preventSelection, true);
    document.addEventListener('dragstart', this._preventSelection, true);
    document.addEventListener('contextmenu', this._preventSelection, true);
  },

  beforeUnmount() {
    window.removeEventListener('resize', this.computeBaseFit);
    
    // Clean up global selection prevention
    if (this._preventSelection) {
      document.removeEventListener('selectstart', this._preventSelection, true);
      document.removeEventListener('dragstart', this._preventSelection, true);
      document.removeEventListener('contextmenu', this._preventSelection, true);
    }
    
    // Clean up body class if component is destroyed while popup is open
    document.body.classList.remove('cropped-popup-active');
  },

  methods: {
    goHome() {
      const ok = window.confirm(
        "Return to the home screen? Any unsaved work on this page will be lost."
      );
      if (ok) {
        this.$router.push({ name: "IIIFInput" });
      }
    },

    clampPan() {
      if (!this.imageReady) return;
      
      const scale = this.zoomLevel;
      const actualWidth = this.baseFitWidth * scale;
      const actualHeight = this.baseFitHeight * scale;
      const viewer = this.$refs.viewer;
      if (!viewer) return;
      
      const vw = viewer.clientWidth;
      const vh = viewer.clientHeight;
      
      const maxPanX = Math.max(0, (actualWidth - vw) / 2);
      const maxPanY = Math.max(0, (actualHeight - vh) / 2);
      
      this.panX = Math.min(Math.max(-maxPanX, this.panX), maxPanX);
      this.panY = Math.min(Math.max(-maxPanY, this.panY), maxPanY);
    },

    zoomIn() {
      if (!this.imageReady) return;
      this.zoomLevel = Math.min(this.maxZoom, +(this.zoomLevel + this.zoomStep).toFixed(2));
      this.clampPan();
    },
    zoomOut() {
      if (!this.imageReady) return;
      // Regular click: step down, but not below min
      this.zoomLevel = Math.max(this.minZoom, +(this.zoomLevel - this.zoomStep).toFixed(2));
      // Optional: clamp pan so content stays reachable
      this.clampPan();
    },
    resetZoom() {
      if (!this.imageReady) return;
      this.zoomLevel = 1;
      this.panX = 0;
      this.panY = 0;
    },
    startHoldReset() {
      // Long press (3s) to reset to 100%
      this._holdTimer = setTimeout(() => {
        this.resetZoom();
        this._holdTimer = null;
      }, 3000);
    },
    cancelHoldReset() {
      if (this._holdTimer) {
        clearTimeout(this._holdTimer);
        this._holdTimer = null;
      }
    },

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
      const viewer = this.$refs.viewer;
      const rect = viewer.getBoundingClientRect();

      // Stage center in viewport coords
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      // Pointer delta from stage center in screen px
      const dxScreen = event.clientX - centerX;
      const dyScreen = event.clientY - centerY;

      // Undo pan & zoom to get into anchor local space (0,0 at anchor center)
      const z = this.zoomLevel || 1;
      const dxLocal = (dxScreen - this.panX) / z;
      const dyLocal = (dyScreen - this.panY) / z;

      // Convert from anchor-center coords to anchor-top-left coords
      const x = dxLocal + (this.baseFitWidth  / 2);
      const y = dyLocal + (this.baseFitHeight / 2);

      return { x, y };
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
      if (!key || typeof key !== 'string') {
        console.error('Invalid bank key:', key);
        return { kind: '', ref: '' };
      }
      const parts = String(key).split(":");
      if (parts.length !== 2) {
        console.error('Invalid bank key format:', key);
        return { kind: '', ref: '' };
      }
      const [kind, ref] = parts;
      return { kind, ref };
    },

    /* ----- Bank helpers ----- */
    camelToTitle(key) {
      if (!key) return "";
      // Special case for minimumHeight
      if (key === "minimumHeight") return "Minim Height";
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
        // Close any open comment input when switching tools
        this.showCommentInput = false;
        this.currentCommentText = "";
        // Clear cropped popup tool state
        this.croppedStartPoint = null;
        this.croppedLive.highlight = null;
        this.croppedLive.underline = null;
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
        // toggle
        if (this.measureModeActive) {
          this.measureModeActive = false;
          this.showToolMessage("Angle measurement mode deactivated.");
          return;
        }
        resetAll();
        // open label chooser first
        this.showAngleLabelPopup = true;
        return;
      }

      if (tool === "highlight") {
        // toggle
        if (this.highlightModeActive) {
          this.highlightModeActive = false;
          this.startPoint = null;
          this.currentSquare = null;
          this.showToolMessage("Highlight mode deactivated.");
          return;
        }
        resetAll();
        this.highlightModeActive = true;
        this.showToolMessage("Highlight mode ACTIVE. Click and drag to add highlights. Click Highlight again to exit.");
        return;
      }

      if (tool === "underline") {
        // toggle
        if (this.underlineModeActive) {
          this.underlineModeActive = false;
          this.startPoint = null;
          this.currentUnderline = null;
          this.showToolMessage("Underline mode deactivated.");
          return;
        }
        resetAll();
        this.underlineModeActive = true;
        this.showToolMessage("Underline mode ACTIVE. Click and drag to add underlines. Click Underline again to exit.");
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
      // toggle off if horizontal band mode already active
      if (this.lengthMeasurementActive && this.activeBandGroup === 'horizontal') {
        this.lengthMeasurementActive = false;
        this.isMeasuring = false;
        this.activeBandGroup = null;
        this.showToolMessage('Horizontal bands deactivated.');
        return;
      }
      // otherwise open chooser for (re)selecting the type
      this.pendingBandGroup = 'horizontal';
      this.showStatsPanel = false;
      this.showHorizontalPopup = true;
      this.showVerticalPopup = false;
    },
    openVerticalPopup() {
      // toggle off if vertical band mode already active
      if (this.lengthMeasurementActive && this.activeBandGroup === 'vertical') {
        this.lengthMeasurementActive = false;
        this.isMeasuring = false;
        this.activeBandGroup = null;
        this.showToolMessage('Vertical bands deactivated.');
        return;
      }
      // otherwise open chooser for (re)selecting the type
      this.pendingBandGroup = 'vertical';
      this.showStatsPanel = false;
      this.showVerticalPopup = true;
      this.showHorizontalPopup = false;
    },
    hideLengthPopup() {
      this.showHorizontalPopup = false;
      this.showVerticalPopup = false;
    },
    beginLength(type) {
      // choose a band type and stay in that mode until the same toolbar button is clicked again
      this.selectedMeasurement = type;
      this.hideLengthPopup();
      this.startLengthMeasurement();
      // remember which group is active (horizontal | vertical)
      this.activeBandGroup = this.pendingBandGroup || this.activeBandGroup || 'horizontal';
      const groupLabel = this.activeBandGroup === 'vertical' ? 'Vertical' : 'Horizontal';
      this.showToolMessage(`${groupLabel} "${type}" measuring is ACTIVE. Click the ${groupLabel} Bands button again to exit.`);
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
      
      // Normal flow: close popup and activate measure mode
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
      // Only proceed if comment mode is actually active
      if (!this.commentModeActive) return;
      
      if (this.suppressNextComment) {
        this.suppressNextComment = false;
        return;
      }

      // Only respond if click is inside the page (anchor) bounds
      const local = this.getMousePosition(event); // anchor-local coords
      if (
        local.x < 0 || local.y < 0 ||
        local.x > this.baseFitWidth || local.y > this.baseFitHeight
      ) return;

      const isLeftHalf = local.x < (this.baseFitWidth / 2);
      const side = isLeftHalf ? 'left' : 'right';
      const t = Math.max(0, Math.min(1, local.y / this.baseFitHeight));

      this.composerTarget = { side, t };
      this.currentCommentText = "";
      this.showCommentInput = true;
    },

    addComment() {
      if (!this.currentCommentText.trim()) return;
      if (!this.comments[this.currentPage]) this.comments[this.currentPage] = [];

      this.comments[this.currentPage].push({
        side: this.composerTarget.side,
        t: Math.max(0, Math.min(1, this.composerTarget.t)),
        text: this.currentCommentText.trim(),
      });

      this.currentCommentText = "";
      this.showCommentInput = false;
      this.commentModeActive = false; // <-- disable comment mode after adding one comment
      this.suppressNextComment = true; // <-- prevents instant re-open
    },

    cancelComment() {
      this.currentCommentText = "";
      this.showCommentInput = false;
      this.commentModeActive = false; // <-- disable comment mode when canceling
      this.suppressNextComment = true; // <-- prevents instant re-open
    },

    startDraggingComment(index, event) {
      this.draggingCommentIndex = index;
      // keep where the pointer is relative to card's top-left; we'll convert to side/t on move
      const viewer = this.$refs.viewer.getBoundingClientRect();
      this.dragOffset = {
        x: event.clientX - viewer.left,
        y: event.clientY - viewer.top,
      };
    },

    dragComment(event) {
      if (this.draggingCommentIndex === null) return;

      // Pointer position in viewer space
      const viewerRect = this.$refs.viewer.getBoundingClientRect();
      const px = event.clientX - viewerRect.left;
      const py = event.clientY - viewerRect.top;

      // Snap horizontally to the closer page edge; map vertically to t
      const box = this.anchorBoxInViewer;
      // If page not ready, skip
      if (box.width <= 0 || box.height <= 0) return;

      const distLeft  = Math.abs(px - box.left);
      const distRight = Math.abs(px - box.right);
      const side = (distLeft <= distRight) ? 'left' : 'right';

      // t is 0..1 within page box
      const t = Math.max(0, Math.min(1, (py - box.top) / box.height));

      const pageComments = this.comments[this.currentPage] || [];
      const c = pageComments[this.draggingCommentIndex];
      if (c) {
        c.side = side;
        c.t = t;
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
      ["internalMargin","intercolumnSpaces","externalMargin"].forEach((t)=>{
        if (this.lengthMeasurements[t]) delete this.lengthMeasurements[t][this.currentPage];
      });
      this.showToolMessage("Vertical lengths cleared.");
      this.showClearDropdown = false;
    },
    clearAll() {
      this.showClearDropdown = false;
      this.showClearConfirmation = true;
    },
    
    confirmClearAll() {
      this.annotationsByPage[this.currentPage] = [];
      this.comments[this.currentPage] = [];
      const all = ["ascenders","descenders","interlinear","upperMargin","lowerMargin","internalMargin","intercolumnSpaces","externalMargin","lineHeight","minimumHeight"];
      all.forEach(t => { if (this.lengthMeasurements[t]) delete this.lengthMeasurements[t][this.currentPage]; });
      this.strokes = [];
      this.measurePoints = [];
      this.calculatedAngle = 0;
      this.showToolMessage("All annotations cleared.");
      this.showClearConfirmation = false;
    },
    
    cancelClearAll() {
      this.showClearConfirmation = false;
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
      // PAN START: when zoomed and user isn't starting another tool action, start panning
      if (this.zoomLevel > 1) {
        const noToolActive = !(
          this.traceModeActive || this.measureModeActive || this.highlightModeActive ||
          this.underlineModeActive || this.lengthMeasurementActive || this.croppingStarted ||
          this.commentModeActive || this.moveModeActive
        );
        // If no tool is active, use drag to pan
        if (noToolActive) {
          this.isPanning = true;
          this._panStart = { x: event.clientX, y: event.clientY, panX: this.panX, panY: this.panY };
          return; // don't trigger drawing if we're panning
        }
      }

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
      // PAN MOVE
      if (this.isPanning && this._panStart) {
        const dx = event.clientX - this._panStart.x;
        const dy = event.clientY - this._panStart.y;
        this.panX = this._panStart.panX + dx;
        this.panY = this._panStart.panY + dy;
        this.clampPan();
        return; // swallow draw events while panning
      }

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
      // PAN END
      if (this.isPanning) {
        this.isPanning = false;
        this._panStart = null;
        return; // end pan, do not create artifacts
      }

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

    /* ---------- Cropped Angle helpers ---------- */
    findNearestCroppedPoint(x, y, threshold = 10) {
      const all = this.croppedAnnotations
        .map((a, i) => ({ a, i }))
        .filter(({ a }) => a && a.type === "measure");

      let best = { annotationIndex: -1, pointIndex: -1, dist: Infinity };
      all.forEach(({ a, i }) => {
        if (a.points && a.points.length > 0) {
          a.points.forEach((p, pi) => {
            const d = Math.hypot(x - p.x, y - p.y);
            if (d < threshold && d < best.dist) best = { annotationIndex: i, pointIndex: pi, dist: d };
          });
        }
      });
      return { annotationIndex: best.annotationIndex, pointIndex: best.pointIndex };
    },

    /* ---------- Move selected ---------- */
    enableMoveMode() {
      if (this.bankSelectedKeys.length === 0) {
        this.showToolMessage("Please select items to move first.");
        return;
      }
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
        try {
          const { kind, ref } = this.parseBankKey(k);
          if (kind === "a") {
            const i = +ref;
            if (isNaN(i)) return;
            const a = this.annotationsByPage[page]?.[i];
            if (!a) return;
            if (a.type === "highlight" || a.type === "underline") {
              a.x = (a.x || 0) + dx; 
              a.y = (a.y || 0) + dy;
            } else if (a.type === "trace" || a.type === "measure") {
              if (Array.isArray(a.points)) {
                a.points = a.points.map((p) => ({ x: (p.x || 0) + dx, y: (p.y || 0) + dy }));
              }
            }
          }
          if (kind === "c") {
            const i = +ref;
            if (isNaN(i)) return;
            const c = this.comments[page]?.[i];
            if (!c) return;
            c.x = (c.x || 0) + dx; 
            c.y = (c.y || 0) + dy;
          }
          if (kind === "l") {
            const id = ref;
            for (const label in this.lengthMeasurements) {
              const arr = this.lengthMeasurements[label]?.[page];
              if (!Array.isArray(arr)) continue;
              const m = arr.find((mm) => String(mm.id) === String(id));
              if (m) {
                m.x = (m.x || 0) + dx; 
                m.y = (m.y || 0) + dy;
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
        } catch (error) {
          console.error('Error applying move delta to item:', k, error);
        }
      });
    },
    deleteSelectedFromBank() {
      if (this.bankSelectedKeys.length === 0) {
        this.showToolMessage("Please select items to delete first.");
        return;
      }
      
      const page = this.currentPage;
      const annIdxs = [];
      const cmtIdxs = [];
      const lengthIds = [];

      // Parse and validate all selected keys first
      this.bankSelectedKeys.forEach((k) => {
        try {
          const { kind, ref } = this.parseBankKey(k);
          if (kind === "a") {
            const idx = parseInt(ref);
            if (!isNaN(idx)) annIdxs.push(idx);
          }
          if (kind === "c") {
            const idx = parseInt(ref);
            if (!isNaN(idx)) cmtIdxs.push(idx);
          }
          if (kind === "l") lengthIds.push(ref);
        } catch (error) {
          console.error('Error parsing bank key:', k, error);
        }
      });

      // Delete annotations (from highest index to lowest to avoid index shifting)
      if (annIdxs.length) {
        if (!this.annotationsByPage[page]) {
          this.annotationsByPage[page] = [];
        }
        const sorted = [...annIdxs].sort((a,b)=>b-a);
        sorted.forEach((i) => {
          if (this.annotationsByPage[page][i] != null) {
            this.annotationsByPage[page].splice(i, 1);
          }
        });
      }
      
      // Delete comments (from highest index to lowest)
      if (cmtIdxs.length) {
        if (!this.comments[page]) {
          this.comments[page] = [];
        }
        const sorted = [...cmtIdxs].sort((a,b)=>b-a);
        sorted.forEach((i) => {
          if (this.comments[page][i] != null) {
            this.comments[page].splice(i, 1);
          }
        });
      }
      
      // Delete length measurements
      if (lengthIds.length) {
        for (const label in this.lengthMeasurements) {
          const pageArr = this.lengthMeasurements[label]?.[page];
          if (Array.isArray(pageArr)) {
            this.lengthMeasurements[label][page] = pageArr.filter((m) => !lengthIds.includes(String(m.id)));
          }
        }
        lengthIds.forEach((id) => { 
          if (this.labelPositions[id]) delete this.labelPositions[id]; 
        });
      }

      // Clear selection after successful deletion
      this.bankSelectedKeys = [];
      this.showToolMessage(`Deleted ${annIdxs.length + cmtIdxs.length + lengthIds.length} items.`);
    },

    /* ---------- Image & crop ---------- */
    computeBaseFit() {
      const img = this.$refs.image;
      const viewer = this.$refs.viewer;
      if (!img || !viewer) return;

      const natW = img.naturalWidth || 0;
      const natH = img.naturalHeight || 0;
      const vw = viewer.clientWidth || 0;
      const vh = viewer.clientHeight || 0;
      if (!natW || !natH || !vw || !vh) return;

      const s = Math.min(vw / natW, vh / natH);
      this.baseFitWidth  = Math.max(1, natW * s);
      this.baseFitHeight = Math.max(1, natH * s);
    },

    handleImageLoad() {
      this.computeBaseFit();
      const img = this.$refs.image;
      if (img && img.naturalWidth) {
        this.scalingFactor = (this.baseFitWidth || img.width) / img.naturalWidth;
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
          
          // Add class to body for proper z-index management
          document.body.classList.add('cropped-popup-active');
          
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
    calculateCroppedAngleStatistics() {
      // Get only angles from cropped annotations
      const croppedAngles = this.croppedAnnotations.filter(annotation => annotation.type === 'measure');
      
      if (croppedAngles.length === 0) {
        alert('No angles found in the cropped image.');
        return;
      }
      
      // Calculate statistics for cropped angles only
      const angleDegrees = croppedAngles.map(annotation => {
        // Use the points array for calculation
        if (annotation.points && annotation.points.length >= 3) {
          const point1 = annotation.points[0];
          const vertex = annotation.points[1]; 
          const point2 = annotation.points[2];
          
          const vector1 = { x: point1.x - vertex.x, y: point1.y - vertex.y };
          const vector2 = { x: point2.x - vertex.x, y: point2.y - vertex.y };
          
          const dot = vector1.x * vector2.x + vector1.y * vector2.y;
          const mag1 = Math.sqrt(vector1.x * vector1.x + vector1.y * vector1.y);
          const mag2 = Math.sqrt(vector2.x * vector2.x + vector2.y * vector2.y);
          
          const cosAngle = dot / (mag1 * mag2);
          const clampedCos = Math.max(-1, Math.min(1, cosAngle));
          return Math.acos(clampedCos) * (180 / Math.PI);
        }
        // Fallback to stored angle value if calculation fails
        return annotation.angle || 0;
      });
      
      // Calculate statistics
      const sum = angleDegrees.reduce((a, b) => a + b, 0);
      const mean = sum / angleDegrees.length;
      const sortedAngles = [...angleDegrees].sort((a, b) => a - b);
      const median = sortedAngles.length % 2 === 0
        ? (sortedAngles[sortedAngles.length / 2 - 1] + sortedAngles[sortedAngles.length / 2]) / 2
        : sortedAngles[Math.floor(sortedAngles.length / 2)];
      
      const variance = angleDegrees.reduce((acc, angle) => acc + Math.pow(angle - mean, 2), 0) / angleDegrees.length;
      const stdDev = Math.sqrt(variance);
      
      // Set results and show popup
      this.angleStatistics = {
        count: croppedAngles.length,
        mean: mean.toFixed(2),
        median: median.toFixed(2),
        stdDev: stdDev.toFixed(2),
        min: Math.min(...angleDegrees).toFixed(2),
        max: Math.max(...angleDegrees).toFixed(2),
        angles: angleDegrees.map(a => a.toFixed(2))
      };
      
      this.showAngleStatistics = true;
    },
    closeCroppedPopup() {
      // Clear cropped annotations (temporary labels will be removed)
      this.croppedAnnotations = [];
      this.croppedLive = { highlight: null, underline: null, trace: null };
      this.croppedStartPoint = null;
      
      this.croppedImage = null;
      
      // Remove class from body
      document.body.classList.remove('cropped-popup-active');
      
      // Reset unified cropped state
      this.croppedLive = {
        trace: null,
        highlight: null,
        underline: null,
        measure: null
      };
      this.croppedAnnotations = [];
      this.croppedBankSelected = [];
      this.croppedBankMulti = false;
      this.croppedMoveActive = false;
      
      // Reset zoom/pan
      this.cropZoom = 1;
      this.cropPanX = 0;
      this.cropPanY = 0;
      this.isCropPanning = false;
    },

    // Cropped image loading and sizing
    onCroppedImgLoad() {
      const img = this.$refs.croppedImg;
      if (!img) return;
      
      // Wait for the image to be fully laid out
      this.$nextTick(() => {
        // Use displayed size (which preserves aspect ratio) for coordinates
        this.croppedBaseW = img.offsetWidth || img.clientWidth;
        this.croppedBaseH = img.offsetHeight || img.clientHeight;
        
        // Fallback to natural size if displayed size is 0
        if (this.croppedBaseW === 0 || this.croppedBaseH === 0) {
          // Calculate the displayed size based on natural dimensions and container
          const container = this.$refs.croppedStage;
          if (container) {
            const containerW = container.clientWidth;
            const containerH = container.clientHeight - 40; // account for padding
            const naturalW = img.naturalWidth;
            const naturalH = img.naturalHeight;
            
            if (naturalW && naturalH) {
              const aspectRatio = naturalW / naturalH;
              if (containerW / containerH > aspectRatio) {
                // Container is wider than image aspect ratio
                this.croppedBaseH = containerH;
                this.croppedBaseW = containerH * aspectRatio;
              } else {
                // Container is taller than image aspect ratio  
                this.croppedBaseW = containerW;
                this.croppedBaseH = containerW / aspectRatio;
              }
            }
          }
        }
        
        // reset view
        this.cropZoom = 1;
        this.cropPanX = 0;
        this.cropPanY = 0;
      });
    },

    // Prevent any image interaction
    handleImageMouseDown(e) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      return false;
    },

    // Prevent main image interaction
    handleMainImageMouseDown(e) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      return false;
    },

    // Cropped zoom/pan methods
    cropZoomIn() {
      this.cropZoom = Math.min(4, +(this.cropZoom + this.cropZoomStep).toFixed(2));
      this._clampCropPan();
    },
    cropZoomOut() {
      this.cropZoom = Math.max(1, +(this.cropZoom - this.cropZoomStep).toFixed(2));
      this._clampCropPan();
    },
    _clampCropPan() {
      // allow small margin
      const margin = 120;
      const maxX = (this.croppedBaseW * (this.cropZoom - 1)) / 2 + margin;
      const maxY = (this.croppedBaseH * (this.cropZoom - 1)) / 2 + margin;
      this.cropPanX = Math.max(-maxX, Math.min(maxX, this.cropPanX));
      this.cropPanY = Math.max(-maxY, Math.min(maxY, this.cropPanY));
    },

    // Coordinate transform for cropped popup
    getCroppedMouse(event) {
      const img = this.$refs.croppedImg;
      const anchor = img?.parentElement; // crop-anchor div
      
      if (!img || !anchor || this.croppedBaseW === 0 || this.croppedBaseH === 0) {
        return { x: 0, y: 0 };
      }

      // Get the anchor bounds (this has the transform applied)
      const anchorRect = anchor.getBoundingClientRect();
      
      // Calculate mouse position relative to the transformed anchor
      const relativeX = event.clientX - anchorRect.left;
      const relativeY = event.clientY - anchorRect.top;
      
      // Convert back to original image coordinates (undo zoom)
      const imageX = relativeX / this.cropZoom;
      const imageY = relativeY / this.cropZoom;
      
      return {
        x: Math.max(0, Math.min(this.croppedBaseW, imageX)),
        y: Math.max(0, Math.min(this.croppedBaseH, imageY))
      };
    },

    // ===== UNIFIED CROPPED MOUSE HANDLERS =====
    cropStageDown(e) {
      // Clear any existing selection immediately
      if (window.getSelection) {
        window.getSelection().removeAllRanges();
      } else if (document.selection) {
        document.selection.empty();
      }
      
      // Prevent default behavior
      e.preventDefault();
      e.stopPropagation();
      
      const toolActive = this.traceModeActive || this.measureModeActive || this.highlightModeActive || this.underlineModeActive;
      
      // Pan when zoomed and no tool active
      if (this.cropZoom > 1 && !toolActive) {
        this.isCropPanning = true;
        this._cPanStart = { x: e.clientX, y: e.clientY, panX: this.cropPanX, panY: this.cropPanY };
        return;
      }

      // Get unified mouse coordinates
      const { x, y } = this.getCroppedMouse(e);

      // HIGHLIGHT / UNDERLINE - Two-click system like main page
      if (this.highlightModeActive || this.underlineModeActive) {
        if (!this.croppedStartPoint) {
          // First click - set start point
          this.croppedStartPoint = { x, y };
          if (this.highlightModeActive) {
            this.croppedLive.highlight = {
              startX: x, startY: y,
              style: { 
                position: 'absolute', 
                left: `${x}px`, 
                top: `${y}px`, 
                width: '0px', 
                height: '0px', 
                backgroundColor: 'rgba(255,255,0,0.3)' 
              }
            };
          } else if (this.underlineModeActive) {
            this.croppedLive.underline = {
              startX: x, startY: y,
              style: { 
                position: 'absolute', 
                left: `${x}px`, 
                top: `${y}px`, 
                width: '0px', 
                height: '2px', 
                backgroundColor: 'blue' 
              }
            };
          }
          return;
        } else {
          // Second click - complete the annotation
          if (this.highlightModeActive && this.croppedLive.highlight) {
            const rect = {
              left: parseInt(this.croppedLive.highlight.style.left),
              top: parseInt(this.croppedLive.highlight.style.top),
              width: parseInt(this.croppedLive.highlight.style.width),
              height: parseInt(this.croppedLive.highlight.style.height)
            };
            
            if (rect.width > 5 && rect.height > 5) { // Minimum size
              this.croppedAnnotations.push({
                type: 'highlight',
                rect: rect,
                color: 'rgba(255,255,0,0.3)'
              });
            }
            this.croppedLive.highlight = null;
          } else if (this.underlineModeActive && this.croppedLive.underline) {
            const line = {
              x1: parseInt(this.croppedLive.underline.style.left),
              y1: parseInt(this.croppedLive.underline.style.top),
              x2: parseInt(this.croppedLive.underline.style.left) + parseInt(this.croppedLive.underline.style.width),
              y2: parseInt(this.croppedLive.underline.style.top)
            };
            
            if (Math.abs(line.x2 - line.x1) > 5) { // Minimum length
              this.croppedAnnotations.push({
                type: 'underline',
                line: line,
                color: 'blue'
              });
            }
            this.croppedLive.underline = null;
          }
          this.croppedStartPoint = null;
          return;
        }
      }

      // Trace mode
      if (this.traceModeActive) {
        this.croppedLive.trace = {
          color: this.generateRandomColor(),
          penWidth: 2,
          points: [{ x, y }]
        };
        return;
      }

      // Measure mode (3-click angle) - Follow main page logic exactly
      if (this.measureModeActive) {
        // First check if clicking near an existing angle point for editing
        const nearest = this.findNearestCroppedPoint(x, y, 10);
        if (nearest.annotationIndex !== -1) {
          // Start editing existing angle
          this.croppedEditingAnnotationIndex = nearest.annotationIndex;
          this.croppedDraggingPoint = nearest.pointIndex;
          const ann = this.croppedAnnotations[this.croppedEditingAnnotationIndex];
          // Copy the points for editing
          this.croppedLive.measure = { points: [...ann.points] };
          return;
        }
        
        // Otherwise, create new angle
        if (!this.croppedLive.measure) {
          this.croppedLive.measure = { points: [] };
        }
        
        // Check if we've already collected 3 points
        if (this.croppedLive.measure.points.length >= 3) return;
        
        this.croppedLive.measure.points.push({ x, y });
        
        if (this.croppedLive.measure.points.length === 3) {
          // Calculate angle and immediately save it (like main page)
          const angle = this.calculateAngle(
            this.croppedLive.measure.points[0],
            this.croppedLive.measure.points[1],
            this.croppedLive.measure.points[2]
          );
          
          // Save to cropped annotations immediately using active label
          this.croppedAnnotations.push({
            type: 'measure',
            point1: this.croppedLive.measure.points[0],
            vertex: this.croppedLive.measure.points[1],
            point2: this.croppedLive.measure.points[2],
            points: [...this.croppedLive.measure.points],
            angle: Math.round(angle),
            label: this.activeAngleLabel || "Unlabeled",
            color: 'blue'
          });
          
          // Add label to list if new (like main page)
          if (this.activeAngleLabel && !this.angleLabels.includes(this.activeAngleLabel)) {
            this.angleLabels.push(this.activeAngleLabel);
          }
          
          // Clear the live measure
          this.croppedLive.measure = null;
        }
        return;
      }
    },

    cropStageMove(e) {
      // Clear any selection that might appear during dragging
      if (window.getSelection && window.getSelection().rangeCount > 0) {
        window.getSelection().removeAllRanges();
      }
      
      // Handle panning
      if (this.isCropPanning && this._cPanStart) {
        const dx = e.clientX - this._cPanStart.x;
        const dy = e.clientY - this._cPanStart.y;
        this.cropPanX = this._cPanStart.panX + dx;
        this.cropPanY = this._cPanStart.panY + dy;
        this._clampCropPan();
        return;
      }

      const { x, y } = this.getCroppedMouse(e);

      // Handle angle point dragging
      if (this.measureModeActive && this.croppedDraggingPoint !== -1 && this.croppedLive.measure) {
        // Update the dragged point position
        this.croppedLive.measure.points[this.croppedDraggingPoint] = { x, y };
        
        // If editing an existing annotation, update it
        if (this.croppedEditingAnnotationIndex !== -1) {
          const ann = this.croppedAnnotations[this.croppedEditingAnnotationIndex];
          ann.points[this.croppedDraggingPoint] = { x, y };
          
          // Recalculate angle
          if (ann.points.length === 3) {
            const angle = this.calculateAngle(ann.points[0], ann.points[1], ann.points[2]);
            ann.angle = Math.round(angle);
          }
        }
        return;
      }

      // Update live highlight
      if (this.croppedLive.highlight) {
        const startX = this.croppedLive.highlight.startX;
        const startY = this.croppedLive.highlight.startY;
        this.croppedLive.highlight.style = {
          position: 'absolute',
          left: `${Math.min(x, startX)}px`,
          top: `${Math.min(y, startY)}px`,
          width: `${Math.abs(x - startX)}px`,
          height: `${Math.abs(y - startY)}px`,
          backgroundColor: 'rgba(255,255,0,0.3)'
        };
        return;
      }

      // Update live underline
      if (this.croppedLive.underline) {
        const startX = this.croppedLive.underline.startX;
        const startY = this.croppedLive.underline.startY;
        this.croppedLive.underline.style = {
          position: 'absolute',
          left: `${Math.min(x, startX)}px`,
          top: `${startY}px`,
          width: `${Math.abs(x - startX)}px`,
          height: '2px',
          backgroundColor: 'blue'
        };
        return;
      }

      // Extend live trace
      if (this.croppedLive.trace) {
        this.croppedLive.trace.points.push({ x, y });
        return;
      }
    },

    cropStageUp(e) {
      // End panning
      if (this.isCropPanning) {
        this.isCropPanning = false;
        this._cPanStart = null;
        return;
      }

      // End angle point dragging
      if (this.measureModeActive && this.croppedDraggingPoint !== -1) {
        this.croppedDraggingPoint = -1;
        this.croppedEditingAnnotationIndex = -1;
        this.croppedLive.measure = null;
        return;
      }

      // For highlights and underlines, don't commit on mouseup anymore
      // They now use two-click system (commit on second mousedown)
      
      // Commit live trace
      if (this.croppedLive.trace && this.croppedLive.trace.points.length > 1) {
        this.croppedAnnotations.push({
          type: 'trace',
          points: [...this.croppedLive.trace.points],
          color: this.croppedLive.trace.color,
          penWidth: this.croppedLive.trace.penWidth
        });
        
        this.croppedLive.trace = null;
        return;
      }
    },

    // ===== CROPPED BANK HANDLERS =====
    enableCroppedMove() {
      this.croppedMoveActive = true;
    },

    disableCroppedMove() {
      this.croppedMoveActive = false;
    },

    deleteSelectedCropped() {
      if (!this.croppedBankSelected.length) return;
      
      // Convert selected keys back to indices and remove from croppedAnnotations
      const indices = this.croppedBankSelected
        .map(key => {
          if (typeof key === 'string' && key.startsWith('c')) {
            const index = parseInt(key.substring(1));
            return isNaN(index) ? -1 : index;
          } else {
            console.warn('Invalid cropped bank key:', key);
            return -1;
          }
        })
        .filter(index => index >= 0)
        .sort((a, b) => b - a);
      
      indices.forEach(index => {
        if (index >= 0 && index < this.croppedAnnotations.length) {
          this.croppedAnnotations.splice(index, 1);
        }
      });
      
      this.croppedBankSelected = [];
    },

    /* ---------- Save to PDF ---------- */
    async saveAnnotations() {
      try {
        const topBar = document.querySelector(".top-bar");
        const navigationBar = document.querySelector(".navigation-bar");
        // cache previous inline visibility (not computed style) so we can restore exactly
        const prevTopVis = topBar ? topBar.style.visibility : "";
        const prevNavVis = navigationBar ? navigationBar.style.visibility : "";
        // cache scroll positions (window + stage)
        const winScroll = { x: window.scrollX, y: window.scrollY };
        const viewerEl = this.$refs.viewer;
        const viewerScroll = viewerEl
          ? { left: viewerEl.scrollLeft, top: viewerEl.scrollTop }
          : null;

        // hide without collapsing layout (prevents reflow/width jumps)
        if (topBar) topBar.style.visibility = "hidden";
        if (navigationBar) navigationBar.style.visibility = "hidden";

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

        // restore visibility and scroll positions exactly as before
        if (topBar) topBar.style.visibility = prevTopVis;
        if (navigationBar) navigationBar.style.visibility = prevNavVis;
        if (viewerEl && viewerScroll) {
          viewerEl.scrollLeft = viewerScroll.left;
          viewerEl.scrollTop = viewerScroll.top;
        }
        window.scrollTo(winScroll.x, winScroll.y);
      } catch (e) {
        console.error("Error saving annotations:", e);
      }
    },

    /* ---------- Stats helpers ---------- */
    extractValues(measurements, type) {
      const vertical = ["internalMargin", "intercolumnSpaces", "externalMargin"];
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
      const vertical = ["internalMargin","intercolumnSpaces","externalMargin"];
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
      const vertical = ["internalMargin","intercolumnSpaces","externalMargin"];
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
.viewer-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background: #f1f1f1; /* gray canvas behind the manuscript */
}
/* Full-bleed blue bars with clean layout */
.top-bar {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 16px;
  background: #e7f0ff;
  border-bottom: 1px solid #c9d8ff;
  padding: 12px 24px;
}
.logo { height: 60px; cursor: pointer; }

.toolbar {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(68px, auto);
  justify-content: center;
  align-items: center;
  gap: 28px;
}
.toolbar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: #222;
  cursor: pointer;
  padding: 6px 4px;
  user-select: none;
  position: relative;
}
.toolbar-item:hover { color: #2b6fde; }
.toolbar-item i { font-size: 22px; line-height: 1; }
.toolbar-item span { font-size: 12px; }

.toolbar-divider {
  width: 1px;
  height: 32px;
  background: #c9d8ff;
  margin: 0 8px;
}

.tool-message {
  position: fixed; top: 60px; left: 50%; transform: translateX(-50%);
  background-color: #007bff; color: white; padding: 8px 14px; border-radius: 6px; z-index: 1200; font-size: 12px;
}

.workspace { display: block; height: calc(100vh - 110px); }
.stage {    
  position: relative;   
  background: #f1f1f1;
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
  -webkit-tap-highlight-color: transparent !important;
}

.stage *,
.stage *::before,
.stage *::after {
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
  -webkit-tap-highlight-color: transparent !important;
}

.stage *::selection,
.stage::selection {
  background: transparent !important;
  color: inherit !important;
}

.stage *::-moz-selection,
.stage::-moz-selection {
  background: transparent !important;
  color: inherit !important;
}
.bank { width: 300px; min-width: 300px; border-left: 1px solid #e5e7eb; }

.navigation-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0;
  padding: 0 24px 10px 24px;
  gap: 10px;
  background: #e7f0ff;
  border-bottom: 1px solid #c9d8ff;
}
.page-input-container { display: flex; align-items: center; gap: 4px; }
.page-input-container input { width: 45px; text-align: center; }

.navigation-bar .btn {
  background: #2b6fde;
  color: #fff;
  border: 1px solid #235acc;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 12px;
}
.navigation-bar .btn:disabled {
  opacity: .45;
  cursor: not-allowed;
}
.navigation-bar input {
  height: 28px;
  padding: 0 8px;
  border: 1px solid #c9d8ff;
  border-radius: 6px;
}

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
.stats-panel {             /* the 'Statistics' quick panel */
  z-index: calc(var(--z-modal-top) + 500);  /* Always above cropped popup */
}

.cropped-popup,            /* cropped image dialog */
.blurred-background {
  z-index: var(--z-modal);           /* modal level */
}

/* When cropped popup is active, other popups should be above it */
.length-popup,
.statistics-popup {
  z-index: 999999 !important;  /* NUCLEAR OPTION - MUST BE ON TOP */
}

/* Just to be safe, their internal cards sit above their own backdrop */
.length-popup-content,
.statistics-popup-content,
.panel-card.stats-card,
.cropped-popup-content {
  position: relative;
  z-index: 1;
}

.pdf-viewer {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  background: #f1f1f1; /* gray behind manuscript */
}
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

.blurred-background { position: fixed; top: 0; left: 0; width: 100%; height: 100%; backdrop-filter: blur(8px); background-color: rgba(0,0,0,0.3); z-index: var(--z-modal); }
.cropped-popup {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  z-index: var(--z-modal-top);
  padding: 20px;
  text-align: center;
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
}

.cropped-popup * {
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
}

/* Global selection prevention when cropped popup is active */
body.cropped-popup-active * {
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
}

body.cropped-popup-active *::selection {
  background: transparent !important;
}

body.cropped-popup-active *::-moz-selection {
  background: transparent !important;
}
.cropped-popup-content img { max-width: 100%; max-height: 300px; margin-bottom: 20px; }
.cropped-popup-content button { margin-top: 10px; padding: 8px 16px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
.cropped-popup-content button:hover { background-color: #0056b3; }

/* Comment card */
.comment-card {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: grab;
  user-select: none;
}
.comment-card:active { cursor: grabbing; }

.comment-pin {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #e7f0ff;       /* light blue */
  color: #2b6fde;            /* blue icon */
  border: 1px solid #c9d8ff;
  font-size: 14px;
  flex: 0 0 auto;
}

.comment-bubble {
  flex: 1 1 auto;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.08);
  padding: 8px 10px;
}
.comment-text {
  font-size: 13px;
  color: #111827;
  line-height: 1.35;
}

/* Composer */
.comment-composer {
  width: 260px;
  background: #ffffff;
  border: 1px solid #c9d8ff;
  border-radius: 12px;
  box-shadow: 0 10px 24px rgba(43, 111, 222, 0.18);
  padding: 10px;
}

.composer-textarea {
  width: 100%;
  min-height: 86px;
  border: 1px solid #dbe4ff;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  resize: vertical;
  outline: none;
}
.composer-textarea:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}

.composer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.btn-blue {
  border: 1px solid #2563eb;
  background: #3b82f6;
  color: #fff;
  padding: 6px 10px;
  font-size: 13px;
  border-radius: 8px;
  cursor: pointer;
  transition: filter .15s, transform .02s;
}
.btn-blue:hover { filter: brightness(0.95); }
.btn-blue:active { transform: translateY(1px); }

.btn-gray {
  border: 1px solid #c7c9d1;
  background: #eef0f5;
  color: #374151;
  padding: 6px 10px;
  font-size: 13px;
  border-radius: 8px;
  cursor: pointer;
  transition: filter .15s, transform .02s;
}
.btn-gray:hover { filter: brightness(0.97); }
.btn-gray:active { transform: translateY(1px); }

.clear-dropdown {
  position: absolute; top: 100%; left: 0; background: white; border: 1px solid #ccc; border-radius: 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); z-index: 1100; min-width: 160px;
}
.clear-dropdown div { padding: 8px 12px; cursor: pointer; }
.clear-dropdown div:hover { background: #f5f5f5; }

.length-popup {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  display: flex; justify-content: center; align-items: center;
  background-color: rgba(0,0,0,0.5); z-index: 999999 !important;
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
.grid-btn.confirm-btn {
  background: #3b82f6;
  border-color: #2563eb;
  color: white;
}
.grid-btn.confirm-btn:hover {
  background: #2563eb;
  border-color: #1d4ed8;
}
.grid-btn.cancel-btn {
  background: #6b7280;
  border-color: #4b5563;
  color: white;
}
.grid-btn.cancel-btn:hover {
  background: #4b5563;
  border-color: #374151;
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
  display: flex; justify-content: center; align-items: center; background: rgba(0,0,0,0.5); z-index: 999999 !important;
}
.statistics-popup-content {
  background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  max-width: 600px; width: 100%;
}
.statistics-popup-content table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
.statistics-popup-content th, .statistics-popup-content td { border: 1px solid #ddd; padding: 8px; text-align: center; }
.statistics-popup-content th { background: #f2f2f2; }
.statistics-popup-content h4 { margin-top: 12px; margin-bottom: 8px; }

/* Stage is a fixed viewport for the page; UI overlays sit on top via z-index */
.pdf-viewer.stage {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  /* no flex centering — the anchor will center itself abs pos */
}

/* New absolute centered container that gets transformed */
.zoom-anchor {
  position: absolute; /* set in JS too */
  z-index: 100;       /* keep content behind bank/buttons/popups */
  will-change: transform;
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
}

.zoom-anchor *,
.zoom-anchor *::before,
.zoom-anchor *::after {
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
  -webkit-tap-highlight-color: transparent !important;
  -webkit-highlight: none !important;
}

.zoom-anchor *::selection,
.zoom-anchor::selection {
  background: transparent !important;
  color: inherit !important;
}

.zoom-anchor *::-moz-selection,
.zoom-anchor::-moz-selection {
  background: transparent !important;
  color: inherit !important;
}

/* NUCLEAR OPTION: Background div instead of img element */
.image-viewer-background {
  width: 100% !important;
  height: 100% !important;
  display: block !important;
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  z-index: -100 !important;
  
  /* Complete interaction prevention */
  pointer-events: none !important;
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
  -webkit-user-drag: none !important;
  -khtml-user-drag: none !important;
  -moz-user-drag: none !important;
  -o-user-drag: none !important;
  outline: none !important;
  border: none !important;
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  appearance: none !important;
  -webkit-tap-highlight-color: transparent !important;
  -webkit-highlight: none !important;
  -moz-user-focus: ignore !important;
  background-color: transparent !important;
  
  /* Prevent any text/content selection */
  -webkit-user-modify: read-only !important;
  -moz-user-modify: read-only !important;
}

.image-viewer-background::selection,
.image-viewer-background *::selection {
  background: transparent !important;
  color: inherit !important;
}

.image-viewer-background::-moz-selection,
.image-viewer-background *::-moz-selection {
  background: transparent !important;
  color: inherit !important;
}

.calculation-image {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain !important;
  opacity: 0 !important;
  pointer-events: none !important;
  user-select: none !important;
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  z-index: -1 !important;
}

.hidden-image-loader {
  display: none !important;
  visibility: hidden !important;
  position: absolute !important;
  top: -9999px !important;
  left: -9999px !important;
  pointer-events: none !important;
  user-select: none !important;
}

/* Ensure drawing layer sits above the image but below buttons/panels */
.drawing-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 120; /* slightly above anchor content if needed */
}

/* Keep bank and buttons well above page content */
.bank-panel { z-index: 1500; }

.image-viewer {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain !important;
  display: block !important;
  
  /* NUCLEAR OPTION: Complete interaction prevention */
  pointer-events: none !important;
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
  -webkit-user-drag: none !important;
  -khtml-user-drag: none !important;
  -moz-user-drag: none !important;
  -o-user-drag: none !important;
  outline: none !important;
  border: none !important;
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  appearance: none !important;
  -webkit-tap-highlight-color: transparent !important;
  -webkit-highlight: none !important;
  -moz-user-focus: ignore !important;
  position: relative !important;
  z-index: -10 !important;
  background: transparent !important;
  
  /* Completely invisible to mouse interactions */
  visibility: hidden !important;
}

/* Make the image visible but completely unselectable */
.zoom-anchor .image-viewer {
  visibility: visible !important;
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  z-index: -100 !important;
  pointer-events: none !important;
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
}

.image-viewer::selection {
  background: transparent !important;
  color: inherit !important;
}

.image-viewer::-moz-selection {
  background: transparent !important;
  color: inherit !important;
}
.page-loading {
  position: absolute; inset: 0;
  display: grid; place-items: center;
  color: #4b5563;
  font-size: 13px;
}

/* Popups must be the absolute top-most layer */
.length-popup,
.stats-panel,
.statistics-popup,
.cropped-popup {
  z-index: 2000;
}

/* Enhanced Cropped Popup Styles */
.cropped-popup {
  position: fixed;
  top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  box-shadow: 0 16px 40px rgba(0,0,0,.2);
  z-index: 2000;
  width: min(1100px, calc(100vw - 48px));
  max-height: calc(100vh - 120px);
  overflow: hidden;
}

.cropped-popup-content {
  padding: 16px 18px 12px;
}

.crop-header {
  display:flex; align-items:center; justify-content:space-between;
}
.crop-header h3 { margin: 0; font-size: 22px; font-weight: 700; }
.crop-actions { display:flex; gap:8px; }

.crop-stage {
  position: relative;
  height: 520px;              /* feel free to tune */
  background: #f7f9ff;
  border: 1px solid #e6ecff;
  border-radius: 12px;
  overflow: hidden;
  margin: 12px 0 10px;
}

.crop-anchor {
  position: absolute;
  will-change: transform;
  z-index: 100;
}

.cropped-image {
  display: block;
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
}

.zoom-btn {
  position: absolute;
  z-index: 1200;
  width: 36px; height: 36px;
  border-radius: 50%;
  border: none;
  background: #3b82f6;
  color: #fff;
  font-size: 20px;
  line-height: 36px;
  text-align: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.zoom-btn:disabled { opacity:.45; cursor:not-allowed; }
.zoom-btn:hover { filter: brightness(.95); }

.mini-bank {
  margin-top: 10px;
  border-top: 1px dashed #e5e7eb;
  padding-top: 10px;
}
.mini-bank-title {
  font-weight: 700; font-size: 14px; color: #334155; margin-bottom: 6px;
}
.mini-bank-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px,1fr));
  gap: 6px;
}
.mini-bank-item {
  display:flex; align-items:center; gap:8px;
  background:#f8fafc; border:1px solid #e5e7eb;
  padding:6px 8px; border-radius:8px;
  font-size:12px; color:#0f172a;
}
.mini-bank-item .dot {
  width:10px; height:10px; border-radius:50%;
}

/* ===== Global modal stacking policy ===== */
:root {
  --z-stage: 0;
  --z-bank: 1500;
  --z-popover: 3000;        /* tooltips, small menus */
  --z-modal: 9000;          /* standard dialogs (crop popup) */
  --z-modal-top: 10000;     /* any popup that must be above all */
}

/* NUCLEAR OPTION: Force angle/trace popups above everything */
.length-popup[v-if],
.statistics-popup[v-if],
div.length-popup,
div.statistics-popup,
.length-popup,
.statistics-popup {
  z-index: 999999 !important;
  position: fixed !important;
}

/* make sure all generic popups use one of these */
.stats-panel,
.cropped-popup {
  z-index: var(--z-modal);
}

/* Angle and trace popups MUST be above cropped popup */
.length-popup,
.statistics-popup {
  z-index: 999999 !important;
}

/* things that should ALWAYS sit above everything */
.length-popup.topmost,
.statistics-popup.topmost,
.stats-panel.topmost {
  z-index: var(--z-modal-top);
}

/* bank should never cover popups */
.bank-panel { z-index: var(--z-bank); }

/* Updated popup styles with new design */
.cropped-popup {
  position: fixed; top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  width: min(1100px, calc(100vw - 48px));
  max-height: calc(100vh - 96px);
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  box-shadow: 0 16px 40px rgba(0,0,0,.2);
  overflow: hidden;
  z-index: var(--z-modal);
}
.cropped-popup-content { padding: 14px 16px 12px; }

.crop-header {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 10px;
  padding: 2px 0 8px;
}
.left-spacer { min-height: 1px; }

.zoom-cluster {
  display: flex; 
  align-items: center; 
  justify-content: space-evenly;
  gap: 12px;
  background: linear-gradient(135deg, #f8faff 0%, #eef3ff 100%); 
  border: 1px solid #d8e1ff; 
  border-radius: 28px;
  padding: 12px 20px;
  box-shadow: 0 2px 8px rgba(47, 96, 227, 0.1);
  justify-self: center;
  min-height: 52px;
  min-width: 180px;
  margin-bottom: 20px;
}

.crop-actions { 
  display: inline-flex; 
  gap: 8px; 
  justify-self: end;
}

.zoom-pill {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36px; 
  width: 36px;
  height: 36px; 
  border-radius: 10px; 
  border: 10px solid #2f60e3;
  background: linear-gradient(135deg, #4a7aed 0%, #3f6eea 100%); 
  color: #fff; 
  font-weight: 700; 
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(47, 96, 227, 0.2);
  flex-shrink: 10;
  margin-top: -30px;
}
.zoom-pill:hover:not(:disabled) { 
  background: linear-gradient(135deg, #2f60e3 0%, #2856d6 100%); 
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(47, 96, 227, 0.3);
}
.zoom-pill:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(47, 96, 227, 0.3);
}
.zoom-pill:disabled { 
  opacity: .45; 
  cursor: not-allowed; 
  transform: none;
  box-shadow: none;
}
.zoom-readout { 
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px; 
  color: #2856d6; 
  font-weight: 600;
  min-width: 60px;
  height: 36px;
  padding: 0 12px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 18px;
  margin: 0;
  flex-shrink: 0;
  border: 1px solid rgba(216, 225, 255, 0.6);
}

/* Mini Toolbar for cropped popup */
.crop-toolbar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: #f8faff;
  border-top: 1px solid #e1e7f0;
  border-bottom: 1px solid #e1e7f0;
  margin-top: 8px;
}

.crop-tool {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s ease;
  color: #555;
  min-width: 60px;
}

.crop-tool:hover {
  background: #e8f0ff;
  color: #2f60e3;
}

.crop-tool.active {
  background: #3f6eea;
  color: #fff;
}

.crop-tool i {
  font-size: 18px;
}

.crop-tool span {
  font-size: 11px;
  font-weight: 500;
}

.crop-tool-divider {
  width: 1px;
  height: 32px;
  background: #d0d7e0;
}

.crop-stage {
  position: relative;
  height: 520px;
  margin-top: 8px;
  background: #f7f9ff;
  border: 1px solid #e6ecff;
  border-radius: 12px;
  overflow: hidden;
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
  -webkit-tap-highlight-color: transparent !important;
  -webkit-highlight: none !important;
}

.crop-stage *,
.crop-stage *::before,
.crop-stage *::after {
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
  -webkit-tap-highlight-color: transparent !important;
  -webkit-highlight: none !important;
}

.crop-stage *::selection,
.crop-stage::selection {
  background: transparent !important;
  color: inherit !important;
}

.crop-stage *::-moz-selection,
.crop-stage::-moz-selection {
  background: transparent !important;
  color: inherit !important;
}

.crop-anchor { 
  position: absolute; 
  will-change: transform; 
  z-index: 100; 
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
}
.cropped-image { 
  display: block !important; 
  width: 100% !important; 
  height: 100% !important; 
  object-fit: contain !important; 
  pointer-events: none !important; 
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
  -webkit-user-drag: none !important;
  -khtml-user-drag: none !important;
  -moz-user-drag: none !important;
  -o-user-drag: none !important;
  outline: none !important;
  border: none !important;
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  appearance: none !important;
  -webkit-tap-highlight-color: transparent !important;
  -webkit-highlight: none !important;
  -moz-user-focus: ignore !important;
  position: absolute !important;
  z-index: -10 !important;
  background: transparent !important;
}

.cropped-image::selection {
  background: transparent !important;
  color: inherit !important;
}

.cropped-image::-moz-selection {
  background: transparent !important;
  color: inherit !important;
}

/* Ensure overlay captures all events */
.image-overlay {
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  -webkit-touch-callout: none !important;
}

.mini-bank {
  margin-top: 10px;
  border-top: 1px dashed #e5e7eb;
  padding-top: 8px;
}

/* keep banks below modals */
.bank-panel, .mini-bank { z-index: var(--z-bank); }
</style>
