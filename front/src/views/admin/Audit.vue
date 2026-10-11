<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import AdminBadge from '../../components/admin/AdminBadge.vue'
import AdminIcon from '../../components/admin/AdminIcon.vue'
import AdminModal from '../../components/admin/AdminModal.vue'
import AdminRemoteTable from '../../components/admin/AdminRemoteTable.vue'
import AdminStats from '../../components/admin/AdminStats.vue'
import { dateLabel } from '../../admin/format'
import { adminList } from '../../service/admin'

const rows = ref([])
const total = ref(0)
const offset = ref(0)
const limit = 20
const stats = ref({})
const loading = ref(false)
const error = ref('')
const actionFilter = ref('')
const actorFilter = ref('')
const selected = ref(null)
let timer

const actionLabels = {
  AUTH_REGISTER_SUCCESS: 'Inscription réussie',
  AUTH_LOGIN_SUCCESS: 'Connexion réussie',
  AUTH_LOGIN_FAILED: 'Échec de connexion',
  AUTH_LOGIN_BLOCKED: 'Connexion bloquée',
  AUTH_LOGIN_INACTIVE: 'Compte inactif',
  AUTH_LOGOUT_ALL_SESSIONS: 'Déconnexion de toutes les sessions',
  HTTP_POST: 'Création',
  HTTP_PUT: 'Remplacement',
  HTTP_PATCH: 'Modification',
  HTTP_DELETE: 'Suppression',
}

const targetLabels = {
  users: 'Utilisateur',
  user: 'Utilisateur',
  organizations: 'Organisation',
  organization: 'Organisation',
  meetings: 'Réunion',
  notifications: 'Notification',
  invitations: 'Invitation',
}

function actionName(value) {
  return actionLabels[value] || value?.replaceAll('_', ' ') || 'Action inconnue'
}

function actorName(row) {
  if (row.actor_name) return row.actor_name
  if (row.actor_email) return row.actor_email
  if (row.actor_id) return `Utilisateur #${row.actor_id}`
  return 'Système ou visiteur non identifié'
}

function targetName(row) {
  const type = targetLabels[row.target_type] || row.target_type || 'Ressource'
  return row.target_id ? `${type} #${row.target_id}` : type
}

function resultName(statusCode) {
  if (!statusCode) return 'Non renseigné'
  return statusCode >= 200 && statusCode < 400
    ? `Succès (${statusCode})`
    : `Échec (${statusCode})`
}

function hashLabel(value) {
  return value ? `${value.slice(0, 12)}…` : 'Non disponible'
}

function detailsLabel(value) {
  if (!value || !Object.keys(value).length) return 'Aucun détail supplémentaire'
  return Object.entries(value)
    .map(([key, item]) => `${key} : ${String(item)}`)
    .join(' · ')
}

const columns = [
  { key: 'created_at', label: 'Date et heure', format: dateLabel },
  { key: 'actor_name', label: 'Acteur', format: (_value, row) => actorName(row) },
  { key: 'action', label: 'Action', format: actionName },
  { key: 'target_type', label: 'Cible', format: (_value, row) => targetName(row) },
  { key: 'path', label: 'Route' },
  { key: 'status_code', label: 'Résultat', format: resultName },
]

const cards = computed(() => [
  { label: 'Actions auditées', value: stats.value.total || 0, icon: 'shield', color: 'purple', note: 'Événements enregistrés' },
  { label: 'Actions réussies', value: stats.value.successful || 0, icon: 'success', color: 'green', note: 'Réponses HTTP 2xx et 3xx' },
  { label: 'Actions en échec', value: stats.value.failed || 0, icon: 'alert', color: 'red', note: 'Réponses HTTP 4xx et 5xx' },
  { label: 'Authentification', value: stats.value.authentication || 0, icon: 'key', color: 'blue', note: 'Connexions et inscriptions' },
])

async function load() {
  loading.value = true
  error.value = ''
  try {
    const actorId = Number(actorFilter.value)
    const data = await adminList('audit', {
      action: actionFilter.value.trim(),
      actor_id: Number.isSafeInteger(actorId) && actorId > 0 ? actorId : '',
      offset: offset.value,
      limit,
    })
    rows.value = data.items
    total.value = data.total
    stats.value = data.stats || {}
  } catch (exception) {
    error.value = exception.message
  } finally {
    loading.value = false
  }
}

function scheduleLoad() {
  clearTimeout(timer)
  offset.value = 0
  timer = setTimeout(load, 250)
}

watch([actionFilter, actorFilter], scheduleLoad)
onMounted(load)
</script>

<template>
  <div class="a-stack">
    <div class="a-toolbar">
      <div>
        <strong>Journal d’audit de la plateforme</strong>
        <p class="a-muted">Actions de sécurité et d’administration réellement enregistrées</p>
      </div>
      <button class="a-button" :disabled="loading" @click="load">
        <AdminIcon name="refresh" />Actualiser
      </button>
    </div>

    <p v-if="error" class="a-card a-panel a-danger-text" role="alert">{{ error }}</p>
    <AdminStats :items="cards" />

    <div class="a-filters a-card">
      <label class="a-search">
        <AdminIcon name="search" />
        <input v-model="actionFilter" type="search" placeholder="Action exacte, ex. AUTH_LOGIN_SUCCESS" />
      </label>
      <label class="a-field">
        <span>Identifiant de l’acteur</span>
        <input v-model="actorFilter" type="number" min="1" placeholder="Tous" />
      </label>
    </div>

    <AdminRemoteTable
      :rows="rows"
      :columns="columns"
      :total="total"
      :offset="offset"
      :limit="limit"
      :loading="loading"
      :selected-id="selected?.id"
      @page="value => { offset = value; load() }"
      @select="id => { selected = rows.find(row => row.id === id) || null }"
    />

    <p class="a-muted">
      L’adresse IP n’est jamais affichée ni stockée en clair. Seule son empreinte HMAC permet de rapprocher des événements issus de la même adresse.
    </p>

    <AdminModal
      :open="!!selected"
      :title="`Événement d’audit #${selected?.id || ''}`"
      hint="Métadonnées techniques enregistrées sans le contenu des requêtes."
      @close="selected = null"
    >
      <dl v-if="selected" class="a-definition">
        <dt>Date</dt><dd>{{ dateLabel(selected.created_at) }}</dd>
        <dt>Acteur</dt><dd>{{ actorName(selected) }}<small v-if="selected.actor_email" style="display:block">{{ selected.actor_email }}</small></dd>
        <dt>Action</dt><dd>{{ actionName(selected.action) }}<small style="display:block">{{ selected.action }}</small></dd>
        <dt>Cible</dt><dd>{{ targetName(selected) }}</dd>
        <dt>Requête</dt><dd>{{ selected.method || '—' }} {{ selected.path || 'Route non renseignée' }}</dd>
        <dt>Résultat</dt><dd><AdminBadge :value="resultName(selected.status_code)" :color="selected.status_code >= 200 && selected.status_code < 400 ? 'green' : 'red'" /></dd>
        <dt>Empreinte IP</dt><dd><code>{{ hashLabel(selected.ip_hash) }}</code></dd>
        <dt>Détails</dt><dd>{{ detailsLabel(selected.details) }}</dd>
      </dl>
    </AdminModal>
  </div>
</template>
