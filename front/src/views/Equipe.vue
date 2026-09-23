<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  ChevronLeft, ChevronRight, Copy, Info, LoaderCircle, Mail,
  MoreHorizontal, RefreshCw, Search, Send, ShieldCheck, Users, X,
} from '@lucide/vue'
import {
  createOrganizationInvitation, getCurrentUser, getOrganizationSettings,
  listOrganizationInvitations, listOrganizationsMembers,
  renewOrganizationInvitation, revokeOrganizationInvitation,
  updateOrganizationMemberRole, updateOrganizationMemberStatus,
} from '@/service/api'

const router = useRouter()
const route = useRoute()
const activeTab = ref('members')
const search = ref('')
const email = ref('')
const invitedRole = ref('member')
const session = ref(null)
const organizationSettings = ref(null)
const initialLoading = ref(true)
const sessionError = ref('')
const listLoading = ref(false)
const listError = ref('')
const saving = ref(false)
const formError = ref('')
const actionError = ref('')
const notice = ref('')
const createdInvitation = ref(null)
const copyMessage = ref('')
const invitationField = ref(null)
const actionDialog = ref(null)
const actionTarget = ref(null)
const actionTab = ref('members')
const selectedRole = ref('member')
const now = ref(Date.now())
const pageSize = 25
const lists = reactive({
  members: { items: [], total: 0, offset: 0, loaded: false },
  invitations: { items: [], total: 0, offset: 0, loaded: false },
})
let requestId = 0
let alive = true
let clock

const tabs = [
  { id: 'members', label: 'Membres', icon: Users },
  { id: 'invitations', label: 'Invitations', icon: Mail },
]
const roleLabels = { owner: 'Propriétaire', admin: 'Admin', member: 'Membre' }
const statusLabels = {
  active: 'Actif', inactive: 'Inactif', pending: 'En attente',
  accepted: 'Acceptée', expired: 'Expirée', revoked: 'Révoquée', declined: 'Refusée',
}
const canManage = computed(() => ['owner', 'admin'].includes(session.value?.role))
const canInvite = computed(() =>
  session.value?.role === 'owner' ||
  (session.value?.role === 'admin' && organizationSettings.value?.allow_admin_invitations),
)
const invitationDuration = computed(() =>
  organizationSettings.value?.invitation_expiration_days || 7,
)
const isOwner = computed(() => session.value?.role === 'owner')
const isMembers = computed(() => activeTab.value === 'members')
const currentList = computed(() => lists[activeTab.value])
const currentRows = computed(() => currentList.value.items)
const filteredRows = computed(() => {
  const query = search.value.trim().toLocaleLowerCase('fr')
  return currentRows.value.filter((row) =>
    [row.name, row.email].filter(Boolean).join(' ').toLocaleLowerCase('fr').includes(query),
  )
})
const busy = computed(() => saving.value || listLoading.value || initialLoading.value)
const pageNumber = computed(() => Math.floor(currentList.value.offset / pageSize) + 1)
const pageCount = computed(() => Math.max(1, Math.ceil(currentList.value.total / pageSize)))
const invitationLink = computed(() => {
  if (!createdInvitation.value) return ''
  const path = router.resolve({ name: 'invitation' }).href
  return new URL(path, window.location.origin).href + '#token=' +
    encodeURIComponent(createdInvitation.value.token)
})

function timestamp(value) {
  if (!value) return NaN
  const normalized = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : value + 'Z'
  return Date.parse(normalized)
}

function formatDate(value) {
  const time = timestamp(value)
  if (!Number.isFinite(time)) return '—'
  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric', month: 'short', year: 'numeric',
  }).format(new Date(time))
}

function rowStatus(row) {
  if (row.status !== 'pending') return row.status
  return row.is_expired || timestamp(row.expires_at) <= now.value ? 'expired' : 'pending'
}

function normalizeMember(member) {
  const name = [member.user?.first_name, member.user?.last_name].filter(Boolean).join(' ').trim()
  return { ...member, name: name || member.user?.email || 'Utilisateur', email: member.user?.email || '' }
}

function initials(row) {
  const words = row.name?.split(/\s+/).filter(Boolean)
  return words?.length
    ? words.map((word) => word[0]).slice(0, 2).join('').toUpperCase()
    : (row.email?.slice(0, 2).toUpperCase() || '?')
}

function editableMember(row) {
  return canManage.value && row && row.role !== 'owner' && row.user_id !== session.value?.user.id
}

function canChangeRole(row) {
  return isOwner.value && editableMember(row)
}

function canChangeStatus(row) {
  return editableMember(row) && (isOwner.value || row.role === 'member')
}

function canRevoke(row) {
  return canManage.value && row && rowStatus(row) === 'pending' &&
    (isOwner.value || row.role === 'member')
}

function canRenew(row) {
  return canInvite.value && row && row.status === 'pending' &&
    rowStatus(row) === 'expired' && (isOwner.value || row.role === 'member')
}

function hasActions(row) {
  return isMembers.value
    ? canChangeRole(row) || canChangeStatus(row)
    : canRevoke(row) || canRenew(row)
}

function errorText(error, fallback) {
  if (error.status === 401) {
    createdInvitation.value = null
    session.value = null
    router.replace({ name: 'login', query: { redirect: route.fullPath } })
    return 'Votre session a expiré. Veuillez vous reconnecter.'
  }
  return error.status ? (error.message || fallback) : 'Connexion impossible. Réessayez dans un instant.'
}

async function loadList(kind = activeTab.value, offset = lists[kind].offset) {
  const id = ++requestId
  listLoading.value = true
  listError.value = ''
  try {
    const fetchPage = kind === 'members' ? listOrganizationsMembers : listOrganizationInvitations
    const response = await fetchPage({ offset, limit: pageSize })
    if (!alive || id !== requestId) return
    if (offset > 0 && response.items.length === 0 && response.total < offset + 1) {
      return await loadList(kind, Math.max(0, Math.ceil(response.total / pageSize) - 1) * pageSize)
    }
    Object.assign(lists[kind], {
      items: kind === 'members' ? response.items.map(normalizeMember) : response.items,
      total: response.total, offset: response.offset, loaded: true,
    })
  } catch (error) {
    if (alive && id === requestId) listError.value = errorText(error, 'Impossible de charger cette liste.')
  } finally {
    if (alive && id === requestId) listLoading.value = false
  }
}

async function initialize() {
  if (saving.value) return
  initialLoading.value = true
  sessionError.value = ''
  try {
    const current = await getCurrentUser()
    if (!alive) return
    session.value = current
    if (!isOwner.value) invitedRole.value = 'member'
    if (canManage.value) {
      organizationSettings.value = await getOrganizationSettings()
      await loadList()
    }
    else {
      lists.members.items = []
      lists.invitations.items = []
      createdInvitation.value = null
    }
  } catch (error) {
    if (alive) sessionError.value = errorText(error, 'Impossible de vérifier vos accès.')
  } finally {
    if (alive) initialLoading.value = false
  }
}

async function changeTab(id) {
  if (saving.value || activeTab.value === id) return
  activeTab.value = id
  search.value = ''
  await loadList(id)
}

async function changePage(delta) {
  if (busy.value) return
  search.value = ''
  await loadList(activeTab.value, Math.max(0, currentList.value.offset + delta * pageSize))
}

async function submitInvitation() {
  if (busy.value || !canInvite.value || !email.value.trim()) return
  saving.value = true
  formError.value = ''
  notice.value = ''
  try {
    const result = await createOrganizationInvitation({
      email: email.value.trim(),
      role: isOwner.value ? invitedRole.value : 'member',
    })
    if (!alive) return
    createdInvitation.value = result
    copyMessage.value = ''
    email.value = ''
    notice.value = 'Invitation créée. Copiez le lien ci-dessous pour le partager.'
    activeTab.value = 'invitations'
    search.value = ''
    await loadList('invitations', 0)
  } catch (error) {
    if (alive) formError.value = errorText(error, 'Impossible de créer l’invitation.')
  } finally {
    if (alive) saving.value = false
  }
}

async function copyInvitation() {
  if (!invitationLink.value) return
  try {
    await navigator.clipboard.writeText(invitationLink.value)
    copyMessage.value = 'Lien copié.'
  } catch {
    invitationField.value?.focus()
    invitationField.value?.select()
    copyMessage.value = 'Sélectionnez puis copiez le lien affiché.'
  }
}

async function openActions(row) {
  if (busy.value || !hasActions(row)) return
  actionTarget.value = row
  actionTab.value = activeTab.value
  selectedRole.value = row.role
  actionError.value = ''
  await nextTick()
  actionDialog.value?.showModal()
}

function closeActions() {
  if (!saving.value) actionDialog.value?.close()
}

async function applyAction(kind) {
  const target = actionTarget.value
  if (saving.value || !target) return
  if (kind === 'role' && !canChangeRole(target)) return
  if (kind === 'status' && !canChangeStatus(target)) return
  if (kind === 'revoke' && !canRevoke(target)) return
  if (kind === 'renew' && !canRenew(target)) return
  saving.value = true
  actionError.value = ''
  notice.value = ''
  try {
    let updated
    if (kind === 'role') updated = await updateOrganizationMemberRole(target.id, selectedRole.value)
    else if (kind === 'status') {
      updated = await updateOrganizationMemberStatus(target.id, target.status === 'active' ? 'inactive' : 'active')
    } else if (kind === 'renew') {
      updated = await renewOrganizationInvitation(target.id)
    } else updated = await revokeOrganizationInvitation(target.id)
    if (!alive) return
    if (kind === 'renew') {
      createdInvitation.value = updated
      copyMessage.value = ''
    }
    const listKind = ['revoke', 'renew'].includes(kind) ? 'invitations' : 'members'
    if (kind !== 'renew') {
      lists[listKind].items = lists[listKind].items.map((row) =>
        row.id === target.id ? (listKind === 'members' ? normalizeMember(updated) : updated) : row,
      )
    }
    if (kind === 'revoke' && createdInvitation.value?.invitation.id === target.id) {
      createdInvitation.value = null
    }
    notice.value = kind === 'renew'
      ? 'Un nouveau lien a été créé. Copiez-le avant de quitter la page.'
      : kind === 'revoke'
        ? 'Invitation révoquée.'
        : 'Les accès du membre ont été mis à jour.'
    actionDialog.value?.close()
    await loadList(listKind)
  } catch (error) {
    if (alive) actionError.value = errorText(error, 'Impossible d’effectuer cette modification.')
  } finally {
    if (alive) saving.value = false
  }
}

onMounted(() => {
  initialize()
  clock = window.setInterval(() => { now.value = Date.now() }, 30000)
})
onBeforeUnmount(() => {
  alive = false
  requestId += 1
  window.clearInterval(clock)
  createdInvitation.value = null
})
</script>

<template>
  <section class="team-page">
    <nav class="breadcrumb" aria-label="Fil d’Ariane">
      <RouterLink to="/setting">Paramètres</RouterLink>
      <ChevronRight :size="15" aria-hidden="true" />
      <span aria-current="page">Équipe</span>
    </nav>

    <header class="page-heading">
      <div>
        <h1>Équipe</h1>
        <p>Gérez les membres de votre organisation et leurs accès à Ruinion AI.</p>
      </div>
      <div v-if="canManage && !initialLoading && !sessionError" class="team-counter">
        <span class="icon-tile">
          <component :is="isMembers ? Users : Mail" :size="23" aria-hidden="true" />
        </span>
        <div>
          <strong>{{ currentList.loaded ? currentList.total : '…' }} {{ isMembers ? 'membres' : 'invitations' }}</strong>
          <span>{{ session.organization?.name || 'Votre organisation' }}</span>
        </div>
      </div>
    </header>

    <div v-if="initialLoading" class="panel state-panel" role="status">
      <LoaderCircle class="spin" :size="22" aria-hidden="true" /> Chargement de votre équipe…
    </div>
    <div v-else-if="sessionError" class="error-box" role="alert">
      <p>{{ sessionError }}</p>
      <button class="secondary-button" type="button" @click="initialize">Réessayer</button>
    </div>
    <div v-else-if="!canManage" class="panel state-panel stack">
      <h2>Accès réservé</h2>
      <p>La gestion de l’équipe est accessible au propriétaire et aux administrateurs.</p>
      <RouterLink to="/reunion">Revenir aux réunions</RouterLink>
    </div>

    <template v-else>
      <p v-if="notice" class="notice" role="status">{{ notice }}</p>

      <nav class="team-tabs" aria-label="Sections de l’équipe">
        <button
          v-for="tab in tabs" :key="tab.id" type="button"
          :class="{ selected: activeTab === tab.id }"
          :aria-pressed="activeTab === tab.id" :disabled="saving"
          @click="changeTab(tab.id)"
        >
          <component :is="tab.icon" :size="19" aria-hidden="true" /> {{ tab.label }}
        </button>
        <button class="inline-refresh" type="button" :disabled="busy" @click="initialize" aria-label="Actualiser l’équipe">
          <RefreshCw :size="18" aria-hidden="true" />
        </button>
      </nav>

      <div class="team-grid">
        <article class="panel directory" :aria-busy="listLoading">
          <header class="directory-heading">
            <div>
              <h2>{{ isMembers ? 'Membres de l’équipe' : 'Invitations' }}</h2>
              <p>{{ isMembers ? 'Les membres et leurs accès à votre organisation.' : 'Suivez les invitations à rejoindre votre équipe.' }}</p>
            </div>
            <label class="search-field">
              <Search :size="17" aria-hidden="true" />
              <input v-model="search" type="search" aria-label="Rechercher dans cette page" placeholder="Rechercher dans cette page…" :disabled="listLoading" />
            </label>
          </header>

          <div v-if="listLoading" class="table-state" role="status">
            <LoaderCircle class="spin" :size="22" aria-hidden="true" /> Chargement…
          </div>
          <div v-else-if="listError" class="table-state">
            <p class="error-box" role="alert">{{ listError }}</p>
            <button type="button" class="secondary-button" @click="loadList()">Réessayer</button>
          </div>
          <div v-else class="table-scroll" tabindex="0" aria-label="Tableau de l’équipe">
            <table>
              <thead>
                <tr>
                  <th scope="col">{{ isMembers ? 'Membre' : 'Adresse e-mail' }}</th>
                  <th scope="col">Rôle</th>
                  <th scope="col">Statut</th>
                  <th scope="col">{{ isMembers ? 'Ajouté le' : 'Créée le' }}</th>
                  <th v-if="!isMembers" scope="col">Expire le</th>
                  <th scope="col" class="actions-heading">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in filteredRows" :key="row.id">
                  <td>
                    <div class="person">
                      <span class="avatar" :class="'avatar-' + (row.id % 5)" aria-hidden="true">{{ initials(row) }}</span>
                      <div class="person-text">
                        <strong>{{ isMembers ? row.name : row.email }}</strong>
                        <span v-if="isMembers">{{ row.email }}</span>
                      </div>
                    </div>
                  </td>
                  <td><span class="role-badge" :class="row.role">{{ roleLabels[row.role] || row.role }}</span></td>
                  <td>
                    <span class="status-badge" :class="rowStatus(row)">
                      <span class="status-dot" aria-hidden="true"></span>
                      {{ statusLabels[rowStatus(row)] || row.status }}
                    </span>
                  </td>
                  <td class="date-cell">{{ formatDate(row.created_at) }}</td>
                  <td v-if="!isMembers" class="date-cell">{{ formatDate(row.expires_at) }}</td>
                  <td class="actions-cell">
                    <button v-if="hasActions(row)" type="button" class="action-button" :disabled="busy" :aria-label="'Actions pour ' + (row.name || row.email)" @click="openActions(row)">
                      <MoreHorizontal :size="19" aria-hidden="true" />
                    </button>
                    <span v-else aria-label="Aucune action disponible">—</span>
                  </td>
                </tr>
                <tr v-if="!filteredRows.length">
                  <td :colspan="isMembers ? 5 : 6" class="empty-state">
                    {{ search ? 'Aucun résultat dans cette page.' : (isMembers ? 'Aucun membre à afficher.' : 'Aucune invitation pour le moment.') }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <footer v-if="currentList.loaded" class="directory-footer">
            <span>{{ filteredRows.length }} affiché(s) · {{ currentList.total }} au total</span>
            <div class="pagination" aria-label="Pagination">
              <button type="button" :disabled="busy || pageNumber <= 1" aria-label="Page précédente" @click="changePage(-1)"><ChevronLeft :size="16" /></button>
              <span>Page {{ pageNumber }} / {{ pageCount }}</span>
              <button type="button" :disabled="busy || pageNumber >= pageCount" aria-label="Page suivante" @click="changePage(1)"><ChevronRight :size="16" /></button>
            </div>
          </footer>
        </article>

        <aside class="invite-column" aria-label="Inviter dans l’équipe">
          <article class="panel invite-panel">
            <header class="card-heading">
              <span class="icon-tile"><Mail :size="22" aria-hidden="true" /></span>
              <div><h2>Inviter un membre</h2><p>Donnez accès à votre espace de réunion.</p></div>
            </header>
            <form @submit.prevent="submitInvitation">
              <label for="team-invite-email">Adresse e-mail <span class="required">*</span></label>
              <input id="team-invite-email" v-model="email" type="email" maxlength="255" placeholder="exemple@entreprise.com" autocomplete="off" :disabled="saving || !canInvite" required />
              <label for="team-invite-role">Rôle <span class="required">*</span></label>
              <select id="team-invite-role" v-model="invitedRole" :disabled="saving || !canInvite" required>
                <option value="member">Membre</option>
                <option v-if="isOwner" value="admin">Administrateur</option>
              </select>
              <p class="field-help">{{ invitedRole === 'member' ? 'Peut consulter et créer des réunions.' : 'Peut aussi inviter des membres et gérer leurs accès.' }}</p>
              <p v-if="formError" class="error-box" role="alert">{{ formError }}</p>
              <p v-if="!canInvite" class="error-box">
                Le propriétaire a désactivé les invitations pour les administrateurs.
              </p>
              <button class="primary-button" type="submit" :disabled="busy || !canInvite || !email.trim()">
                <LoaderCircle v-if="saving" class="spin" :size="17" aria-hidden="true" /><Send v-else :size="17" aria-hidden="true" />
                {{ saving ? 'Veuillez patienter…' : 'Créer l’invitation' }}
              </button>
            </form>
            <div class="info-box">
              <Info :size="18" aria-hidden="true" />
              <p>Un lien valable {{ invitationDuration }} jour{{ invitationDuration > 1 ? 's' : '' }} sera créé. Partagez-le avec la personne invitée ; aucun e-mail automatique n’est envoyé.</p>
            </div>
          </article>

          <article v-if="createdInvitation" class="panel link-panel">
            <h3>Lien d’invitation</h3>
            <p>{{ createdInvitation.invitation.email }}</p>
            <input ref="invitationField" :value="invitationLink" readonly aria-label="Lien d’invitation à copier" @focus="$event.target.select()" />
            <button type="button" class="secondary-button" @click="copyInvitation"><Copy :size="16" aria-hidden="true" /> Copier le lien</button>
            <p v-if="copyMessage" role="status">{{ copyMessage }}</p>
            <p class="field-help">Copiez ce lien avant de quitter la page : il ne pourra plus être affiché ensuite.</p>
          </article>

          <article class="panel permissions-card">
            <ShieldCheck :size="22" aria-hidden="true" />
            <div><h3>Des accès maîtrisés</h3><p>Le propriétaire attribue les rôles. Les administrateurs gèrent l’accès des membres simples.</p></div>
          </article>
        </aside>
      </div>
    </template>

    <dialog ref="actionDialog" class="dialog" aria-labelledby="team-action-title" @cancel="saving && $event.preventDefault()" @close="actionTarget = null">
      <template v-if="actionTarget">
        <header class="dialog-heading">
          <div><h2 id="team-action-title">{{ actionTab === 'members' ? 'Gérer le membre' : 'Révoquer l’invitation' }}</h2><p>{{ actionTarget.name || actionTarget.email }}</p></div>
          <button type="button" class="action-button" :disabled="saving" aria-label="Fermer" @click="closeActions"><X :size="20" /></button>
        </header>
        <p v-if="actionError" class="error-box" role="alert">{{ actionError }}</p>
        <template v-if="actionTab === 'members'">
          <div v-if="canChangeRole(actionTarget)" class="dialog-block">
            <label for="member-role-edit">Rôle dans l’organisation</label>
            <select id="member-role-edit" v-model="selectedRole" :disabled="saving">
              <option value="member">Membre</option><option value="admin">Administrateur</option>
            </select>
            <button type="button" class="secondary-button" :disabled="saving || selectedRole === actionTarget.role" @click="applyAction('role')">Enregistrer le rôle</button>
          </div>
          <div v-if="canChangeStatus(actionTarget)" class="dialog-block">
            <p>{{ actionTarget.status === 'active' ? 'Cette personne perdra l’accès à cette organisation. Ses réunions seront conservées.' : 'Cette personne retrouvera son accès à cette organisation.' }}</p>
            <button type="button" :class="actionTarget.status === 'active' ? 'danger-button' : 'secondary-button'" :disabled="saving" @click="applyAction('status')">
              {{ actionTarget.status === 'active' ? 'Désactiver l’accès' : 'Réactiver l’accès' }}
            </button>
          </div>
        </template>
        <div v-else-if="canRenew(actionTarget)" class="dialog-block">
          <p>L’ancien lien restera inutilisable. Un nouveau lien sera créé avec la durée définie dans les paramètres.</p>
          <button type="button" class="secondary-button" :disabled="saving" @click="applyAction('renew')">Générer un nouveau lien</button>
        </div>
        <div v-else class="dialog-block">
          <p>Le lien d’invitation deviendra inutilisable.</p>
          <button type="button" class="danger-button" :disabled="saving || !canRevoke(actionTarget)" @click="applyAction('revoke')">Révoquer l’invitation</button>
        </div>
        <p v-if="saving" role="status">Enregistrement en cours…</p>
      </template>
    </dialog>
  </section>
</template>

<style scoped>
.team-page { padding: 24px; color: #0f172a; }
.breadcrumb { display: flex; align-items: center; gap: 10px; color: #64748b; font-size: 13px; }
.breadcrumb a:hover { color: #2563eb; }
.breadcrumb [aria-current] { color: #334155; }
.page-heading { display: flex; align-items: center; justify-content: space-between; gap: 24px; margin: 20px 0; }
h1 { margin: 0 0 6px; font-size: 32px; font-weight: 750; letter-spacing: -1px; }
h2 { margin: 0; font-size: 17px; font-weight: 700; }
h3 { margin: 0 0 6px; font-size: 14px; font-weight: 700; }
p { margin: 0; color: #64748b; font-size: 13px; line-height: 1.65; }
.page-heading p { font-size: 14px; }
.team-counter { display: flex; align-items: center; gap: 14px; padding: 18px 22px; background: white; border: 1px solid #e2e8f0; border-radius: 14px; flex-shrink: 0; }
.team-counter strong, .team-counter span:not(.icon-tile) { display: block; }
.team-counter strong { font-size: 14px; font-weight: 650; }
.team-counter div > span { margin-top: 4px; font-size: 12px; color: #64748b; }
.icon-tile { display: grid; place-items: center; width: 44px; height: 44px; flex-shrink: 0; border-radius: 12px; background: #eff6ff; color: #2563eb; }
.team-tabs { display: flex; gap: 12px; margin-bottom: 24px; border-bottom: 1px solid #e2e8f0; }
.team-tabs button { display: flex; align-items: center; gap: 9px; padding: 14px 20px; border-bottom: 3px solid transparent; color: #64748b; font-size: 14px; font-weight: 600; cursor: pointer; }
.team-tabs button.selected { color: #2563eb; border-bottom-color: #2563eb; }
.team-grid { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 22px; align-items: start; }
.panel { background: white; border: 1px solid #e2e8f0; border-radius: 16px; box-shadow: 0 3px 16px #0f172a03; }
.directory { min-width: 0; overflow: hidden; }
.directory-heading { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; padding: 22px; }
.directory-heading p { margin-top: 4px; }
.search-field { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 9px; color: #94a3b8; max-width: 100%; }
.search-field input { min-width: 0; width: 190px; border: 0; outline: none; color: #334155; font-size: 12px; background: transparent; }
.search-field:focus-within { border-color: #2563eb; box-shadow: 0 0 0 3px #dbeafe; }
.table-scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 12px; text-align: left; }
th { background: #f8fafc; color: #64748b; font-weight: 600; }
th, td { padding: 16px; border-top: 1px solid #edf2f7; white-space: nowrap; }
tbody tr:hover { background: #f8fafc80; }
.person { display: flex; align-items: center; gap: 11px; }
.avatar { display: grid; place-items: center; width: 39px; height: 39px; flex-shrink: 0; border-radius: 50%; font-size: 12px; font-weight: 700; }
.avatar-0 { background: #d1fae5; color: #047857; }
.avatar-1 { background: #dbeafe; color: #1d4ed8; }
.avatar-2 { background: #ede9fe; color: #6d28d9; }
.avatar-3 { background: #fef3c7; color: #92400e; }
.avatar-4 { background: #fce7f3; color: #be185d; }
.person-text strong, .person-text span { display: block; }
.person-text strong { font-size: 13px; font-weight: 600; }
.person-text span { margin-top: 4px; color: #64748b; font-size: 11px; }
.role-badge, .status-badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 9px; border-radius: 8px; font-size: 11px; font-weight: 600; }
.role-badge.owner { background: #f3e8ff; color: #7e22ce; }
.role-badge.admin { background: #dbeafe; color: #1d4ed8; }
.role-badge.member { background: #f1f5f9; color: #475569; }
.status-badge.active, .status-badge.accepted { background: #ecfdf5; color: #047857; }
.status-badge.pending { background: #fffbeb; color: #92400e; }
.status-badge.expired, .status-badge.declined { background: #fff1f2; color: #be123c; }
.status-badge.inactive, .status-badge.revoked { background: #f1f5f9; color: #64748b; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.date-cell { color: #475569; }
.actions-heading, .actions-cell { text-align: right; }
.action-button { display: inline-flex; padding: 6px; color: #94a3b8; }
button:disabled { cursor: not-allowed; }
.empty-state { padding: 40px 20px; text-align: center; color: #64748b; }
.directory-footer { padding: 14px 22px; border-top: 1px solid #edf2f7; font-size: 12px; color: #64748b; }
.invite-column { display: grid; gap: 18px; }
.invite-panel { padding: 22px; }
.card-heading { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 24px; }
.card-heading p { margin-top: 5px; font-size: 12px; }
form label { display: block; margin: 18px 0 8px; font-size: 13px; font-weight: 600; }
.required { color: #e11d48; }
form input, form select { width: 100%; min-width: 0; padding: 12px; border: 1px solid #dbe2ea; border-radius: 9px; background: white; color: #334155; font: inherit; font-size: 13px; }
.field-help { margin-top: 8px; font-size: 12px; }
.primary-button { display: flex; align-items: center; justify-content: center; gap: 9px; width: 100%; margin-top: 24px; padding: 13px; border-radius: 9px; background: #2563eb; color: white; font-size: 13px; font-weight: 650; }
.primary-button:disabled { opacity: .65; }
.info-box { display: flex; align-items: flex-start; gap: 10px; margin-top: 18px; padding: 13px; border-radius: 10px; background: #eff6ff; color: #2563eb; }
.info-box svg, .permissions-card > svg { flex-shrink: 0; margin-top: 2px; }
.info-box p { color: #475569; font-size: 12px; }
.permissions-card { display: flex; align-items: flex-start; gap: 12px; padding: 20px; color: #2563eb; }
.permissions-card h3 { color: #334155; }
.permissions-card p { font-size: 12px; }
button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible, .table-scroll:focus-visible { outline: 2px solid #2563eb; outline-offset: 3px; }
@media (max-width: 1279px) {
  .team-grid { grid-template-columns: minmax(0, 1fr); }
  .page-heading { align-items: flex-start; flex-direction: column; }
  .invite-column { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); align-items: start; }
}
@media (max-width: 639px) {
  .team-page { padding: 12px 0; }
  h1 { font-size: 28px; }
  .team-counter { width: 100%; }
  .team-tabs { gap: 0; }
  .team-tabs button { padding: 13px 14px; }
  .invite-column { grid-template-columns: minmax(0, 1fr); }
  .search-field { width: 100%; }
  .search-field input { width: 100%; }
  .directory-heading { padding: 18px; }
}

.notice { margin: 16px 0; padding: 12px 15px; border: 1px solid #a7f3d0; border-radius: 10px; background: #ecfdf5; color: #065f46; font-size: 13px; }
.error-box { margin: 12px 0; padding: 12px 15px; border: 1px solid #fecdd3; border-radius: 10px; background: #fff1f2; color: #be123c; font-size: 13px; }
.state-panel { display: flex; align-items: center; gap: 12px; padding: 24px; margin-top: 24px; }
.state-panel.stack { display: block; }
.state-panel a { display: inline-block; margin-top: 12px; color: #2563eb; }
.table-state { padding: 32px 22px; text-align: center; }
.directory-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.pagination { display: flex; align-items: center; gap: 10px; }
.secondary-button, .pagination button { display: inline-flex; align-items: center; justify-content: center; gap: 7px; border: 1px solid #dbe2ea; border-radius: 8px; background: white; padding: 9px 12px; color: #334155; font-size: 12px; }
.secondary-button:hover:not(:disabled), .pagination button:hover:not(:disabled) { background: #eff6ff; border-color: #93c5fd; }
button:not(:disabled) { cursor: pointer; }
button:disabled { opacity: .55; }
.action-button:not(:disabled) { color: #475569; }
.action-button:hover:not(:disabled) { background: #eff6ff; border-radius: 6px; color: #2563eb; }
.inline-refresh { margin-left: auto; }
.link-panel { padding: 20px; border-color: #93c5fd; }
.link-panel input { width: 100%; margin: 12px 0; padding: 10px; border: 1px solid #dbe2ea; border-radius: 8px; font-size: 12px; }
.link-panel p { overflow-wrap: anywhere; }
.link-panel .secondary-button { width: 100%; }
.dialog { width: min(440px, calc(100vw - 32px)); max-height: calc(100dvh - 40px); overflow-y: auto; margin: auto; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; color: #0f172a; box-shadow: 0 20px 80px #0f172a30; }
.dialog::backdrop { background: #0f172a66; }
.dialog-heading { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.dialog-heading p { margin-top: 6px; overflow-wrap: anywhere; }
.dialog-block { margin-top: 22px; padding-top: 18px; border-top: 1px solid #e2e8f0; }
.dialog-block label { display: block; margin-bottom: 8px; font-size: 13px; font-weight: 600; }
.dialog-block select { width: 100%; padding: 10px; border: 1px solid #dbe2ea; border-radius: 8px; font: inherit; font-size: 13px; }
.dialog-block button { margin-top: 14px; }
.danger-button { display: inline-flex; align-items: center; gap: 8px; padding: 10px 14px; border: 1px solid #fecdd3; border-radius: 8px; background: #fff1f2; color: #be123c; font-size: 13px; }
.spin { animation: team-spin .8s linear infinite; }
@keyframes team-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .spin { animation: none; } }

</style>
