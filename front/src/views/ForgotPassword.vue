<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import {
  ArrowLeft,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  Lock,
  Mail,
} from '@lucide/vue'
import logo from '@/assets/logo.png'
import logoR from '@/assets/logoR.png'
import {
  requestPasswordReset,
  resetPassword,
  verifyPasswordResetCode,
} from '@/service/api'

const step = ref('email')
const email = ref('')
const code = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const isSubmitting = ref(false)
const message = ref('')
const errorMessage = ref('')
const resendCooldown = ref(0)
const resetToken = ref('')
let resendTimer

const title = computed(() => {
  if (step.value === 'success') return 'Mot de passe modifié'
  if (step.value === 'password') return 'Choisissez un nouveau mot de passe'
  if (step.value === 'code') return 'Saisissez votre code'
  return 'Mot de passe oublié'
})

function startResendCooldown() {
  window.clearInterval(resendTimer)
  resendCooldown.value = 120
  resendTimer = window.setInterval(() => {
    resendCooldown.value -= 1
    if (resendCooldown.value <= 0) window.clearInterval(resendTimer)
  }, 1000)
}

onBeforeUnmount(() => window.clearInterval(resendTimer))

async function requestCode() {
  if (!email.value.trim()) {
    errorMessage.value = 'Saisissez votre adresse e-mail.'
    return
  }

  try {
    isSubmitting.value = true
    errorMessage.value = ''
    const result = await requestPasswordReset(email.value.trim())
    message.value = result.message
    step.value = 'code'
    startResendCooldown()
  } catch (error) {
    errorMessage.value = error.message || "Impossible d'envoyer le code."
  } finally {
    isSubmitting.value = false
  }
}

async function submitCode() {
  if (!/^\d{8}$/.test(code.value)) {
    errorMessage.value = 'Le code doit contenir exactement 8 chiffres.'
    return
  }

  try {
    isSubmitting.value = true
    errorMessage.value = ''
    const result = await verifyPasswordResetCode(email.value.trim(), code.value)
    resetToken.value = result.reset_token
    step.value = 'password'
  } catch (error) {
    errorMessage.value = error.message || 'Impossible de vérifier le code.'
  } finally {
    isSubmitting.value = false
  }
}

async function submitNewPassword() {
  if (newPassword.value.length < 8) {
    errorMessage.value = 'Le mot de passe doit contenir au moins 8 caractères.'
    return
  }
  if (new TextEncoder().encode(newPassword.value).length > 72) {
    errorMessage.value = 'Le mot de passe est trop long.'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'Les deux mots de passe ne correspondent pas.'
    return
  }

  try {
    isSubmitting.value = true
    errorMessage.value = ''
    await resetPassword({
      reset_token: resetToken.value,
      new_password: newPassword.value,
    })
    step.value = 'success'
  } catch (error) {
    errorMessage.value = error.message || 'Impossible de modifier le mot de passe.'
  } finally {
    isSubmitting.value = false
  }
}

async function resendCode() {
  if (resendCooldown.value > 0) return
  code.value = ''
  await requestCode()
}
</script>

<template>
  <main class="grid min-h-screen bg-gradient-to-br from-white via-slate-50 to-blue-50/60 px-5 py-8 text-[#071124]">
    <RouterLink class="absolute left-6 top-6 flex w-fit items-center sm:left-10 sm:top-8" to="/connexion">
      <img :src="logo" alt="Ruinion AI" class="h-12 w-auto max-w-[220px] object-contain" />
    </RouterLink>

    <section class="m-auto w-full max-w-[460px] rounded-2xl border border-slate-200 bg-white px-7 py-10 shadow-[0_26px_70px_rgba(15,23,42,0.10)] sm:px-9">
      <div class="grid justify-items-center text-center">
        <img :src="logoR" alt="" class="h-16 w-16" aria-hidden="true" />
        <div
          v-if="step === 'success'"
          class="mt-7 grid h-14 w-14 place-items-center rounded-full bg-emerald-50 text-emerald-600"
        >
          <CheckCircle2 :size="30" />
        </div>
        <h1 class="mt-7 text-2xl font-black text-slate-950">{{ title }}</h1>
        <p v-if="step === 'email'" class="mt-3 text-sm font-medium leading-6 text-slate-500">
          Indiquez l'adresse associée à votre compte. Nous vous enverrons un code temporaire.
        </p>
        <p v-else-if="step === 'code'" class="mt-3 text-sm font-medium leading-6 text-slate-500">
          Entrez le code envoyé à <strong class="text-slate-700">{{ email }}</strong>.
        </p>
        <p v-else-if="step === 'password'" class="mt-3 text-sm font-medium leading-6 text-slate-500">
          Votre code a été validé. Vous pouvez maintenant renseigner votre nouveau mot de passe.
        </p>
        <p v-else class="mt-3 text-sm font-medium leading-6 text-slate-500">
          Votre nouveau mot de passe est actif. Toutes vos anciennes sessions ont été déconnectées.
        </p>
      </div>

      <form v-if="step === 'email'" class="mt-8 grid gap-5" @submit.prevent="requestCode">
        <label class="grid gap-2 text-sm font-bold text-slate-600">
          Adresse e-mail
          <span class="relative">
            <Mail class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="20" />
            <input
              v-model="email"
              class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-4 font-semibold outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              type="email"
              autocomplete="email"
              required
              autofocus
              placeholder="votre@email.com"
            />
          </span>
        </label>

        <button
          class="inline-flex h-13 cursor-pointer items-center justify-center gap-2 rounded-lg bg-blue-600 font-black text-white shadow-[0_14px_28px_rgba(37,99,235,0.25)] transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          type="submit"
          :disabled="isSubmitting"
        >
          <LoaderCircle v-if="isSubmitting" class="h-5 w-5 animate-spin" />
          Recevoir mon code
        </button>
      </form>

      <form v-else-if="step === 'code'" class="mt-7 grid gap-5" @submit.prevent="submitCode">
        <p v-if="message" class="rounded-lg bg-blue-50 px-4 py-3 text-center text-sm font-semibold text-blue-700">
          {{ message }}
        </p>

        <label class="grid gap-2 text-sm font-bold text-slate-600">
          Code temporaire
          <span class="relative">
            <KeyRound class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="20" />
            <input
              v-model="code"
              class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-4 text-center text-xl font-black tracking-[0.25em] outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              inputmode="numeric"
              autocomplete="one-time-code"
              maxlength="8"
              pattern="[0-9]{8}"
              required
              placeholder="00000000"
            />
          </span>
        </label>

        <button
          class="inline-flex h-13 cursor-pointer items-center justify-center gap-2 rounded-lg bg-blue-600 font-black text-white shadow-[0_14px_28px_rgba(37,99,235,0.25)] transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          type="submit"
          :disabled="isSubmitting"
        >
          <LoaderCircle v-if="isSubmitting" class="h-5 w-5 animate-spin" />
          Vérifier le code
        </button>

        <button
          class="cursor-pointer text-sm font-bold text-blue-600 hover:text-blue-700 disabled:cursor-not-allowed disabled:text-slate-400"
          type="button"
          :disabled="isSubmitting || resendCooldown > 0"
          @click="resendCode"
        >
          {{ resendCooldown > 0 ? `Renvoyer un code dans ${resendCooldown} s` : 'Renvoyer un code' }}
        </button>
      </form>

      <form v-else-if="step === 'password'" class="mt-7 grid gap-5" @submit.prevent="submitNewPassword">
        <label class="grid gap-2 text-sm font-bold text-slate-600">
          Nouveau mot de passe
          <span class="relative">
            <Lock class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" :size="20" />
            <input
              v-model="newPassword"
              class="h-13 w-full rounded-lg border border-slate-200 bg-white pl-12 pr-12 font-semibold outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="new-password"
              minlength="8"
              required
              placeholder="8 caractères minimum"
            />
            <button
              class="absolute right-4 top-1/2 grid h-8 w-8 -translate-y-1/2 cursor-pointer place-items-center rounded-md text-slate-400 hover:bg-slate-100 hover:text-blue-600"
              type="button"
              :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
              @click="showPassword = !showPassword"
            >
              <EyeOff v-if="showPassword" :size="20" />
              <Eye v-else :size="20" />
            </button>
          </span>
        </label>

        <label class="grid gap-2 text-sm font-bold text-slate-600">
          Confirmer le mot de passe
          <input
            v-model="confirmPassword"
            class="h-13 w-full rounded-lg border border-slate-200 bg-white px-4 font-semibold outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="new-password"
            minlength="8"
            required
            placeholder="Saisissez-le une seconde fois"
          />
        </label>

        <button
          class="inline-flex h-13 cursor-pointer items-center justify-center gap-2 rounded-lg bg-blue-600 font-black text-white shadow-[0_14px_28px_rgba(37,99,235,0.25)] transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          type="submit"
          :disabled="isSubmitting"
        >
          <LoaderCircle v-if="isSubmitting" class="h-5 w-5 animate-spin" />
          Modifier mon mot de passe
        </button>
      </form>

      <RouterLink
        v-if="step === 'success'"
        class="mt-8 inline-flex h-13 w-full cursor-pointer items-center justify-center rounded-lg bg-blue-600 font-black text-white transition hover:bg-blue-700"
        to="/connexion"
      >
        Se connecter
      </RouterLink>

      <p v-if="errorMessage" class="mt-5 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold text-red-600">
        {{ errorMessage }}
      </p>

      <RouterLink
        v-if="step !== 'success'"
        class="mt-7 flex cursor-pointer items-center justify-center gap-2 text-sm font-bold text-slate-500 transition hover:text-blue-600"
        to="/connexion"
      >
        <ArrowLeft :size="17" />
        Retour à la connexion
      </RouterLink>
    </section>
  </main>
</template>
