import assert from 'node:assert/strict'
import test from 'node:test'

import { onboardingSteps, stepsForRole } from '../src/onboarding/steps.js'

test('onboarding step identifiers are unique', () => {
  const ids = onboardingSteps.map((step) => step.id)
  assert.equal(new Set(ids).size, ids.length)
})

test('role-specific steps are hidden from ordinary members', () => {
  const memberSteps = stepsForRole('member').map((step) => step.id)
  const ownerSteps = stepsForRole('owner').map((step) => step.id)

  assert.equal(memberSteps.includes('invite_team'), false)
  assert.equal(memberSteps.includes('organization_profile'), false)
  assert.equal(ownerSteps.includes('invite_team'), true)
  assert.equal(ownerSteps.includes('organization_profile'), true)
})
