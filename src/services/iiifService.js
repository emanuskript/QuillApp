/**
 * Minimal IIIF manifest parser (v2 + v3 tolerant)
 * Returns an array of image URLs (full size).
 */
export async function fetchIIIFImages(manifestUrl) {
  const res = await fetch(manifestUrl);
  if (!res.ok) throw new Error(`Failed to fetch IIIF manifest: ${res.status}`);
  const manifest = await res.json();

  // v2: sequences[0].canvases[*].images[0].resource.service['@id']/full/full/0/default.jpg
  const canvasesV2 = manifest?.sequences?.[0]?.canvases;
  if (Array.isArray(canvasesV2) && canvasesV2.length) {
    const urls = canvasesV2
      .map((c) => c?.images?.[0]?.resource?.service?.["@id"])
      .filter(Boolean)
      .map((id) => `${id}/full/full/0/default.jpg`);
    if (urls.length) return urls;
  }

  // v3: items[*].items[0].body.service[0].id or items[*].items[0].body.service.id
  const canvasesV3 = manifest?.items;
  if (Array.isArray(canvasesV3) && canvasesV3.length) {
    const urls = canvasesV3
      .map((canvas) => {
        const annoPage = canvas?.items?.[0];
        const anno = annoPage?.items?.[0];
        const body = anno?.body;
        const service = Array.isArray(body?.service) ? body.service[0] : body?.service;
        const id = service?.["@id"] || service?.id;
        return id ? `${id}/full/full/0/default.jpg` : null;
      })
      .filter(Boolean);
    if (urls.length) return urls;
  }

  // Fallback: try any painting body with id that looks like an image
  const fallback = canvasesV3?.map((canvas) => {
    const annoPage = canvas?.items?.[0];
    const anno = annoPage?.items?.[0];
    const body = anno?.body;
    const id = body?.id;
    return id || null;
  }).filter(Boolean);

  return fallback && fallback.length ? fallback : [];
}
