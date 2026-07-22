import { ref, reactive, computed } from 'vue'

const DEFAULT_FILTERS = {
  brightness: 0,      // -100 to 100 (0 = normal)
  contrast: 1,        // 0 to 3 (1 = normal)
  saturation: 1,      // 0 to 3 (1 = normal)
  invert: false,
  grayscale: false,
  threshold: null,    // null = off, 0-255 = threshold value
  sharpen: false,     // Sharpen filter toggle
  edgeDetect: false   // Edge detection toggle
}

// Per-page filter storage (shared across all component instances)
const filtersByPage = reactive({})

// Current page tracker (shared across all component instances)
const currentPage = ref(0)

/**
 * Composable for managing per-page image adjustments
 * Filters are stored per page and persist during the session
 */
export function useImageAdjustments() {
  // Get filters for current page (with defaults)
  const currentFilters = computed(() => {
    return filtersByPage[currentPage.value] || { ...DEFAULT_FILTERS }
  })

  // Check if any filters are active on current page
  const hasActiveFilters = computed(() => {
    const f = currentFilters.value
    return f.brightness !== 0 ||
           f.contrast !== 1 ||
           f.saturation !== 1 ||
           f.invert ||
           f.grayscale ||
           f.threshold !== null ||
           f.sharpen ||
           f.edgeDetect
  })

  // Set a specific filter value for current page
  const setFilter = (key, value) => {
    if (!filtersByPage[currentPage.value]) {
      filtersByPage[currentPage.value] = { ...DEFAULT_FILTERS }
    }
    filtersByPage[currentPage.value][key] = value
  }

  // Get filters for a specific page
  const getFiltersForPage = (page) => {
    return filtersByPage[page] || { ...DEFAULT_FILTERS }
  }

  const getAllFilters = () => {
    return Object.entries(filtersByPage).reduce((all, [page, filters]) => {
      all[page] = { ...DEFAULT_FILTERS, ...filters }
      return all
    }, {})
  }

  // Reset all filters for current page
  const resetFilters = () => {
    filtersByPage[currentPage.value] = { ...DEFAULT_FILTERS }
  }

  // Reset all filters for all pages
  const resetAllFilters = () => {
    Object.keys(filtersByPage).forEach(key => delete filtersByPage[key])
  }

  const replaceAllFilters = (nextFiltersByPage = {}) => {
    resetAllFilters()
    Object.entries(nextFiltersByPage || {}).forEach(([page, filters]) => {
      if (filters && typeof filters === 'object') {
        filtersByPage[page] = { ...DEFAULT_FILTERS, ...filters }
      }
    })
  }

  // Copy filters from current page to another page
  const copyFiltersToPage = (targetPage) => {
    filtersByPage[targetPage] = { ...currentFilters.value }
  }

  // Apply current page's filters to all pages
  const applyToAllPages = (totalPages) => {
    const currentSettings = { ...currentFilters.value }
    for (let i = 0; i < totalPages; i++) {
      filtersByPage[i] = { ...currentSettings }
    }
  }

  // Set current page (call this when page changes)
  const setCurrentPage = (page) => {
    currentPage.value = page
  }

  // Get current page number
  const getCurrentPage = () => currentPage.value

  return {
    currentFilters,
    hasActiveFilters,
    setFilter,
    getFiltersForPage,
    getAllFilters,
    resetFilters,
    resetAllFilters,
    replaceAllFilters,
    copyFiltersToPage,
    applyToAllPages,
    setCurrentPage,
    getCurrentPage,
    DEFAULT_FILTERS
  }
}
