<template>
  <!-- Compact, anchored panel (old layout restored) -->
  <aside class="bank">
    <header class="bank__header">
      <span class="bank__title">Annotations — Page {{ page + 1 }}</span>
    </header>

    <!-- Items -->
    <section class="bank__list" v-if="items && items.length">
      <div
        v-for="item in items"
        :key="item.key"
        class="bank__row"
        :class="{ 'bank__row--selected': selectedKeys.includes(item.key) }"
        @click="toggle(item.key)"
      >
        <!-- keep color as-is (old colors) -->
        <span
          v-if="item.color"
          class="bank__dot"
          :style="{ backgroundColor: item.color }"
          aria-hidden="true"
        />
        <div class="bank__text">
          <div class="bank__title-line">
            <span class="bank__row-title">{{ item.title }}</span>
            <span class="bank__badge" v-if="item.category">{{ pretty(item.category) }}</span>
          </div>
          <div class="bank__subtitle" v-if="item.subtitle">{{ item.subtitle }}</div>
        </div>
      </div>
    </section>

    <section v-else class="bank__empty">
      No annotations on this page.
    </section>

    <!-- Footer controls (Move / Delete back; Single/Multi kept, styled) -->
    <footer class="bank__footer">
      <button class="bank__btn" @click="$emit('toggle-multi')">
        {{ multiSelect ? 'Multi-select' : 'Single-select' }}
      </button>
      <button
        class="bank__btn bank__btn--primary"
        :disabled="!selectedKeys.length"
        @click="$emit('request-move')"
      >
        Move
      </button>
      <button
        class="bank__btn bank__btn--danger"
        :disabled="!selectedKeys.length"
        @click="$emit('request-delete')"
      >
        Delete
      </button>
    </footer>
  </aside>
</template>

<script>
export default {
  name: "AnnotationsBank",
  props: {
    page: { type: Number, required: true },
    items: { type: Array, default: () => [] },
    selectedKeys: { type: Array, default: () => [] },
    multiSelect: { type: Boolean, default: true },
    moveActive: { type: Boolean, default: false },
  },
  emits: ["update:selected", "toggle-multi", "request-move", "cancel-move", "request-delete"],
  methods: {
    toggle(key) {
      const set = new Set(this.selectedKeys);
      if (set.has(key)) {
        set.delete(key);
      } else {
        if (this.multiSelect) {
          set.add(key);
        } else {
          set.clear();
          set.add(key);
        }
      }
      this.$emit("update:selected", Array.from(set));
    },
    pretty(cat) {
      return String(cat)
        .replace(/_/g, " ")
        .replace(/(^|\s)\S/g, (m) => m.toUpperCase());
    },
  },
};
</script>

<style scoped>
/* Light blue theme + old compact layout feel */
:root{
  --panel-bg: rgba(241, 248, 255, 0.96); /* soft light blue */
  --panel-border: #cfe2ff;
  --panel-text: #0c2a53;

  --blue: #0d6efd;
  --blue-600:#0b5ed7;

  --danger:#dc3545;
  --danger-600:#bb2d3b;
}

/* anchored, compact */
.bank{
  position: fixed;
  right: 16px;
  bottom: 16px;
  width: 260px;
  max-height: 52vh;
  display: flex;
  flex-direction: column;
  background: var(--panel-bg);
  color: var(--panel-text);
  border: 1px solid var(--panel-border);
  border-radius: 12px;
  box-shadow: 0 10px 26px rgba(0,0,0,.18);
  overflow: hidden;
  z-index: 1500;
  font-size: 12px;
}

/* header (thin like old) */
.bank__header{
  padding: 8px 10px;
  border-bottom: 1px solid var(--panel-border);
  background: rgba(255,255,255,.9);
}
.bank__title{ font-weight: 600; }

/* list */
.bank__list{ overflow: auto; padding: 6px; }
.bank__row{
  display:flex; gap:8px; align-items:flex-start;
  padding:7px 8px; border-radius:10px; cursor:pointer; user-select:none;
}
.bank__row:hover{ background: rgba(13,110,253,.08); }
.bank__row--selected{
  outline: 2px solid rgba(13,110,253,.55);
  background: rgba(13,110,253,.12);
}
.bank__dot{
  width:10px; height:10px; border-radius:999px; margin-top:3px;
  border:1px solid rgba(0,0,0,.15); flex:none;
}
.bank__text{ flex:1; min-width:0; }
.bank__title-line{ display:flex; align-items:center; gap:6px; }
.bank__row-title{ font-weight:600; font-size:12px; line-height:1.15; }
.bank__badge{
  font-size:10px; background:#e7f1ff; border:1px solid #cfe2ff; color:#0a58ca;
  padding:2px 6px; border-radius:999px;
}
.bank__subtitle{
  font-size:11px; color:#2d496f; opacity:.9; margin-top:2px;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}

/* empty */
.bank__empty{ padding:16px 10px; color:#5a7aa9; text-align:center; }

/* footer (blue buttons like requested) */
.bank__footer{
  display:flex; gap:8px; padding:8px; border-top:1px solid var(--panel-border);
  background: rgba(255,255,255,.92);
}
.bank__btn{
  flex:1; appearance:none; border:1px solid #b6d1ff; background:#e7f1ff;
  color:#0a58ca; font-weight:600; padding:6px 8px; border-radius:8px; cursor:pointer;
}
.bank__btn:hover{ background:#d9e9ff; }
.bank__btn:disabled{ opacity:.5; cursor:not-allowed; }

.bank__btn--primary{
  background: #3b82f6; border-color: #3b82f6; color:#fff;
}
.bank__btn--primary:hover{ background: #2563eb; border-color: #2563eb; }

.bank__btn--danger{
  background: #dc2626; border-color: #dc2626; color:#fff;
}
.bank__btn--danger:hover{ background: #b91c1c; border-color: #b91c1c; }
</style>
