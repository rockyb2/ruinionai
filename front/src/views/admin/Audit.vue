<script setup>
import { computed, ref } from "vue";
import {
  AdminAvatar,
  AdminBadge,
  AdminChart,
  AdminIcon,
  AdminModal,
  AdminPanel,
  AdminStats,
  AdminTable,
} from "../../components/admin";
import { audit, alerts, notify } from "../../admin/demo";
const selected = ref(null),
  sessionsOpen = ref(false);
const devices = ref([
  {
    name: "PC Bureau",
    system: "Windows 11 · Chrome",
    time: "Actif maintenant",
    icon: "laptop",
  },
  {
    name: "Portable",
    system: "Windows 11 · Edge",
    time: "Il y a 3 heures",
    icon: "laptop",
  },
  {
    name: "Téléphone",
    system: "Android · Chrome",
    time: "Il y a 1 jour",
    icon: "phone",
  },
  {
    name: "PC Maison",
    system: "Windows · Chrome",
    time: "Il y a 5 jours",
    icon: "laptop",
  },
]);
const columns = [
  { key: "id", label: "#" },
  { key: "date", label: "Date et heure" },
  { key: "user", label: "Utilisateur" },
  { key: "organization", label: "Organisation" },
  { key: "action", label: "Action" },
  { key: "details", label: "Détails" },
  { key: "ip", label: "Adresse IP" },
  { key: "status", label: "Statut" },
];
const stats = computed(() => [
  {
    label: "Actions auditées",
    value: audit.length,
    icon: "shield",
    change: "↗ +28 %",
  },
  {
    label: "Connexions",
    value: 623,
    icon: "key",
    color: "blue",
    change: "↗ +12 %",
  },
  {
    label: "Tentatives échouées",
    value: audit.filter((a) => a.status === "Échec").length,
    icon: "lock",
    color: "red",
    change: "↗ +71 %",
    negative: true,
  },
  {
    label: "Comptes désactivés",
    value: 5,
    icon: "users",
    color: "orange",
    change: "↗ +25 %",
    negative: true,
  },
  {
    label: "Alertes de sécurité",
    value: 7,
    icon: "alert",
    color: "red",
    change: "↘ −30 %",
  },
]);
function revoke() {
  devices.value = devices.value.slice(0, 1);
  notify(
    "Autres sessions de démonstration fermées. Votre session réelle reste active.",
  );
}
</script>
<template>
  <AdminStats :items="stats" />
  <div class="a-stack">
    <div class="a-grid a-grid-chart">
      <AdminPanel title="Activité de sécurité"
        ><AdminChart
          title="Connexions et actions sensibles en septembre" /></AdminPanel
      ><AdminPanel title="Répartition des actions"
        ><AdminChart
          kind="donut"
          :total="String(audit.length)"
          unit="actions"
          :legend="[
            { label: 'Utilisateurs', value: '', percent: 32, color: '#713cff' },
            {
              label: 'Organisations',
              value: '',
              percent: 21,
              color: '#2185ff',
            },
            { label: 'Abonnements', value: '', percent: 14, color: '#19bc96' },
            {
              label: 'Configuration IA',
              value: '',
              percent: 12,
              color: '#ffae32',
            },
            { label: 'Sécurité', value: '', percent: 11, color: '#fb8040' },
            { label: 'Autres', value: '', percent: 10, color: '#c5ccdf' },
          ]" /></AdminPanel
      ><AdminPanel title="Niveau de sécurité"
        ><template #action><AdminBadge value="Bon" color="green" /></template>
        <ul class="a-check-list">
          <li
            v-for="item in [
              'Authentification obligatoire',
              'Sessions sécurisées (HTTPS)',
              'Protection contre les tentatives répétées',
              'Sauvegardes automatiques',
              'Surveillance des activités',
            ]"
            :key="item"
          >
            <AdminIcon name="success" :size="15" />{{ item
            }}<AdminBadge value="Activé" color="green" />
          </li>
        </ul>
        <RouterLink
          to="/admin/configurations?tab=Sécurité"
          class="a-button a-button-soft a-button-wide a-spaced"
          ><AdminIcon name="settings" :size="15" />Paramètres de
          sécurité<AdminIcon name="arrow" :size="14" /></RouterLink
        ><small class="a-spaced" style="display: block"
          >État fictif : aucune vérification de l’infrastructure.</small
        ></AdminPanel
      >
    </div>
    <div class="a-split">
      <AdminTable
        :rows="audit"
        :columns="columns"
        :tabs="[
          'Connexions',
          'Utilisateurs',
          'Organisations',
          'Abonnements',
          'Sécurité',
        ]"
        tab-key="category"
        :filters="[
          { key: 'user', label: 'Utilisateur' },
          { key: 'organization', label: 'Organisation' },
          { key: 'status', label: 'Statut' },
        ]"
        label="actions"
        search-placeholder="Rechercher une action, un utilisateur…"
        export-name="audit-demo.csv"
        :page-size="10"
        @select="selected = $event"
        ><template #id="{ value }">#{{ value }}</template
        ><template #date="{ row }"
          >{{ row.date
          }}<small style="display: block">{{ row.time }}</small></template
        ><template #user="{ value }"
          ><div class="a-identity">
            <AdminAvatar :name="value" />{{ value }}
          </div></template
        ><template #status="{ value }"
          ><AdminBadge :value="value" dot /></template
      ></AdminTable>
      <div class="a-stack">
        <AdminPanel title="Session actuelle"
          ><div class="a-identity">
            <span class="a-profile-avatar">CA</span><strong>Charles</strong
            ><AdminBadge value="Super administrateur" color="purple" />
          </div>
          <dl class="a-definition a-spaced">
            <dt>Adresse IP</dt>
            <dd>192.0.2.10</dd>
            <dt>Localisation</dt>
            <dd>Abidjan, Côte d’Ivoire</dd>
            <dt>Navigateur</dt>
            <dd>Chrome · Démonstration</dd>
            <dt>Système</dt>
            <dd>Windows 11</dd>
            <dt>Dernière activité</dt>
            <dd>Il y a 2 minutes</dd>
          </dl>
          <button
            class="a-button a-button-danger a-button-wide a-spaced"
            @click="revoke"
          >
            <AdminIcon name="lock" :size="15" />Fermer les autres sessions
          </button></AdminPanel
        >
        <AdminPanel title="Appareils connectés"
          ><template #action
            ><button class="a-link" @click="sessionsOpen = !sessionsOpen">
              {{ sessionsOpen ? "Réduire" : `Voir tous (${devices.length})` }}
            </button></template
          >
          <div class="a-list">
            <div
              v-for="device in sessionsOpen ? devices : devices.slice(0, 3)"
              :key="device.name"
              class="a-list-item"
            >
              <AdminIcon :name="device.icon" :size="19" />
              <div>
                <strong>{{ device.name }}</strong
                ><small>{{ device.system }}</small>
              </div>
              <AdminBadge
                :value="device.time"
                :color="device.time === 'Actif maintenant' ? 'green' : 'gray'"
              />
            </div></div
        ></AdminPanel>
        <AdminPanel title="Alertes récentes"
          ><template #action
            ><RouterLink to="/admin/incidents" class="a-link"
              >Voir toutes</RouterLink
            ></template
          >
          <div class="a-list">
            <RouterLink
              v-for="alert in alerts"
              :key="alert.title"
              to="/admin/incidents"
              class="a-list-item"
              ><AdminIcon name="alert" :size="16" class="a-danger-text" />
              <div>
                {{ alert.title }}<small>{{ alert.time }}</small>
              </div></RouterLink
            >
          </div></AdminPanel
        >
      </div>
    </div>
  </div>
  <AdminModal
    :open="!!selected"
    :title="`Action #${selected?.id || ''}`"
    @close="selected = null"
    ><dl v-if="selected" class="a-definition">
      <dt>Action</dt>
      <dd>{{ selected.action }}</dd>
      <dt>Utilisateur</dt>
      <dd>{{ selected.user }}</dd>
      <dt>Organisation</dt>
      <dd>{{ selected.organization }}</dd>
      <dt>Date</dt>
      <dd>{{ selected.date }} · {{ selected.time }}</dd>
      <dt>Adresse IP</dt>
      <dd>{{ selected.ip }}</dd>
      <dt>Détails</dt>
      <dd>{{ selected.details }}</dd>
      <dt>Résultat</dt>
      <dd><AdminBadge :value="selected.status" /></dd></dl
  ></AdminModal>
</template>
