<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { adminList } from '../../service/admin'
const props = defineProps({ resource: String, modelValue: [Number, String], label: String, activeOnly: Boolean })
const emit = defineEmits(['update:modelValue'])
const query = ref(''), rows = ref([]), error = ref(''), loading = ref(false), total = ref(0)
let timer, sequence = 0
async function search() {
  const ticket = ++sequence
  loading.value = true
  error.value = ''
  try {
    const result = await adminList(props.resource, { q: query.value, limit: 20, ...(props.activeOnly ? { is_active: true } : {}) })
    if (ticket !== sequence) return
    rows.value = result.items
    total.value = result.total
  } catch (e) { if (ticket === sequence) error.value = e.message }
  finally { if (ticket === sequence) loading.value = false }
}
watch(query, () => { clearTimeout(timer); timer = setTimeout(search, 250) })
watch(() => props.resource, search, { immediate: true })
onBeforeUnmount(() => { clearTimeout(timer); sequence++ })
</script>
<template>
  <div class="a-field">
    <label>{{ label }} — rechercher<input v-model="query" type="search" :aria-label="`Rechercher : ${label}`" placeholder="Nom ou e-mail" /></label>
    <select :value="modelValue || ''" required :aria-label="label" @change="emit('update:modelValue', Number($event.target.value))">
      <option disabled value="">Sélectionner</option>
      <option v-if="modelValue && !rows.some(row => row.id === Number(modelValue))" :value="modelValue">Sélection #{{ modelValue }}</option>
      <option v-for="row in rows" :key="row.id" :value="row.id">{{ row.name }}{{ row.email ? ` · ${row.email}` : '' }}</option>
    </select>
    <small v-if="loading" role="status">Recherche…</small>
    <small v-else-if="total > rows.length">{{ total }} résultats : précisez votre recherche pour trouver le bon compte.</small>
    <small v-if="error" role="alert">{{ error }}</small>
  </div>
</template>
