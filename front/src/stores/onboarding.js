import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { resetOnboardingState, updateOnboardingState } from '@/service/api'
import { ONBOARDING_VERSION, stepsForRole } from '@/onboarding/steps'

export const useOnboardingStore = defineStore('onboarding', () => {
  const initialized = ref(false)
  const saving = ref(false)
  const role = ref('member')
  const steps = ref({})
  const completedAt = ref(null)
  const dismissedAt = ref(null)
  const panelOpen = ref(true)
  const error = ref('')

  const availableSteps = computed(() => stepsForRole(role.value))
  const completedCount = computed(() =>
    availableSteps.value.filter((step) => Boolean(steps.value[step.id])).length,
  )
  const totalCount = computed(() => availableSteps.value.length)
  const progress = computed(() => totalCount.value
    ? Math.round((completedCount.value / totalCount.value) * 100)
    : 100)
  const finished = computed(() => totalCount.value > 0 && completedCount.value === totalCount.value)

  function initialize(user, userRole) {
    role.value = userRole || 'member'
    const versionMatches = user?.onboarding_version === ONBOARDING_VERSION
    steps.value = versionMatches ? { ...(user?.onboarding_steps || {}) } : {}
    completedAt.value = versionMatches ? user?.onboarding_completed_at || null : null
    dismissedAt.value = versionMatches ? user?.onboarding_dismissed_at || null : null
    panelOpen.value = !dismissedAt.value && !completedAt.value
    initialized.value = true
  }

  function applyState(state) {
    steps.value = { ...steps.value, ...(state.steps || {}) }
    completedAt.value = state.completed_at || null
    dismissedAt.value = state.dismissed_at || null
  }

  async function persist(payload) {
    saving.value = true
    error.value = ''
    try {
      const state = await updateOnboardingState(payload)
      applyState(state)
      return state
    } catch (failure) {
      error.value = failure.message || 'Progression non sauvegardée.'
      throw failure
    } finally {
      saving.value = false
    }
  }

  async function completeStep(stepId) {
    if (!availableSteps.value.some((step) => step.id === stepId) || steps.value[stepId]) return
    const previous = { ...steps.value }
    steps.value = { ...steps.value, [stepId]: true }
    const isComplete = availableSteps.value.every((step) => steps.value[step.id])
    try {
      await persist({
        steps: { [stepId]: true },
        ...(isComplete ? { completed: true } : {}),
      })
      if (isComplete) panelOpen.value = true
    } catch {
      steps.value = previous
    }
  }

  async function dismiss() {
    panelOpen.value = false
    try { await persist({ dismissed: true }) } catch { panelOpen.value = true }
  }

  async function reopen() {
    panelOpen.value = true
    if (dismissedAt.value) await persist({ dismissed: false })
  }

  async function reset() {
    saving.value = true
    error.value = ''
    try {
      const state = await resetOnboardingState()
      steps.value = { ...(state.steps || {}) }
      completedAt.value = state.completed_at || null
      dismissedAt.value = state.dismissed_at || null
      panelOpen.value = true
    } catch (failure) {
      error.value = failure.message || 'Tutoriel non réinitialisé.'
    } finally {
      saving.value = false
    }
  }

  return {
    initialized, saving, steps, completedAt, dismissedAt, panelOpen, error,
    availableSteps, completedCount, totalCount, progress, finished,
    initialize, completeStep, dismiss, reopen, reset,
  }
})
