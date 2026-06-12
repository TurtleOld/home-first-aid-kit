<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import MediaImage from './MediaImage.vue'
import { compressImageFile } from '../utils/image'

const props = defineProps({
  existingUrl: {
    type: String,
    default: ''
  }
})

const file = defineModel('file', { type: [File, Object], default: null })
const removed = defineModel('removed', { type: Boolean, default: false })

const preview = ref('')

const existingPhotoUrl = computed(() => (removed.value ? '' : props.existingUrl))

async function onChange(event) {
  const selected = event.target.files?.[0] || null
  removed.value = false

  if (preview.value) {
    URL.revokeObjectURL(preview.value)
    preview.value = ''
  }

  if (!selected) {
    file.value = null
    return
  }

  file.value = await compressImageFile(selected)
  preview.value = URL.createObjectURL(file.value)
}

function clear() {
  file.value = null
  if (preview.value) {
    URL.revokeObjectURL(preview.value)
    preview.value = ''
  }
  if (existingPhotoUrl.value) {
    removed.value = true
  }
}

onBeforeUnmount(() => {
  if (preview.value) {
    URL.revokeObjectURL(preview.value)
  }
})
</script>

<template>
  <div class="photo-field">
    <img v-if="preview" class="photo-preview" :src="preview" alt="Фото лекарства" />
    <MediaImage
      v-else-if="existingPhotoUrl"
      class="photo-preview"
      :src="existingPhotoUrl"
      alt="Фото лекарства"
    />
    <div class="photo-controls">
      <input type="file" accept="image/*" @change="onChange" />
      <button v-if="preview || existingPhotoUrl" class="text-button" type="button" @click="clear">
        Убрать фото
      </button>
    </div>
  </div>
</template>
