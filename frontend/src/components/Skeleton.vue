<script setup>
defineProps({
  width: { type: String, default: '100%' },
  height: { type: String, default: '1em' },
  radius: { type: String, default: '6px' }
})
</script>

<template>
  <span
    class="skeleton"
    :style="{ width, height, borderRadius: radius }"
    aria-hidden="true"
  ></span>
</template>
