import { PDFDocument } from "pdf-lib";
import html2canvas from "html2canvas";

/**
 * Capture a DOM element into a PNG data URL (uses html2canvas).
 * @param {HTMLElement} el
 * @param {object} [opts]
 * @returns {Promise<string>} dataURL
 */
export async function captureElementToPng(el, opts = {}) {
  const canvas = await html2canvas(el, {
    scale: 2,
    useCORS: true,
    logging: false,
    ...opts,
  });
  return canvas.toDataURL("image/png");
}

/**
 * Export an array of PNG data URLs into a single PDF
 * @param {string[]} pngDataUrls
 * @returns {Promise<Blob>}
 */
export async function pngsToPdf(pngDataUrls) {
  const pdf = await PDFDocument.create();
  for (const dataUrl of pngDataUrls) {
    const png = await pdf.embedPng(dataUrl);
    const page = pdf.addPage([png.width, png.height]);
    page.drawImage(png, { x: 0, y: 0, width: png.width, height: png.height });
  }
  const bytes = await pdf.save();
  return new Blob([bytes], { type: "application/pdf" });
}

/**
 * Hide elements temporarily during capture.
 * @param {HTMLElement[]} elements
 * @param {string} display
 */
export function withHidden(elements = [], display = "none") {
  const prev = elements.map((el) => el?.style?.display ?? "");
  elements.forEach((el) => { if (el) el.style.display = display; });
  return () => elements.forEach((el, i) => { if (el) el.style.display = prev[i]; });
}
