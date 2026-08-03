<script setup>
import ToolButton from './ToolButton.vue'
import { TooltipProvider } from '@/components/ui/tooltip'

const props = defineProps({
  activeTool: { type: String, default: '' },
  hasActiveFilters: { type: Boolean, default: false },
  isOperationInProgress: { type: Boolean, default: false }
})

const emit = defineEmits([
  'select-tool',
  'toggle-adjustments',
  'open-horizontal',
  'open-vertical',
  'open-statistics',
  'start-crop'
])

const toolGroups = [
  {
    name: 'Navigate',
    tools: [
      { id: 'pan', icon: 'hand', label: 'Pan', shortcut: 'Space' }
    ]
  },
  {
    name: 'Annotate',
    tools: [
      { id: 'comment', icon: 'message-square', label: 'Comment', shortcut: 'C' },
      { id: 'highlight', icon: 'highlighter', label: 'Highlight', shortcut: 'H' },
      { id: 'underline', icon: 'underline', label: 'Underline', shortcut: 'U' },
      { id: 'trace', icon: 'pencil', label: 'Trace', shortcut: 'T' },
      { id: 'crop', icon: 'scissors', label: 'Crop', shortcut: '' }
    ]
  },
  {
    name: 'Measure',
    tools: [
      { id: 'measure', icon: 'chevron-up', label: 'Measure Angle', shortcut: 'A' },
      { id: 'distance', icon: 'ruler', label: 'Measure Distance', shortcut: 'D' },
      { id: 'horizontal', icon: 'move-horizontal', label: 'Horizontal Bands', shortcut: '' },
      { id: 'vertical', icon: 'move-vertical', label: 'Vertical Bands', shortcut: '' }
    ]
  },
  {
    name: 'Utility',
    tools: [
      { id: 'adjust', icon: 'sliders-horizontal', label: 'Image Adjustments', shortcut: '' },
      { id: 'stats', icon: 'calculator', label: 'Statistics', shortcut: '' }
    ]
  }
]

function handleToolClick(toolId) {
  if (props.isOperationInProgress) return

  switch (toolId) {
    case 'horizontal':
      emit('open-horizontal')
      break
    case 'vertical':
      emit('open-vertical')
      break
    case 'adjust':
      emit('toggle-adjustments')
      break
    case 'stats':
      emit('open-statistics')
      break
    case 'crop':
      emit('start-crop')
      break
    case 'pan':
      emit('select-tool', '')
      break
    default:
      emit('select-tool', toolId)
  }
}

function isToolActive(toolId) {
  if (toolId === 'pan') return props.activeTool === ''
  if (toolId === 'adjust') return props.hasActiveFilters
  return props.activeTool === toolId
}
</script>

<template>
  <TooltipProvider :delay-duration="300">
    <div class="flex flex-col items-center py-2 gap-1 h-full bg-card border-r border-border">
      <template v-for="(group, groupIndex) in toolGroups" :key="group.name">
        <div v-if="groupIndex > 0" class="w-8 h-px bg-border my-1" />

        <ToolButton
          v-for="tool in group.tools"
          :key="tool.id"
          :icon="tool.icon"
          :label="tool.label"
          :shortcut="tool.shortcut"
          :active="isToolActive(tool.id)"
          :disabled="isOperationInProgress && tool.id !== activeTool"
          :data-tour-tool="tool.id"
          @click="handleToolClick(tool.id)"
        />
      </template>
    </div>
  </TooltipProvider>
</template>
