<script setup>
import { computed } from 'vue'
import { REFERENCE_SECTION_LABELS } from '../constants/medicine'

const props = defineProps({
  referenceData: {
    type: Object,
    default: null
  }
})

const sections = computed(() => {
  if (!props.referenceData) {
    return []
  }

  return Object.entries(REFERENCE_SECTION_LABELS)
    .map(([key, label]) => ({ key, label, text: props.referenceData[key] }))
    .filter((section) => section.text)
})
</script>

<template>
  <details v-if="sections.length" class="reference-note">
    <summary>Инструкция из справочника ({{ sections.length }} разделов)</summary>
    <dl>
      <template v-for="section in sections" :key="section.key">
        <dt>{{ section.label }}</dt>
        <dd>{{ section.text }}</dd>
      </template>
    </dl>
  </details>
</template>
