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
  background: #e7f0ff;           /* match top bar */
  border-bottom: 1px solid #c9d8ff;
  padding: 6px 0;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 5px 0;
  gap: 8px;
  font-family: "Arial", "Helvetica", sans-serif;
  font-size: 13px;
}

.navigation-bar > * {
  margin-top: 8px;
}

.page-input-container {
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-input-container input {
  width: 45px;
  text-align: center;
  padding: 4px 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
  outline: none;
  font-size: 12px;
}

.page-input-container input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 1px rgba(0, 123, 255, 0.15);
}

.nav-btn {
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  border: none;
  background: #3b82f6;  /* blue */
  color: #fff;
  box-shadow: 0 1px 0 rgba(0,0,0,0.06);
}
.nav-btn:hover { background: #2f6fe0; }
.nav-btn:disabled {
  background: #9fbdfd;
  cursor: not-allowed;
}
</style>
