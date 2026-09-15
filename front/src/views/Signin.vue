<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  AudioLines,
  Building2,
  CheckCircle2,
  Eye,
  EyeOff,
  FileText,
  LoaderCircle,
  Lock,
  Mail,
  Mic,
  ShieldCheck,
  Sparkles,
  SquareCheckBig,
  User,
} from '@lucide/vue'

import signinVisual from '../assets/visuelsignin.png'
import { registerUser } from '@/service/api'

const router = useRouter()

const firstName = ref('')
const lastName = ref('')
const organizationName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const rememberMe = ref(true)
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const isSubmitting = ref(false)
const errorMessage = ref('')

function validateForm() {
  if (
    !firstName.value.trim() ||
    !lastName.value.trim() ||
    !organizationName.value.trim() ||
    !email.value.trim() ||
    !password.value
  ) {
    return 'Tous les champs sont nécessaires pour créer votre espace.'
  }

  if (password.value.length < 8) {
    return 'Le mot de passe doit contenir au moins 8 caractères.'
  }

  if (password.value !== confirmPassword.value) {
    return 'Les deux mots de passe ne correspondent pas.'
  }

  return ''
}

async function handleSignup() {
  const validationError = validateForm()

  if (validationError) {
    errorMessage.value = validationError
    return
  }

  try {
    isSubmitting.value = true
    errorMessage.value = ''

    await registerUser(
      {
        first_name: firstName.value,
        last_name: lastName.value,
        organization_name: organizationName.value,
        email: email.value,
        password: password.value,
      },
      rememberMe.value,
    )

    router.push('/reunion')
  } catch (error) {
    errorMessage.value = error.message || 'Inscription impossible pour le moment.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="min-h-screen overflow-hidden bg-white text-[#071124]">
    <section class="relative mx-auto grid min-h-screen w-full max-w-[1728px] grid-cols-1 lg:grid-cols-[1fr_600px]">
      <div class="relative px-6 py-8 sm:px-10 lg:px-14 xl:px-16">
        <RouterLink class="flex w-fit items-center gap-4" to="/login">
          <div class="grid h-12 w-12 place-items-center rounded-2xl bg-blue-600 text-white shadow-[0_18px_34px_rgba(37,99,235,0.28)]">
            <AudioLines :size="26" :stroke-width="2.6" />
          </div>
          <div>
            <p class="text-2xl font-black leading-none tracking-normal">
              RUINION <span class="text-blue-600">AI</span>
            </p>
            <p class="mt-2 text-sm font-medium text-slate-500">
              Votre mémoire de réunion collaborative
            </p>
          </div>
        </RouterLink>

        <div class="relative z-10 mt-14 max-w-[650px]">
          <p class="inline-flex items-center gap-2 rounded-full bg-blue-50 px-4 py-2 text-sm font-black text-blue-600">
            <Sparkles class="h-4 w-4" />
            Lancement de votre workspace
          </p>
          <h1 class="mt-6 text-4xl font-black leading-[1.18] tracking-normal text-slate-950 sm:text-5xl lg:text-[3.25rem]">
            Créez un espace d'équipe prêt pour vos comptes rendus IA.
          </h1>
          <p class="mt-7 max-w-lg text-lg font-medium leading-8 text-slate-500">
            Votre organisation devient le coffre-fort de vos réunions, décisions et prochaines actions.
          </p>
        </div>

        <div class="relative z-10 mt-10 grid max-w-lg gap-6">
          <div class="flex gap-5">
            <div class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-600">
              <Mic :size="27" />
            </div>
            <div>
              <h2 class="text-base font-black tracking-normal text-slate-950">Capture de réunion</h2>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Enregistrez ou importez un audio depuis votre espace sécurisé.
              </p>
            </div>
          </div>

          <div class="flex gap-5">
            <div class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-600">
              <FileText :size="27" />
            </div>
            <div>
              <h2 class="text-base font-black tracking-normal text-slate-950">Mémoire organisée</h2>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Les comptes rendus restent rattachés à votre entreprise.
              </p>
            </div>
          </div>

          <div class="flex gap-5">
            <div class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-600">
              <SquareCheckBig :size="27" />
            </div>
            <div>
              <h2 class="text-base font-black tracking-normal text-slate-950">Décisions actionnables</h2>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Les résumés courts et longs préparent la future aide à la décision.
              </p>
            </div>
          </div>
        </div>

        <img
          class="pointer-events-none absolute left-[44%] top-[23%] hidden w-[590px] max-w-none -translate-x-4 select-none lg:block xl:left-[45%] xl:w-[700px]"
          :src="signinVisual"
          alt=""
          aria-hidden="true"
        />

        <div class="relative z-10 mt-10 grid max-w-[720px] gap-4 border-t border-slate-100 pt-8 md:grid-cols-3">
          <div class="flex gap-3">
            <CheckCircle2 class="mt-1 shrink-0 text-emerald-500" :size="22" />
            <p class="text-sm font-bold leading-6 text-slate-600">Admin créé automatiquement</p>
          </div>
          <div class="flex gap-3">
            <CheckCircle2 class="mt-1 shrink-0 text-emerald-500" :size="22" />
            <p class="text-sm font-bold leading-6 text-slate-600">Organisation isolée en base</p>
          </div>
          <div class="flex gap-3">
            <CheckCircle2 class="mt-1 shrink-0 text-emerald-500" :size="22" />
            <p class="text-sm font-bold leading-6 text-slate-600">Prêt pour inviter une équipe</p>
          </div>
        </div>
      </div>

      <aside class="relative grid place-items-center bg-gradient-to-br from-white via-slate-50 to-blue-50/60 px-6 py-10 lg:px-12">
        <form
          class="w-full max-w-[520px] rounded-2xl border border-slate-200 bg-white/95 px-7 py-8 shadow-[0_26px_70px_rgba(15,23,42,0.10)] backdrop-blur sm:px-10 lg:py-10"
          @submit.prevent="handleSignup"
        >
          <div>
            <h2 class="text-3xl font-black tracking-normal text-slate-950">Créer votre espace</h2>
            <p class="mt-3 text-base font-medium text-slate-500">
              Un compte admin et une organisation sont créés ensemble.
            </p>
          </div>

          <div class="mt-8 grid gap-4">
            <div class="grid gap-4 sm:grid-cols-2">
              <label class="grid gap-2 text-sm font-bold text-slate-700">
                Prénom
                <span class="relative">
                  <User class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="19" />
                  <input
                    v-model="firstName"
                    class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-4 text-base font-semibold text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                    type="text"
                    autocomplete="given-name"
                    placeholder="Jonathan"
                  />
                </span>
              </label>

              <label class="grid gap-2 text-sm font-bold text-slate-700">
                Nom
                <span class="relative">
                  <User class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="19" />
                  <input
                    v-model="lastName"
                    class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-4 text-base font-semibold text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                    type="text"
                    autocomplete="family-name"
                    placeholder="Kouassi"
                  />
                </span>
              </label>
            </div>

            <label class="grid gap-2 text-sm font-bold text-slate-700">
              Organisation
              <span class="relative">
                <Building2 class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="20" />
                <input
                  v-model="organizationName"
                  class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-4 text-base font-semibold text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  type="text"
                  autocomplete="organization"
                  placeholder="Nom de votre entreprise"
                />
              </span>
            </label>

            <label class="grid gap-2 text-sm font-bold text-slate-700">
              Adresse e-mail
              <span class="relative">
                <Mail class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="20" />
                <input
                  v-model="email"
                  class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-4 text-base font-semibold text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  type="email"
                  autocomplete="email"
                  placeholder="votre@email.com"
                />
              </span>
            </label>

            <label class="grid gap-2 text-sm font-bold text-slate-700">
              Mot de passe
              <span class="relative">
                <Lock class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="20" />
                <input
                  v-model="password"
                  class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-12 text-base font-semibold text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  placeholder="Minimum 8 caractères"
                />
                <button
                  class="absolute right-4 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-md text-slate-400 transition hover:bg-slate-100 hover:text-blue-600"
                  type="button"
                  :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
                  @click="showPassword = !showPassword"
                >
                  <EyeOff v-if="showPassword" :size="20" />
                  <Eye v-else :size="20" />
                </button>
              </span>
            </label>

            <label class="grid gap-2 text-sm font-bold text-slate-700">
              Confirmation
              <span class="relative">
                <Lock class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="20" />
                <input
                  v-model="confirmPassword"
                  class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-12 text-base font-semibold text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  placeholder="Répétez le mot de passe"
                />
                <button
                  class="absolute right-4 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-md text-slate-400 transition hover:bg-slate-100 hover:text-blue-600"
                  type="button"
                  :aria-label="showConfirmPassword ? 'Masquer la confirmation' : 'Afficher la confirmation'"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <EyeOff v-if="showConfirmPassword" :size="20" />
                  <Eye v-else :size="20" />
                </button>
              </span>
            </label>
          </div>

          <label class="mt-5 flex cursor-pointer items-center gap-3 text-sm font-semibold text-slate-500">
            <input
              v-model="rememberMe"
              class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              type="checkbox"
            />
            Rester connecté
          </label>

          <p
            v-if="errorMessage"
            class="mt-5 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold text-red-600"
          >
            {{ errorMessage }}
          </p>

          <div class="mt-6 flex gap-4 rounded-lg bg-blue-50 px-5 py-4">
            <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-blue-600 text-white">
              <ShieldCheck :size="22" />
            </div>
            <p class="text-sm font-medium leading-6 text-slate-600">
              Vos réunions seront rattachées à cette organisation et isolées des autres espaces.
            </p>
          </div>

          <button
            class="mt-7 inline-flex h-13 w-full items-center justify-center gap-2 rounded-lg bg-blue-600 text-base font-black text-white shadow-[0_14px_28px_rgba(37,99,235,0.25)] transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
            type="submit"
            :disabled="isSubmitting"
          >
            <LoaderCircle v-if="isSubmitting" class="h-5 w-5 animate-spin" />
            Créer l'espace
          </button>

          <p class="mt-8 text-center text-sm font-medium text-slate-500">
            Vous avez déjà un compte ?
            <RouterLink class="font-black text-blue-600 transition hover:text-blue-700" to="/login">
              Se connecter
            </RouterLink>
          </p>
        </form>
      </aside>
    </section>
  </main>
</template>
