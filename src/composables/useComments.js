import { reactive } from "vue";

export function useComments(totalPagesProvider) {
  // comments[page] = [{text, x, y}]
  const comments = reactive([]);

  function ensurePages(n) {
    if (!n || n <= 0) return;
    while (comments.length < n) comments.push([]);
  }

  function add(page, comment) {
    ensurePages((totalPagesProvider && totalPagesProvider()) || 0);
    if (!comments[page]) comments[page] = [];
    comments[page].push(comment);
  }

  function clear(page) {
    comments[page] = [];
  }

  return { comments, add, clear, ensurePages };
}
