<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import {
  AdminAvatar,
  AdminBadge,
  AdminChart,
  AdminIcon,
  AdminPanel,
  AdminStats,
  AdminTable,
} from "../../components/admin";
import {
  organisations,
  meetings,
  money,
  number,
  sum,
  duration,
  activity,
} from "../../admin/demo";
const router = useRouter(),
  period = ref("30"),
  year = ref("2026");
const records = computed(() =>
  period.value === "30" ? meetings : meetings.slice(0, 7),
);
const total = computed(() => sum(records.value, "cost")),
  hours = computed(() => Math.round(sum(records.value, "duration") / 60));
const stats = computed(() => [
  {
    label: "Heures audio",
    value: hours.value + " h",
    icon: "audio",
    change: "↗ +15 %",
  },
  {
    label: "Réunions traitées",
    value: records.value.length,
    icon: "building",
    color: "blue",
    change: "↗ +22 %",
  },
  {
    label: "Coût IA total",
    value: money(total.value),
    icon: "database",
    color: "red",
    change: "↗ +8 %",
    negative: true,
  },
  {
    label: "Coût moyen / réunion",
    value: money(total.value / records.value.length),
    icon: "credit",
    color: "green",
    change: "↘ −12 %",
  },
  {
    label: "Coût moyen / organisation",
    value: money(
      total.value / new Set(records.value.map((r) => r.organization)).size,
    ),
    icon: "users",
    color: "orange",
    change: "↘ −8 %",
  },
]);
const legend = computed(() => [
  {
    label: "Transcription (Voxtral)",
    value: money(total.value * 0.71),
    percent: 71,
    color: "#713cff",
  },
  {
    label: "Résumé (LLM)",
    value: money(total.value * 0.29),
    percent: 29,
    color: "#2185ff",
  },
]);
const orgColumns = [
  { key: "name", label: "Organisation" },
  { key: "plan", label: "Plan" },
  { key: "meetings", label: "Réunions" },
  { key: "hours", label: "Audio" },
  { key: "cost", label: "Coût IA" },
];
const meetingColumns = [
  { key: "title", label: "Titre" },
  { key: "organization", label: "Organisation" },
  { key: "duration", label: "Durée" },
  { key: "cost", label: "Coût IA" },
  { key: "status", label: "Statut" },
];
</script>
<template>
  <div class="a-toolbar">
    <span class="a-muted">Consommation et estimations de démonstration</span
    ><label class="a-identity"
      ><AdminIcon name="calendar" :size="16" /><select
        v-model="period"
        class="a-select"
        aria-label="Période des coûts"
      >
        <option value="30">1 – 30 septembre 2026</option>
        <option value="7">24 – 30 septembre 2026</option>
      </select></label
    >
  </div>
  <AdminStats :items="stats" />
  <div class="a-stack">
    <div class="a-grid a-grid-chart">
      <AdminPanel title="Évolution de l’usage et des coûts"
        ><AdminChart
          :values="period === '30' ? activity : activity.slice(-7)"
          :labels="
            period === '7'
              ? [
                  '24 sept.',
                  '25 sept.',
                  '26 sept.',
                  '27 sept.',
                  '28 sept.',
                  '29 sept.',
                  '30 sept.',
                ]
              : undefined
          " /></AdminPanel
      ><AdminPanel title="Répartition des coûts IA"
        ><AdminChart
          kind="donut"
          :total="number(total)"
          :legend="legend"
          title="Coûts par service" /></AdminPanel
      ><AdminPanel title="Coûts par fournisseur IA"
        ><template #action
          ><RouterLink class="a-link" to="/admin/aifournisseurs"
            >Voir les détails</RouterLink
          ></template
        >
        <div class="a-list">
          <div
            v-for="provider in [
              { name: 'Mistral AI', icon: 'cpu', color: 'orange', percent: 41 },
              {
                name: 'OpenRouter',
                icon: 'network',
                color: 'navy',
                percent: 29,
              },
              { name: 'Voxtral', icon: 'audio', color: 'blue', percent: 25 },
              { name: 'Autres', icon: 'more', color: 'gray', percent: 5 },
            ]"
            :key="provider.name"
            class="a-list-item"
          >
            <span class="a-icon-tile" :class="provider.color"
              ><AdminIcon :name="provider.icon" :size="18"
            /></span>
            <div>
              <div class="a-toolbar" style="margin-bottom: 7px">
                <strong>{{ provider.name }}</strong
                ><small>{{ money((total * provider.percent) / 100) }}</small>
              </div>
              <div class="a-progress">
                <span :style="{ width: provider.percent + '%' }" />
              </div>
            </div>
            <small>{{ provider.percent }} %</small>
          </div>
        </div></AdminPanel
      >
    </div>
    <div class="a-grid a-grid-chart">
      <AdminPanel title="Usage par organisation"
        ><template #action
          ><RouterLink to="/admin/organisations" class="a-link"
            >Voir toutes</RouterLink
          ></template
        ><AdminTable
          compact
          :rows="organisations.slice(0, 5)"
          :columns="orgColumns"
          @select="router.push(`/admin/organisations?id=${$event.id}`)"
          ><template #name="{ row }"
            ><div class="a-identity">
              <AdminAvatar :name="row.name" />{{ row.name }}
            </div></template
          ><template #plan="{ value }"><AdminBadge :value="value" /></template
          ><template #hours="{ value }">{{ value }} h</template
          ><template #cost="{ value }">{{ money(value) }}</template></AdminTable
        ></AdminPanel
      ><AdminPanel title="Usage par type de service"
        ><div class="a-list">
          <div
            v-for="item in [
              {
                name: 'Transcription (Voxtral)',
                volume: hours + ' heures',
                percent: 71,
                icon: 'audio',
              },
              {
                name: 'Résumé de réunions',
                volume: records.length + ' résumés',
                percent: 29,
                icon: 'file',
              },
              {
                name: 'Documents Word',
                volume:
                  records.filter((m) => m.status === 'Terminé').length +
                  ' exports',
                percent: 0,
                icon: 'folder',
              },
            ]"
            :key="item.name"
            class="a-list-item"
          >
            <span class="a-icon-tile purple"
              ><AdminIcon :name="item.icon" :size="17"
            /></span>
            <div>
              <strong>{{ item.name }}</strong
              ><small>{{ item.volume }}</small>
              <div class="a-progress a-spaced">
                <span :style="{ width: item.percent + '%' }" />
              </div>
            </div>
            <small>{{ item.percent }} %</small>
          </div>
        </div></AdminPanel
      ><AdminPanel title="Coûts par mois"
        ><template #action
          ><select
            v-model="year"
            class="a-select"
            style="width: 80px"
            aria-label="Année des coûts"
          >
            <option>2026</option>
            <option>2025</option>
          </select></template
        ><AdminChart
          kind="monthly"
          :values="
            year === '2026' ? [64, 72, 96, 110, 128] : [34, 48, 52, 68, 81]
          "
          :labels="['Mai', 'Juin', 'Juil.', 'Août', 'Sept.']"
          title="Coûts mensuels en milliers de FCFA"
      /></AdminPanel>
    </div>
    <div class="a-grid a-grid-2">
      <AdminPanel title="Détail des coûts par service"
        ><div class="a-table-scroll">
          <table class="a-mini-table">
            <thead>
              <tr>
                <th>Service</th>
                <th>Volume</th>
                <th>Coût total</th>
                <th>Part</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  <div class="a-identity">
                    <span class="a-icon-tile small purple"
                      ><AdminIcon name="audio" :size="16" /></span
                    >Transcription (Voxtral)
                  </div>
                </td>
                <td>{{ hours }} heures</td>
                <td>{{ money(total * 0.71) }}</td>
                <td>71 %</td>
              </tr>
              <tr>
                <td>
                  <div class="a-identity">
                    <span class="a-icon-tile small blue"
                      ><AdminIcon name="file" :size="16" /></span
                    >Résumé (Mistral Large)
                  </div>
                </td>
                <td>{{ records.length }} résumés</td>
                <td>{{ money(total * 0.29) }}</td>
                <td>29 %</td>
              </tr>
              <tr>
                <td>
                  <div class="a-identity">
                    <span class="a-icon-tile small green"
                      ><AdminIcon name="folder" :size="16" /></span
                    >Documents
                  </div>
                </td>
                <td>{{ records.length }} exports</td>
                <td>0 FCFA</td>
                <td>0 %</td>
              </tr>
            </tbody>
          </table>
        </div></AdminPanel
      ><AdminPanel title="Dernières réunions · coûts"
        ><template #action
          ><RouterLink class="a-link" to="/admin/reunions"
            >Voir toutes</RouterLink
          ></template
        ><AdminTable
          compact
          :rows="records.slice(0, 4)"
          :columns="meetingColumns"
          @select="router.push(`/admin/reunions?id=${$event.id}`)"
          ><template #duration="{ value }">{{ duration(value) }}</template
          ><template #cost="{ value }">{{ money(value) }}</template
          ><template #status="{ value }"
            ><AdminBadge :value="value" /></template></AdminTable
      ></AdminPanel>
    </div>
  </div>
</template>
