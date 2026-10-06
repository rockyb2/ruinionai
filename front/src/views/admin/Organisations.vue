<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminDetail from '../../components/admin/AdminDetail.vue'
import AdminIcon from '../../components/admin/AdminIcon.vue'
import AdminLookup from '../../components/admin/AdminLookup.vue'
import AdminModal from '../../components/admin/AdminModal.vue'
import AdminPanel from '../../components/admin/AdminPanel.vue'
import AdminRemoteTable from '../../components/admin/AdminRemoteTable.vue'
import AdminStats from '../../components/admin/AdminStats.vue'
import { adminList, adminRequest } from '../../service/admin'
import { audioDuration, dateLabel, roleName } from '../../admin/format'

const route = useRoute(), router = useRouter()
const rows = ref([]), total = ref(0), offset = ref(0), limit = 20, stats = ref({}), loading = ref(false)
const query = ref(''), error = ref(''), message = ref(''), selected = ref(null), members = ref([]), meetings = ref([])
const modal = ref(false), editing = ref(false), memberModal = ref(false)
const form = ref({ name: '', description: '', owner_user_id: '' })
const memberForm = ref({ user_id: '', role: 'member', status: 'active' })
let timer
const columns = [
  { key: 'name', label: 'Organisation' }, { key: 'members_count', label: 'Membres' },
  { key: 'meetings_count', label: 'Réunions' }, { key: 'audio_seconds', label: 'Audio', format: audioDuration },
  { key: 'created_at', label: 'Créée le', format: dateLabel },
]
const cards = computed(() => [
  { label: 'Organisations', value: stats.value.organizations || 0, icon: 'building', color: 'purple', note: 'En base de données' },
  { label: 'Membres', value: stats.value.members || 0, icon: 'users', color: 'green', note: 'Toutes organisations' },
  { label: 'Réunions', value: stats.value.meetings || 0, icon: 'video', color: 'blue', note: 'Toutes organisations' },
  { label: 'Heures audio', value: Math.round((stats.value.audio_seconds || 0) / 3600), icon: 'audio', color: 'orange', note: 'Durée réellement mesurée' },
])

async function load() {
  loading.value = true; error.value = ''
  try {
    const data = await adminList('organizations', { q: query.value, offset: offset.value, limit })
    rows.value = data.items; total.value = data.total; stats.value = data.stats
    const requested = Number(route.query.id)
    if (requested && requested !== selected.value?.id) await select(requested)
  } catch (e) { error.value = e.message }
  finally { loading.value = false }
}
async function select(id) {
  error.value = ''
  try {
    const [org, memberPage, meetingPage] = await Promise.all([
      adminRequest(`/organizations/${id}`), adminRequest(`/organizations/${id}/members?limit=100`),
      adminList('meetings', { organization_id: id, limit: 10 }),
    ])
    selected.value = org; members.value = memberPage.items; meetings.value = meetingPage.items
    router.replace({ query: { ...route.query, id } })
  } catch (e) { error.value = e.message }
}
function closeDetail() { selected.value = null; members.value = []; meetings.value = []; router.replace({ query: {} }) }
function openCreate() { editing.value = false; form.value = { name: '', description: '', owner_user_id: '' }; modal.value = true }
function openEdit() { editing.value = true; form.value = { name: selected.value.name, description: selected.value.description }; modal.value = true }
async function save() {
  error.value = ''
  try {
    const path = editing.value ? `/organizations/${selected.value.id}` : '/organizations'
    const data = await adminRequest(path, { method: editing.value ? 'PATCH' : 'POST', body: form.value })
    modal.value = false; message.value = editing.value ? 'Organisation modifiée.' : 'Organisation créée.'
    await load(); await select(data.id)
  } catch (e) { error.value = e.message }
}
async function remove() {
  if (!confirm(`Supprimer « ${selected.value.name} » ? Cette action exige que ses réunions aient déjà été supprimées.`)) return
  try { await adminRequest(`/organizations/${selected.value.id}`, { method: 'DELETE' }); closeDetail(); message.value = 'Organisation supprimée.'; await load() }
  catch (e) { error.value = e.message }
}
async function saveMember() {
  try {
    await adminRequest(`/organizations/${selected.value.id}/members/${memberForm.value.user_id}`, { method: 'PUT', body: memberForm.value })
    memberModal.value = false; await select(selected.value.id); message.value = 'Membre enregistré.'
  } catch (e) { error.value = e.message }
}
async function removeMember(member) {
  if (!confirm(`Retirer ${member.name || member.email} de cette organisation ?`)) return
  try { await adminRequest(`/organizations/${selected.value.id}/members/${member.user_id}`, { method: 'DELETE' }); await select(selected.value.id) }
  catch (e) { error.value = e.message }
}
watch(query, () => { clearTimeout(timer); offset.value = 0; timer = setTimeout(load, 250) })
onMounted(load)
</script>

<template>
  <div class="a-stack">
    <div class="a-toolbar"><div><strong>Gestion réelle des organisations</strong><p class="a-muted">Données actuelles de la plateforme</p></div><button class="a-button a-button-primary" @click="openCreate"><AdminIcon name="plus" />Nouvelle organisation</button></div>
    <p v-if="error" class="a-card a-panel a-danger-text" role="alert">{{ error }}</p><p v-if="message" class="a-card a-panel a-success-text" role="status">{{ message }}</p>
    <AdminStats :items="cards" />
    <div class="a-split" :class="{ 'a-no-detail': !selected }">
      <div class="a-stack"><label class="a-search a-card"><AdminIcon name="search" /><input v-model="query" type="search" placeholder="Rechercher une organisation…" /></label>
        <AdminRemoteTable :rows="rows" :columns="columns" :total="total" :offset="offset" :limit="limit" :loading="loading" :selected-id="selected?.id" @page="value => { offset = value; load() }" @select="select" /></div>
      <AdminDetail v-if="selected" :title="selected.name" :subtitle="selected.description || 'Sans description'" status="Organisation" @close="closeDetail">
        <AdminPanel title="Informations générales"><dl class="a-definition"><dt>Nom</dt><dd>{{ selected.name }}</dd><dt>Description</dt><dd>{{ selected.description || 'Non renseignée' }}</dd><dt>Créée le</dt><dd>{{ dateLabel(selected.created_at) }}</dd><dt>Expiration des invitations</dt><dd>{{ selected.invitation_expiration_days }} jours</dd></dl></AdminPanel>
        <AdminPanel title="Membres"><template #action><button class="a-link" @click="memberForm = { user_id: '', role: 'member', status: 'active' }; memberModal = true">Ajouter</button></template><div class="a-list"><div v-for="member in members" :key="member.id" class="a-list-item"><div><strong>{{ member.name || member.email }}</strong><small>{{ member.email }} · {{ roleName(member.role) }}</small></div><button class="a-link a-danger-text" @click="removeMember(member)">Retirer</button></div><p v-if="!members.length" class="a-muted">Aucun membre.</p></div></AdminPanel>
        <AdminPanel title="Dernières réunions"><div class="a-list"><RouterLink v-for="meeting in meetings" :key="meeting.id" :to="`/admin/reunions?id=${meeting.id}`" class="a-list-item"><AdminIcon name="video" /><div>{{ meeting.title }}<small>{{ dateLabel(meeting.date) }}</small></div></RouterLink><p v-if="!meetings.length" class="a-muted">Aucune réunion.</p></div></AdminPanel>
        <template #footer><button class="a-button a-button-danger" @click="remove"><AdminIcon name="trash" />Supprimer</button><button class="a-button a-button-primary" @click="openEdit"><AdminIcon name="edit" />Modifier</button></template>
      </AdminDetail>
    </div>
    <AdminModal :open="modal" :title="editing ? 'Modifier l’organisation' : 'Nouvelle organisation'" hint="Les données seront enregistrées dans la base." @close="modal = false"><form class="a-form" @submit.prevent="save"><label class="a-field">Nom<input v-model="form.name" required maxlength="150" /></label><label class="a-field">Description<textarea v-model="form.description" maxlength="500" /></label><AdminLookup v-if="!editing" v-model="form.owner_user_id" resource="users" label="Propriétaire initial" active-only /><div class="a-form-footer"><button type="button" class="a-button" @click="modal = false">Annuler</button><button class="a-button a-button-primary">Enregistrer</button></div></form></AdminModal>
    <AdminModal :open="memberModal" title="Ajouter ou modifier un membre" hint="Un compte existant sera rattaché à l’organisation." @close="memberModal = false"><form class="a-form" @submit.prevent="saveMember"><AdminLookup v-model="memberForm.user_id" resource="users" label="Utilisateur" active-only /><label class="a-field">Rôle<select v-model="memberForm.role"><option value="member">Membre</option><option value="admin">Administrateur</option><option value="owner">Propriétaire</option></select></label><label class="a-field">Statut<select v-model="memberForm.status"><option value="active">Actif</option><option value="inactive">Inactif</option></select></label><div class="a-form-footer"><button type="button" class="a-button" @click="memberModal = false">Annuler</button><button class="a-button a-button-primary">Enregistrer</button></div></form></AdminModal>
  </div>
</template>
