import { captureElementToPng, pngsToPdf, withHidden } from "@/services/exportService";

/**
 * Save current annotations into a multi-page PDF by capturing the viewer element per page.
 * This mirrors existing behavior but is abstracted into a composable-friendly API.
 */
export function useExport() {
  async function saveAnnotatedPdf(viewEl, pages, goToPage, getSkipPredicate = () => false) {
    // hide toolbar/navigation if they exist in DOM (optional – resilient)
    const topBar = document.querySelector(".top-bar");
    const navBar = document.querySelector(".navigation-bar");
    const restore = withHidden([topBar, navBar], "none");

    try {
      const shots = [];
      for (let i = 0; i < pages; i++) {
        goToPage(i);
        // allow DOM to update
        // eslint-disable-next-line no-await-in-loop
        await new Promise((r) => setTimeout(r, 50));

        if (getSkipPredicate(i)) continue;
        // eslint-disable-next-line no-await-in-loop
        const dataUrl = await captureElementToPng(viewEl, {
          ignoreElements: (el) =>
            el.classList?.contains("top-bar") ||
            el.classList?.contains("navigation-bar"),
        });
        shots.push(dataUrl);
      }
      const blob = await pngsToPdf(shots);
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "annotated-document.pdf";
      link.click();
      URL.revokeObjectURL(link.href);
    } finally {
      restore();
    }
  }

  return { saveAnnotatedPdf };
}
