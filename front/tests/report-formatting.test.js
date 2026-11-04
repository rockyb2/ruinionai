import assert from 'node:assert/strict'
import test from 'node:test'

import { inlineSegments, meetingTextBlocks } from '../src/utils/reportFormatting.js'

test('meeting report exposes meaningful headings and removes legacy brackets', () => {
  const blocks = meetingTextBlocks(`2. Points importants
Dossier : Résolution des problèmes financiers avec un client (Golf)
Contexte : Une facture reste à valider.
- [Golf] Le client doit confirmer le montant.`)

  assert.deepEqual(blocks.map((block) => block.type), [
    'section',
    'dossier',
    'label',
    'dossier-reference',
  ])
  assert.equal(blocks[1].dossier, 'Résolution des problèmes financiers avec un client (Golf)')
  assert.equal(blocks[3].dossier, 'Golf')
  assert.equal(blocks[3].text, 'Le client doit confirmer le montant.')
})

test('meeting report turns markdown bold into explicit strong segments', () => {
  assert.deepEqual(inlineSegments('Un **point essentiel** à retenir.'), [
    { text: 'Un ', strong: false },
    { text: 'point essentiel', strong: true },
    { text: ' à retenir.', strong: false },
  ])
})
