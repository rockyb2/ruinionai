<script setup>
import { ref } from 'vue'
import {
  AudioLines,
  Download,
  Eye,
  FileText,
  Lock,
  Mail,
  Mic,
  ShieldCheck,
  Sparkles,
  SquareCheckBig,
  User,
} from '@lucide/vue'
import signinVisual from '../assets/visuelsignin.png'

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)

function handleSignup() {
  console.log({
    fullName: fullName.value,
    email: email.value,
  })
}
</script>

<template>
  <main class="min-h-screen overflow-hidden bg-white text-[#071124]">
    <section class="relative mx-auto grid min-h-screen w-full max-w-[1728px] grid-cols-1 lg:grid-cols-[1fr_620px]">
      <div class="relative px-6 py-8 sm:px-10 lg:px-14 xl:px-16">
        <div class="flex items-center gap-4">
          <div class="grid h-12 w-12 place-items-center rounded-2xl bg-blue-600 text-white shadow-[0_18px_34px_rgba(37,99,235,0.28)]">
            <AudioLines :size="26" :stroke-width="2.6" />
          </div>
          <div>
            <p class="text-2xl font-black leading-none tracking-normal">
              REUNION <span class="text-blue-600">AI</span>
            </p>
            <p class="mt-2 text-sm font-medium text-slate-500">
              Votre assistant de réunion intelligent
            </p>
          </div>
        </div>

        <div class="relative z-10 mt-16 max-w-[650px] lg:mt-14">
          <h1 class="text-4xl font-black leading-[1.18] tracking-normal text-slate-950 sm:text-5xl lg:text-[3.35rem]">
            Créez votre compte et boostez vos réunions avec
            <span class="text-blue-600"> l’IA</span>
          </h1>
          <p class="mt-7 max-w-lg text-lg font-medium leading-8 text-slate-500">
            Transcrivez, analysez et obtenez des résumés intelligents en quelques clics.
          </p>
        </div>

        <div class="relative z-10 mt-9 grid max-w-lg gap-6">
          <div class="flex gap-5">
            <div class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-600">
              <Mic :size="28" />
            </div>
            <div>
              <h2 class="text-base font-black tracking-normal text-slate-950">Transcription précise</h2>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Reconnaissance vocale avancée dans plusieurs langues.
              </p>
            </div>
          </div>

          <div class="flex gap-5">
            <div class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-600">
              <Sparkles :size="27" />
            </div>
            <div>
              <h2 class="text-base font-black tracking-normal text-slate-950">Résumés intelligents</h2>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Synthèse automatique des points clés, décisions et actions.
              </p>
            </div>
          </div>

          <div class="flex gap-5">
            <div class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-600">
              <SquareCheckBig :size="27" />
            </div>
            <div>
              <h2 class="text-base font-black tracking-normal text-slate-950">Actions & décisions</h2>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Identification automatique des tâches et responsabilités.
              </p>
            </div>
          </div>

          <div class="flex gap-5">
            <div class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-600">
              <Download :size="28" />
            </div>
            <div>
              <h2 class="text-base font-black tracking-normal text-slate-950">Export facile</h2>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Exportez vos résumés en PDF, Word ou Markdown.
              </p>
            </div>
          </div>
        </div>

        <img
          class="pointer-events-none absolute left-[43%] top-[24%] hidden w-[590px] max-w-none -translate-x-4 select-none lg:block xl:left-[45%] xl:w-[710px]"
          :src="signinVisual"
          alt=""
          aria-hidden="true"
        />

        <div class="relative z-10 mt-10 max-w-[620px] rounded-2xl bg-blue-50/70 p-6 shadow-[0_18px_44px_rgba(37,99,235,0.07)] lg:mt-9">
          <div class="flex gap-5">
            <div class="text-5xl font-black leading-none text-blue-600">“</div>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium leading-6 text-slate-600">
                Reunion AI a transformé notre façon de collaborer. Nos réunions sont maintenant plus productives et mieux suivies.
              </p>
              <div class="mt-5 flex flex-wrap items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                  <div class="grid h-11 w-11 place-items-center rounded-full bg-gradient-to-br from-blue-200 to-slate-200 text-sm font-black text-slate-700">
                    KA
                  </div>
                  <div>
                    <p class="text-sm font-black text-slate-950">Koffi A.</p>
                    <p class="text-xs font-medium text-slate-500">Chef de projet</p>
                  </div>
                </div>
                <div class="flex items-center gap-2 text-sm font-black text-slate-700">
                  <span class="text-amber-400">★★★★★</span>
                  4.9/5
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <aside class="relative grid place-items-center bg-gradient-to-br from-white via-slate-50 to-blue-50/60 px-6 py-10 lg:px-12">
        <form
          class="w-full max-w-[520px] rounded-2xl border border-slate-200 bg-white/90 px-7 py-9 shadow-[0_26px_70px_rgba(15,23,42,0.10)] backdrop-blur sm:px-10 lg:py-11"
          @submit.prevent="handleSignup"
        >
          <div>
            <h2 class="text-3xl font-black tracking-normal text-slate-950">Créer un compte</h2>
            <p class="mt-3 text-base font-medium text-slate-500">
              Rejoignez des milliers d’équipes productives.
            </p>
          </div>

          <div class="mt-9 grid gap-5">
            <label class="grid gap-2 text-sm font-bold text-slate-700">
              Nom complet
              <span class="relative">
                <User class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="20" />
                <input
                  v-model="fullName"
                  class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-4 text-base font-semibold text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  type="text"
                  autocomplete="name"
                  placeholder="Votre nom complet"
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
                  aria-label="Afficher le mot de passe"
                  @click="showPassword = !showPassword"
                >
                  <Eye :size="20" />
                </button>
              </span>
            </label>

            <label class="grid gap-2 text-sm font-bold text-slate-700">
              Confirmer le mot de passe
              <span class="relative">
                <Lock class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="20" />
                <input
                  v-model="confirmPassword"
                  class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-12 text-base font-semibold text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  placeholder="Répétez votre mot de passe"
                />
                <button
                  class="absolute right-4 top-1/2 grid h-8 w-8 -translate-y-1/2 place-items-center rounded-md text-slate-400 transition hover:bg-slate-100 hover:text-blue-600"
                  type="button"
                  aria-label="Afficher la confirmation du mot de passe"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <Eye :size="20" />
                </button>
              </span>
            </label>
          </div>

          <div class="mt-6 flex gap-4 rounded-lg bg-blue-50 px-5 py-4">
            <div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-blue-600 text-white">
              <ShieldCheck :size="24" />
            </div>
            <p class="text-sm font-medium leading-6 text-slate-600">
              En créant un compte, vous acceptez nos
              <a class="font-black text-blue-600 hover:text-blue-700" href="#">Conditions d’utilisation</a>
              et
              <a class="font-black text-blue-600 hover:text-blue-700" href="#">Politique de confidentialité</a>.
            </p>
          </div>

          <button
            class="mt-7 h-13 w-full rounded-lg bg-blue-600 text-base font-black text-white shadow-[0_14px_28px_rgba(37,99,235,0.25)] transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200"
            type="submit"
          >
            S’inscrire
          </button>

          <div class="my-8 flex items-center gap-4 text-sm font-medium text-slate-400">
            <span class="h-px flex-1 bg-slate-200"></span>
            ou continuer avec
            <span class="h-px flex-1 bg-slate-200"></span>
          </div>

          <div class="grid gap-3 sm:grid-cols-2">
            <button
              class="flex h-13 items-center justify-center gap-3 rounded-lg border border-slate-200 bg-white text-base font-black text-slate-800 transition hover:border-blue-200 hover:bg-blue-50"
              type="button"
            >
              <span class="text-xl font-black text-[#4285F4]">G</span>
              Google
            </button>
            <button
              class="flex h-13 items-center justify-center gap-3 rounded-lg border border-slate-200 bg-white text-base font-black text-slate-800 transition hover:border-blue-200 hover:bg-blue-50"
              type="button"
            >
              <span class="grid grid-cols-2 gap-0.5">
                <span class="h-2.5 w-2.5 bg-[#f25022]"></span>
                <span class="h-2.5 w-2.5 bg-[#7fba00]"></span>
                <span class="h-2.5 w-2.5 bg-[#00a4ef]"></span>
                <span class="h-2.5 w-2.5 bg-[#ffb900]"></span>
              </span>
              Microsoft
            </button>
          </div>

          <p class="mt-10 text-center text-sm font-medium text-slate-500">
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
