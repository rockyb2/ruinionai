<script setup>
import { computed, ref } from "vue";
import {
  AdminAvatar,
  AdminBadge,
  AdminChart,
  AdminDetail,
  AdminIcon,
  AdminPanel,
  AdminStats,
  AdminTable,
} from "../../components/admin";
import { incidents, duration, notify, exportFile } from "../../admin/demo";
import { useDemoSelection } from "../../admin/useDemoSelection";
const selected = useDemoSelection(incidents),
  showLogs = ref(false);
const columns = [
  { key: "id", label: "#" },
  { key: "title", label: "Titre" },
  { key: "service", label: "Service" },
  { key: "severity", label: "Criticité" },
  { key: "status", label: "Statut" },
  { key: "organization", label: "Organisation" },
  { key: "date", label: "Début" },
  { key: "duration", label: "Durée" },
];
const stats = computed(() => [
  {
    label: "Incidents critiques",
    value: incidents.filter((i) => i.severity === "Critique").length,
    icon: "alert",
    color: "red",
    change: "↗ +100 %",
    negative: true,
  },
  {
    label: "Incidents majeurs",
    value: incidents.filter((i) => i.severity === "Majeur").length,
    icon: "alert",
    color: "orange",
    change: "↘ −25 %",
  },
  {
    label: "Incidents mineurs",
    value: incidents.filter((i) => i.severity === "Mineur").length,
    icon: "activity",
    color: "blue",
    change: "↘ −12 %",
  },
  {
    label: "Incidents résolus",
    value: incidents.filter((i) => i.status === "Résolu").length,
    icon: "success",
    color: "green",
    change: "↗ +31 %",
  },
  {
    label: "Temps moyen de résolution",
    value: "38 min",
    icon: "clock",
    color: "navy",
    change: "↘ −45 %",
  },
]);
function download() {
  exportFile(
    `incident-${selected.value.id}-demo.txt`,
    JSON.stringify({ demo: true, ...selected.value }, null, 2),
  );
  notify("Journal de démonstration téléchargé.");
}
</script>
<template>
  <AdminStats :items="stats" />
  <div class="a-stack">
    <div class="a-grid a-grid-chart">
      <AdminPanel title="Évolution des incidents"
        ><AdminChart
          kind="incidents"
          :values="[
            4, 3, 6, 4, 8, 6, 3, 4, 5, 3, 9, 6, 20, 5, 8, 4, 6, 4, 12, 4, 5, 3,
            4, 7, 5, 3, 6, 4, 14, 8,
          ]"
          title="Incidents de septembre 2026" /></AdminPanel
      ><AdminPanel title="Répartition par type"
        ><AdminChart
          kind="donut"
          :total="String(incidents.length)"
          unit="incidents"
          :legend="[
            {
              label: 'Transcription',
              value: '',
              percent: 36,
              color: '#713cff',
            },
            { label: 'Résumé (LLM)', value: '', percent: 25, color: '#2185ff' },
            { label: 'Documents', value: '', percent: 14, color: '#19bc96' },
            { label: 'Fournisseurs', value: '', percent: 16, color: '#ffae32' },
            {
              label: 'Infrastructure',
              value: '',
              percent: 9,
              color: '#d4dcec',
            },
          ]" /></AdminPanel
      ><AdminPanel title="Statut des services"
        ><template #action
          ><RouterLink to="/admin/aifournisseurs" class="a-link"
            >Voir les fournisseurs</RouterLink
          ></template
        >
        <div class="a-list">
          <div
            v-for="item in [
              {
                name: 'Transcription (Voxtral)',
                icon: 'audio',
                status: 'Opérationnel',
                uptime: '99,3 %',
              },
              {
                name: 'Résumé (Mistral Large)',
                icon: 'cpu',
                status: 'Opérationnel',
                uptime: '98,1 %',
              },
              {
                name: 'OpenRouter',
                icon: 'network',
                status: 'Dégradé',
                uptime: '95,2 %',
              },
              {
                name: 'Documents',
                icon: 'file',
                status: 'Opérationnel',
                uptime: '99,8 %',
              },
              {
                name: 'Stockage',
                icon: 'database',
                status: 'Opérationnel',
                uptime: '100 %',
              },
            ]"
            :key="item.name"
            class="a-list-item"
          >
            <AdminIcon :name="item.icon" :size="16" />
            <div>{{ item.name }}</div>
            <AdminBadge :value="item.status" dot /><small>{{
              item.uptime
            }}</small>
          </div>
        </div></AdminPanel
      >
    </div>
    <div class="a-split" :class="{ 'a-no-detail': !selected }">
      <AdminTable
        :rows="incidents"
        :columns="columns"
        :tabs="['Critique', 'Majeur', 'Mineur']"
        tab-key="severity"
        :filters="[
          { key: 'service', label: 'Service' },
          { key: 'status', label: 'Statut' },
        ]"
        :selected-id="selected?.id"
        label="incidents"
        search-placeholder="Rechercher un incident…"
        export-name="incidents-demo.csv"
        @select="
          selected = $event;
          showLogs = false;
        "
        ><template #id="{ value }">#{{ value }}</template
        ><template #severity="{ value }"
          ><AdminBadge :value="value" dot /></template
        ><template #status="{ value }"
          ><AdminBadge :value="value" dot /></template
        ><template #duration="{ value }">{{
          duration(value)
        }}</template></AdminTable
      >
      <AdminDetail
        v-if="selected"
        :title="`#${selected.id} — ${selected.title}`"
        subtitle="Détails de l’incident de démonstration"
        :status="selected.status"
        @close="selected = null"
        ><AdminPanel title="Informations de l’incident"
          ><template #action
            ><AdminBadge :value="selected.severity" dot
          /></template>
          <dl class="a-definition">
            <dt>Service</dt>
            <dd>{{ selected.service }}</dd>
            <dt>Début</dt>
            <dd>{{ selected.date }} · 14:23</dd>
            <dt>Durée</dt>
            <dd>{{ duration(selected.duration) }}</dd>
            <dt>Organisation</dt>
            <dd>
              <span class="a-identity"
                ><AdminAvatar :name="selected.organization" />{{
                  selected.organization
                }}</span
              >
            </dd>
            <dt>Statut</dt>
            <dd><AdminBadge :value="selected.status" /></dd>
            <dt>Impact</dt>
            <dd>Traitement de certaines réunions interrompu.</dd>
            <dt>Description</dt>
            <dd>{{ selected.description }}</dd>
          </dl>
          <div class="a-actions a-spaced">
            <a
              class="a-button"
              href="https://cloud.langfuse.com"
              target="_blank"
              rel="noopener noreferrer"
              >Ouvrir Langfuse<AdminIcon name="external" :size="14" /></a
            ><button
              class="a-button a-button-primary"
              @click="showLogs = !showLogs"
            >
              <AdminIcon name="file" :size="14" />{{
                showLogs ? "Masquer les logs" : "Voir les logs"
              }}
            </button>
          </div></AdminPanel
        >
        <AdminPanel v-if="showLogs" title="Logs de démonstration">
          <pre class="a-log">
14:23  WARN  {{ selected.service }} : interruption détectée
14:26  INFO  Nouvelle tentative sur le modèle de secours
14:31  INFO  Réponse du fournisseur reçue
16:37  {{
              selected.status === "Résolu"
                ? "INFO  Incident résolu"
                : "WARN  Surveillance en cours"
            }}</pre>
          <button class="a-button a-spaced" @click="download">
            <AdminIcon name="download" :size="15" />Exporter le journal
          </button></AdminPanel
        >
        <AdminPanel title="Chronologie de l’incident"
          ><ol class="a-timeline">
            <li
              v-for="(event, i) in [
                {
                  time: '14:23',
                  text: 'Incident détecté et alerte déclenchée',
                },
                { time: '14:26', text: 'Bascule vers le modèle de secours' },
                { time: '14:31', text: 'Vérification du rétablissement' },
                {
                  time: '16:37',
                  text:
                    selected.status === 'Résolu'
                      ? 'Retour à la normale'
                      : 'Surveillance en cours',
                },
              ]"
              :key="event.time"
            >
              <span
                class="a-step"
                :class="i === 0 ? 'red' : i === 1 ? 'orange' : 'green'"
                >{{ i + 1 }}</span
              >
              <div>
                <strong>{{ event.time }}</strong
                ><small>{{ event.text }}</small>
              </div>
            </li>
          </ol></AdminPanel
        ><template #footer
          ><button
            class="a-button a-button-primary a-button-wide"
            @click="
              selected.status =
                selected.status === 'Résolu' ? 'En cours' : 'Résolu';
              notify('État de l’incident de démonstration mis à jour.');
            "
          >
            {{
              selected.status === "Résolu"
                ? "Rouvrir l’incident"
                : "Marquer comme résolu"
            }}
          </button></template
        ></AdminDetail
      >
    </div>
  </div>
</template>
