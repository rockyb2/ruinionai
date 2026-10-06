<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminDetail from '../../components/admin/AdminDetail.vue'
import AdminIcon from '../../components/admin/AdminIcon.vue'
import AdminLookup from '../../components/admin/AdminLookup.vue'
import AdminModal from '../../components/admin/AdminModal.vue'
import AdminPanel from '../../components/admin/AdminPanel.vue'
import AdminRemoteTable from '../../components/admin/AdminRemoteTable.vue'
import AdminStats from '../../components/admin/AdminStats.vue'
import { activeMeeting, audioDuration, dateLabel, stateName } from '../../admin/format'
import { adminFile, adminList, adminRequest } from '../../service/admin'

const route = useRoute(), router = useRouter()
const rows = ref([]), total = ref(0), offset = ref(0), limit = 20, stats = ref({}), loading = ref(false)
const query = ref(''), status = ref(''), error = ref(''), message = ref(''), selected = ref(null), tab = ref('Vue d’ensemble')
const modal = ref(false), editing = ref(false), form = ref({ organization_id: '', title: '', transcription: '' })
const audioUrl = ref('')
let timer
const columns = [
  { key: 'title', label: 'Réunion' }, { key: 'organization_name', label: 'Organisation' },
  { key: 'created_by_name', label: 'Créée par' }, { key: 'date', label: 'Date', format: dateLabel },
  { key: 'audio_duration', label: 'Durée', format: audioDuration },
  { key: 'processing_status', label: 'Traitement', format: stateName },
]
const cards = computed(() => [
  { label: 'Réunions', value: stats.value.total || 0, icon: 'video', color: 'blue', note: 'En base de données' },
  { label: 'Heures audio', value: Math.round((stats.value.audio_seconds || 0) / 3600), icon: 'clock', color: 'orange', note: 'Durée réellement mesurée' },
  { label: 'Terminées', value: stats.value.completed || 0, icon: 'success', color: 'green', note: 'Pipeline terminé' },
  { label: 'Échecs', value: stats.value.failed || 0, icon: 'failure', color: 'red', note: 'À examiner ou relancer' },
])
async function load() {
  loading.value = true; error.value = ''
  try {
    const data = await adminList('meetings', { q: query.value, status: status.value, offset: offset.value, limit })
    rows.value = data.items; total.value = data.total; stats.value = data.stats
    const requested = Number(route.query.id); if (requested && requested !== selected.value?.id) await select(requested)
  } catch (e) { error.value = e.message } finally { loading.value = false }
}
function clearAudio() { if (audioUrl.value) URL.revokeObjectURL(audioUrl.value); audioUrl.value = '' }
async function select(id) {
  clearAudio(); error.value = ''
  try {
    selected.value = await adminRequest(`/meetings/${id}`); tab.value = 'Vue d’ensemble'; router.replace({ query: { ...route.query, id } })
    if (selected.value.audio_available) {
      try { audioUrl.value = URL.createObjectURL(await adminFile(id, 'audio')) } catch (e) { error.value = e.message }
    }
  } catch (e) { error.value = e.message }
}
function closeDetail() { clearAudio(); selected.value = null; router.replace({ query: {} }) }
function openCreate() { editing.value = false; form.value = { organization_id: '', title: '', transcription: '' }; modal.value = true }
function openEdit() { editing.value = true; form.value = { title: selected.value.title, date: selected.value.date?.slice(0, 16) }; modal.value = true }
async function save() {
  try {
    const body = { ...form.value }; if (body.date) body.date = new Date(body.date).toISOString()
    const result = await adminRequest(editing.value ? `/meetings/${selected.value.id}` : '/meetings', { method: editing.value ? 'PATCH' : 'POST', body })
    modal.value = false; message.value = editing.value ? 'Réunion modifiée.' : 'Réunion créée.'; await load(); await select(result.id)
  } catch (e) { error.value = e.message }
}
async function retry() {
  try { selected.value = await adminRequest(`/meetings/${selected.value.id}/summary`, { method: 'POST' }); message.value = 'Traitement placé en attente.'; await load() }
  catch (e) { error.value = e.message }
}
async function downloadReport() {
  try { const blob = await adminFile(selected.value.id, 'report'); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `compte-rendu-${selected.value.id}.docx`; a.click(); URL.revokeObjectURL(url) }
  catch (e) { error.value = e.message }
}
async function remove() {
  if (!confirm(`Supprimer définitivement la réunion « ${selected.value.title} » et ses fichiers ?`)) return
  try { await adminRequest(`/meetings/${selected.value.id}`, { method: 'DELETE' }); closeDetail(); await load(); message.value = 'Réunion et fichiers associés supprimés.' }
  catch (e) { error.value = e.message }
}
watch([query, status], () => { clearTimeout(timer); offset.value = 0; timer = setTimeout(load, 250) })
onMounted(load); onBeforeUnmount(clearAudio)
</script>

<template>
  <div class="a-stack">
    <div class="a-toolbar"><div><strong>Réunions de toute la plateforme</strong><p class="a-muted">Transcriptions, résumés, documents et état du traitement</p></div><button class="a-button a-button-primary" @click="openCreate"><AdminIcon name="plus" />Nouvelle réunion</button></div>
    <p v-if="error" class="a-card a-panel a-danger-text" role="alert">{{ error }}</p><p v-if="message" class="a-card a-panel a-success-text" role="status">{{ message }}</p>
    <AdminStats :items="cards" />
    <div class="a-split" :class="{ 'a-no-detail': !selected }"><div class="a-stack"><div class="a-filters a-card"><label class="a-search"><AdminIcon name="search" /><input v-model="query" type="search" placeholder="Titre ou organisation…" /></label><label class="a-field"><span>Traitement</span><select v-model="status"><option value="">Tous</option><option value="queued">En attente</option><option value="transcribing">Transcription</option><option value="writing">Rédaction</option><option value="building">Création du Word</option><option value="completed">Terminées</option><option value="failed">Échecs</option></select></label></div><AdminRemoteTable :rows="rows" :columns="columns" :total="total" :offset="offset" :limit="limit" :loading="loading" :selected-id="selected?.id" @page="value => { offset = value; load() }" @select="select" /></div>
      <AdminDetail v-if="selected" v-model="tab" :title="selected.title" :subtitle="`${selected.organization_name} · ${dateLabel(selected.date)}`" :status="stateName(selected.processing_status)" :tabs="['Vue d’ensemble', 'Transcription', 'Résumé']" @close="closeDetail">
        <AdminPanel v-if="tab === 'Vue d’ensemble'" title="Informations"><dl class="a-definition"><dt>Organisation</dt><dd><RouterLink :to="`/admin/organisations?id=${selected.organization_id}`">{{ selected.organization_name }}</RouterLink></dd><dt>Créée par</dt><dd>{{ selected.created_by_name }}</dd><dt>Date</dt><dd>{{ dateLabel(selected.date) }}</dd><dt>Durée audio</dt><dd>{{ audioDuration(selected.audio_duration) }}</dd><dt>Participants</dt><dd>{{ selected.participants || 'Non renseignés' }}</dd></dl><audio v-if="audioUrl" class="a-spaced" style="width:100%" :src="audioUrl" controls preload="metadata" /><p v-if="selected.processing_error" class="a-danger-text a-spaced">{{ selected.processing_error }}</p></AdminPanel>
        <AdminPanel v-else-if="tab === 'Transcription'" title="Transcription complète"><p class="a-transcript-text">{{ selected.transcription || 'La transcription n’est pas encore disponible.' }}</p></AdminPanel>
        <AdminPanel v-else title="Résultats"><h3>Résumé court</h3><p>{{ selected.summary_short || 'Non disponible.' }}</p><div class="a-divider" /><h3>Compte rendu détaillé</h3><p class="a-transcript-text">{{ selected.summary_long || 'Non disponible.' }}</p></AdminPanel>
        <template #footer><button class="a-button a-button-danger" :disabled="activeMeeting(selected)" @click="remove"><AdminIcon name="trash" />Supprimer</button><button class="a-button" :disabled="activeMeeting(selected)" @click="openEdit"><AdminIcon name="edit" />Modifier</button><button class="a-button" :disabled="activeMeeting(selected) || !selected.has_source_audio" @click="retry"><AdminIcon name="refresh" />Relancer</button><button class="a-button a-button-primary" :disabled="!selected.has_report" @click="downloadReport"><AdminIcon name="download" />Word</button></template>
      </AdminDetail></div>
    <AdminModal :open="modal" :title="editing ? 'Modifier la réunion' : 'Nouvelle réunion'" hint="La création administrative peut partir d’une transcription existante. L’import audio reste disponible dans l’espace réunion." @close="modal = false"><form class="a-form" @submit.prevent="save"><AdminLookup v-if="!editing" v-model="form.organization_id" resource="organizations" label="Organisation" /><label class="a-field">Titre<input v-model="form.title" required maxlength="250" /></label><label v-if="editing" class="a-field">Date<input v-model="form.date" type="datetime-local" /></label><label v-else class="a-field">Transcription existante (facultatif)<textarea v-model="form.transcription" rows="8" maxlength="500000" /></label><div class="a-form-footer"><button type="button" class="a-button" @click="modal = false">Annuler</button><button class="a-button a-button-primary">Enregistrer</button></div></form></AdminModal>
  </div>
</template>

<style scoped>.a-transcript-text { white-space: pre-wrap; line-height: 1.7; max-height: 52vh; overflow: auto; }</style>
