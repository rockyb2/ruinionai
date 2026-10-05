<script setup>
import { computed, reactive, ref } from "vue";
import {
  AdminBadge,
  AdminChart,
  AdminIcon,
  AdminModal,
  AdminPanel,
  AdminStats,
  AdminTable,
} from "../../components/admin";
import {
  providers,
  models,
  money,
  number,
  sum,
  notify,
} from "../../admin/demo";
const tab = ref("Vue d’ensemble"),
  service = ref("Transcription"),
  modal = ref(false),
  selectedModel = ref(null),
  providerName = ref(""),
  providerModal = ref(false);
const providerForm = reactive({ name: "", status: "Actif" });
const serviceConfig = reactive(
  Object.fromEntries(
    ["Transcription", "Résumé (LLM)", "Vectorisation", "Synthèse vocale"].map(
      (s) => [
        s,
        {
          primary:
            models.find((m) => m.service === s && m.role === "Principal")
              ?.name || "Aucun",
          fallback:
            models.find((m) => m.service === s && m.role === "Secours")?.name ||
            "Aucun",
          timeout: 30,
        },
      ],
    ),
  ),
);
const config = computed(() => serviceConfig[service.value]);
const filteredModels = computed(() =>
  tab.value === "Vue d’ensemble"
    ? models
    : models.filter((m) => m.service === tab.value),
);
const stats = computed(() => [
  {
    label: "Fournisseurs actifs",
    value: providers.filter((p) => p.status === "Actif").length,
    icon: "cpu",
    change: "→ Stable",
  },
  {
    label: "Modèles configurés",
    value: models.length,
    icon: "network",
    color: "blue",
    change: "↗ +2",
  },
  {
    label: "Appels IA (30 j)",
    value: number(sum(models, "calls")),
    icon: "activity",
    color: "green",
    change: "↗ +18 %",
  },
  {
    label: "Coût IA (30 j)",
    value: money(sum(models, "cost")),
    icon: "database",
    color: "red",
    change: "↗ +12 %",
    negative: true,
  },
]);
const columns = [
  { key: "name", label: "Modèle" },
  { key: "provider", label: "Fournisseur" },
  { key: "service", label: "Service" },
  { key: "status", label: "Statut" },
  { key: "role", label: "Rôle" },
  { key: "calls", label: "Appels" },
  { key: "success", label: "Succès" },
  { key: "latency", label: "Latence" },
  { key: "cost", label: "Coût" },
];
function openKey(name) {
  providerName.value = name;
  modal.value = true;
}
function simulateKey() {
  providers.find((p) => p.name === providerName.value).configured = true;
  modal.value = false;
  notify("Clé fictive configurée. Aucune clé réelle n’est stockée.");
}
function saveProvider() {
  if (!providerForm.name.trim()) return;
  providers.push({
    name: providerForm.name.trim(),
    status: providerForm.status,
    icon: "cpu",
    color: "purple",
    models: 0,
    calls: 0,
    success: "—",
    latency: "—",
    configured: false,
  });
  providerModal.value = false;
  providerForm.name = "";
  notify("Fournisseur de démonstration ajouté.");
}
</script>
<template>
  <AdminStats :items="stats" />
  <div class="a-split">
    <div class="a-stack">
      <AdminPanel
        title="Fournisseurs IA"
        subtitle="Statut des fournisseurs et des modèles"
        ><template #action
          ><button
            class="a-button a-button-primary"
            @click="providerModal = true"
          >
            <AdminIcon name="plus" :size="14" />Ajouter un fournisseur
          </button></template
        >
        <div class="a-tabs" style="margin-bottom: 15px">
          <button
            v-for="item in [
              'Vue d’ensemble',
              'Transcription',
              'Résumé (LLM)',
              'Vectorisation',
              'Synthèse vocale',
            ]"
            :key="item"
            :class="{ active: tab === item }"
            @click="tab = item"
          >
            {{ item }}
          </button>
        </div>
        <div class="a-provider-grid">
          <article
            v-for="provider in providers"
            :key="provider.name"
            class="a-provider"
          >
            <div class="a-identity">
              <span class="a-icon-tile small" :class="provider.color"
                ><AdminIcon :name="provider.icon" :size="19"
              /></span>
              <h3>{{ provider.name }}</h3>
            </div>
            <AdminBadge :value="provider.status" />
            <p>
              {{ provider.models }} modèles<br />{{
                number(provider.calls)
              }}
              appels
            </p>
            <p>
              <span class="a-success-text"
                >{{ provider.success }} de succès</span
              ><br />Latence moyenne : {{ provider.latency }}
            </p>
            <button
              class="a-link"
              @click="
                provider.status =
                  provider.status === 'Actif' ? 'Inactif' : 'Actif';
                notify('Statut du fournisseur simulé modifié.');
              "
            >
              {{ provider.status === "Actif" ? "Désactiver" : "Activer" }}
            </button>
          </article>
        </div></AdminPanel
      >
      <AdminPanel
        title="Modèles configurés"
        subtitle="Sélectionnez un modèle pour consulter ses paramètres"
        ><AdminTable
          compact
          :rows="filteredModels"
          :columns="columns"
          :page-size="20"
          @select="selectedModel = $event"
          ><template #service="{ value }"
            ><AdminBadge :value="value" color="blue" /></template
          ><template #status="{ value }"><AdminBadge :value="value" /></template
          ><template #role="{ value }"><AdminBadge :value="value" /></template
          ><template #cost="{ value }">{{ money(value) }}</template></AdminTable
        ></AdminPanel
      >
      <div class="a-grid a-grid-2">
        <AdminPanel title="Performance des modèles"
          ><AdminChart
            title="Appels, succès et latence des modèles" /></AdminPanel
        ><AdminPanel title="Répartition des appels"
          ><AdminChart
            kind="donut"
            total="12 842"
            unit="appels"
            :legend="[
              {
                label: 'Transcription',
                value: '1 952',
                percent: 15,
                color: '#713cff',
              },
              {
                label: 'Résumé (LLM)',
                value: '10 813',
                percent: 82,
                color: '#2185ff',
              },
              { label: 'Autres', value: '338', percent: 3, color: '#19b5a3' },
            ]"
        /></AdminPanel>
      </div>
    </div>
    <div class="a-stack">
      <AdminPanel title="Gestion des clés API"
        ><template #action><AdminIcon name="shield" :size="22" /></template>
        <p class="a-note">
          Clés fictives uniquement. N’entrez aucune clé réelle dans cette
          maquette.
        </p>
        <div class="a-list a-spaced">
          <div
            v-for="provider in providers"
            :key="provider.name"
            class="a-list-item"
          >
            <span class="a-icon-tile" :class="provider.color"
              ><AdminIcon :name="provider.icon" :size="17"
            /></span>
            <div>
              <strong>{{ provider.name }}</strong
              ><small>{{
                provider.configured ? "•••••••• démo" : "Non configurée"
              }}</small>
            </div>
            <AdminBadge
              :value="provider.configured ? 'Configurée' : 'Absente'"
              :color="provider.configured ? 'green' : 'gray'"
            /><button
              class="a-icon-button"
              :aria-label="`Configurer la clé ${provider.name}`"
              @click="openKey(provider.name)"
            >
              <AdminIcon
                :name="provider.configured ? 'edit' : 'plus'"
                :size="15"
              />
            </button>
          </div></div
      ></AdminPanel>
      <AdminPanel title="Configuration des services"
        ><div class="a-tabs">
          <button
            v-for="item in Object.keys(serviceConfig)"
            :key="item"
            :class="{ active: service === item }"
            @click="service = item"
          >
            {{ item }}
          </button>
        </div>
        <div class="a-form a-spaced">
          <label class="a-field"
            >Modèle principal<select v-model="config.primary">
              <option>Aucun</option>
              <option
                v-for="model in models.filter((m) => m.service === service)"
                :key="model.id"
              >
                {{ model.name }}
              </option>
            </select></label
          ><label class="a-field"
            >Modèle de secours<select v-model="config.fallback">
              <option>Aucun</option>
              <option
                v-for="model in models.filter(
                  (m) => m.service === service && m.name !== config.primary,
                )"
                :key="model.id"
              >
                {{ model.name }}
              </option>
            </select></label
          ><label class="a-field"
            >Délai maximum par appel<select v-model.number="config.timeout">
              <option :value="30">30 secondes</option>
              <option :value="60">60 secondes</option>
              <option :value="90">90 secondes</option>
            </select></label
          ><button
            class="a-button a-button-primary"
            @click="
              notify(
                'Configuration simulée enregistrée. Le traitement réel reste inchangé.',
              )
            "
          >
            <AdminIcon name="save" :size="15" />Enregistrer
          </button>
        </div></AdminPanel
      >
      <AdminPanel title="Alertes et limites"
        ><template #action
          ><RouterLink to="/admin/incidents" class="a-link"
            >Voir les incidents</RouterLink
          ></template
        >
        <div class="a-list">
          <div
            v-for="item in [
              {
                text: '17 limites de requêtes OpenRouter',
                icon: 'alert',
                color: 'orange',
                time: 'Il y a 2 h',
              },
              {
                text: 'Latence Voxtral : 12,3 secondes',
                icon: 'clock',
                color: 'orange',
                time: 'Il y a 3 h',
              },
              {
                text: 'Quota mensuel Mistral : 68 % utilisé',
                icon: 'database',
                color: 'blue',
                time: 'Il y a 1 j',
              },
            ]"
            :key="item.text"
            class="a-list-item"
          >
            <span class="a-icon-tile" :class="item.color"
              ><AdminIcon :name="item.icon" :size="16"
            /></span>
            <div>
              {{ item.text }}<small>{{ item.time }}</small>
            </div>
          </div>
        </div></AdminPanel
      >
    </div>
  </div>
  <AdminModal
    :open="modal"
    :title="`Clé API · ${providerName}`"
    @close="modal = false"
    ><p class="a-muted">
      Le bouton ci-dessous simule l’ajout d’une clé pour prévisualiser son état
      configuré.
    </p>
    <button class="a-button a-button-primary a-spaced" @click="simulateKey">
      Utiliser une clé de démonstration
    </button></AdminModal
  >
  <AdminModal
    :open="!!selectedModel"
    :title="selectedModel?.name"
    @close="selectedModel = null"
    ><template v-if="selectedModel"
      ><dl class="a-definition">
        <dt>Fournisseur</dt>
        <dd>{{ selectedModel.provider }}</dd>
        <dt>Service</dt>
        <dd>{{ selectedModel.service }}</dd>
        <dt>Rôle</dt>
        <dd>{{ selectedModel.role }}</dd>
        <dt>Appels</dt>
        <dd>{{ selectedModel.calls }}</dd>
        <dt>Succès</dt>
        <dd>{{ selectedModel.success }}</dd>
        <dt>Coût estimé</dt>
        <dd>{{ money(selectedModel.cost) }}</dd>
      </dl>
      <button
        class="a-button a-button-primary a-spaced"
        @click="
          selectedModel.status =
            selectedModel.status === 'Actif' ? 'Inactif' : 'Actif';
          notify('Statut du modèle simulé modifié.');
          selectedModel = null;
        "
      >
        {{
          selectedModel.status === "Actif"
            ? "Désactiver le modèle"
            : "Activer le modèle"
        }}
      </button></template
    ></AdminModal
  >
  <AdminModal
    :open="providerModal"
    title="Ajouter un fournisseur"
    @close="providerModal = false"
    ><form class="a-form" @submit.prevent="saveProvider">
      <label class="a-field"
        >Nom du fournisseur<input
          v-model="providerForm.name"
          required
          maxlength="60" /></label
      ><label class="a-field"
        >Statut<select v-model="providerForm.status">
          <option>Actif</option>
          <option>Inactif</option>
        </select></label
      ><button class="a-button a-button-primary">
        Ajouter à la démonstration
      </button>
    </form></AdminModal
  >
</template>
