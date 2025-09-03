<template>
  <div class="comments-layer">
    <!-- Existing comments -->
    <div
      v-for="(comment, index) in comments"
      :key="'comment-' + index"
      class="comment-container"
      :style="{ top: comment.y + 'px', left: comment.x + 'px' }"
      @mousedown="onCommentMouseDown(index, $event)"
      @mouseup="onCommentMouseUp"
      @mousemove="onCommentMouseMove"
    >
      <div class="comment-icon">💬</div>
      <div class="comment-bubble">
        <div class="comment-content">{{ comment.text }}</div>
      </div>
    </div>

    <!-- New comment input box -->
    <div v-if="showInput" class="comment-input-container">
      <textarea
        class="comment-input-box"
        v-model="localText"
        placeholder="Add your comment..."
      ></textarea>
      <div class="comment-input-actions">
        <button class="btn-save-comment" @click="addComment">Add</button>
        <button class="btn-cancel-comment" @click="cancelComment">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "CommentsLayer",
  props: {
    comments: {
      type: Array,
      required: true,
      default: () => [],
    },
    showInput: {
      type: Boolean,
      required: true,
      default: false,
    },
    // draft is still provided by the parent but we won't mutate it directly
    draft: {
      type: Object,
      required: true,
      default: () => ({ text: "", x: 0, y: 0 }),
    },
  },
  emits: ["add", "cancel", "drag-start", "drag-move", "drag-stop"],
  data() {
    return {
      localText: this.draft?.text || "",
    };
  },
  watch: {
    // keep localText in sync if parent replaces draft
    draft: {
      deep: true,
      immediate: false,
      handler(v) {
        this.localText = (v && v.text) || "";
      },
    },
  },
  methods: {
    addComment() {
      const payload = {
        ...(this.draft || { x: 0, y: 0 }),
        text: this.localText || "",
      };
      this.$emit("add", payload);
      this.localText = "";
    },
    cancelComment() {
      this.localText = this.draft?.text || "";
      this.$emit("cancel");
    },
    onCommentMouseDown(index, event) {
      this.$emit("drag-start", { index, event });
    },
    onCommentMouseMove(event) {
      this.$emit("drag-move", event);
    },
    onCommentMouseUp() {
      this.$emit("drag-stop");
    },
  },
};
</script>

<style scoped>
.comments-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.comment-container {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: grab;
  z-index: 10;
}
.comment-container:active {
  cursor: grabbing;
}

.comment-icon {
  font-size: 24px;
  background-color: #ffecb3;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.comment-bubble {
  margin-left: 8px;
  padding: 8px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
}
.comment-bubble::after {
  content: "";
  position: absolute;
  top: 50%;
  left: -8px;
  width: 0;
  height: 0;
  border: 8px solid transparent;
  border-right-color: #fff;
  transform: translateY(-50%);
}

.comment-content {
  font-size: 14px;
  color: #333;
}

.comment-input-container {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #fff;
  border: 1px solid #ccc;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 10px;
  width: 300px;
  z-index: 1000;
}

.comment-input-box {
  width: 100%;
  height: 60px;
  border: 1px solid #ccc;
  border-radius: 5px;
  padding: 8px;
  font-size: 14px;
  margin-bottom: 8px;
  resize: none;
}

.comment-input-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-save-comment,
.btn-cancel-comment {
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 5px 10px;
  font-size: 14px;
  cursor: pointer;
}

.btn-cancel-comment {
  background-color: #6c757d;
  margin-left: 10px;
}

.btn-save-comment:hover {
  background-color: #0056b3;
}

.btn-cancel-comment:hover {
  background-color: #5a6268;
}
</style>
