import { computed, onBeforeUnmount, reactive, watch } from 'vue'

const SEARCH_DEBOUNCE_MS = 350

export function useMedicineFilters(loadMedicines) {
  const filters = reactive({
    search: '',
    status: '',
    storage: '',
    lowStock: false
  })

  const hasFilters = computed(() =>
    Boolean(filters.search || filters.status || filters.storage || filters.lowStock)
  )

  let searchDebounce = null
  watch(
    () => filters.search,
    () => {
      clearTimeout(searchDebounce)
      searchDebounce = setTimeout(loadMedicines, SEARCH_DEBOUNCE_MS)
    }
  )
  onBeforeUnmount(() => clearTimeout(searchDebounce))

  function toggleFilter(name, value) {
    filters[name] = filters[name] === value ? '' : value
    loadMedicines()
  }

  function toggleLowStockFilter() {
    filters.lowStock = !filters.lowStock
    loadMedicines()
  }

  function focusStatus(value) {
    filters.lowStock = false
    toggleFilter('status', value)
  }

  function focusLowStock() {
    filters.status = ''
    toggleLowStockFilter()
  }

  function resetFilters() {
    filters.search = ''
    filters.status = ''
    filters.storage = ''
    filters.lowStock = false
    loadMedicines()
  }

  return {
    filters,
    hasFilters,
    toggleFilter,
    toggleLowStockFilter,
    focusStatus,
    focusLowStock,
    resetFilters
  }
}
