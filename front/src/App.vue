<script setup>
import { onBeforeUnmount, onErrorCaptured, onMounted, ref } from 'vue'

const appError = ref('')

function showError(error) {
  appError.value = error?.message || 'Une erreur inattendue empêche cette page de s’afficher.'
}

function handleGlobalError(event) {
  showError(event.detail)
}

function reloadPage() {
  window.location.reload()
}

onErrorCaptured((error) => {
  showError(error)
  return false
})
onMounted(() => window.addEventListener('ruinion-app-error', handleGlobalError))
onBeforeUnmount(() => window.removeEventListener('ruinion-app-error', handleGlobalError))
</script>

<template>
  <main v-if="appError" class="grid min-h-screen place-items-center bg-slate-50 p-6 text-slate-900">
    <section class="w-full max-w-lg rounded-2xl border border-red-100 bg-white p-8 text-center shadow-xl shadow-slate-200/50" role="alert">
      <p class="text-xs font-black uppercase tracking-wider text-red-600">Affichage interrompu</p>
      <h1 class="mt-3 text-2xl font-black">Cette page n’a pas pu s’afficher</h1>
      <p class="mt-3 text-sm leading-6 text-slate-600">{{ appError }}</p>
      <div class="mt-6 flex flex-wrap justify-center gap-3">
        <button type="button" class="rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold text-white" @click="reloadPage">Recharger</button>
        <a href="/réunion" class="rounded-xl border border-slate-200 px-5 py-3 text-sm font-bold text-slate-700">Retour à l’accueil</a>
      </div>
    </section>
  </main>
  <RouterView v-else />
</template>
