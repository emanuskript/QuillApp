<template>
  <div class="navigation-bar">
    <button
      :disabled="currentPage <= 0"
      @click="$emit('prev')"
      aria-label="Previous page"
      class="nav-btn"
    >
      ⬅️ Prev
    </button>

    <div class="page-input-container">
      <label for="pageInput">Page:</label>
      <input
        id="pageInput"
        type="number"
        v-model.number="localPageInput"
        :max="totalPages"
        :min="1"
        @blur="emitGoTo"
        @keyup.enter="emitGoTo"
        aria-label="Go to page"
      />
      <span>/ {{ totalPages }}</span>
    </div>

    <button
      :disabled="currentPage >= totalPages - 1"
      @click="$emit('next')"
      aria-label="Next page"
      class="nav-btn"
    >
      Next ➡️
    </button>
  </div>
</template>

<script>
export default {
  name: "NavigationBar",
  props: {
    currentPage: { type: Number, required: true }, // 0-based
    totalPages: { type: Number, required: true },
    pageInput: { type: Number, required: true }, // 1-based
  },
  emits: ["prev", "next", "go-to"],
  data() {
    return {
      localPageInput: this.pageInput, // keep a local model for the input
    };
  },
  watch: {
    // keep input in sync if parent changes page externally
    pageInput(newVal) {
      this.localPageInput = newVal;
    },
  },
  methods: {
    emitGoTo() {
      // clamp to [1, totalPages], parent will convert to 0-based
      const clamped = Math.max(1, Math.min(this.localPageInput || 1, this.totalPages || 1));
      this.localPageInput = clamped;
      this.$emit("go-to", clamped);
    },
  },
};
</script>

<style scoped>
.navigation-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 10px 0;
  gap: 10px;
  font-family: "Arial", "Helvetica", sans-serif;
}

.page-input-container {
  display: flex;
  align-items: center;
  gap: 5px;
}

.page-input-container input {
  width: 60px;
  text-align: center;
  padding: 6px 8px;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: #fff;
  outline: none;
}

.page-input-container input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.15);
}

.nav-btn {
  background-color: #f1f1f1;
  color: #333;
  border: 1px solid #ddd;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease, border 0.15s ease;
}

.nav-btn:hover:not(:disabled) {
  background-color: #e9f3ff;
  color: #007bff;
  border-color: #b6daff;
}

.nav-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
