<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminDetail from '../../components/admin/AdminDetail.vue'
import AdminIcon from '../../components/admin/AdminIcon.vue'
import AdminModal from '../../components/admin/AdminModal.vue'
import AdminPanel from '../../components/admin/AdminPanel.vue'
import AdminRemoteTable from '../../components/admin/AdminRemoteTable.vue'
import AdminStats from '../../components/admin/AdminStats.vue'
import { adminList, adminRequest } from '../../service/admin'
import { dateLabel, roleName } from '../../admin/format'

const route = useRoute(), router = useRouter()
const rows = ref([]), total = ref(0), offset = ref(0), limit = 20, stats = ref({}), loading = ref(false)
const query = ref(''), activeFilter = ref(''), error = ref(''), message = ref(''), selected = ref(null)
const modal = ref(false), editing = ref(false), passwordModal = ref(false)
const form = ref({ first_name: '', last_name: '', email: '', password: '' }), password = ref('')
let timer
const columns = [
  { key: 'name', label: 'Utilisateur' }, { key: 'email', label: 'E-mail' },
  { key: 'memberships', label: 'Organisations', format: value => value.length },
  { key: 'meetings_count', label: 'Réunions créées' },
  { key: 'is_active', label: 'Statut', format: value => value ? 'Actif' : 'Inactif' },
  { key: 'created_at', label: 'Créé le', format: dateLabel },
]
const cards = computed(() => [
  { label: 'Utilisateurs', value: stats.value.total || 0, icon: 'users', color: 'green', note: 'Comptes enregistrés' },
  { label: 'Actifs', value: stats.value.active || 0, icon: 'success', color: 'blue', note: 'Accès autorisé' },
  { label: 'Inactifs', value: stats.value.inactive || 0, icon: 'clock', color: 'orange', note: 'Accès bloqué' },
  { label: 'Super administrateurs', value: stats.value.super_admins || 0, icon: 'shield', color: 'purple', note: 'Accès plateforme' },
])
async function load() {
  loading.value = true; error.value = ''
  try {
    const data = await adminList('users', { q: query.value, offset: offset.value, limit, is_active: activeFilter.value })
    rows.value = data.items; total.value = data.total; stats.value = data.stats
    const requested = Number(route.query.id); if (requested && requested !== selected.value?.id) await select(requested)
  } catch (e) { error.value = e.message } finally { loading.value = false }
}
async function select(id) {
  try { selected.value = await adminRequest(`/users/${id}`); router.replace({ query: { ...route.query, id } }) }
  catch (e) { error.value = e.message }
}
function closeDetail() { selected.value = null; router.replace({ query: {} }) }
function openCreate() { editing.value = false; form.value = { first_name: '', last_name: '', email: '', password: '' }; modal.value = true }
function openEdit() { editing.value = true; form.value = { first_name: selected.value.first_name, last_name: selected.value.last_name, email: selected.value.email }; modal.value = true }
async function save() {
  try {
    const result = await adminRequest(editing.value ? `/users/${selected.value.id}` : '/users', { method: editing.value ? 'PATCH' : 'POST', body: form.value })
    modal.value = false; message.value = editing.value ? 'Utilisateur modifié.' : 'Utilisateur créé.'; await load(); await select(result.id)
  } catch (e) { error.value = e.message }
}
async function toggleActive() {
  try { selected.value = await adminRequest(`/users/${selected.value.id}`, { method: 'PATCH', body: { is_active: !selected.value.is_active } }); await load(); message.value = selected.value.is_active ? 'Compte réactivé.' : 'Compte désactivé.' }
  catch (e) { error.value = e.message }
}
async function resetPassword() {
  try { await adminRequest(`/users/${selected.value.id}/password`, { method: 'POST', body: { password: password.value } }); passwordModal.value = false; password.value = ''; message.value = 'Mot de passe remplacé.' }
  catch (e) { error.value = e.message }
}
async function remove() {
  if (!confirm(`Supprimer le compte de ${selected.value.name || selected.value.email} ?`)) return
  try { await adminRequest(`/users/${selected.value.id}`, { method: 'DELETE' }); closeDetail(); await load(); message.value = 'Compte supprimé.' }
  catch (e) { error.value = e.message }
}
watch([query, activeFilter], () => { clearTimeout(timer); offset.value = 0; timer = setTimeout(load, 250) })
onMounted(load)
</script>

<template>
  <div class="a-stack">
    <div class="a-toolbar"><div><strong>Comptes de la plateforme</strong><p class="a-muted">Les rôles d’équipe se gèrent depuis chaque organisation</p></div><button class="a-button a-button-primary" @click="openCreate"><AdminIcon name="plus" />Nouvel utilisateur</button></div>
    <p v-if="error" class="a-card a-panel a-danger-text" role="alert">{{ error }}</p><p v-if="message" class="a-card a-panel a-success-text" role="status">{{ message }}</p>
    <AdminStats :items="cards" />
    <div class="a-split" :class="{ 'a-no-detail': !selected }"><div class="a-stack"><div class="a-filters a-card"><label class="a-search"><AdminIcon name="search" /><input v-model="query" type="search" placeholder="Nom ou e-mail…" /></label><label class="a-field"><span>Statut</span><select v-model="activeFilter"><option value="">Tous</option><option value="true">Actifs</option><option value="false">Inactifs</option></select></label></div><AdminRemoteTable :rows="rows" :columns="columns" :total="total" :offset="offset" :limit="limit" :loading="loading" :selected-id="selected?.id" @page="value => { offset = value; load() }" @select="select" /></div>
      <AdminDetail v-if="selected" :title="selected.name || selected.email" :subtitle="selected.email" :status="selected.is_active ? 'Actif' : 'Inactif'" @close="closeDetail">
        <AdminPanel title="Informations personnelles"><dl class="a-definition"><dt>Prénom</dt><dd>{{ selected.first_name }}</dd><dt>Nom</dt><dd>{{ selected.last_name }}</dd><dt>E-mail</dt><dd>{{ selected.email }}</dd><dt>Créé le</dt><dd>{{ dateLabel(selected.created_at) }}</dd><dt>Réunions créées</dt><dd>{{ selected.meetings_count }}</dd><dt>Accès plateforme</dt><dd>{{ selected.is_super_admin ? 'Super administrateur' : 'Utilisateur' }}</dd></dl></AdminPanel>
        <AdminPanel title="Organisations et rôles"><div class="a-list"><RouterLink v-for="membership in selected.memberships" :key="membership.id" :to="`/admin/organisations?id=${membership.organization_id}`" class="a-list-item"><AdminIcon name="building" /><div><strong>{{ membership.organization_name }}</strong><small>{{ roleName(membership.role) }} · {{ membership.status === 'active' ? 'Actif' : 'Inactif' }}</small></div></RouterLink><p v-if="!selected.memberships.length" class="a-muted">Ce compte n’appartient à aucune organisation.</p></div></AdminPanel>
        <template #footer><button class="a-button a-button-danger" @click="remove"><AdminIcon name="trash" />Supprimer</button><button class="a-button" @click="toggleActive">{{ selected.is_active ? 'Désactiver' : 'Réactiver' }}</button><button class="a-button" @click="password = ''; passwordModal = true"><AdminIcon name="key" />Mot de passe</button><button class="a-button a-button-primary" @click="openEdit"><AdminIcon name="edit" />Modifier</button></template>
      </AdminDetail></div>
    <AdminModal :open="modal" :title="editing ? 'Modifier l’utilisateur' : 'Nouvel utilisateur'" hint="Le compte sera enregistré dans la base." @close="modal = false"><form class="a-form" @submit.prevent="save"><label class="a-field">Prénom<input v-model="form.first_name" required maxlength="150" /></label><label class="a-field">Nom<input v-model="form.last_name" required maxlength="150" /></label><label class="a-field">E-mail<input v-model="form.email" type="email" required /></label><label v-if="!editing" class="a-field">Mot de passe temporaire<input v-model="form.password" type="password" required minlength="8" maxlength="72" /></label><div class="a-form-footer"><button type="button" class="a-button" @click="modal = false">Annuler</button><button class="a-button a-button-primary">Enregistrer</button></div></form></AdminModal>
    <AdminModal :open="passwordModal" title="Remplacer le mot de passe" hint="L’utilisateur devra employer ce nouveau mot de passe à sa prochaine connexion." @close="passwordModal = false"><form class="a-form" @submit.prevent="resetPassword"><label class="a-field">Nouveau mot de passe<input v-model="password" type="password" required minlength="8" maxlength="72" autocomplete="new-password" /></label><div class="a-form-footer"><button type="button" class="a-button" @click="passwordModal = false">Annuler</button><button class="a-button a-button-primary">Enregistrer</button></div></form></AdminModal>
  </div>
</template>
