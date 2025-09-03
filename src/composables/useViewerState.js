import { reactive, computed, ref } from "vue";

export function useViewerState() {
  const images = ref([]);               // string[]
  const currentPage = ref(0);
  const pageInput = ref(1);
  const scalingFactor = ref(1);

  const totalPages = computed(() => images.value.length);
  const currentImage = computed(() => images.value[currentPage.value] || null);

  function setImages(arr) {
    images.value = Array.isArray(arr) ? arr : [];
    currentPage.value = 0;
    pageInput.value = 1;
  }

  function setScalingFromImage(imgEl) {
    if (!imgEl) return;
    const displayed = imgEl.width;
    const natural = imgEl.naturalWidth || displayed || 1;
    scalingFactor.value = displayed / natural;
  }

  function goToPage(n) {
    const idx = Math.max(0, Math.min(n, totalPages.value - 1));
    currentPage.value = idx;
    pageInput.value = idx + 1;
  }

  function nextPage() {
    if (currentPage.value < totalPages.value - 1) goToPage(currentPage.value + 1);
  }
  function prevPage() {
    if (currentPage.value > 0) goToPage(currentPage.value - 1);
  }

  return {
    images, currentPage, pageInput, totalPages, currentImage, scalingFactor,
    setImages, setScalingFromImage, goToPage, nextPage, prevPage,
  };
}
