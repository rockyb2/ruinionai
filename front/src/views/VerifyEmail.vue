<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CheckCircle2, LoaderCircle, Mail, RefreshCw, TriangleAlert } from '@lucide/vue'

import logo from '@/assets/logo.png'
import { resendVerificationEmail, verifyEmail } from '@/service/api'

const route = useRoute()
const router = useRouter()

const storedEmail = window.sessionStorage.getItem('ruinionai.pending_verification_email') || ''
const email = ref(typeof route.query.email === 'string' ? route.query.email : storedEmail)
const fragmentToken = new URLSearchParams(route.hash.replace(/^#/, '')).get('token') || ''
const legacyQueryToken = typeof route.query.token === 'string' ? route.query.token : ''
const initialToken = fragmentToken || legacyQueryToken
const alreadyVerified = route.query.verified === '1'
const state = ref(alreadyVerified ? 'success' : initialToken ? 'verifying' : 'pending')
const message = ref(
  alreadyVerified
    ? 'Votre adresse e-mail est vérifiée. Vous pouvez vous connecter.'
    : 'Un e-mail de vérification vient de vous être envoyé.',
)
const isResending = ref(false)
const resendMessage = ref('')

async function confirmEmail() {
  const token = initialToken
  if (!token) return

  try {
    const result = await verifyEmail(token)
    state.value = 'success'
    message.value = result.message
    window.sessionStorage.removeItem('ruinionai.pending_verification_email')
    await router.replace({ name: 'verify-email', query: { verified: '1' } })
  } catch (error) {
    state.value = 'error'
    message.value = error.message || "Impossible de vérifier l'adresse e-mail."
    await router.replace({
      name: 'verify-email',
      query: email.value ? { email: email.value } : {},
    })
  }
}

async function resend() {
  if (!email.value.trim()) {
    resendMessage.value = 'Saisissez votre adresse e-mail.'
    return
  }

  try {
    isResending.value = true
    resendMessage.value = ''
    const result = await resendVerificationEmail(email.value.trim())
    resendMessage.value = result.message
  } catch (error) {
    resendMessage.value = error.message || "Impossible de renvoyer l'e-mail."
  } finally {
    isResending.value = false
  }
}

onMounted(confirmEmail)
</script>

<template>
  <main class="grid min-h-screen place-items-center bg-gradient-to-br from-slate-50 via-white to-blue-50 px-5 py-12 text-slate-950">
    <section class="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-[0_28px_80px_rgba(15,23,42,0.10)] sm:p-11">
      <RouterLink class="mx-auto block w-fit" to="/connexion">
        <img :src="logo" alt="Ruinion AI" class="h-14 w-auto" />
      </RouterLink>

      <div class="mx-auto mt-10 grid h-20 w-20 place-items-center rounded-full" :class="state === 'error' ? 'bg-red-50 text-red-600' : state === 'success' ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600'">
        <LoaderCircle v-if="state === 'verifying'" class="animate-spin" :size="38" />
        <CheckCircle2 v-else-if="state === 'success'" :size="38" />
        <TriangleAlert v-else-if="state === 'error'" :size="38" />
        <Mail v-else :size="38" />
      </div>

      <h1 class="mt-7 text-3xl font-black">
        {{ state === 'verifying' ? 'Vérification en cours' : state === 'success' ? 'Adresse vérifiée' : state === 'error' ? 'Lien non valide' : 'Vérifiez votre boîte mail' }}
      </h1>
      <p class="mt-4 text-base font-medium leading-7 text-slate-600">{{ message }}</p>

      <RouterLink
        v-if="state === 'success'"
        class="mt-8 inline-flex h-12 w-full items-center justify-center rounded-xl bg-blue-600 font-black text-white transition hover:bg-blue-700"
        to="/connexion"
      >
        Se connecter
      </RouterLink>

      <form v-else-if="state !== 'verifying'" class="mt-8 grid gap-4 text-left" @submit.prevent="resend">
        <label class="grid gap-2 text-sm font-bold text-slate-700">
          Adresse e-mail
          <input
            v-model="email"
            class="h-12 rounded-xl border border-slate-200 px-4 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
            type="email"
            autocomplete="email"
            placeholder="votre@email.com"
            required
          />
        </label>
        <button
          class="inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-blue-600 font-black text-white transition hover:bg-blue-700 disabled:bg-slate-300"
          type="submit"
          :disabled="isResending"
        >
          <LoaderCircle v-if="isResending" class="animate-spin" :size="19" />
          <RefreshCw v-else :size="19" />
          Renvoyer l'e-mail
        </button>
        <p v-if="resendMessage" class="rounded-xl bg-slate-50 px-4 py-3 text-center text-sm font-semibold text-slate-600">
          {{ resendMessage }}
        </p>
      </form>

      <p v-if="state !== 'success'" class="mt-7 text-sm font-medium text-slate-500">
        Déjà vérifié ?
        <RouterLink class="font-black text-blue-600 hover:text-blue-700" to="/connexion">Se connecter</RouterLink>
      </p>
    </section>
  </main>
</template>
