<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { api } from '../api/client'

const props = defineProps({
  src: { type: String, default: '' },
  alt: { type: String, default: '' }
})

const objectUrl = ref('')

function revoke() {
  if (objectUrl.value) {
    URL.revokeObjectURL(objectUrl.value)
    objectUrl.value = ''
  }
}

async function load(url) {
  revoke()
  if (!url) {
    return
  }

  try {
    const blob = await api.getBlob(url)
    objectUrl.value = URL.createObjectURL(blob)
  } catch {
    objectUrl.value = ''
  }
}

watch(() => props.src, load, { immediate: true })
onBeforeUnmount(revoke)
</script>

<template>
  <img v-if="objectUrl" :src="objectUrl" :alt="alt" loading="lazy" />
</template>
