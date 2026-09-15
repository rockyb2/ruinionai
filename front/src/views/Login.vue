<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AudioLines,
  CheckCircle2,
  Eye,
  EyeOff,
  FileText,
  LoaderCircle,
  Lock,
  Mail,
  Mic,
  ShieldCheck,
  SquareCheckBig,
} from '@lucide/vue'

import loginVisual from '../assets/visuel1login.png'
import { loginUser } from '@/service/api'

const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const rememberMe = ref(true)
const showPassword = ref(false)
const isSubmitting = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  if (!email.value.trim() || !password.value) {
    errorMessage.value = 'Renseignez votre email et votre mot de passe.'
    return
  }

  try {
    isSubmitting.value = true
    errorMessage.value = ''

    await loginUser(
      {
        email: email.value,
        password: password.value,
      },
      rememberMe.value,
    )

    const redirectTo =
      typeof route.query.redirect === 'string' ? route.query.redirect : '/reunion'

    router.push(redirectTo)
  } catch (error) {
    errorMessage.value = error.message || 'Connexion impossible pour le moment.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="min-h-screen overflow-hidden bg-white text-[#071124]">
    <section class="relative mx-auto grid min-h-screen w-full max-w-[1728px] grid-cols-1 lg:grid-cols-[1fr_540px]">
      <div class="relative px-6 py-8 sm:px-10 lg:px-16">
        <RouterLink class="flex w-fit items-center gap-4" to="/login">
          <div class="grid h-12 w-12 place-items-center rounded-2xl bg-blue-600 text-white shadow-[0_18px_34px_rgba(37,99,235,0.28)]">
            <AudioLines :size="26" :stroke-width="2.6" />
          </div>
          <div>
            <p class="text-2xl font-black leading-none tracking-normal">
              RUINION <span class="text-blue-600">AI</span>
            </p>
            <p class="mt-2 text-sm font-medium text-slate-500">
              Mémoire de réunion pour équipes exigeantes
            </p>
          </div>
        </RouterLink>

        <div class="relative z-10 mt-16 max-w-[660px] lg:mt-14">
          <p class="inline-flex items-center gap-2 rounded-full bg-blue-50 px-4 py-2 text-sm font-black text-blue-600">
            <ShieldCheck class="h-4 w-4" />
            Espace sécurisé
          </p>
          <h1 class="mt-6 text-4xl font-black leading-[1.18] tracking-normal text-slate-950 sm:text-5xl lg:text-[3.35rem]">
            Retrouvez chaque décision, chaque action, chaque réunion.
          </h1>
          <p class="mt-7 max-w-lg text-lg font-medium leading-8 text-slate-500">
            Connectez-vous à votre espace et transformez vos réunions en comptes rendus exploitables.
          </p>
        </div>

        <div class="relative z-10 mt-12 grid max-w-lg gap-7">
          <div class="flex gap-5">
            <div class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-600">
              <Mic :size="27" />
            </div>
            <div>
              <h2 class="text-base font-black tracking-normal text-slate-950">Transcription centralisée</h2>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Vos réunions restent rattachées au bon espace d'équipe.
              </p>
            </div>
          </div>

          <div class="flex gap-5">
            <div class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-600">
              <FileText :size="27" />
            </div>
            <div>
              <h2 class="text-base font-black tracking-normal text-slate-950">Résumés courts et détaillés</h2>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Une lecture rapide pour décider, un compte rendu complet pour garder la trace.
              </p>
            </div>
          </div>

          <div class="flex gap-5">
            <div class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-600">
              <SquareCheckBig :size="27" />
            </div>
            <div>
              <h2 class="text-base font-black tracking-normal text-slate-950">Actions et responsabilités</h2>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Les prochaines étapes deviennent visibles dès la fin de la réunion.
              </p>
            </div>
          </div>
        </div>

        <img
          class="pointer-events-none absolute left-[45%] top-[26%] hidden w-[620px] max-w-none -translate-x-10 select-none lg:block xl:w-[720px]"
          :src="loginVisual"
          alt=""
          aria-hidden="true"
        />

        <div class="relative z-10 mt-14 grid gap-4 border-t border-slate-100 pt-8 md:grid-cols-3 lg:max-w-[870px]">
          <div class="flex gap-3">
            <CheckCircle2 class="mt-1 shrink-0 text-emerald-500" :size="22" />
            <p class="text-sm font-bold leading-6 text-slate-600">Données isolées par organisation</p>
          </div>
          <div class="flex gap-3">
            <CheckCircle2 class="mt-1 shrink-0 text-emerald-500" :size="22" />
            <p class="text-sm font-bold leading-6 text-slate-600">Accès sécurisé par JWT</p>
          </div>
          <div class="flex gap-3">
            <CheckCircle2 class="mt-1 shrink-0 text-emerald-500" :size="22" />
            <p class="text-sm font-bold leading-6 text-slate-600">Prêt pour une équipe SaaS</p>
          </div>
        </div>
      </div>

      <aside class="relative grid place-items-center bg-gradient-to-br from-white via-slate-50 to-blue-50/60 px-6 py-10 lg:px-12">
        <form
          class="w-full max-w-[456px] rounded-2xl border border-slate-200 bg-white/95 px-7 py-10 shadow-[0_26px_70px_rgba(15,23,42,0.10)] backdrop-blur sm:px-9 lg:py-12"
          @submit.prevent="handleLogin"
        >
          <div class="grid justify-items-center text-center">
            <div class="grid h-14 w-14 place-items-center rounded-2xl bg-blue-600 text-white shadow-[0_16px_32px_rgba(37,99,235,0.32)]">
              <AudioLines :size="30" :stroke-width="2.6" />
            </div>
            <h2 class="mt-8 text-2xl font-black tracking-normal text-slate-950">
              Connexion
            </h2>
            <p class="mt-2 text-sm font-medium text-slate-500">
              Accédez à votre espace Ruinion AI
            </p>
          </div>

          <div class="mt-9 grid gap-6">
            <label class="grid gap-2 text-sm font-bold text-slate-600">
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

            <label class="grid gap-2 text-sm font-bold text-slate-600">
              Mot de passe
              <span class="relative">
                <Lock class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="20" />
                <input
                  v-model="password"
                  class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-12 text-base font-semibold text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  placeholder="Votre mot de passe"
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
          </div>

          <div class="mt-5 flex items-center justify-between gap-3 text-sm font-semibold">
            <label class="flex cursor-pointer items-center gap-3 text-slate-500">
              <input
                v-model="rememberMe"
                class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                type="checkbox"
              />
              Se souvenir de moi
            </label>
          </div>

          <p
            v-if="errorMessage"
            class="mt-5 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold text-red-600"
          >
            {{ errorMessage }}
          </p>

          <button
            class="mt-7 inline-flex h-13 w-full items-center justify-center gap-2 rounded-lg bg-blue-600 text-base font-black text-white shadow-[0_14px_28px_rgba(37,99,235,0.25)] transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
            type="submit"
            :disabled="isSubmitting"
          >
            <LoaderCircle v-if="isSubmitting" class="h-5 w-5 animate-spin" />
            Se connecter
          </button>

          <p class="mt-10 text-center text-sm font-medium text-slate-500">
            Pas encore de compte ?
            <RouterLink class="font-black text-blue-600 transition hover:text-blue-700" to="/signin">
              Créer un espace
            </RouterLink>
          </p>
        </form>
      </aside>
    </section>
  </main>
</template>
