<script setup>
import { computed } from "vue";
import { activity } from "../../admin/demo";
const props = defineProps({
  kind: { type: String, default: "activity" },
  values: { type: Array, default: () => activity },
  labels: {
    type: Array,
    default: () => [
      "1 sept.",
      "5 sept.",
      "10 sept.",
      "15 sept.",
      "20 sept.",
      "25 sept.",
      "30 sept.",
    ],
  },
  title: { type: String, default: "Activité des 30 derniers jours" },
  total: { type: String, default: "128 450" },
  unit: { type: String, default: "FCFA" },
  legend: {
    type: Array,
    default: () => [
      {
        label: "Transcription",
        value: "91 200 FCFA",
        percent: 71,
        color: "#713cff",
      },
      {
        label: "Résumé (LLM)",
        value: "37 250 FCFA",
        percent: 29,
        color: "#2185ff",
      },
    ],
  },
});
const max = computed(
  () => Math.ceil((Math.max(...props.values) * 1.25) / 50) * 50,
);
const x = (i) => 42 + i * (590 / Math.max(props.values.length - 1, 1));
const y = (value) => 205 - (value / max.value) * 160;
const line = computed(() =>
  props.values
    .map((v, i) => `${x(i)},${y(v * (i % 3 ? 1.05 : 1.25))}`)
    .join(" "),
);
const secondary = computed(() =>
  props.values.map((v, i) => `${x(i)},${y(v * 0.48)}`).join(" "),
);
const donut = computed(() => {
  let angle = 0;
  return `conic-gradient(${props.legend
    .map((item) => {
      const from = angle;
      angle += item.percent;
      return `${item.color} ${from}% ${angle}%`;
    })
    .join(", ")})`;
});
</script>
<template>
  <div v-if="kind === 'donut'" class="a-donut-wrap">
    <div
      class="a-donut"
      :style="{ background: donut }"
      role="img"
      :aria-label="`${title} : ${legend.map((item) => `${item.label} ${item.percent} %`).join(', ')}`"
    >
      <div>
        <strong>{{ total }}</strong
        ><span>{{ unit }}</span>
      </div>
    </div>
    <ul class="a-legend-list">
      <li v-for="item in legend" :key="item.label">
        <span
          class="a-legend-dot"
          :style="{ background: item.color }"
        /><span>{{ item.label }}</span
        ><strong>{{ item.value }}</strong
        ><small>{{ item.percent }} %</small>
      </li>
    </ul>
  </div>
  <div v-else class="a-chart">
    <div
      v-if="kind === 'activity' || kind === 'incidents'"
      class="a-chart-legend"
    >
      <span
        ><i style="background: #9270ff" />{{
          kind === "incidents" ? "Mineurs" : "Réunions"
        }}</span
      ><span
        ><i style="background: #2185ff" />{{
          kind === "incidents" ? "Majeurs" : "Heures audio"
        }}</span
      ><span
        ><i style="background: #19b5a3" />{{
          kind === "incidents" ? "Critiques" : "Coût IA"
        }}</span
      >
    </div>
    <svg viewBox="0 0 660 245" role="img" :aria-label="title">
      <g v-for="i in 5" :key="i">
        <line
          x1="40"
          x2="638"
          :y1="45 + (i - 1) * 40"
          :y2="45 + (i - 1) * 40"
          stroke="#eaf0f8"
        />
        <text x="29" :y="49 + (i - 1) * 40" text-anchor="end">
          {{ Math.round((max * (5 - i)) / 4) }}
        </text>
      </g>
      <g v-for="(v, i) in values" :key="i">
        <rect
          :x="kind === 'monthly' ? 60 + i * (560 / values.length) : x(i) - 5"
          :y="y(v)"
          :width="kind === 'monthly' ? 38 : 10"
          :height="205 - y(v)"
          rx="3"
          :fill="
            kind === 'monthly' && i === values.length - 1
              ? '#6238ff'
              : '#a58bff'
          "
          :opacity="kind === 'monthly' ? 1 : 0.65"
        >
          <title>{{ v }} · {{ labels[Math.min(i, labels.length - 1)] }}</title>
        </rect>
      </g>
      <template v-if="kind !== 'monthly'">
        <polyline
          :points="line"
          fill="none"
          stroke="#2083ff"
          stroke-width="2.5"
          stroke-linejoin="round"
        />
        <polyline
          :points="secondary"
          fill="none"
          stroke="#16bba3"
          stroke-width="2"
          stroke-linejoin="round"
        />
        <circle
          v-for="(v, i) in values"
          :key="i"
          :cx="x(i)"
          :cy="y(v * (i % 3 ? 1.05 : 1.25))"
          r="2.3"
          fill="#2083ff"
        >
          <title>{{ v }} réunions</title>
        </circle>
      </template>
      <g v-for="(label, i) in labels" :key="label">
        <text
          :x="
            kind === 'monthly'
              ? 80 + i * (560 / values.length)
              : 42 + i * (590 / (labels.length - 1))
          "
          y="232"
          text-anchor="middle"
        >
          {{ label }}
        </text>
      </g>
    </svg>
  </div>
</template>
