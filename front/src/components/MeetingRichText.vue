<script setup>
import { computed } from 'vue'
import { meetingTextBlocks } from '@/utils/reportFormatting'

const props = defineProps({ text: { type: String, default: '' } })
const blocks = computed(() => meetingTextBlocks(props.text))
</script>

<template>
  <div v-if="blocks.length" class="space-y-3 text-sm leading-7 text-slate-700">
    <template v-for="(block, index) in blocks" :key="`${block.type}-${index}`">
      <h3 v-if="block.type === 'section'" class="mt-7 border-b border-blue-100 pb-2 text-base font-extrabold text-slate-900 first:mt-0">
        <span class="mr-1.5 text-blue-600">{{ block.number }}</span> <span class="underline decoration-blue-200 decoration-2 underline-offset-4">{{ block.text }}</span>
      </h3>

      <h4 v-else-if="block.type === 'dossier'" class="mt-6 text-lg font-extrabold leading-7 text-slate-950 underline decoration-blue-300 decoration-2 underline-offset-4">
        Dossier : {{ block.dossier }}
      </h4>

      <p v-else-if="block.type === 'dossier-reference'" class="rounded-lg border-l-2 border-blue-200 bg-blue-50/50 px-3 py-2">
        <strong class="font-extrabold text-slate-900 underline decoration-blue-200 underline-offset-4">Dossier : {{ block.dossier }}</strong>
        <span v-if="block.text"> — </span><template v-for="(segment, segmentIndex) in block.segments" :key="segmentIndex"><strong v-if="segment.strong" class="font-extrabold text-slate-900">{{ segment.text }}</strong><span v-else>{{ segment.text }}</span></template>
      </p>

      <p v-else-if="block.type === 'label'">
        <strong class="font-extrabold text-slate-900 underline decoration-slate-300 underline-offset-4">{{ block.label }} :</strong><span v-if="block.text"> </span><template v-for="(segment, segmentIndex) in block.segments" :key="segmentIndex"><strong v-if="segment.strong" class="font-extrabold text-slate-900">{{ segment.text }}</strong><span v-else>{{ segment.text }}</span></template>
      </p>

      <div v-else-if="block.type === 'bullet'" class="flex items-start gap-3 pl-1">
        <span class="mt-[0.72rem] h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />
        <p><template v-for="(segment, segmentIndex) in block.segments" :key="segmentIndex"><strong v-if="segment.strong" class="font-extrabold text-slate-900">{{ segment.text }}</strong><span v-else>{{ segment.text }}</span></template></p>
      </div>

      <p v-else><template v-for="(segment, segmentIndex) in block.segments" :key="segmentIndex"><strong v-if="segment.strong" class="font-extrabold text-slate-900">{{ segment.text }}</strong><span v-else>{{ segment.text }}</span></template></p>
    </template>
  </div>
  <p v-else class="text-sm leading-8 text-slate-400">Ce contenu n’est pas encore disponible.</p>
</template>
