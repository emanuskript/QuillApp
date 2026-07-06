<template>
  <Dialog :open="visible" @update:open="handleOpenChange">
    <DialogContent class="sm:max-w-xl" @keydown.esc="$emit('close')">
      <DialogHeader>
        <DialogTitle>Statistics</DialogTitle>
        <DialogDescription>
          Measurement statistics for horizontal and vertical lengths.
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-6 py-4">
        <!-- Horizontal Lengths -->
        <div>
          <h4 class="section-title">Horizontal Lengths</h4>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Measurement</TableHead>
                <TableHead class="text-right">Average</TableHead>
                <TableHead class="text-right">Std Dev</TableHead>
                <TableHead class="text-right">Mode</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="(stats, type) in horizontal" :key="type">
                <TableCell class="font-medium">{{ formatType(type) }}</TableCell>
                <TableCell class="text-right">{{ stats.average.toFixed(2) }}</TableCell>
                <TableCell class="text-right">{{ stats.standardDeviation.toFixed(2) }}</TableCell>
                <TableCell class="text-right">
                  {{ typeof stats.mode === "number" ? stats.mode.toFixed(2) : stats.mode }}
                </TableCell>
              </TableRow>
              <TableRow v-if="!hasHorizontalData">
                <TableCell colspan="4" class="text-center text-muted-foreground">
                  No horizontal measurements yet
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <!-- Vertical Lengths -->
        <div>
          <h4 class="section-title">Vertical Lengths</h4>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Measurement</TableHead>
                <TableHead class="text-right">Average</TableHead>
                <TableHead class="text-right">Std Dev</TableHead>
                <TableHead class="text-right">Mode</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="(stats, type) in vertical" :key="type">
                <TableCell class="font-medium">{{ formatType(type) }}</TableCell>
                <TableCell class="text-right">{{ stats.average.toFixed(2) }}</TableCell>
                <TableCell class="text-right">{{ stats.standardDeviation.toFixed(2) }}</TableCell>
                <TableCell class="text-right">
                  {{ typeof stats.mode === "number" ? stats.mode.toFixed(2) : stats.mode }}
                </TableCell>
              </TableRow>
              <TableRow v-if="!hasVerticalData">
                <TableCell colspan="4" class="text-center text-muted-foreground">
                  No vertical measurements yet
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>

      <DialogFooter>
        <Button @click="$emit('close')">Close</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script>
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export default {
  name: "StatisticsPopup",
  components: {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    Button,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
  },
  props: {
    visible: { type: Boolean, default: false },
    horizontal: { type: Object, default: () => ({}) },
    vertical: { type: Object, default: () => ({}) },
  },
  emits: ['close'],
  computed: {
    hasHorizontalData() {
      return Object.keys(this.horizontal || {}).length > 0;
    },
    hasVerticalData() {
      return Object.keys(this.vertical || {}).length > 0;
    },
  },
  methods: {
    formatType(type) {
      const map = {
        ascenders: "Ascenders",
        descenders: "Descenders",
        interlinear: "Interlinear",
        upperMargin: "Upper Margin",
        lowerMargin: "Lower Margin",
        lineHeight: "Line Height",
        minimumHeight: "Minim",
        internalMargin: "Internal Margin",
        intercolumnSpaces: "Intercolumn Spaces",
      };
      return map[type] || type;
    },
    handleOpenChange(open) {
      if (!open) {
        this.$emit('close');
      }
    },
  },
};
</script>

<style scoped>
.section-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: hsl(var(--foreground));
  margin-bottom: 0.5rem;
}
</style>
