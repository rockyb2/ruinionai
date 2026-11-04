<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Check,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  LoaderCircle,
  RotateCcw,
  X,
} from '@lucide/vue'

import { highlightOnboardingFeature, runOnboardingTour } from '@/onboarding/tours'
import { useOnboardingStore } from '@/stores/onboarding'

const props = defineProps({
  user: { type: Object, required: true },
  role: { type: String, default: 'member' },
})

const router = useRouter()
const onboarding = useOnboardingStore()
const tourActive = ref(false)
let disposed = false

const delay = (milliseconds) => new Promise((resolve) => window.setTimeout(resolve, milliseconds))

async function launchStep(step) {
  onboarding.error = ''
  tourActive.value = true
  await router.push(step.route)
  await nextTick()

  for (let attempt = 0; attempt < 12 && !disposed; attempt += 1) {
    await delay(attempt ? 160 : 320)
    const started = runOnboardingTour(step.tour, {
      onComplete: () => {
        if (step.completeOnTour) onboarding.completeStep(step.id)
      },
      onClose: () => {
        tourActive.value = false
      },
    })
    if (started) return
  }
  tourActive.value = false
  onboarding.error = "Cette aide n'est pas encore disponible sur cet écran."
}

function handleCompletedStep(event) {
  const stepId = event.detail?.step || event.detail
  if (typeof stepId === 'string') onboarding.completeStep(stepId)
}

onMounted(async () => {
  onboarding.initialize(props.user, props.role)
  window.addEventListener('ruinion-onboarding-complete', handleCompletedStep)

  const hintKey = `ruinion.onboarding.hint.v${props.user.onboarding_version || 1}`
  if (
    onboarding.panelOpen &&
    !onboarding.completedCount &&
    !window.sessionStorage.getItem(hintKey)
  ) {
    window.sessionStorage.setItem(hintKey, '1')
    await nextTick()
    await delay(700)
    if (!disposed) {
      highlightOnboardingFeature(
        '[data-tour="onboarding-checklist"]',
        'Votre parcours de prise en main',
        'Avancez à votre rythme. Chaque étape ouvre une aide interactive et se valide lorsque vous réalisez vraiment l’action.',
      )
    }
  }
})

onBeforeUnmount(() => {
  disposed = true
  window.removeEventListener('ruinion-onboarding-complete', handleCompletedStep)
})
</script>

<template>
  <section
    v-if="onboarding.initialized && onboarding.panelOpen && !tourActive"
    data-tour="onboarding-checklist"
    class="relative shrink-0 overflow-hidden rounded-xl border border-slate-200 bg-slate-50"
    aria-label="Checklist de prise en main"
  >
    <div class="absolute inset-x-0 top-0 h-0.5 bg-slate-200">
      <div class="h-full bg-blue-600 transition-all duration-500" :style="{ width: `${onboarding.progress}%` }" />
    </div>

    <header class="flex items-center gap-2 px-3 pb-2 pt-3">
      <div class="min-w-0 flex-1">
        <h2 class="truncate text-xs font-black text-slate-900">Prise en main</h2>
        <p class="mt-0.5 text-[10px] font-semibold text-slate-400">{{ onboarding.completedCount }}/{{ onboarding.totalCount }} étapes · {{ onboarding.progress }}%</p>
      </div>
      <button class="rounded-md p-1 text-slate-400 hover:bg-white hover:text-slate-700 disabled:opacity-50" type="button" :disabled="onboarding.saving" :aria-label="onboarding.finished ? 'Fermer définitivement le tutoriel' : 'Réduire la checklist'" @click="onboarding.finished ? onboarding.dismiss() : onboarding.panelOpen = false">
        <X class="h-3.5 w-3.5" />
      </button>
    </header>

    <div v-if="onboarding.finished" class="border-t border-slate-200 px-3 py-3">
      <div class="flex items-start gap-3">
        <CheckCircle2 class="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
        <div>
          <h3 class="text-xs font-black text-slate-900">Tutoriel terminé</h3>
          <p class="mt-1 text-[11px] font-medium leading-4 text-slate-500">Vous maîtrisez les fonctions essentielles.</p>
        </div>
      </div>
      <button class="mt-2 inline-flex items-center gap-1.5 text-[11px] font-bold text-slate-500 hover:text-blue-600" type="button" :disabled="onboarding.saving" @click="onboarding.reset">
        <RotateCcw class="h-3 w-3" /> Revoir le parcours
      </button>
    </div>

    <template v-else>
      <div class="max-h-52 overflow-y-auto border-t border-slate-200 px-2 py-1.5">
        <button
          v-for="(step, index) in onboarding.availableSteps"
          :key="step.id"
          class="group flex w-full items-center gap-2 rounded-lg px-1.5 py-1.5 text-left transition hover:bg-white"
          type="button"
          @click="launchStep(step)"
        >
          <span
            class="grid h-4 w-4 shrink-0 place-items-center rounded border text-[9px] font-black transition"
            :class="onboarding.steps[step.id] ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-slate-300 bg-white text-slate-400 group-hover:border-blue-400 group-hover:text-blue-600'"
          >
            <Check v-if="onboarding.steps[step.id]" class="h-3 w-3" />
            <span v-else>{{ index + 1 }}</span>
          </span>
          <strong class="min-w-0 flex-1 truncate text-[11px] font-semibold" :class="onboarding.steps[step.id] ? 'text-slate-400 line-through' : 'text-slate-700'">{{ step.label }}</strong>
          <ChevronRight class="h-3 w-3 shrink-0 text-slate-300 transition group-hover:text-blue-600" />
        </button>
      </div>

      <p v-if="onboarding.error" class="mx-2 mb-2 rounded-lg bg-red-50 px-2 py-1.5 text-[10px] font-bold leading-4 text-red-600">{{ onboarding.error }}</p>

      <footer v-if="onboarding.saving" class="flex items-center justify-end border-t border-slate-200 px-3 py-2">
        <span class="inline-flex items-center gap-1.5 text-[10px] font-bold text-blue-600"><LoaderCircle class="h-3 w-3 animate-spin" /> Sauvegarde</span>
      </footer>
    </template>
  </section>

  <button
    v-else-if="onboarding.initialized && !tourActive && !onboarding.finished"
    class="flex w-full shrink-0 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-left transition hover:border-blue-200 hover:bg-blue-50"
    type="button"
    aria-label="Ouvrir la checklist de prise en main"
    @click="onboarding.reopen"
  >
    <CircleHelp class="h-4 w-4 shrink-0 text-blue-600" />
    <span class="min-w-0 flex-1 truncate text-xs font-bold text-slate-700">Prise en main</span>
    <span class="text-[10px] font-black text-blue-600">{{ onboarding.progress }}%</span>
  </button>
</template>
