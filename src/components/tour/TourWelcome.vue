<script setup>
import { ref } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import Icon from '@/components/ui/icon/Icon.vue'
import { useTour } from '@/composables/useTour'

const emit = defineEmits(['start', 'skip'])

const { skipTour } = useTour()
const dontShowAgain = ref(false)

function handleStart() {
  emit('start')
}

function handleSkip() {
  if (dontShowAgain.value) {
    skipTour()
  }
  emit('skip')
}

function handleOpenChange(open) {
  if (!open) {
    handleSkip()
  }
}
</script>

<template>
  <Dialog :open="true" @update:open="handleOpenChange">
    <DialogContent class="tour-welcome sm:max-w-[440px]">
      <DialogHeader class="tour-welcome__header">
        <div class="tour-welcome__icon">
          <Icon name="graduation-cap" :size="32" />
        </div>
        <DialogTitle class="tour-welcome__title">Welcome to QuillApp!</DialogTitle>
        <DialogDescription class="tour-welcome__description">
          QuillApp helps you analyze and annotate manuscripts with powerful tools.
          Would you like a quick tour of the main features?
        </DialogDescription>
      </DialogHeader>

      <div class="tour-welcome__features">
        <div class="tour-welcome__feature">
          <Icon name="highlighter" :size="18" />
          <span>Highlight and underline text</span>
        </div>
        <div class="tour-welcome__feature">
          <Icon name="pencil" :size="18" />
          <span>Trace letterforms with customizable pen</span>
        </div>
        <div class="tour-welcome__feature">
          <Icon name="ruler" :size="18" />
          <span>Measure, calibrate, and resize dimensions</span>
        </div>
        <div class="tour-welcome__feature">
          <Icon name="sparkles" :size="18" />
          <span>AI-powered scribe detection</span>
        </div>
      </div>

      <DialogFooter class="tour-welcome__footer">
        <div class="tour-welcome__checkbox">
          <Checkbox id="dont-show" v-model:checked="dontShowAgain" />
          <label for="dont-show">Don't show this again</label>
        </div>

        <div class="tour-welcome__buttons">
          <Button variant="ghost" @click="handleSkip">
            Skip for now
          </Button>
          <Button @click="handleStart">
            <Icon name="play" :size="16" />
            Start Tour
          </Button>
        </div>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<style scoped>
.tour-welcome__header {
  text-align: center;
}

.tour-welcome__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  border-radius: 16px;
  background: hsl(var(--primary) / 0.1);
  color: hsl(var(--primary));
}

.tour-welcome__title {
  font-size: 20px;
  text-align: center;
}

.tour-welcome__description {
  text-align: center;
  margin-top: 8px;
}

.tour-welcome__features {
  display: grid;
  gap: 12px;
  margin: 20px 0;
  padding: 16px;
  border-radius: 8px;
  background: hsl(var(--muted));
}

.tour-welcome__feature {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: hsl(var(--foreground));
}

.tour-welcome__feature svg {
  color: hsl(var(--primary));
  flex-shrink: 0;
}

.tour-welcome__footer {
  flex-direction: column;
  gap: 16px;
}

.tour-welcome__checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: hsl(var(--muted-foreground));
}

.tour-welcome__buttons {
  display: flex;
  gap: 8px;
  width: 100%;
}

.tour-welcome__buttons > * {
  flex: 1;
}
</style>
