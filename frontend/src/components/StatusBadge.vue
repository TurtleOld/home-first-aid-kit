<script setup>
import { statusLabel } from '../constants/medicine'

defineProps({
  status: {
    type: String,
    required: true
  }
})
</script>

<template>
  <span class="status-badge" :data-status="status">
    <span class="status-dot" aria-hidden="true"></span>
    {{ statusLabel(status) }}
  </span>
</template>
