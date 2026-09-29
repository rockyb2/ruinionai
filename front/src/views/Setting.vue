<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  BellRing,
  Building2,
  CalendarClock,
  CheckCircle2,
  LoaderCircle,
  Save,
  ShieldCheck,
  UserRound,
  Users,
} from '@lucide/vue'

import {
  getCurrentUser,
  getOrganizationSettings,
  updateOrganizationSettings,
} from '@/service/api'
import { roleLabel } from '@/utils/organization'

const router = useRouter()
const session = ref(null)
const settings = ref(null)
const isLoading = ref(true)
const isSaving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const form = reactive({
  name: '',
  description: '',
  invitation_expiration_days: 7,
  allow_admin_invitations: true,
  invitation_notifications_enabled: true,
})

const user = computed(() => session.value?.user)
const isOwner = computed(() => session.value?.role === 'owner')
const userName = computed(() =>
  [user.value?.first_name, user.value?.last_name].filter(Boolean).join(' ') || 'Utilisateur',
)

function fillForm(value) {
  form.name = value.name || ''
  form.description = value.description || ''
  form.invitation_expiration_days = value.invitation_expiration_days || 7
  form.allow_admin_invitations = Boolean(value.allow_admin_invitations)
  form.invitation_notifications_enabled = Boolean(
    value.invitation_notifications_enabled,
  )
}

async function loadSettings() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    session.value = await getCurrentUser()
    settings.value = await getOrganizationSettings()
    fillForm(settings.value)
  } catch (error) {
    if (error.status === 401) {
      await router.push('/login')
      return
    }
    errorMessage.value = error.message || 'Impossible de charger les paramètres.'
  } finally {
    isLoading.value = false
  }
}

async function saveSettings() {
  if (!isOwner.value || isSaving.value) return
  if (!form.name.trim()) {
    errorMessage.value = "Le nom de l'organisation est obligatoire."
    return
  }

  isSaving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    settings.value = await updateOrganizationSettings({
      name: form.name.trim(),
      description: form.description.trim() || null,
      invitation_expiration_days: Number(form.invitation_expiration_days),
      allow_admin_invitations: form.allow_admin_invitations,
      invitation_notifications_enabled: form.invitation_notifications_enabled,
    })
    fillForm(settings.value)
    successMessage.value = 'Les paramètres de l’organisation ont été enregistrés.'
    session.value = {
      ...session.value,
      organization: {
        ...session.value.organization,
        name: settings.value.name,
      },
    }

    window.dispatchEvent(
      new CustomEvent('organization-updated', {
        detail: { name: settings.value.name },
      }),
    )
  } catch (error) {
    errorMessage.value = error.status
      ? (error.message || 'Impossible d’enregistrer les paramètres.')
      : 'Connexion impossible. Réessayez dans un instant.'
  } finally {
    isSaving.value = false
  }
}

onMounted(loadSettings)
</script>

<template>
  <section class="min-h-full space-y-6">
    <header class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p class="text-xs font-black uppercase tracking-[0.14em] text-blue-600">
        Organisation
      </p>
      <div class="mt-2 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-3xl font-black text-slate-950">Paramètres de l’équipe</h1>
          <p class="mt-2 max-w-2xl text-sm font-semibold leading-6 text-slate-500">
            Gérez l’identité de l’organisation, la durée des invitations et les notifications internes.
          </p>
        </div>
        <span
          v-if="session"
          class="rounded-full px-3 py-1.5 text-xs font-black uppercase"
          :class="isOwner ? 'bg-violet-50 text-violet-700' : 'bg-slate-100 text-slate-600'"
        >
          {{ roleLabel(session.role) }}
        </span>
      </div>
    </header>

    <div
      v-if="isLoading"
      class="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-6 py-8 shadow-sm"
      role="status"
    >
      <LoaderCircle class="h-5 w-5 animate-spin text-blue-600" />
      <p class="text-sm font-bold text-slate-600">Chargement des paramètres…</p>
    </div>

    <div
      v-else-if="errorMessage && !settings"
      class="rounded-2xl border border-red-100 bg-red-50 p-6"
      role="alert"
    >
      <p class="text-sm font-bold text-red-700">{{ errorMessage }}</p>
      <button
        class="mt-4 rounded-xl border border-red-200 bg-white px-4 py-2 text-sm font-black text-red-700"
        type="button"
        @click="loadSettings"
      >
        Réessayer
      </button>
    </div>

    <form v-else class="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]" @submit.prevent="saveSettings">
      <div class="space-y-6">
        <article class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start gap-4">
            <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-blue-50 text-blue-600">
              <Building2 class="h-6 w-6" />
            </span>
            <div>
              <h2 class="text-lg font-black text-slate-900">Informations générales</h2>
              <p class="mt-1 text-sm font-semibold text-slate-500">
                Ces informations identifient l’espace de travail.
              </p>
            </div>
          </div>

          <div class="mt-6 grid gap-5">
            <label class="grid gap-2 text-sm font-black text-slate-700">
              Nom de l’organisation
              <input
                v-model="form.name"
                class="h-12 rounded-xl border border-slate-200 px-4 font-semibold outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:bg-slate-50"
                maxlength="150"
                required
                :disabled="!isOwner || isSaving"
              />
            </label>

            <label class="grid gap-2 text-sm font-black text-slate-700">
              Description
              <textarea
                v-model="form.description"
                class="min-h-28 resize-y rounded-xl border border-slate-200 p-4 font-medium leading-6 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:bg-slate-50"
                maxlength="500"
                placeholder="Expliquez comment votre équipe utilise Ruinion AI."
                :disabled="!isOwner || isSaving"
              ></textarea>
              <span class="text-right text-xs font-semibold text-slate-400">
                {{ form.description.length }}/500
              </span>
            </label>
          </div>
        </article>

        <article class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start gap-4">
            <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-amber-50 text-amber-600">
              <CalendarClock class="h-6 w-6" />
            </span>
            <div>
              <h2 class="text-lg font-black text-slate-900">Règles d’invitation</h2>
              <p class="mt-1 text-sm font-semibold text-slate-500">
                Définissez la durée des liens et les droits des administrateurs.
              </p>
            </div>
          </div>

          <label class="mt-6 grid gap-2 text-sm font-black text-slate-700">
            Durée de validité d’un lien
            <select
              v-model.number="form.invitation_expiration_days"
              class="h-12 rounded-xl border border-slate-200 px-4 font-semibold outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:bg-slate-50"
              :disabled="!isOwner || isSaving"
            >
              <option :value="1">1 jour</option>
              <option :value="3">3 jours</option>
              <option :value="7">7 jours</option>
              <option :value="14">14 jours</option>
              <option :value="30">30 jours</option>
            </select>
          </label>

          <div class="mt-6 flex items-start justify-between gap-5 rounded-xl bg-slate-50 p-4">
            <div class="flex gap-3">
              <Users class="mt-0.5 h-5 w-5 shrink-0 text-blue-600" />
              <div>
                <p class="text-sm font-black text-slate-800">Autoriser les administrateurs à inviter</p>
                <p class="mt-1 text-xs font-semibold leading-5 text-slate-500">
                  Ils pourront créer et renouveler les invitations de membres simples.
                </p>
              </div>
            </div>
            <button
              class="relative h-7 w-12 shrink-0 rounded-full transition disabled:opacity-60"
              :class="form.allow_admin_invitations ? 'bg-blue-600' : 'bg-slate-300'"
              type="button"
              role="switch"
              :aria-checked="form.allow_admin_invitations"
              :disabled="!isOwner || isSaving"
              @click="form.allow_admin_invitations = !form.allow_admin_invitations"
            >
              <span
                class="absolute top-1 h-5 w-5 rounded-full bg-white shadow transition"
                :class="form.allow_admin_invitations ? 'left-6' : 'left-1'"
              ></span>
            </button>
          </div>
        </article>
      </div>

      <div class="space-y-6">
        <article class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start gap-4">
            <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-violet-50 text-violet-600">
              <BellRing class="h-6 w-6" />
            </span>
            <div>
              <h2 class="text-lg font-black text-slate-900">Notifications</h2>
              <p class="mt-1 text-sm font-semibold text-slate-500">
                Alertes internes liées aux invitations.
              </p>
            </div>
          </div>

          <div class="mt-6 flex items-start justify-between gap-5 rounded-xl bg-slate-50 p-4">
            <div>
              <p class="text-sm font-black text-slate-800">Activité des invitations</p>
              <p class="mt-1 text-xs font-semibold leading-5 text-slate-500">
                Invitations bientôt expirées, expirées ou acceptées.
              </p>
            </div>
            <button
              class="relative h-7 w-12 shrink-0 rounded-full transition disabled:opacity-60"
              :class="form.invitation_notifications_enabled ? 'bg-blue-600' : 'bg-slate-300'"
              type="button"
              role="switch"
              :aria-checked="form.invitation_notifications_enabled"
              :disabled="!isOwner || isSaving"
              @click="form.invitation_notifications_enabled = !form.invitation_notifications_enabled"
            >
              <span
                class="absolute top-1 h-5 w-5 rounded-full bg-white shadow transition"
                :class="form.invitation_notifications_enabled ? 'left-6' : 'left-1'"
              ></span>
            </button>
          </div>
        </article>

        <article class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start gap-4">
            <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-emerald-50 text-emerald-600">
              <UserRound class="h-6 w-6" />
            </span>
            <div>
              <h2 class="text-lg font-black text-slate-900">Votre accès</h2>
              <p class="mt-1 text-sm font-semibold text-slate-500">{{ userName }}</p>
            </div>
          </div>
          <dl class="mt-5 grid gap-3">
            <div class="rounded-xl bg-slate-50 px-4 py-3">
              <dt class="text-xs font-black uppercase text-slate-400">Adresse e-mail</dt>
              <dd class="mt-1 break-all text-sm font-bold text-slate-700">{{ user?.email }}</dd>
            </div>
            <div class="rounded-xl bg-slate-50 px-4 py-3">
              <dt class="text-xs font-black uppercase text-slate-400">Rôle</dt>
              <dd class="mt-1 text-sm font-black uppercase text-blue-600">{{ roleLabel(session?.role) }}</dd>
            </div>
          </dl>
          <p v-if="!isOwner" class="mt-4 flex gap-2 rounded-xl bg-amber-50 p-4 text-xs font-bold leading-5 text-amber-800">
            <ShieldCheck class="mt-0.5 h-4 w-4 shrink-0" />
            Seul le propriétaire peut modifier les paramètres de l’organisation.
          </p>
        </article>

        <p
          v-if="errorMessage"
          class="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold text-red-700"
          role="alert"
        >
          {{ errorMessage }}
        </p>
        <p
          v-if="successMessage"
          class="flex items-center gap-2 rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700"
          role="status"
        >
          <CheckCircle2 class="h-5 w-5" />
          {{ successMessage }}
        </p>

        <button
          v-if="isOwner"
          class="inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-blue-600 font-black text-white shadow-lg shadow-blue-200 transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
          type="submit"
          :disabled="isSaving"
        >
          <LoaderCircle v-if="isSaving" class="h-5 w-5 animate-spin" />
          <Save v-else class="h-5 w-5" />
          {{ isSaving ? 'Enregistrement…' : 'Enregistrer les modifications' }}
        </button>
      </div>
    </form>
  </section>
</template>
