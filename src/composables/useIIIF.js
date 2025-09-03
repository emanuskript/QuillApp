import { fetchIIIFImages } from "@/services/iiifService";
import { ref } from "vue";

export function useIIIF() {
  const loading = ref(false);
  const error = ref("");

  async function loadManifest(url) {
    loading.value = true; error.value = "";
    try {
      const urls = await fetchIIIFImages(url);
      return urls;
    } catch (e) {
      error.value = e?.message || "Failed to fetch IIIF manifest.";
      return [];
    } finally {
      loading.value = false;
    }
  }

  return { loading, error, loadManifest };
}
