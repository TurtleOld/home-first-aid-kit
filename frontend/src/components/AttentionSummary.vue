<script setup>
import { computed, onMounted, reactive } from 'vue'
import { api } from '../api/client'

defineProps({
  activeStatus: {
    type: String,
    default: ''
  },
  activeLowStock: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['focus-status', 'focus-low-stock'])

const summary = reactive({
  expired: 0,
  expiringSoon: 0,
  lowStock: 0
})

const hasAttention = computed(
  () => summary.expired > 0 || summary.expiringSoon > 0 || summary.lowStock > 0
)

// Сводка считается по всей аптечке, без учёта текущих фильтров,
// чтобы показывать «требует внимания» независимо от того, что сейчас отфильтровано.
async function refresh() {
  try {
    const all = await api.get('/medicines')
    summary.expired = all.filter((item) => item.status === 'expired').length
    summary.expiringSoon = all.filter((item) => item.status === 'expiring_soon').length
    summary.lowStock = all.filter((item) => item.is_low_stock).length
  } catch {
    // Сводка необязательна — список лекарств покажет ошибку сам.
  }
}

onMounted(refresh)

defineExpose({ refresh })
</script>

<template>
  <div class="attention-summary" role="group" aria-label="Требует внимания">
    <template v-if="hasAttention">
      <button
        v-if="summary.expired"
        type="button"
        class="attention-card attention-card-danger"
        :class="{ 'attention-active': activeStatus === 'expired' }"
        @click="emit('focus-status', 'expired')"
      >
        <span class="attention-count">{{ summary.expired }}</span>
        <span class="attention-label">просрочено</span>
      </button>
      <button
        v-if="summary.expiringSoon"
        type="button"
        class="attention-card attention-card-warning"
        :class="{ 'attention-active': activeStatus === 'expiring_soon' }"
        @click="emit('focus-status', 'expiring_soon')"
      >
        <span class="attention-count">{{ summary.expiringSoon }}</span>
        <span class="attention-label">истекает</span>
      </button>
      <button
        v-if="summary.lowStock"
        type="button"
        class="attention-card attention-card-stock"
        :class="{ 'attention-active': activeLowStock }"
        @click="emit('focus-low-stock')"
      >
        <span class="attention-count">{{ summary.lowStock }}</span>
        <span class="attention-label">заканчивается</span>
      </button>
    </template>
    <p v-else class="attention-ok">Всё в порядке: ничего просроченного и заканчивающегося нет.</p>
  </div>
</template>
