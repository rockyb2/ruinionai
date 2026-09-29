<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { LoaderCircle, Search, Users, X } from '@lucide/vue'
import { listMeetingInvitees } from '@/service/api'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
const search = ref('')
const members = ref([])
const total = ref(0)
const offset = ref(0)
const loading = ref(false)
const error = ref('')
const selectedIds = computed(() => new Set(props.modelValue.map(member => member.member_id)))
const limit = 20
let requestId = 0
let searchTimer

async function loadMembers(nextOffset = 0) {
  const id = ++requestId
  loading.value = true
  error.value = ''
  try {
    const result = await listMeetingInvitees({ q: search.value.trim(), offset: nextOffset, limit })
    if (id !== requestId) return
    members.value = result.items
    total.value = result.total
    offset.value = result.offset
  } catch (failure) {
    if (id === requestId) error.value = failure.message || 'Impossible de charger les membres.'
  } finally {
    if (id === requestId) loading.value = false
  }
}

function toggleMember(member) {
  if (props.disabled) return
  const selected = selectedIds.value.has(member.member_id)
  if (!selected && props.modelValue.length >= 100) return
  emit('update:modelValue', selected
    ? props.modelValue.filter(item => item.member_id !== member.member_id)
    : [...props.modelValue, member])
}

watch(search, () => {
  clearTimeout(searchTimer)
  ++requestId
  loading.value = true
  searchTimer = setTimeout(() => loadMembers(), 250)
})
onMounted(loadMembers)
onBeforeUnmount(() => { ++requestId; clearTimeout(searchTimer) })
</script>

<template>
  <fieldset class="mt-6 min-w-0" :disabled="disabled">
    <legend class="flex items-center gap-2 text-sm font-black text-slate-700">
      <Users class="h-4 w-4 text-blue-600" /> Inviter des membres de l’équipe
      <span class="font-semibold text-slate-400">(facultatif)</span>
    </legend>
    <p class="mt-2 text-xs leading-5 text-slate-500">Vous êtes l’organisateur. Sélectionnez les membres à inviter dans l’application.</p>

    <div v-if="modelValue.length" class="mt-3 flex flex-wrap gap-2" aria-label="Membres sélectionnés">
      <span v-for="member in modelValue" :key="member.member_id" class="inline-flex max-w-full items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-xs font-bold text-blue-700">
        <span class="truncate">{{ member.name }}</span>
        <button v-if="!disabled" type="button" :aria-label="`Retirer ${member.name}`" class="rounded p-0.5 hover:bg-blue-100 focus-visible:outline-2" @click="toggleMember(member)"><X class="h-3.5 w-3.5" /></button>
      </span>
    </div>

    <template v-if="!disabled">
      <label class="mt-3 flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2.5 focus-within:border-blue-500">
        <Search class="h-4 w-4 shrink-0 text-slate-400" />
        <input v-model="search" type="search" maxlength="100" aria-label="Rechercher un membre à inviter" placeholder="Rechercher un membre par nom ou e-mail…" class="min-w-0 w-full bg-transparent text-sm outline-none" />
      </label>
      <div v-if="loading" class="mt-3 flex items-center gap-2 py-4 text-sm text-slate-500" role="status"><LoaderCircle class="h-4 w-4 animate-spin" /> Chargement des membres…</div>
      <div v-else-if="error" class="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700" role="alert">
        {{ error }} <button type="button" class="ml-2 font-bold underline" @click="loadMembers()">Réessayer</button>
      </div>
      <div v-else-if="members.length" class="mt-3 max-h-56 overflow-y-auto rounded-lg border border-slate-200">
        <label v-for="member in members" :key="member.member_id" class="flex cursor-pointer items-center gap-3 border-b border-slate-100 px-3 py-3 last:border-0 hover:bg-blue-50" :class="selectedIds.has(member.member_id) ? 'bg-blue-50/70' : ''">
          <input type="checkbox" :checked="selectedIds.has(member.member_id)" :disabled="!selectedIds.has(member.member_id) && modelValue.length >= 100" :aria-label="`Inviter ${member.name}`" class="h-4 w-4 shrink-0 accent-blue-600" @change="toggleMember(member)" />
          <span class="min-w-0"><span class="block truncate text-sm font-bold text-slate-700">{{ member.name }}</span><span class="block truncate text-xs text-slate-500">{{ member.email }}</span></span>
        </label>
      </div>
      <p v-else class="mt-3 rounded-lg bg-slate-50 p-4 text-sm text-slate-500">{{ search ? 'Aucun membre ne correspond à votre recherche.' : 'Aucun autre membre actif dans votre équipe pour le moment.' }}</p>
      <div v-if="total > limit && !error" class="mt-3 flex items-center justify-between text-xs text-slate-500">
        <button type="button" class="rounded border px-2 py-1 disabled:opacity-40" :disabled="loading || offset === 0" @click="loadMembers(offset - limit)">Précédent</button>
        <span>{{ offset + 1 }}–{{ Math.min(offset + limit, total) }} sur {{ total }}</span>
        <button type="button" class="rounded border px-2 py-1 disabled:opacity-40" :disabled="loading || offset + limit >= total" @click="loadMembers(offset + limit)">Suivant</button>
      </div>
      <p class="mt-2 text-xs text-slate-500" aria-live="polite">{{ modelValue.length }} membre(s) sélectionné(s) · 100 maximum</p>
    </template>
  </fieldset>
</template>
