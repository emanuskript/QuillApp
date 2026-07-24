<script setup>
import { ref, computed, watch } from 'vue'
import { Button } from '@/components/ui/button'
import Icon from '@/components/ui/icon/Icon.vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { readJsonFile, validateJsonImport } from '@/services/annotationExportService'

const props = defineProps({
  open: { type: Boolean, default: false },
  hasExistingAnnotations: { type: Boolean, default: false },
  currentManifest: { type: String, default: '' },
  currentPageCount: { type: Number, default: 0 }
})

const emit = defineEmits(['update:open', 'import'])

const internalOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

const selectedFile = ref(null)
const parsedData = ref(null)
const error = ref(null)
const warning = ref(null)
const isDragging = ref(false)
const isImporting = ref(false)
const fileInput = ref(null)

// Reset state when dialog opens
watch(() => props.open, (open) => {
  if (open) {
    selectedFile.value = null
    parsedData.value = null
    error.value = null
    warning.value = null
    isDragging.value = false
    isImporting.value = false
  }
})

const showReplaceConfirm = computed(() => {
  return props.hasExistingAnnotations && parsedData.value && !error.value
})

async function processFile(file) {
  selectedFile.value = file
  error.value = null
  warning.value = null
  parsedData.value = null

  // Validate file type
  if (!file.name.endsWith('.json')) {
    error.value = 'Please select a JSON file (.json)'
    return
  }

  try {
    const data = await readJsonFile(file)
    const validation = validateJsonImport(data)

    if (!validation.valid) {
      error.value = validation.errors.join('. ')
      return
    }

    // Check for manifest mismatch
    if (props.currentManifest && data.metadata?.iiifManifest) {
      if (props.currentManifest !== data.metadata.iiifManifest) {
        warning.value = 'This file was exported from a different document. Annotations may not align correctly.'
      }
    }

    // Check for page count mismatch
    if (props.currentPageCount && data.metadata?.totalPages) {
      if (data.metadata.totalPages > props.currentPageCount) {
        warning.value = (warning.value ? warning.value + ' ' : '') +
          `Some annotations are for pages ${props.currentPageCount + 1}-${data.metadata.totalPages} which don't exist in this document.`
      }
    }

    parsedData.value = data
  } catch (err) {
    if (err.message.includes('too large')) {
      error.value = err.message
    } else {
      error.value = 'Invalid JSON file. Please select a valid Seshat export file.'
    }
  }
}

function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (file) {
    processFile(file)
  }
}

function handleDrop(event) {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) {
    processFile(file)
  }
}

function handleImport() {
  if (!parsedData.value) return

  isImporting.value = true

  // Small delay to show loading state
  setTimeout(() => {
    emit('import', parsedData.value)
    isImporting.value = false
    internalOpen.value = false
  }, 300)
}

function close() {
  internalOpen.value = false
}
</script>

<template>
  <Dialog v-model:open="internalOpen">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>Import Annotations</DialogTitle>
        <DialogDescription>
          Select a Seshat annotations file (.json) to restore your work.
        </DialogDescription>
      </DialogHeader>

      <!-- File Upload Area -->
      <div class="py-4">
        <div
          class="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
                 hover:border-primary hover:bg-primary/5 transition-colors"
          :class="{ 'border-primary bg-primary/5': isDragging }"
          @click="fileInput?.click()"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <input
            ref="fileInput"
            type="file"
            accept=".json,application/json"
            class="hidden"
            @change="handleFileSelect"
          />
          <Icon name="upload" :size="32" class="mx-auto mb-2 text-muted-foreground" />
          <p v-if="!selectedFile" class="text-sm text-muted-foreground">
            Drop file here or click to browse
          </p>
          <p v-else class="text-sm font-medium">
            {{ selectedFile.name }}
          </p>
        </div>

        <!-- Error Display -->
        <div v-if="error" class="mt-3 p-3 bg-destructive/10 text-destructive text-sm rounded-md">
          {{ error }}
        </div>

        <!-- Warning Display -->
        <div v-if="warning" class="mt-3 p-3 bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 text-sm rounded-md">
          {{ warning }}
        </div>

        <!-- Replace Confirmation -->
        <div v-if="showReplaceConfirm" class="mt-3 p-3 bg-muted rounded-md text-sm">
          <p class="font-medium">You have existing annotations.</p>
          <p class="text-muted-foreground">Importing will replace all current annotations.</p>
        </div>

        <!-- File Info -->
        <div v-if="parsedData && !error" class="mt-3 p-3 bg-muted/50 rounded-md text-sm space-y-1">
          <p><span class="font-medium">Document:</span> {{ parsedData.metadata?.documentName || 'Unknown' }}</p>
          <p><span class="font-medium">Exported:</span> {{ new Date(parsedData.exportedAt).toLocaleString() }}</p>
          <p><span class="font-medium">Version:</span> {{ parsedData.version }}</p>
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="close">Cancel</Button>
        <Button
          @click="handleImport"
          :disabled="!parsedData || !!error || isImporting"
        >
          <Icon v-if="isImporting" name="loader-2" :size="16" class="mr-2 animate-spin" />
          {{ showReplaceConfirm ? 'Replace & Import' : 'Import' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
