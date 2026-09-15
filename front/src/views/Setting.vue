<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Building2, LoaderCircle, LogOut, ShieldCheck, UserRound } from '@lucide/vue'

import { getCurrentUser, logoutUser } from '@/service/api'

const router = useRouter()

const session = ref(null)
const isLoading = ref(true)
const errorMessage = ref('')

const user = computed(() => session.value?.user)
const organization = computed(() => session.value?.organization)

const userName = computed(() => {
  if (!user.value) {
    return 'Utilisateur'
  }

  return `${user.value.first_name || ''} ${user.value.last_name || ''}`.trim()
})

async function loadSession() {
  try {
    isLoading.value = true
    errorMessage.value = ''
    session.value = await getCurrentUser()
  } catch (error) {
    if (error.status === 401) {
      router.push('/login')
      return
    }

    errorMessage.value = error.message || 'Impossible de charger les paramètres.'
  } finally {
    isLoading.value = false
  }
}

function handleLogout() {
  logoutUser()
  router.push('/login')
}

onMounted(loadSession)
</script>

<template>
  <section class="min-h-full rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
    <header class="border-b border-slate-100 pb-5">
      <p class="text-xs font-black uppercase tracking-normal text-blue-600">Administration</p>
      <h1 class="mt-2 text-2xl font-black text-slate-900">Paramètres</h1>
      <p class="mt-1 max-w-2xl text-sm font-semibold leading-6 text-slate-500">
        Gérez les informations de votre compte et de l'organisation active.
      </p>
    </header>

    <div v-if="isLoading" class="mt-8 flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-5 py-4">
      <LoaderCircle class="h-5 w-5 animate-spin text-blue-600" />
      <p class="text-sm font-bold text-slate-600">Chargement des paramètres...</p>
    </div>

    <p
      v-else-if="errorMessage"
      class="mt-6 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold text-red-600"
    >
      {{ errorMessage }}
    </p>

    <div v-else class="mt-6 grid gap-5 xl:grid-cols-[1fr_0.9fr]">
      <article class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="flex items-center gap-4">
          <div class="grid h-12 w-12 place-items-center rounded-xl bg-blue-600 text-white">
            <UserRound class="h-6 w-6" />
          </div>
          <div>
            <h2 class="text-lg font-black text-slate-900">Compte utilisateur</h2>
            <p class="text-sm font-semibold text-slate-500">Identité utilisée pour accéder à Ruinion AI.</p>
          </div>
        </div>

        <dl class="mt-6 grid gap-4 sm:grid-cols-2">
          <div class="rounded-xl bg-slate-50 px-4 py-3">
            <dt class="text-xs font-black uppercase text-slate-400">Nom</dt>
            <dd class="mt-1 text-sm font-black text-slate-800">{{ userName }}</dd>
          </div>
          <div class="rounded-xl bg-slate-50 px-4 py-3">
            <dt class="text-xs font-black uppercase text-slate-400">Email</dt>
            <dd class="mt-1 break-all text-sm font-black text-slate-800">{{ user?.email }}</dd>
          </div>
          <div class="rounded-xl bg-slate-50 px-4 py-3">
            <dt class="text-xs font-black uppercase text-slate-400">Statut</dt>
            <dd class="mt-1 text-sm font-black text-emerald-600">
              {{ user?.is_active ? 'Actif' : 'Inactif' }}
            </dd>
          </div>
          <div class="rounded-xl bg-slate-50 px-4 py-3">
            <dt class="text-xs font-black uppercase text-slate-400">Rôle</dt>
            <dd class="mt-1 text-sm font-black uppercase text-blue-600">{{ session?.role }}</dd>
          </div>
        </dl>
      </article>

      <article class="rounded-2xl border border-blue-100 bg-blue-50/60 p-5">
        <div class="flex items-center gap-4">
          <div class="grid h-12 w-12 place-items-center rounded-xl bg-blue-600 text-white">
            <Building2 class="h-6 w-6" />
          </div>
          <div>
            <h2 class="text-lg font-black text-slate-900">Organisation</h2>
            <p class="text-sm font-semibold text-slate-500">Espace de travail isolé en base.</p>
          </div>
        </div>

        <div class="mt-6 rounded-xl bg-white px-4 py-4">
          <p class="text-xs font-black uppercase text-slate-400">Nom de l'organisation</p>
          <p class="mt-2 text-xl font-black text-slate-900">{{ organization?.name }}</p>
        </div>

        <div class="mt-4 flex gap-3 rounded-xl bg-white px-4 py-4">
          <ShieldCheck class="mt-1 h-5 w-5 shrink-0 text-emerald-500" />
          <p class="text-sm font-semibold leading-6 text-slate-600">
            Les réunions créées depuis ce compte sont automatiquement rattachées à cette organisation.
          </p>
        </div>
      </article>
    </div>

    <div class="mt-6 flex justify-end">
      <button
        class="inline-flex items-center justify-center gap-2 rounded-xl border border-red-100 bg-red-50 px-5 py-3 text-sm font-black text-red-600 transition hover:bg-red-100"
        type="button"
        @click="handleLogout"
      >
        <LogOut class="h-4 w-4" />
        Se déconnecter
      </button>
    </div>
  </section>
</template>
