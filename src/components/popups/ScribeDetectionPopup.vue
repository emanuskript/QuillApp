<template>
  <div 
    v-if="isVisible" 
    class="scribe-popup-overlay"
    @click.self="closePopup"
  >
    <div class="scribe-popup-container">
      <!-- Header -->
      <div class="popup-header pharaonic-header">
        <div class="header-content">
          <div class="header-left">
            <img :src="require('@/assets/pharosight_icon_no_text.png')" alt="PharoSight" class="pharaonic-icon" />
            <span class="pharosight-text">PharoSight</span>
            <h3>Multiple Scribe Detection</h3>
          </div>
          <button 
            class="close-button"
            @click="closePopup"
          >
            ×
          </button>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="popup-content">
        <!-- Left Panel - Manuscript Page -->
        <div class="left-panel">
          <div class="image-container">
            <img 
              v-if="currentPageImage" 
              :src="currentPageImage" 
              alt="Manuscript page"
              class="manuscript-image"
              @load="onImageLoad"
            >
            <div v-else class="image-placeholder">
              <div class="page-indicator">
                <i class="fa-regular fa-file-text"></i>
                <h4>Manuscript Page {{ currentPage || 1 }}</h4>
                <p>Page {{ currentPage || 1 }} of {{ totalPages || 250 }}</p>
                <p class="loading-text">Loading manuscript image...</p>
              </div>
            </div>


          </div>
        </div>

        <!-- Right Panel - Analysis Results -->
        <div class="right-panel">
          <div class="analysis-section">
            <!-- Analysis Controls -->
            <div class="controls-section" v-if="!isAnalyzing && !hasResults">
              <div class="toolbar-actions">
                <button @click="analyzeScribes" :disabled="isAnalyzing" class="pharaonic-btn primary">
                  <span>Analyze Scribes</span>
                </button>
                <button @click="exportPDF" :disabled="!hasResults" class="pharaonic-btn secondary">
                  Export PDF
                </button>
              </div>

              <!-- Professional Parameter Controls -->
              <div class="params-container">
                <h4 class="params-title">Analysis Parameters</h4>
                <div class="params-grid">
                  <div class="param-group">
                    <label class="param-label">
                      <i class="info-icon" data-tooltip="sensitivity">ⓘ</i>
                      Sensitivity (z-thresh)
                    </label>
                    <div class="input-group">
                      <input type="range" min="1.2" max="3.0" step="0.1" v-model.number="params.z_thresh" class="range-input">
                      <span class="param-value">{{ params.z_thresh?.toFixed(1) ?? 'auto' }}</span>
                    </div>
                  </div>

                  <div class="param-group">
                    <label class="param-label">
                      <i class="info-icon" data-tooltip="min_gap">ⓘ</i>
                      Min Gap (lines)
                    </label>
                    <div class="input-group">
                      <input type="number" min="1" max="10" v-model.number="params.min_gap" class="number-input">
                    </div>
                  </div>

                  <div class="param-group">
                    <label class="param-label">
                      <i class="info-icon" data-tooltip="min_run">ⓘ</i>
                      Min Run (lines)
                    </label>
                    <div class="input-group">
                      <input type="number" min="1" max="10" v-model.number="params.min_run" class="number-input">
                    </div>
                  </div>

                  <div class="param-group">
                    <label class="param-label">
                      <i class="info-icon" data-tooltip="illum_frac">ⓘ</i>
                      Illumination Fraction
                    </label>
                    <div class="input-group">
                      <input type="number" step="0.005" v-model.number="params.illum_frac" class="number-input">
                    </div>
                  </div>

                  <div class="param-group">
                    <label class="param-label">
                      <i class="info-icon" data-tooltip="sauvola_window">ⓘ</i>
                      Sauvola Window
                    </label>
                    <div class="input-group">
                      <input type="number" min="15" step="2" v-model.number="params.sauvola_window" class="number-input">
                    </div>
                  </div>

                  <div class="param-group">
                    <label class="param-label">
                      <i class="info-icon" data-tooltip="algorithm">ⓘ</i>
                      Algorithm
                    </label>
                    <div class="input-group">
                      <select v-model="params.algo" class="select-input">
                        <option value="auto">Auto</option>
                        <option value="peaks">Peaks</option>
                        <option value="ruptures">Ruptures</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Pharaonic Loading Animation -->
            <div v-if="isAnalyzing" class="loading-section pharaonic-loading">
              <div class="pharaonic-spinner">
                <div class="ankh-spinner"></div>
                <div class="hieroglyph-ring"></div>
              </div>
              <div class="loading-text">
                <h4>{{ loadingMessage }}</h4>
                <p class="loading-detail">{{ loadingDetail }}</p>
              </div>
            </div>

            <!-- Results Display -->
            <div v-else-if="hasResults" class="results-section">
              <div class="results-header">
                <h4>Detected Scribes</h4>
                <div class="results-actions">
                  <button @click="analyzeAgain" class="pharaonic-btn primary">
                    Analyze Again
                  </button>
                  <button @click="exportPDF" class="pharaonic-btn secondary">
                    Export PDF
                  </button>
                </div>
              </div>
              
              <!-- Detected Scribes -->
              <div v-if="results.scribe_changes && results.scribe_changes.length > 0" class="detected-scribes">
                <div 
                  v-for="(change, index) in results.scribe_changes" 
                  :key="`change-${index}`"
                  :id="`scribe-result-${change.scribe}`"
                  class="scribe-item"
                  :class="{ 'highlighted': highlightedScribe === change.scribe }"
                >
                  <!-- Scribe Header with Letter Label -->
                  <div class="scribe-header">
                    <h5 class="scribe-title">{{ change.scribe }}</h5>
                    <span class="confidence">{{ Math.round(change.confidence * 100) }}%</span>
                  </div>
                  
                  <!-- Explanation directly under title -->
                  <p class="explanation">{{ change.explanation }}</p>
                  
                  <!-- Scribe Preview Screenshots -->
                  <div class="scribe-previews" v-if="change.samples && change.samples.length">
                    <img
                      v-for="(src, i) in change.samples.slice(0, 2)"
                      :key="i"
                      :src="`${backendBase}${src}`"
                      :alt="`${change.scribe} sample ${i + 1}`"
                      class="scribe-shot"
                      loading="lazy"
                      decoding="async"
                      @error="handleImageError"
                      @load="handleImageLoad"
                    />
                  </div>
                  
                  <!-- Line Screenshot (Original Canvas Method) -->
                  <div class="line-screenshot-container">
                    <canvas 
                      :ref="`lineCanvas${index}`"
                      class="line-screenshot"
                      width="400"
                      height="60"
                    ></canvas>
                    <div class="screenshot-overlay">
                      <span class="line-range">Lines {{ change.start_line }}-{{ change.end_line }}</span>
                    </div>
                  </div>
                  
                  <p class="location">Lines {{ change.start_line }}-{{ change.end_line }}</p>
                </div>
              </div>

              <!-- Summary Statistics -->
              <div v-if="results.statistics" class="statistics-section">
                <h5>Analysis Summary</h5>
                <div class="stat-grid">
                  <div class="stat-item">
                    <span class="stat-label">Total Scribes:</span>
                    <span class="stat-value">{{ results.statistics.total_scribes }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">Confidence:</span>
                    <span class="stat-value">{{ Math.round(results.statistics.overall_confidence * 100) }}%</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">Analysis Time:</span>
                    <span class="stat-value">{{ results.statistics.analysis_time }}ms</span>
                  </div>
                </div>
                
                <!-- Scientific Disclaimer -->
                <div class="analysis-disclaimer">
                  <h6>Disclaimer</h6>
                  <p class="disclaimer-text">
                    <strong>These results are computational estimates and not definitive determinations.</strong> 
                    Scribe detection accuracy depends on multiple interdependent factors:
                  </p>
                  <ul class="disclaimer-factors">
                    <li><strong>Image Quality:</strong> Resolution, contrast, illumination uniformity, and digital artifacts</li>
                    <li><strong>Paleographic Variables:</strong> Ink composition, parchment/paper texture, writing instrument characteristics</li>
                    <li><strong>Manuscript Condition:</strong> Age-related degradation, staining, fading, physical damage</li>
                    <li><strong>Writing Context:</strong> Formal vs. cursive scripts, fatigue effects, temporal writing variations</li>
                    <li><strong>Algorithm Limitations:</strong> Feature extraction methods, statistical thresholds, training data biases</li>
                    <li><strong>Preprocessing Effects:</strong> Binarization artifacts, noise reduction impact, geometric normalization</li>
                  </ul>
                  <p class="disclaimer-conclusion">
                    <em>Professional paleographic expertise should always complement computational analysis. 
                    Results should be validated through traditional codicological methods and cross-referenced with historical evidence.</em>
                  </p>
                </div>
              </div>
            </div>

            <!-- No Results State -->
            <div v-else-if="analysisCompleted && !hasResults" class="no-results">
              <p>No scribe changes detected in this page.</p>
            </div>

            <!-- Initial State -->
            <div v-else-if="!isAnalyzing" class="initial-state">
              <p>Click "Analyze Scribes" to detect different handwriting styles on this page.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ScribeDetectionPopup',
  props: {
    currentPage: {
      type: Number,
      default: 1
    },
    totalPages: {
      type: Number,
      default: 1
    },
    currentPageImage: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      isVisible: false,
      isAnalyzing: false,
      analysisCompleted: false,
      results: null,
      totalLinesEstimate: 25, // Default estimate for line visualization
      highlightedScribe: null,
      loadingMessage: 'Analyzing handwriting patterns...',
      loadingDetail: 'Initializing scribe detection algorithm',
      params: {
        z_thresh: 2.0,
        min_gap: 2,
        min_run: 2,
        illum_frac: 0.035,
        sauvola_window: 31,
        algo: 'auto'
      }
    }
  },
  watch: {
    results: {
      handler(newResults) {
        if (newResults && newResults.scribe_changes) {
          console.log('Analysis results received:', {
            scribe_changes: newResults.scribe_changes?.length || 0,
            line_screenshots: newResults.line_screenshots?.length || 0,
            ocr_available: newResults.ocr_available,
            total_lines: newResults.total_lines
          })
          
          // Add a small delay to ensure DOM is fully rendered
          setTimeout(() => {
            this.$nextTick(() => {
              // Use OCR line screenshots if available, otherwise fall back to canvas
              if (newResults.line_screenshots && newResults.line_screenshots.length > 0) {
                console.log('Using OCR-extracted line screenshots:', newResults.line_screenshots.length)
                console.log('Sample line screenshot:', newResults.line_screenshots[0])
                this.displayOcrLineScreenshots(newResults)
              } else {
                console.log('No OCR screenshots available, using canvas method')
                console.log('line_screenshots field:', newResults.line_screenshots)
                // Capture screenshots for each scribe change using canvas
                newResults.scribe_changes.forEach((change, index) => {
                  this.captureLineScreenshot(change, index)
                })
              }
            })
          }, 100)
        }
      },
      immediate: true
    }
  },
  computed: {
    hasResults() {
      return this.results && (this.results.primary_scribe || (this.results.scribe_changes && this.results.scribe_changes.length > 0))
    },
    backendBase() {
      return 'http://localhost:5001'
    }
  },
  methods: {
    openPopup() {
      this.isVisible = true
      this.resetAnalysis()
    },
    
    closePopup() {
      this.isVisible = false
      this.resetAnalysis()
    },
    
    resetAnalysis() {
      this.isAnalyzing = false
      this.analysisCompleted = false
      this.results = null
    },
    
    analyzeAgain() {
      this.resetAnalysis()
      // This will show the parameter controls again since hasResults will be false
    },
    
    onImageLoad() {
      console.log('Manuscript image loaded successfully')
    },
    
    highlightScribe(scribeName) {
      this.highlightedScribe = scribeName
    },
    
    handleImageError(event) {
      console.error('Failed to load scribe sample image:', event.target.src)
      event.target.style.display = 'none'
    },
    
    handleImageLoad(event) {
      console.log('Scribe sample image loaded successfully:', event.target.src)
    },
    
    displayOcrLineScreenshots(results) {
      console.log('Displaying OCR line screenshots')
      console.log('Available screenshots:', results.line_screenshots?.length || 0)
      
      // If no OCR screenshots, use canvas method
      if (!results.line_screenshots || results.line_screenshots.length === 0) {
        console.log('No OCR screenshots available, using canvas fallback')
        return
      }
      
      // Update each canvas with the corresponding screenshot
      results.scribe_changes.forEach((change, index) => {
        // Find the canvas for this scribe change
        this.$nextTick(() => {
          const canvas = this.$refs[`lineCanvas${index}`]
          if (!canvas || !canvas[0]) {
            console.warn(`Canvas ref not found for index ${index}`)
            return
          }
          
          // Find OCR screenshots for this scribe change
          const relatedScreenshots = results.line_screenshots.filter(lineData => 
            lineData.lineNumber >= change.start_line && lineData.lineNumber <= change.end_line
          )
          
          console.log(`Scribe change ${change.scribe}: found ${relatedScreenshots.length} related screenshots`)
          
          if (relatedScreenshots.length > 0) {
            // Use the first related screenshot
            const lineData = relatedScreenshots[0]
            const ctx = canvas[0].getContext('2d')
            
            // Create an image from the base64 data
            const img = new Image()
            img.onload = () => {
              // Clear the canvas
              ctx.clearRect(0, 0, canvas[0].width, canvas[0].height)
              
              // Draw the screenshot image
              ctx.drawImage(img, 0, 0, canvas[0].width, canvas[0].height)
              
              console.log(`Successfully displayed screenshot for line ${lineData.lineNumber}`)
            }
            
            img.onerror = () => {
              console.error(`Failed to load screenshot for line ${lineData.lineNumber}`)
              // Draw error indicator
              ctx.fillStyle = '#ff0000'
              ctx.fillRect(0, 0, canvas[0].width, canvas[0].height)
              ctx.fillStyle = '#ffffff'
              ctx.font = '12px Arial'
              ctx.fillText('Image Load Error', 10, 30)
            }
            
            // Set the image source to trigger loading
            img.src = lineData.screenshot
          }
        })
      })
      
      console.log('OCR line screenshots display complete')
    },
    
    captureLineScreenshot(change, index) {
      // Use a longer timeout to ensure everything is rendered
      setTimeout(() => {
        this.$nextTick(() => {
          const canvas = this.$refs[`lineCanvas${index}`]
          if (!canvas || !canvas[0]) {
            console.warn(`Canvas ref not found for index ${index}`)
            return
          }
          
          const ctx = canvas[0].getContext('2d')
          const manuscriptImg = this.$refs.manuscriptImage
          
          if (!manuscriptImg) {
            console.warn('Manuscript image ref not found')
            return
          }
          
          // Wait for image to be fully loaded and visible
          if (!manuscriptImg.complete || manuscriptImg.naturalWidth === 0) {
            console.log('Image not ready, retrying in 500ms...')
            setTimeout(() => this.captureLineScreenshot(change, index), 500)
            return
          }
          
          const imgNaturalWidth = manuscriptImg.naturalWidth
          const imgNaturalHeight = manuscriptImg.naturalHeight
          
          console.log(`Image dimensions: ${imgNaturalWidth}x${imgNaturalHeight}`)
          console.log(`Capturing lines ${change.start_line}-${change.end_line} for ${change.scribe}`)
          
          if (imgNaturalWidth === 0 || imgNaturalHeight === 0) {
            console.warn('Image dimensions not available, retrying...')
            setTimeout(() => this.captureLineScreenshot(change, index), 500)
            return
          }
          
          // Use the actual total lines from results
          const totalLines = this.results?.statistics?.total_lines || 30
          console.log(`Total lines in document: ${totalLines}`)
          
          // More precise positioning based on manuscript structure
          const topMargin = 0.08 // 8% top margin
          const bottomMargin = 0.12 // 12% bottom margin  
          const textAreaHeight = 1 - topMargin - bottomMargin
          
          // Calculate line spacing
          const lineSpacing = textAreaHeight / totalLines
          
          // Calculate positions for the specific lines with padding
          const startLineIndex = Math.max(0, change.start_line - 1)
          const endLineIndex = Math.min(totalLines - 1, change.end_line - 1)
          
          // Add padding above and below the target lines
          const paddingLines = 1.0
          const startY = topMargin + ((startLineIndex - paddingLines) * lineSpacing)
          const endY = topMargin + ((endLineIndex + paddingLines + 1) * lineSpacing)
          
          // Crop area calculations - wider area to capture full lines
          const cropX = 0.02 // 2% left margin
          const cropWidth = 0.96 // 96% width to include full lines
          const cropY = Math.max(0, startY)
          const cropHeight = Math.min(1 - cropY, endY - startY)
          
          console.log(`Crop percentages - x:${cropX}, y:${cropY}, w:${cropWidth}, h:${cropHeight}`)
          
          // Convert to pixel coordinates
          const sourceX = Math.round(cropX * imgNaturalWidth)
          const sourceY = Math.round(cropY * imgNaturalHeight)
          const sourceWidth = Math.round(cropWidth * imgNaturalWidth)
          const sourceHeight = Math.round(cropHeight * imgNaturalHeight)
          
          console.log(`Source pixels: x=${sourceX}, y=${sourceY}, w=${sourceWidth}, h=${sourceHeight}`)
          
          // Ensure we have valid dimensions
          if (sourceWidth <= 0 || sourceHeight <= 0) {
            console.error('Invalid crop dimensions calculated')
            return
          }
          
          // Set canvas dimensions
          const canvasWidth = 400
          const aspectRatio = sourceWidth / sourceHeight
          const canvasHeight = Math.max(60, Math.round(canvasWidth / aspectRatio))
          
          canvas[0].width = canvasWidth
          canvas[0].height = canvasHeight
          
          // Clear canvas
          ctx.clearRect(0, 0, canvasWidth, canvasHeight)
          
          try {
            // Draw the cropped section
            ctx.drawImage(
              manuscriptImg,
              sourceX, sourceY, sourceWidth, sourceHeight,
              0, 0, canvasWidth, canvasHeight
            )
            
            // Add a border to help visualize the crop
            ctx.strokeStyle = 'rgba(220, 20, 60, 0.8)'
            ctx.lineWidth = 2
            ctx.strokeRect(1, 1, canvasWidth - 2, canvasHeight - 2)
            
            // Add line indicators
            ctx.strokeStyle = 'rgba(255, 0, 0, 0.4)'
            ctx.lineWidth = 1
            
            // Draw lines to indicate where each text line should be
            for (let i = startLineIndex; i <= endLineIndex; i++) {
              const relativeY = ((topMargin + (i * lineSpacing)) - cropY) / cropHeight
              const lineY = relativeY * canvasHeight
              
              if (lineY >= 0 && lineY <= canvasHeight) {
                ctx.beginPath()
                ctx.moveTo(10, lineY)
                ctx.lineTo(canvasWidth - 10, lineY)
                ctx.stroke()
                
                // Add line number
                ctx.fillStyle = 'rgba(255, 0, 0, 0.8)'
                ctx.font = '10px Arial'
                ctx.fillText(`${i + 1}`, 5, lineY - 2)
              }
            }
            
            console.log(`✓ Successfully captured screenshot for lines ${change.start_line}-${change.end_line}`)
            
          } catch (error) {
            console.error('Failed to capture line screenshot:', error)
            // Draw a detailed error placeholder
            ctx.fillStyle = '#f8f9fa'
            ctx.fillRect(0, 0, canvasWidth, canvasHeight)
            
            ctx.fillStyle = '#dc3545'
            ctx.font = 'bold 14px Arial'
            ctx.textAlign = 'center'
            ctx.fillText('Capture Failed', canvasWidth / 2, canvasHeight / 2 - 20)
            
            ctx.fillStyle = '#6c757d'
            ctx.font = '12px Arial'
            ctx.fillText(`Lines ${change.start_line}-${change.end_line}`, canvasWidth / 2, canvasHeight / 2)
            ctx.fillText(change.scribe, canvasWidth / 2, canvasHeight / 2 + 20)
          }
        })
      }, 200) // Initial delay to ensure DOM is ready
    },
    
    // Debug method to help calibrate line positioning
    showLineGrid() {
      const manuscriptImg = this.$refs.manuscriptImage
      if (!manuscriptImg || !manuscriptImg.complete) return
      
      // Create a temporary overlay to show all line positions
      const overlay = document.createElement('canvas')
      const ctx = overlay.getContext('2d')
      
      overlay.style.position = 'absolute'
      overlay.style.top = '0'
      overlay.style.left = '0'
      overlay.style.width = '100%'
      overlay.style.height = '100%'
      overlay.style.pointerEvents = 'none'
      overlay.style.zIndex = '1000'
      
      manuscriptImg.parentElement.appendChild(overlay)
      
      // Set canvas size to match image
      const rect = manuscriptImg.getBoundingClientRect()
      overlay.width = rect.width
      overlay.height = rect.height
      
      // Draw line grid
      const totalLines = 30
      const topMargin = 0.10
      const bottomMargin = 0.15
      const textAreaHeight = 1 - topMargin - bottomMargin
      const lineSpacing = textAreaHeight / totalLines
      
      ctx.strokeStyle = 'rgba(255, 0, 0, 0.5)'
      ctx.lineWidth = 1
      
      for (let i = 0; i < totalLines; i++) {
        const y = (topMargin + (i * lineSpacing)) * overlay.height
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(overlay.width, y)
        ctx.stroke()
        
        // Add line number
        ctx.fillStyle = 'red'
        ctx.font = '12px Arial'
        ctx.fillText(`Line ${i + 1}`, 5, y - 2)
      }
      
      // Remove overlay after 5 seconds
      setTimeout(() => {
        overlay.remove()
      }, 5000)
    },
    
    async analyzeScribes() {
      if (this.isAnalyzing) return
      
      this.isAnalyzing = true
      this.analysisCompleted = false
      this.results = null
      this.loadingMessage = 'Preparing manuscript image...'
      this.loadingDetail = 'Processing image for analysis'
      
      try {
        console.log('Starting scribe analysis...')

        if (!this.currentPageImage) {
          throw new Error('No page image available for analysis')
        }
        
        this.loadingMessage = 'Fetching manuscript data...'
        this.loadingDetail = 'Converting image format'
        
        // Fetch the image and convert to blob for upload
        const imageResponse = await fetch(this.currentPageImage)
        if (!imageResponse.ok) {
          throw new Error('Failed to fetch page image')
        }
        const imageBlob = await imageResponse.blob()
        
        this.loadingMessage = 'Configuring analysis parameters...'
        this.loadingDetail = 'Setting up detection algorithms'
        
        // Create FormData for upload (+ params)
        const formData = new FormData()
        formData.append('image', imageBlob, 'manuscript_page.jpg')
        if (this.params.z_thresh) formData.append('z_thresh', String(this.params.z_thresh))
        formData.append('min_gap', String(this.params.min_gap))
        formData.append('min_run', String(this.params.min_run))
        formData.append('illum_frac', String(this.params.illum_frac))
        formData.append('sauvola_window', String(this.params.sauvola_window))
        formData.append('algo', this.params.algo)
        
        this.loadingMessage = 'Analyzing handwriting patterns...'
        this.loadingDetail = 'Running scribe detection algorithms'
        
        // Call the Python backend
        const response = await fetch('http://localhost:5001/analyze', {
          method: 'POST',
          body: formData
        })
        
        if (!response.ok) {
          throw new Error(`Analysis failed: ${response.statusText}`)
        }
        
        this.loadingMessage = 'Processing results...'
        this.loadingDetail = 'Identifying unique scribes'
        
        const data = await response.json()
        console.log('Raw backend response:', {
          scribe_changes: data.scribe_changes?.length || 0,
          line_screenshots: data.line_screenshots?.length || 0,
          scribe_samples: Object.keys(data.scribe_samples || {}).length,
          ocr_available: data.ocr_available,
          total_lines: data.total_lines
        })
        
        // Transform backend response to frontend format
        this.results = this.transformBackendResults(data)
        console.log('Analysis results transformed:', this.results)
        
      } catch (error) {
        console.error('Analysis failed:', error)
        alert(`Scribe analysis failed: ${error.message}`)
        
      } finally {
        this.isAnalyzing = false
        this.analysisCompleted = true
      }
    },
    
    transformBackendResults(data) {
      const scribeChanges = data.scribe_changes || []
      const totalLines = data.total_lines || 30
      
      // Use the backend scribe changes directly - no more "primary scribe" creation
      const transformedChanges = scribeChanges.map((change) => ({
        scribe: change.scribe || `Scribe at line ${change.line_number}`,
        confidence: change.confidence || 0.7,
        start_line: change.start_line || change.line_number,
        end_line: change.end_line || (change.line_number + 1),
        explanation: change.explanation || "Handwriting change detected through analysis.",
        samples: change.samples || []
      }))
      
      // Calculate statistics
      const totalScribes = transformedChanges.length
      const avgConfidence = transformedChanges.length > 0 
        ? transformedChanges.reduce((sum, s) => sum + s.confidence, 0) / totalScribes
        : 0.8
      
      console.log('Transformed results:', {
        scribe_changes: transformedChanges,
        total_scribes: totalScribes,
        line_screenshots: data.line_screenshots?.length || 0
      })

      return {
        scribe_changes: transformedChanges,
        line_screenshots: data.line_screenshots || [],
        ocr_available: data.ocr_available,
        statistics: {
          total_scribes: totalScribes,
          overall_confidence: avgConfidence,
          analysis_time: 1500,
          total_lines: totalLines
        }
      }
    },

    async exportPDF() {
      try {
        const el = this.$el.querySelector('.results-section')
        if (!el) return
        const { jsPDF } = await import('jspdf')
        const html2canvas = (await import('html2canvas')).default
        const canvas = await html2canvas(el, { scale: 2 })
        const imgData = canvas.toDataURL('image/png')
        const pdf = new jsPDF('p', 'pt', 'a4')
        const pageWidth = pdf.internal.pageSize.getWidth()
        const pageHeight = pdf.internal.pageSize.getHeight()
        // fit within margins
        const margin = 24
        const w = pageWidth - margin * 2
        const h = canvas.height * (w / canvas.width)
        pdf.addImage(imgData, 'PNG', margin, margin, w, Math.min(h, pageHeight - margin*2))
        pdf.save(`scribe-analysis-page-${this.currentPage || 1}.pdf`)
      } catch (e) {
        console.error(e)
        alert('Failed to export PDF')
      }
    }
  }
}
</script>

<style scoped>
.scribe-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.scribe-popup-container {
  width: 90%;
  max-width: 1200px;
  height: 85%;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.popup-header {
  background: #2c3e50;
  color: white;
  padding: 1.75rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.popup-header h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.popup-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.left-panel {
  flex: 1;
  background: #f8f9fa;
  border-right: 1px solid #e9ecef;
  overflow: visible; /* Allow arrows to extend beyond panel */
  position: relative;
  padding: 0;
  margin: 0;
}

.image-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 0;
  margin: 0;
}

.manuscript-image {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Line Screenshot Styles */
.line-screenshot-container {
  position: relative;
  margin-bottom: 12px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.line-screenshot {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 8px;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
}

.screenshot-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.line-range {
  color: #ffc107;
}

.image-placeholder {
  text-align: center;
  color: #6c757d;
  padding: 2rem;
}

.page-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.page-indicator i {
  font-size: 4rem;
  color: #007bff;
  opacity: 0.7;
}

.page-indicator h4 {
  margin: 0;
  font-size: 1.5rem;
  color: #2c3e50;
}

.page-indicator p {
  margin: 0;
  font-size: 1rem;
  color: #6c757d;
}

.loading-text {
  margin-top: 1rem !important;
  font-style: italic;
  font-size: 0.9rem !important;
  color: #007bff !important;
}

.right-panel {
  flex: 1;
  background: white;
  overflow-y: auto;
  margin-left: -80px; /* Allow space for arrows from left panel */
  padding-left: 80px; /* Restore content padding */
  z-index: 5;
}

.analysis-section {
  padding: 1.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.controls-section {
  margin-bottom: 1.5rem;
}

.analyze-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  width: 100%;
}

.analyze-btn {
  background: linear-gradient(45deg, #6f42c1, #8b5fbf);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(111, 66, 193, 0.3);
}

.analyze-btn:hover:not(:disabled) {
  background: linear-gradient(45deg, #5a36a3, #7148a1);
  box-shadow: 0 4px 12px rgba(111, 66, 193, 0.4);
  transform: translateY(-1px);
}

.analyze-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.debug-btn {
  background: #17a2b8;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  margin-left: 10px;
  transition: background 0.2s ease;
}

.debug-btn:hover {
  background: #138496;
}

.analyze-button:hover:not(:disabled) {
  background: #0056b3;
}

.analyze-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.loading-section {
  text-align: center;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.results-section {
  flex: 1;
}

.results-section h4 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.scribe-item {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border-left: 4px solid #1e40af;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.scribe-item.highlighted {
  border-left-color: #007bff !important;
  background: rgba(0, 123, 255, 0.1) !important;
  box-shadow: 0 0 15px rgba(0, 123, 255, 0.3);
  transform: scale(1.02);
}

.scribe-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.scribe-title {
  margin: 0;
  color: #1e40af;
  font-size: 1.2rem;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.confidence {
  background: #1e40af;
  color: white;
  padding: 0.4rem 0.8rem;
  border-radius: 16px;
  font-size: 0.85rem;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(30, 64, 175, 0.3);
}

.location {
  font-size: 0.9rem;
  color: #6c757d;
  margin: 1rem 0 0.5rem 0;
  font-style: italic;
  font-weight: 500;
}

.explanation {
  font-size: 0.95rem;
  color: #495057;
  margin: 0 0 1rem 0;
  line-height: 1.5;
  background: rgba(30, 64, 175, 0.05);
  padding: 0.8rem;
  border-radius: 8px;
  border-left: 3px solid #fbbf24;
}

.additional-scribes h5 {
  color: #2c3e50;
  margin: 1.5rem 0 1rem 0;
  font-size: 1rem;
}

.statistics-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e9ecef;
}

.statistics-section h5 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1rem;
}

.stat-grid {
  display: grid;
  gap: 0.75rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.stat-label {
  color: #6c757d;
  font-size: 0.9rem;
}

.stat-value {
  font-weight: 600;
  color: #2c3e50;
}

/* Disclaimer Styling */
.analysis-disclaimer {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  border-left: 3px solid #6c757d;
}

.analysis-disclaimer h6 {
  color: #495057;
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  font-weight: 600;
}

.disclaimer-text {
  color: #495057;
  font-size: 0.85rem;
  line-height: 1.5;
  margin: 0 0 0.75rem 0;
}

.disclaimer-factors {
  color: #495057;
  font-size: 0.8rem;
  line-height: 1.4;
  margin: 0 0 0.75rem 0;
  padding-left: 1rem;
}

.disclaimer-factors li {
  margin-bottom: 0.4rem;
}

.disclaimer-factors strong {
  color: #343a40;
  font-weight: 600;
}

.disclaimer-conclusion {
  color: #495057;
  font-size: 0.8rem;
  line-height: 1.4;
  margin: 0;
  font-style: italic;
  border-top: 1px solid #dee2e6;
  padding-top: 0.75rem;
}

.no-results, .initial-state {
  text-align: center;
  color: #6c757d;
  padding: 2rem;
  font-style: italic;
}

/* Responsive Design */
@media (max-width: 768px) {
  .popup-content {
    flex-direction: column;
  }
  
  .left-panel {
    flex: 0 0 40%;
    border-right: none;
    border-bottom: 1px solid #e9ecef;
  }
  
  .right-panel {
    flex: 1;
  }
  
  .scribe-popup-container {
    width: 95%;
    height: 90%;
  }
}
/* Scribe preview samples styling */
.scribe-previews {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin: 8px 0 12px;
}

.scribe-shot {
  display: block;
  width: 160px;
  max-width: 30%;
  aspect-ratio: 5 / 2;
  object-fit: cover;
  border-radius: 8px;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(147, 51, 234, 0.1);
  background: rgba(255, 255, 255, 0.05);
}

.scribe-shot:hover {
  transform: scale(1.02);
  transition: transform 0.2s ease;
}

/* Ensure scribe modal has highest z-index */
.scribe-popup-overlay {
  z-index: 7000 !important;
}

.scribe-popup-container {
  z-index: 7001 !important;
}

.export-btn { margin-left: 8px; }
.params {
  display: grid;
  grid-template-columns: repeat(3, minmax(180px, 1fr));
  gap: 8px;
  margin-top: 8px;
}
.params label { display:flex; align-items:center; gap:8px; font-size: 0.9rem; }
.param-val { opacity: 0.7; }

/* Pharaonic Theme Styles */
.pharaonic-header {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 50%, #020617 100%);
  border-bottom: 4px solid #fbbf24;
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 -2px 10px rgba(251, 191, 36, 0.2);
}

.pharaonic-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    /* Visible pharaonic geometric patterns */
    radial-gradient(circle at 20% 30%, rgba(251, 191, 36, 0.25) 2px, transparent 3px),
    radial-gradient(circle at 80% 70%, rgba(251, 191, 36, 0.2) 2px, transparent 3px),
    radial-gradient(circle at 50% 20%, rgba(251, 191, 36, 0.15) 1px, transparent 2px),
    radial-gradient(circle at 30% 80%, rgba(251, 191, 36, 0.15) 1px, transparent 2px),
    /* Pharaonic zigzag patterns */
    repeating-linear-gradient(
      45deg,
      transparent,
      transparent 15px,
      rgba(251, 191, 36, 0.12) 15px,
      rgba(251, 191, 36, 0.12) 18px,
      transparent 18px,
      transparent 30px
    ),
    repeating-linear-gradient(
      -45deg,
      transparent,
      transparent 20px,
      rgba(251, 191, 36, 0.08) 20px,
      rgba(251, 191, 36, 0.08) 23px,
      transparent 23px,
      transparent 40px
    ),
    /* Pharaonic border pattern with hieroglyph-like lines */
    linear-gradient(
      to right,
      rgba(251, 191, 36, 0.2) 0%,
      rgba(251, 191, 36, 0.1) 5%,
      transparent 15%,
      transparent 85%,
      rgba(251, 191, 36, 0.1) 95%,
      rgba(251, 191, 36, 0.2) 100%
    ),
    /* Additional ancient Egyptian inspired pattern */
    repeating-linear-gradient(
      90deg,
      transparent,
      transparent 8px,
      rgba(251, 191, 36, 0.06) 8px,
      rgba(251, 191, 36, 0.06) 10px
    );
  background-size: 60px 60px, 80px 80px, 40px 40px, 50px 50px, 30px 30px, 35px 35px, 100% 100%, 20px 20px;
  pointer-events: none;
}

.pharaonic-title {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 2;
}

.pharaonic-icon {
  height: 52px;
  width: auto;
  object-fit: contain;
  filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.3));
}

.pharosight-text {
  color: #fbbf24;
  font-size: 1.5rem;
  font-weight: 700;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
  filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.3));
  margin-right: 12px;
}

.title-text {
  color: #ffffff;
  font-weight: 700;
  font-size: 1.3rem;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.page-info {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 600;
  border: 1px solid rgba(251, 191, 36, 0.3);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* Professional Parameter Controls */
.params-container {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
  margin: 16px 0;
  border: 2px solid #e2e8f0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.params-title {
  color: #1e40af;
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 16px 0;
  text-align: center;
  padding-bottom: 8px;
  border-bottom: 2px solid #fbbf24;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.param-group {
  background: white;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.param-group:hover {
  border-color: #fbbf24;
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.1);
  transform: translateY(-1px);
}

.param-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  font-size: 0.95rem;
}

.info-icon {
  color: #6b7280;
  cursor: help;
  font-size: 0.9rem;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  transition: all 0.2s ease;
  position: relative;
}

.info-icon:hover {
  background: #fbbf24;
  color: white;
  transform: scale(1.1);
}

/* Advanced Tooltips */
.info-icon::after {
  content: attr(data-tooltip-content);
  position: absolute;
  top: 50%;
  left: calc(100% + 15px);
  transform: translateY(-50%);
  background: linear-gradient(145deg, #1e293b, #334155);
  color: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
  border: 2px solid #fbbf24;
  font-size: 0.75rem;
  line-height: 1.3;
  width: 280px;
  white-space: normal;
  z-index: 999999 !important;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
  pointer-events: none;
  font-weight: normal;
}

/* Tooltip backdrop */
.info-icon:hover::after {
  backdrop-filter: blur(2px);
}

.info-icon::before {
  content: '';
  position: absolute;
  top: 50%;
  left: calc(100% + 9px);
  transform: translateY(-50%);
  border: 6px solid transparent;
  border-right-color: #fbbf24;
  z-index: 1000000 !important;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
}

.info-icon:hover::after,
.info-icon:hover::before {
  opacity: 1;
  visibility: visible;
}

/* Sensitivity tooltip */
.info-icon[data-tooltip="sensitivity"]::after {
  content: "🎯 SENSITIVITY (Z-THRESHOLD)\A\AControls how sensitive the algorithm is to detecting handwriting changes between scribes.\A\A📉 LOWER VALUES (1.2-2.0): Detect more subtle differences, may find more scribe changes but could create false positives.\A\A📈 HIGHER VALUES (2.5-3.0): Only detect major handwriting differences, more conservative but fewer false alarms.\A\A🎚️ RANGE: 1.2 to 3.0\A💡 RECOMMENDED: 2.0-2.5 for most manuscripts";
  white-space: pre-line;
}

/* Min Gap tooltip */
.info-icon[data-tooltip="min_gap"]::after {
  content: "📏 MINIMUM GAP (LINES)\A\AMinimum number of lines required between detected scribe changes.\A\A📉 LOWER VALUES (1-3): Allow scribe changes with fewer lines in between, detects rapid alternations.\A\A📈 HIGHER VALUES (4-10): Require more separation between changes, reduces noise from brief interruptions.\A\A🎚️ RANGE: 1 to 10 lines\A💡 RECOMMENDED: 2-4 for typical manuscripts\A⚠️ Too low may detect every small variation";
  white-space: pre-line;
}

/* Min Run tooltip */
.info-icon[data-tooltip="min_run"]::after {
  content: "✍️ MINIMUM RUN (LINES)\A\AMinimum number of consecutive lines a scribe must write to be considered a separate scribe.\A\A📉 LOWER VALUES (1-2): Detect brief scribe contributions, good for collaborative writing.\A\A📈 HIGHER VALUES (3-10): Only identify substantial scribe contributions, filters out corrections.\A\A🎚️ RANGE: 1 to 10 lines\A💡 RECOMMENDED: 2-3 for most cases\A⚠️ Too high may miss legitimate scribe changes";
  white-space: pre-line;
}

/* Illumination Fraction tooltip */
.info-icon[data-tooltip="illum_frac"]::after {
  content: "💡 ILLUMINATION FRACTION\A\AControls illumination correction during image preprocessing to handle uneven lighting.\A\A📉 LOWER VALUES (0.1-0.3): Minimal correction, preserves original contrast but may keep shadows.\A\A📈 HIGHER VALUES (0.4-0.8): Strong correction, removes shadows but may over-brighten.\A\A🎚️ RANGE: 0.1 to 0.8\A💡 RECOMMENDED: 0.2-0.4 for most manuscripts\A⚠️ Too high may wash out ink details";
  white-space: pre-line;
}

/* Sauvola Window tooltip */
.info-icon[data-tooltip="sauvola_window"]::after {
  content: "🖼️ SAUVOLA WINDOW SIZE\A\AWindow size for Sauvola binarization (converting grayscale to black/white).\A\A📉 SMALLER VALUES (15-25): Better for fine details and thin strokes, may be noisy.\A\A📈 LARGER VALUES (35-51): Smoother results, better for thick writing, may lose fine details.\A\A🎚️ RANGE: 15+ (odd numbers only)\A💡 RECOMMENDED: 25-35 for most manuscripts\A⚠️ Must be odd number for algorithm";
  white-space: pre-line;
}

/* Algorithm tooltip */
.info-icon[data-tooltip="algorithm"]::after {
  content: "⚙️ DETECTION ALGORITHM\A\A🤖 AUTO: Automatically selects best algorithm based on manuscript characteristics (RECOMMENDED).\A\A⛰️ PEAKS: Fast peak-detection algorithm, good for clear handwriting differences.\A\A🔬 RUPTURES: Rigorous change-point detection, more accurate but slower processing.\A\A💡 RECOMMENDED: Use 'Auto' unless you have specific requirements\A⚡ PEAKS: Fastest processing\A🎯 RUPTURES: Most accurate results";
  white-space: pre-line;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.range-input, .number-input, .select-input {
  flex: 1;
  padding: 8px 12px;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.range-input:focus, .number-input:focus, .select-input:focus {
  outline: none;
  border-color: #1e40af;
  box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
}

.param-value {
  min-width: 45px;
  padding: 4px 8px;
  background: #1e40af;
  color: white;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.9rem;
  text-align: center;
}

/* Pharaonic Buttons */
.pharaonic-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.pharaonic-btn.primary {
  background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
  color: white;
  border: 2px solid #1d4ed8;
}

.pharaonic-btn.primary:hover {
  background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(30, 64, 175, 0.3);
}

.pharaonic-btn.secondary {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  color: white;
  border: 2px solid #047857;
}

.pharaonic-btn.secondary:hover {
  background: linear-gradient(135deg, #047857 0%, #059669 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(5, 150, 105, 0.3);
}

.pharaonic-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.pharaonic-btn.small {
  padding: 8px 16px;
  font-size: 0.85rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.pharaonic-btn.small:hover {
  box-shadow: 0 4px 12px rgba(30, 64, 175, 0.2);
  transform: translateY(-1px);
}

/* Results Header */
.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.results-header h4 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.results-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 20px;
}

/* Pharaonic Loading Animation */
.pharaonic-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 12px;
  margin: 20px;
  border: 3px solid #fbbf24;
  box-shadow: 0 8px 24px rgba(251, 191, 36, 0.2);
}

.pharaonic-spinner {
  position: relative;
  width: 80px;
  height: 80px;
  margin-bottom: 24px;
}

.ankh-spinner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  color: #fbbf24;
  font-size: 2.5rem;
  animation: pharaonicPulse 1.5s ease-in-out infinite;
}

.ankh-spinner::before {
  content: '☥';
  display: block;
  text-align: center;
  filter: drop-shadow(0 0 10px rgba(251, 191, 36, 0.5));
}

.hieroglyph-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top: 3px solid #fbbf24;
  border-right: 3px solid #1e40af;
  border-radius: 50%;
  animation: pharaonicRotate 2s linear infinite;
}

.loading-text {
  text-align: center;
}

.loading-text h4 {
  color: #1e40af;
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0 0 8px 0;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.loading-detail {
  color: #6b7280;
  font-size: 0.95rem;
  margin: 0;
  font-style: italic;
}

@keyframes pharaonicRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes pharaonicPulse {
  0%, 100% { 
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
  50% { 
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0.8;
  }
}

</style>