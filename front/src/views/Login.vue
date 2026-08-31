<script setup>
import { ref } from 'vue'
import {
  AudioLines,
  Cloud,
  Download,
  Eye,
  FileText,
  Lock,
  Mail,
  Mic,
  ShieldCheck,
  SquareCheckBig,
} from '@lucide/vue'
import loginVisual from '../assets/visuel1login.png'
import { useRouter } from 'vue-router'
const email = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)
const router = useRouter()

function handleLogin() {
  if (email.value)  {
    router.push('/')
  }
  else{
    console.log("Erreur")
  }


  console.log({
    email: email.value,
    rememberMe: rememberMe.value,
  })
}


</script>

<template>
  <main class="min-h-screen overflow-hidden bg-white text-[#071124]">
    <section class="relative mx-auto grid min-h-screen w-full max-w-[1728px] grid-cols-1 lg:grid-cols-[1fr_560px]">
      <div class="relative px-6 py-8 sm:px-10 lg:px-16 lg:py-8">
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

        <div class="relative z-10 mt-16 max-w-[660px] lg:mt-14">
          <h1 class="text-4xl font-black leading-[1.18] tracking-normal text-slate-950 sm:text-5xl lg:text-[3.45rem]">
            Des réunions plus productives grâce à
            <span class="text-blue-600"> l’IA</span>
          </h1>
          <p class="mt-7 max-w-lg text-lg font-medium leading-8 text-slate-500">
            Enregistrez, transcrivez et obtenez des résumés intelligents en quelques clics.
          </p>
        </div>

        <div class="relative z-10 mt-12 grid max-w-lg gap-8">
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
              <FileText :size="27" />
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
          class="pointer-events-none absolute left-[40%] top-[26%] hidden w-[650px] max-w-none -translate-x-10 select-none lg:block xl:w-[760px]"
          :src="loginVisual"
          alt=""
          aria-hidden="true"
        />

        <div class="relative z-10 mt-14 grid gap-5 border-t border-slate-100 pt-8 md:grid-cols-3 lg:mt-16 lg:max-w-[870px]">
          <div class="flex gap-4">
            <ShieldCheck class="mt-1 shrink-0 text-blue-600" :size="25" />
            <div>
              <h3 class="text-sm font-black tracking-normal text-slate-950">Sécurisé et confidentiel</h3>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Vos données sont protégées de bout en bout.
              </p>
            </div>
          </div>

          <div class="flex gap-4 border-slate-200 md:border-l md:pl-8">
            <Lock class="mt-1 shrink-0 text-blue-600" :size="25" />
            <div>
              <h3 class="text-sm font-black tracking-normal text-slate-950">Conforme RGPD</h3>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Vos données ne sont jamais partagées.
              </p>
            </div>
          </div>

          <div class="flex gap-4 border-slate-200 md:border-l md:pl-8">
            <Cloud class="mt-1 shrink-0 text-blue-600" :size="25" />
            <div>
              <h3 class="text-sm font-black tracking-normal text-slate-950">Accessible partout</h3>
              <p class="mt-2 text-sm font-medium leading-6 text-slate-500">
                Accédez à vos réunions depuis n’importe quel appareil.
              </p>
            </div>
          </div>
        </div>
      </div>

      <aside class="relative grid place-items-center bg-gradient-to-br from-white via-slate-50 to-blue-50/60 px-6 py-10 lg:px-12">
        <form
          class="w-full max-w-[456px] rounded-2xl border border-slate-200 bg-white/90 px-7 py-10 shadow-[0_26px_70px_rgba(15,23,42,0.10)] backdrop-blur sm:px-9 lg:py-12"
          @submit.prevent="handleLogin"
        >
          <div class="grid justify-items-center text-center">
            <div class="grid h-14 w-14 place-items-center rounded-2xl bg-blue-600 text-white shadow-[0_16px_32px_rgba(37,99,235,0.32)]">
              <AudioLines :size="30" :stroke-width="2.6" />
            </div>
            <p class="mt-5 text-xl font-black tracking-normal text-slate-950">
              REUNION <span class="text-blue-600">AI</span>
            </p>
            <h2 class="mt-8 text-2xl font-black tracking-normal text-slate-950">
              Bienvenue !
            </h2>
            <p class="mt-2 text-sm font-medium text-slate-500">
              Connectez-vous à votre compte
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
                <input
                  v-model="password"
                  class="h-13 w-full rounded-lg border border-slate-200 bg-white px-4 pr-12 text-base font-semibold text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  placeholder="••••••••••"
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
          </div>

          <div class="mt-5 flex flex-wrap items-center justify-between gap-3 text-sm font-semibold">
            <label class="flex cursor-pointer items-center gap-3 text-slate-500">
              <input
                v-model="rememberMe"
                class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                type="checkbox"
              />
              Se souvenir de moi
            </label>
            <a class="font-black text-blue-600 transition hover:text-blue-700" href="#">
              Mot de passe oublié ?
            </a>
          </div>

          <button
            class="mt-8 h-13 w-full rounded-lg bg-blue-600 text-base font-black text-white shadow-[0_14px_28px_rgba(37,99,235,0.25)] transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200"
            type="submit" 
          >
            Se connecter
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
            Pas encore de compte ?
            <RouterLink class="font-black text-blue-600 transition hover:text-blue-700" to="/signin">
              S’inscrire
            </RouterLink>
          </p>
        </form>
      </aside>
    </section>
  </main>
</template>
