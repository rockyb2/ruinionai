<script setup>
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  AudioLines,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  Lock,
  LogOut,
  Mail,
  ShieldCheck,
  UserPlus,
} from '@lucide/vue'

import {
  acceptOrganizationInvitation,
  clearAuthToken,
  isAuthenticated,
  loginUser,
  registerFromInvitation,
} from '@/service/api'

const route = useRoute()
const router = useRouter()
const mode = ref(isAuthenticated() ? 'accept' : 'login')
const loading = ref(false)
const errorMessage = ref('')
const showPassword = ref(false)
const rememberMe = ref(true)
const loginForm = ref({ email: '', password: '' })
const registerForm = ref({ firstName: '', lastName: '', password: '' })

const token = computed(() => {
  const fragment = route.hash.replace(/^#/, '')
  return new URLSearchParams(fragment).get('token')?.trim() || ''
})
const validToken = computed(() => /^[A-Za-z0-9_-]{32,256}$/.test(token.value))

function passwordIsValid(password) {
  return password.length >= 8 && new TextEncoder().encode(password).length <= 72
}

function apiError(error, fallback) {
  if (!error?.status) return 'Connexion impossible. Réessayez dans un instant.'
  return error.message || fallback
}

async function acceptInvitation() {
  if (loading.value || !validToken.value) return

  loading.value = true
  errorMessage.value = ''
  try {
    await acceptOrganizationInvitation(token.value)
    await router.replace({ name: 'reunion' })
  } catch (error) {
    if (error.status === 401) mode.value = 'login'
    errorMessage.value = apiError(error, "Impossible d'accepter cette invitation.")
  } finally {
    loading.value = false
  }
}

async function loginAndAccept() {
  if (!loginForm.value.email.trim() || !loginForm.value.password) {
    errorMessage.value = 'Renseignez votre adresse e-mail et votre mot de passe.'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    await loginUser(
      {
        email: loginForm.value.email.trim(),
        password: loginForm.value.password,
      },
      rememberMe.value,
    )
    await acceptOrganizationInvitation(token.value)
    await router.replace({ name: 'reunion' })
  } catch (error) {
    if (isAuthenticated()) mode.value = 'accept'
    errorMessage.value = apiError(error, "Impossible de se connecter et d'accepter l'invitation.")
  } finally {
    loading.value = false
  }
}

async function registerAndAccept() {
  const form = registerForm.value
  if (!form.firstName.trim() || !form.lastName.trim()) {
    errorMessage.value = 'Renseignez votre prénom et votre nom.'
    return
  }
  if (!passwordIsValid(form.password)) {
    errorMessage.value = 'Le mot de passe doit contenir au moins 8 caractères et 72 octets maximum.'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    await registerFromInvitation(
      {
        token: token.value,
        first_name: form.firstName.trim(),
        last_name: form.lastName.trim(),
        password: form.password,
      },
      rememberMe.value,
    )
    await router.replace({ name: 'reunion' })
  } catch (error) {
    errorMessage.value = apiError(error, "Impossible de créer le compte avec cette invitation.")
  } finally {
    loading.value = false
  }
}

function useAnotherAccount() {
  clearAuthToken()
  mode.value = 'login'
  errorMessage.value = ''
}
</script>

<template>
  <main class="min-h-screen bg-slate-50 px-5 py-8 text-slate-950 sm:px-8 lg:grid lg:place-items-center">
    <section class="mx-auto grid w-full max-w-6xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_28px_90px_rgba(15,23,42,0.10)] lg:grid-cols-[1.05fr_0.95fr]">
      <div class="relative overflow-hidden bg-gradient-to-br from-blue-700 via-blue-600 to-indigo-600 px-7 py-10 text-white sm:px-12 lg:min-h-[680px] lg:px-14 lg:py-14">
        <div class="absolute -right-28 -top-28 h-80 w-80 rounded-full border-[44px] border-white/10"></div>
        <div class="absolute -bottom-32 -left-24 h-96 w-96 rounded-full bg-indigo-400/20 blur-2xl"></div>

        <RouterLink class="relative flex w-fit items-center gap-3" to="/login">
          <span class="grid h-12 w-12 place-items-center rounded-2xl bg-white text-blue-600 shadow-lg">
            <AudioLines :size="26" :stroke-width="2.6" />
          </span>
          <span class="text-xl font-black">RUINION AI</span>
        </RouterLink>

        <div class="relative mt-20 max-w-xl">
          <span class="inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-2 text-sm font-bold backdrop-blur">
            <ShieldCheck :size="17" />
            Invitation sécurisée
          </span>
          <h1 class="mt-7 text-4xl font-black leading-tight sm:text-5xl">
            Rejoignez votre équipe de travail.
          </h1>
          <p class="mt-6 max-w-lg text-base font-medium leading-7 text-blue-100 sm:text-lg">
            Acceptez l'invitation pour accéder aux réunions, aux transcriptions et aux comptes rendus partagés par votre organisation.
          </p>
        </div>

        <div class="relative mt-14 grid gap-5 text-sm font-semibold text-blue-50">
          <p class="flex items-center gap-3">
            <CheckCircle2 class="shrink-0 text-emerald-300" :size="21" />
            Votre compte reste protégé par votre mot de passe.
          </p>
          <p class="flex items-center gap-3">
            <CheckCircle2 class="shrink-0 text-emerald-300" :size="21" />
            L'invitation ne peut être utilisée qu'une seule fois.
          </p>
          <p class="flex items-center gap-3">
            <CheckCircle2 class="shrink-0 text-emerald-300" :size="21" />
            Vous rejoignez uniquement l'organisation qui vous a invité.
          </p>
        </div>
      </div>

      <div class="grid content-center px-6 py-10 sm:px-12 lg:px-14">
        <div v-if="!validToken" class="text-center">
          <span class="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-red-50 text-red-600">
            <KeyRound :size="30" />
          </span>
          <h2 class="mt-6 text-2xl font-black">Lien d'invitation invalide</h2>
          <p class="mx-auto mt-3 max-w-sm text-sm font-medium leading-6 text-slate-500">
            Le lien est incomplet ou a été modifié. Demandez un nouveau lien à l'administrateur de l'équipe.
          </p>
          <RouterLink class="mt-7 inline-flex h-12 items-center justify-center rounded-xl bg-blue-600 px-6 font-black text-white hover:bg-blue-700" to="/login">
            Aller à la connexion
          </RouterLink>
        </div>

        <template v-else>
          <div class="mb-8">
            <p class="text-sm font-black uppercase tracking-[0.16em] text-blue-600">Invitation d'équipe</p>
            <h2 class="mt-3 text-3xl font-black">
              {{ mode === 'register' ? 'Créer votre compte' : mode === 'login' ? 'Se connecter' : "Accepter l'invitation" }}
            </h2>
            <p class="mt-3 text-sm font-medium leading-6 text-slate-500">
              <template v-if="mode === 'register'">
                L'adresse e-mail utilisée sera celle à laquelle l'invitation a été envoyée.
              </template>
              <template v-else-if="mode === 'login'">
                Connectez-vous avec l'adresse e-mail qui a reçu cette invitation.
              </template>
              <template v-else>
                Vous êtes connecté. Confirmez pour rejoindre l'organisation.
              </template>
            </p>
          </div>

          <p v-if="errorMessage" role="alert" class="mb-5 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold leading-6 text-red-700">
            {{ errorMessage }}
          </p>

          <form v-if="mode === 'login'" class="grid gap-5" @submit.prevent="loginAndAccept">
            <label class="grid gap-2 text-sm font-bold text-slate-700">
              Adresse e-mail
              <span class="relative">
                <Mail class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="19" />
                <input
                  v-model="loginForm.email"
                  class="h-12 w-full rounded-xl border border-slate-200 pl-11 pr-4 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  type="email"
                  autocomplete="email"
                  required
                />
              </span>
            </label>

            <label class="grid gap-2 text-sm font-bold text-slate-700">
              Mot de passe
              <span class="relative">
                <Lock class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="19" />
                <input
                  v-model="loginForm.password"
                  class="h-12 w-full rounded-xl border border-slate-200 pl-11 pr-12 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  required
                />
                <button
                  class="absolute right-3 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-blue-600"
                  type="button"
                  :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
                  @click="showPassword = !showPassword"
                >
                  <EyeOff v-if="showPassword" :size="19" />
                  <Eye v-else :size="19" />
                </button>
              </span>
            </label>

            <label class="flex items-center gap-3 text-sm font-semibold text-slate-500">
              <input v-model="rememberMe" class="h-4 w-4 rounded border-slate-300 text-blue-600" type="checkbox" />
              Se souvenir de moi
            </label>

            <button class="inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-blue-600 font-black text-white shadow-lg shadow-blue-200 hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none" type="submit" :disabled="loading">
              <LoaderCircle v-if="loading" class="animate-spin" :size="20" />
              Se connecter et accepter
            </button>

            <button class="h-11 rounded-xl font-bold text-blue-600 hover:bg-blue-50" type="button" :disabled="loading" @click="mode = 'register'; errorMessage = ''">
              Je n'ai pas encore de compte
            </button>
          </form>

          <form v-else-if="mode === 'register'" class="grid gap-5" @submit.prevent="registerAndAccept">
            <div class="grid gap-5 sm:grid-cols-2">
              <label class="grid gap-2 text-sm font-bold text-slate-700">
                Prénom
                <input v-model="registerForm.firstName" class="h-12 rounded-xl border border-slate-200 px-4 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100" autocomplete="given-name" maxlength="100" required />
              </label>
              <label class="grid gap-2 text-sm font-bold text-slate-700">
                Nom
                <input v-model="registerForm.lastName" class="h-12 rounded-xl border border-slate-200 px-4 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100" autocomplete="family-name" maxlength="100" required />
              </label>
            </div>

            <label class="grid gap-2 text-sm font-bold text-slate-700">
              Mot de passe
              <span class="relative">
                <Lock class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="19" />
                <input
                  v-model="registerForm.password"
                  class="h-12 w-full rounded-xl border border-slate-200 pl-11 pr-12 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  minlength="8"
                  maxlength="72"
                  required
                />
                <button
                  class="absolute right-3 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-blue-600"
                  type="button"
                  :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
                  @click="showPassword = !showPassword"
                >
                  <EyeOff v-if="showPassword" :size="19" />
                  <Eye v-else :size="19" />
                </button>
              </span>
              <span class="font-medium text-slate-400">8 caractères minimum.</span>
            </label>

            <label class="flex items-center gap-3 text-sm font-semibold text-slate-500">
              <input v-model="rememberMe" class="h-4 w-4 rounded border-slate-300 text-blue-600" type="checkbox" />
              Se souvenir de moi
            </label>

            <button class="inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-blue-600 font-black text-white shadow-lg shadow-blue-200 hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none" type="submit" :disabled="loading">
              <LoaderCircle v-if="loading" class="animate-spin" :size="20" />
              Créer le compte et rejoindre
            </button>

            <button class="h-11 rounded-xl font-bold text-blue-600 hover:bg-blue-50" type="button" :disabled="loading" @click="mode = 'login'; errorMessage = ''">
              J'ai déjà un compte
            </button>
          </form>

          <div v-else class="grid gap-4">
            <div class="rounded-2xl border border-blue-100 bg-blue-50 p-5">
              <div class="flex gap-4">
                <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white text-blue-600 shadow-sm">
                  <UserPlus :size="22" />
                </span>
                <div>
                  <h3 class="font-black text-slate-900">Prêt à rejoindre l'équipe</h3>
                  <p class="mt-1 text-sm font-medium leading-6 text-slate-500">
                    Votre accès sera ajouté dès que vous confirmez.
                  </p>
                </div>
              </div>
            </div>

            <button class="inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-blue-600 font-black text-white shadow-lg shadow-blue-200 hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none" type="button" :disabled="loading" @click="acceptInvitation">
              <LoaderCircle v-if="loading" class="animate-spin" :size="20" />
              <UserPlus v-else :size="20" />
              Accepter l'invitation
            </button>

            <button class="inline-flex h-11 items-center justify-center gap-2 rounded-xl font-bold text-slate-500 hover:bg-slate-100 hover:text-slate-800" type="button" :disabled="loading" @click="useAnotherAccount">
              <LogOut :size="18" />
              Utiliser un autre compte
            </button>
          </div>

          <p class="mt-7 flex items-start gap-3 rounded-xl bg-slate-50 px-4 py-3 text-xs font-semibold leading-5 text-slate-500">
            <ShieldCheck class="mt-0.5 shrink-0 text-blue-600" :size="17" />
            La durée du lien est définie par l’organisation. S’il n’est plus valide, contactez l’administrateur de l’équipe.
          </p>
        </template>
      </div>
    </section>
  </main>
</template>
