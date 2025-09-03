import { reactive } from "vue";

export function useAnnotations(totalPagesProvider) {
  // annotationsByPage[page] = [{type: 'highlight'|'underline'|'trace'|'measure', ...}]
  const annotationsByPage = reactive([]);

  function ensurePages(n) {
    if (!n || n <= 0) return;
    while (annotationsByPage.length < n) annotationsByPage.push([]);
  }

  function add(page, entry) {
    ensurePages((totalPagesProvider && totalPagesProvider()) || 0);
    if (!annotationsByPage[page]) annotationsByPage[page] = [];
    annotationsByPage[page].push(entry);
  }

  function replaceAt(page, index, entry) {
    if (annotationsByPage[page] && annotationsByPage[page][index]) {
      annotationsByPage[page][index] = entry;
    }
  }

  function filterType(page, type) {
    if (annotationsByPage[page]) {
      annotationsByPage[page] = annotationsByPage[page].filter((a) => a.type !== type);
    }
  }

  function clearPage(page) {
    annotationsByPage[page] = [];
  }

  return {
    annotationsByPage,
    add,
    replaceAt,
    filterType,
    clearPage,
    ensurePages,
  };
}
