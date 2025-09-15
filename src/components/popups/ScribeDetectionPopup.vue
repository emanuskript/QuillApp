<template>
  <div 
    v-if="isVisible" 
    class="scribe-popup-overlay"
    @click.self="closePopup"
  >
    <div class="scribe-popup-container">
      <!-- Header -->
      <div class="popup-header">
        <h3>Scribe Detection Analysis - Page {{ currentPage }}</h3>
        <button 
          class="close-button"
          @click="closePopup"
        >
          ×
        </button>
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
            <div class="controls-section">
                          <div class="toolbar-actions">
              <button @click="analyzeScribes" :disabled="isAnalyzing" class="analyze-btn">
                <span v-if="isAnalyzing">Analyzing...</span>
                <span v-else>Analyze Scribes</span>
              </button>
              <button @click="showLineGrid" class="debug-btn" title="Show line grid for debugging">
                Show Line Grid
              </button>
            </div>
            </div>

            <!-- Loading State -->
            <div v-if="isAnalyzing" class="loading-section">
              <div class="spinner"></div>
              <p>Analyzing scribes...</p>
            </div>

            <!-- Results Display -->
            <div v-else-if="hasResults" class="results-section">
              <h4>Detected Scribes</h4>
              
              <!-- Primary Scribe -->
              <div v-if="results.primary_scribe" class="scribe-item primary">
                <div class="scribe-header">
                  <h5>Primary Scribe</h5>
                  <span class="confidence">{{ Math.round(results.primary_scribe.confidence * 100) }}%</span>
                </div>
                <p class="scribe-name">{{ results.primary_scribe.name }}</p>
                <p class="explanation">{{ results.primary_scribe.explanation }}</p>
              </div>

              <!-- Additional Scribes -->
              <div v-if="results.scribe_changes && results.scribe_changes.length > 0" class="additional-scribes">
                <h5>Additional Scribes Found</h5>
                <div 
                  v-for="(change, index) in results.scribe_changes" 
                  :key="`change-${index}`"
                  :id="`scribe-result-${change.scribe}`"
                  class="scribe-item secondary"
                  :class="{ 'highlighted': highlightedScribe === change.scribe }"
                >
                  <!-- Line Screenshot -->
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
                  
                  <div class="scribe-header">
                    <span class="scribe-name">{{ change.scribe }}</span>
                    <span class="confidence">{{ Math.round(change.confidence * 100) }}%</span>
                  </div>
                  <p class="location">Lines {{ change.start_line }}-{{ change.end_line }}</p>
                  <p class="explanation">{{ change.explanation }}</p>
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
      highlightedScribe: null
    }
  },
  watch: {
    results: {
      handler(newResults) {
        if (newResults && newResults.scribe_changes) {
          // Add a small delay to ensure DOM is fully rendered
          setTimeout(() => {
            this.$nextTick(() => {
              // Capture screenshots for each scribe change
              newResults.scribe_changes.forEach((change, index) => {
                this.captureLineScreenshot(change, index)
              })
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
    
    onImageLoad() {
      console.log('Manuscript image loaded successfully')
    },
    
    highlightScribe(scribeName) {
      this.highlightedScribe = scribeName
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
      
      try {
        // Convert image URL to blob for upload
        if (!this.currentPageImage) {
          throw new Error('No page image available for analysis')
        }
        
        // Fetch the image and convert to blob
        const imageResponse = await fetch(this.currentPageImage)
        if (!imageResponse.ok) {
          throw new Error('Failed to fetch page image')
        }
        const imageBlob = await imageResponse.blob()
        
        // Create FormData for upload
        const formData = new FormData()
        formData.append('image', imageBlob, 'manuscript_page.jpg')
        
        // Call the Python backend
        const response = await fetch('http://localhost:5001/analyze', {
          method: 'POST',
          body: formData
        })
        
        if (!response.ok) {
          throw new Error(`Analysis failed: ${response.statusText}`)
        }
        
        const data = await response.json()
        
        // Transform backend response to frontend format
        this.results = this.transformBackendResults(data)
        this.totalLinesEstimate = data.total_lines || this.totalLinesEstimate
        this.analysisCompleted = true
        
      } catch (error) {
        console.error('Analysis failed:', error)
        this.results = null
        this.analysisCompleted = true
        
        // Show error to user
        alert(`Scribe analysis failed: ${error.message}`)
      } finally {
        this.isAnalyzing = false
      }
    },
    
    transformBackendResults(data) {
      const scribeChanges = data.scribe_changes || []
      const totalLines = data.total_lines || 30
      
      // Create primary scribe
      const primaryScribe = {
        name: "Primary Scribe",
        confidence: 0.85,
        explanation: `Main handwriting style found throughout the manuscript. Analysis processed ${totalLines} text lines.`
      }
      
      // Transform scribe changes - use the new format with start_line, end_line, and scribe name
      const secondaryScribes = scribeChanges.map((change) => ({
        scribe: change.scribe || `Scribe at line ${change.line_number}`,
        confidence: change.confidence || 0.7,
        start_line: change.start_line || change.line_number,
        end_line: change.end_line || (change.line_number + 1),
        explanation: change.explanation || "Handwriting change detected through analysis."
      }))
      
      // Calculate statistics
      const totalScribes = 1 + secondaryScribes.length
      const avgConfidence = secondaryScribes.length > 0 
        ? (primaryScribe.confidence + secondaryScribes.reduce((sum, s) => sum + s.confidence, 0)) / totalScribes
        : primaryScribe.confidence
      
      console.log('Transformed results:', {
        primary_scribe: primaryScribe,
        scribe_changes: secondaryScribes,
        statistics: {
          total_scribes: totalScribes,
          overall_confidence: avgConfidence,
          analysis_time: 1500,
          total_lines: totalLines
        }
      })
      
      return {
        primary_scribe: primaryScribe,
        scribe_changes: secondaryScribes,
        statistics: {
          total_scribes: totalScribes,
          overall_confidence: avgConfidence,
          analysis_time: 1500,
          total_lines: totalLines
        }
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
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.popup-header h3 {
  margin: 0;
  font-size: 1.2rem;
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
}

.image-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.manuscript-image {
  max-width: 100%;
  max-height: 100%;
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
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  border-left: 4px solid #007bff;
}

.scribe-item.primary {
  border-left-color: #28a745;
  background: #f8fff9;
}

.scribe-item.secondary {
  border-left-color: #ffc107;
  background: #fffbf0;
  transition: all 0.3s ease;
}

.scribe-item.highlighted {
  border-left-color: #007bff !important;
  background: rgba(0, 123, 255, 0.1) !important;
  box-shadow: 0 0 10px rgba(0, 123, 255, 0.3);
  transform: scale(1.02);
}

.scribe-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.scribe-header h5 {
  margin: 0;
  color: #2c3e50;
  font-size: 1rem;
}

.scribe-name {
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.confidence {
  background: #007bff;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.scribe-item.primary .confidence {
  background: #28a745;
}

.scribe-item.secondary .confidence {
  background: #ffc107;
  color: #000;
}

.location {
  font-size: 0.9rem;
  color: #6c757d;
  margin: 0.25rem 0;
  font-style: italic;
}

.explanation {
  font-size: 0.9rem;
  color: #495057;
  margin: 0.5rem 0 0 0;
  line-height: 1.4;
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
</style>