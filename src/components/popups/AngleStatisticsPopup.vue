<template>
  <div v-if="visible" class="statistics-popup">
    <div class="statistics-popup-content">
      <h3>Angle Statistics</h3>

      <table>
        <thead>
          <tr>
            <th>Average</th>
            <th>Standard Deviation</th>
            <th>Mode</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{{ fmt(stats.average) }}</td>
            <td>{{ fmt(stats.standardDeviation) }}</td>
            <td>
              {{
                typeof stats.mode === "number"
                  ? fmt(stats.mode)
                  : (stats.mode || "No mode")
              }}
            </td>
          </tr>
        </tbody>
      </table>

      <button @click="$emit('close')">Close</button>
    </div>
  </div>
</template>

<script>
export default {
  name: "AngleStatisticsPopup",
  props: {
    visible: { type: Boolean, default: false },
    stats: {
      type: Object,
      default: () => ({ average: 0, standardDeviation: 0, mode: "No mode" }),
    },
  },
  methods: {
    fmt(v) {
      const n = Number(v);
      return Number.isFinite(n) ? n.toFixed(2) : "0.00";
    },
  },
};
</script>

<style scoped>
.statistics-popup {
  position: fixed;
  inset: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1100;
}

.statistics-popup-content {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  max-width: 420px;
  width: 100%;
  font-family: "Arial", "Helvetica", sans-serif;
}

.statistics-popup-content table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.statistics-popup-content th,
.statistics-popup-content td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
}

.statistics-popup-content th {
  background-color: #f2f2f2;
}

.statistics-popup-content h3 {
  margin-bottom: 16px;
}

.statistics-popup-content button {
  margin-top: 8px;
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.statistics-popup-content button:hover {
  background-color: #0056b3;
}
</style>
