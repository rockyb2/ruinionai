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
  users,
  meetings,
  models,
  alerts,
  money,
  number,
  sum,
  duration,
  activity,
} from "../../admin/demo";
const router = useRouter(),
  period = ref("30");
const visibleMeetings = computed(() =>
  period.value === "7" ? meetings.slice(0, 7) : meetings,
);
const stats = computed(() => [
  {
    label: "Organisations",
    value: organisations.length,
    icon: "building",
    change: "↗ +12 %",
  },
  {
    label: "Utilisateurs",
    value: users.length,
    icon: "users",
    color: "green",
    change: "↗ +18 %",
  },
  {
    label: "Réunions",
    value: visibleMeetings.value.length,
    icon: "video",
    color: "blue",
    change: "↗ +22 %",
  },
  {
    label: "Heures audio",
    value: Math.round(sum(visibleMeetings.value, "duration") / 60) + " h",
    icon: "clock",
    color: "orange",
    change: "↗ +15 %",
  },
  {
    label: "Coût IA",
    value: money(sum(visibleMeetings.value, "cost")),
    icon: "database",
    color: "red",
    change: "↗ +8 %",
    negative: true,
  },
  {
    label: "Taux de succès",
    value:
      (
        (visibleMeetings.value.filter((m) => m.status === "Terminé").length /
          visibleMeetings.value.length) *
        100
      )
        .toFixed(1)
        .replace(".", ",") + " %",
    icon: "success",
    color: "green",
    change: "↘ −0,4 %",
    negative: true,
  },
]);
const orgColumns = [
  { key: "name", label: "Organisation" },
  { key: "plan", label: "Plan" },
  { key: "members", label: "Membres" },
  { key: "meetings", label: "Réunions" },
  { key: "hours", label: "Audio" },
  { key: "cost", label: "Coût IA" },
  { key: "status", label: "Statut" },
];
const meetingColumns = [
  { key: "id", label: "#" },
  { key: "title", label: "Titre" },
  { key: "organization", label: "Organisation" },
  { key: "duration", label: "Durée" },
  { key: "cost", label: "Coût IA" },
  { key: "status", label: "Statut" },
];
const totalCost = computed(() => sum(visibleMeetings.value, "cost"));
const legend = computed(() => [
  {
    label: "Transcription",
    value: money(totalCost.value * 0.71),
    percent: 71,
    color: "#713cff",
  },
  {
    label: "Résumé (LLM)",
    value: money(totalCost.value * 0.29),
    percent: 29,
    color: "#2185ff",
  },
]);
</script>
<template>
  <div class="a-toolbar">
    <span class="a-identity a-muted"
      ><span class="a-dot a-success-text" />Vue de démonstration de la
      plateforme</span
    ><label class="a-identity"
      ><AdminIcon name="calendar" :size="16" /><select
        v-model="period"
        class="a-select"
        aria-label="Période du tableau de bord"
      >
        <option value="30">1 – 30 septembre 2026</option>
        <option value="7">24 – 30 septembre 2026</option>
      </select></label
    >
  </div>
  <AdminStats :items="stats" />
  <div class="a-stack">
    <div class="a-grid a-grid-chart">
      <AdminPanel :title="`Activité des ${period} derniers jours`"
        ><AdminChart
          :values="period === '7' ? activity.slice(-7) : activity"
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
          :total="number(totalCost)"
          :legend="legend"
          title="Répartition des coûts IA" /></AdminPanel
      ><AdminPanel title="Incidents récents"
        ><template #action
          ><RouterLink to="/admin/incidents" class="a-link"
            >Voir tous</RouterLink
          ></template
        >
        <div class="a-list">
          <RouterLink
            v-for="alert in alerts"
            :key="alert.title"
            to="/admin/incidents"
            class="a-list-item"
            ><span
              class="a-icon-tile"
              :class="alert.severity === 'Critique' ? 'red' : 'orange'"
              ><AdminIcon name="alert" :size="16"
            /></span>
            <div>
              <strong>{{ alert.title }}</strong>
              <p>{{ alert.text }}</p>
              <small>{{ alert.time }}</small>
            </div>
            <AdminBadge :value="alert.severity"
          /></RouterLink></div
      ></AdminPanel>
    </div>
    <div class="a-grid a-grid-main">
      <AdminPanel title="Top organisations par usage"
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
          ><template #cost="{ value }">{{ money(value) }}</template
          ><template #status="{ value }"
            ><AdminBadge :value="value" /></template></AdminTable
      ></AdminPanel>
      <AdminPanel title="Utilisation des modèles"
        ><template #action
          ><RouterLink to="/admin/aifournisseurs" class="a-link"
            >Voir les détails</RouterLink
          ></template
        >
        <div class="a-table-scroll">
          <table class="a-mini-table">
            <thead>
              <tr>
                <th>Modèle</th>
                <th>Appels</th>
                <th>Succès</th>
                <th>Latence</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="model in models.slice(0, 5)" :key="model.id">
                <td>
                  <div class="a-identity">
                    <span
                      class="a-icon-tile small"
                      :class="model.provider === 'Voxtral' ? 'purple' : 'blue'"
                      ><AdminIcon name="cpu" :size="15" /></span
                    >{{ model.name }}
                  </div>
                </td>
                <td>{{ number(model.calls) }}</td>
                <td class="a-success-text">{{ model.success }}</td>
                <td>{{ model.latency }}</td>
              </tr>
            </tbody>
          </table>
        </div></AdminPanel
      >
    </div>
    <div class="a-grid a-grid-main">
      <AdminPanel title="Dernières réunions"
        ><template #action
          ><RouterLink to="/admin/reunions" class="a-link"
            >Voir toutes</RouterLink
          ></template
        ><AdminTable
          compact
          :rows="visibleMeetings.slice(0, 5)"
          :columns="meetingColumns"
          @select="router.push(`/admin/reunions?id=${$event.id}`)"
          ><template #id="{ value }">#{{ value }}</template
          ><template #duration="{ value }">{{ duration(value) }}</template
          ><template #cost="{ value }">{{ money(value) }}</template
          ><template #status="{ value }"
            ><AdminBadge :value="value" /></template></AdminTable
      ></AdminPanel>
      <AdminPanel title="Alertes et tâches"
        ><div class="a-list">
          <RouterLink
            v-for="item in [
              {
                text: '3 réunions en échec à relancer',
                icon: 'alert',
                color: 'red',
                path: 'reunions',
              },
              {
                text: 'Organisations proches de leur quota',
                icon: 'clock',
                color: 'orange',
                path: 'abonnements',
              },
              {
                text: 'Vérifier les modèles de secours',
                icon: 'cpu',
                color: 'blue',
                path: 'aifournisseurs',
              },
              {
                text: 'Consulter le journal de sécurité',
                icon: 'shield',
                color: 'purple',
                path: 'audit',
              },
            ]"
            :key="item.text"
            :to="`/admin/${item.path}`"
            class="a-list-item"
            ><span class="a-icon-tile" :class="item.color"
              ><AdminIcon :name="item.icon" :size="16"
            /></span>
            <div>{{ item.text }}</div>
            <AdminIcon name="right" :size="14"
          /></RouterLink></div
      ></AdminPanel>
    </div>
  </div>
</template>
