<script setup>
import { computed, reactive, ref } from "vue";
import {
  AdminBadge,
  AdminDetail,
  AdminIcon,
  AdminModal,
  AdminPanel,
  AdminStats,
  AdminTable,
} from "../../components/admin";
import {
  meetings,
  organisations,
  money,
  duration,
  sum,
  notify,
  exportFile,
} from "../../admin/demo";
import { useDemoSelection } from "../../admin/useDemoSelection";
const selected = useDemoSelection(meetings),
  tab = ref("Vue d’ensemble"),
  modal = ref(false),
  editing = ref(false);
const form = reactive({ title: "", organization: "Ivoir Trips", duration: 60 });
const columns = [
  { key: "id", label: "#" },
  { key: "title", label: "Titre" },
  { key: "organization", label: "Organisation" },
  { key: "date", label: "Date" },
  { key: "duration", label: "Durée" },
  { key: "cost", label: "Coût IA" },
  { key: "status", label: "Statut" },
];
const stats = computed(() => [
  {
    label: "Total réunions",
    value: meetings.length,
    icon: "video",
    color: "blue",
    change: "↗ +22 %",
  },
  {
    label: "Heures audio",
    value: Math.round(sum(meetings, "duration") / 60) + " h",
    icon: "clock",
    color: "orange",
    change: "↗ +15 %",
  },
  {
    label: "Réunions réussies",
    value: meetings.filter((m) => m.status === "Terminé").length,
    icon: "success",
    color: "green",
    note: "Traitement terminé",
  },
  {
    label: "Échecs",
    value: meetings.filter((m) => m.status === "Erreur").length,
    icon: "failure",
    color: "red",
    note: "À relancer",
  },
]);
const transcription = [
  {
    time: "00:00",
    text: "Bonjour à tous. Nous allons faire le point sur les objectifs de cette réunion.",
  },
  {
    time: "00:24",
    text: "Nous avons identifié trois priorités : améliorer le suivi client, finaliser le budget et coordonner les prochaines actions.",
  },
  {
    time: "01:10",
    text: "Le budget sera préparé par l’équipe financière. Chaque responsable transmettra ses besoins avant vendredi.",
  },
  {
    time: "02:05",
    text: "Nous validons le calendrier proposé. Le prochain point d’avancement est fixé à lundi.",
  },
];
const transcriptSearch = ref("");
const transcriptRows = computed(() =>
  transcription.filter((row) =>
    row.text
      .toLocaleLowerCase("fr")
      .includes(transcriptSearch.value.toLocaleLowerCase("fr")),
  ),
);
const summary =
  "L’équipe a défini les priorités du mois : suivi client, validation du budget et coordination des actions. Le calendrier a été approuvé. Les responsables transmettront leurs besoins avant vendredi ; un point de suivi aura lieu lundi.";
function openForm(edit = false) {
  editing.value = edit;
  Object.assign(
    form,
    edit
      ? selected.value
      : { title: "", organization: organisations[0].name, duration: 60 },
  );
  modal.value = true;
}
function save() {
  if (!form.title.trim()) return;
  if (editing.value) Object.assign(selected.value, form);
  else {
    const meeting = {
      ...form,
      id: Math.max(...meetings.map((m) => m.id)) + 1,
      date: "30/09/2026",
      creator: "Charles Atta",
      cost: 0,
      status: "En cours",
    };
    meetings.unshift(meeting);
    selected.value = meeting;
  }
  modal.value = false;
  notify("Réunion de démonstration enregistrée.");
}
function download(kind) {
  exportFile(
    `reunion-${selected.value.id}-${kind}-demo.${kind === "resume" ? "json" : "txt"}`,
    kind === "resume"
      ? JSON.stringify(
          { title: selected.value.title, summary, demo: true },
          null,
          2,
        )
      : `DÉMONSTRATION — ${selected.value.title}\n\n${transcription.map((r) => r.time + " " + r.text).join("\n\n")}`,
  );
  notify("Exemple téléchargé. Aucun document réel n’est utilisé.");
}
</script>
<template>
  <div class="a-toolbar">
    <span class="a-muted">Activité de septembre 2026</span
    ><button class="a-button a-button-primary" @click="openForm()">
      <AdminIcon name="plus" :size="16" />Nouvelle réunion
    </button>
  </div>
  <AdminStats :items="stats" />
  <div class="a-split" :class="{ 'a-no-detail': !selected }">
    <AdminTable
      :rows="meetings"
      :columns="columns"
      :tabs="['Terminé', 'En cours', 'Erreur']"
      :filters="[{ key: 'organization', label: 'Organisation' }]"
      :selected-id="selected?.id"
      :page-size="10"
      label="réunions"
      search-placeholder="Rechercher une réunion…"
      export-name="reunions-demo.csv"
      @select="
        selected = $event;
        tab = 'Vue d’ensemble';
      "
      ><template #id="{ value }">#{{ value }}</template
      ><template #duration="{ value }">{{ duration(value) }}</template
      ><template #cost="{ value }">{{ money(value) }}</template
      ><template #status="{ value }"><AdminBadge :value="value" /></template
    ></AdminTable>
    <AdminDetail
      v-if="selected"
      v-model="tab"
      :title="`#${selected.id} — ${selected.title}`"
      :subtitle="`${selected.organization} · ${selected.date} · ${duration(selected.duration)}`"
      :status="selected.status"
      :tabs="[
        'Vue d’ensemble',
        'Transcription',
        'Résumé',
        'Documents',
        'Logs IA',
      ]"
      @close="selected = null"
    >
      <template v-if="tab === 'Vue d’ensemble'"
        ><div class="a-grid a-grid-2">
          <AdminPanel title="Informations générales"
            ><template #action
              ><button class="a-link" @click="openForm(true)">
                <AdminIcon name="edit" :size="13" />Modifier
              </button></template
            >
            <dl class="a-definition">
              <dt>Titre</dt>
              <dd>{{ selected.title }}</dd>
              <dt>Organisation</dt>
              <dd>{{ selected.organization }}</dd>
              <dt>Créée par</dt>
              <dd>{{ selected.creator }}</dd>
              <dt>Date</dt>
              <dd>{{ selected.date }} · 10:14</dd>
              <dt>Durée</dt>
              <dd>{{ duration(selected.duration) }}</dd>
              <dt>Langue</dt>
              <dd>Français</dd>
              <dt>Participants</dt>
              <dd>8 participants</dd>
            </dl></AdminPanel
          ><AdminPanel title="Coût et modèles"
            ><div class="a-toolbar">
              <span class="a-muted">Coût total</span
              ><strong>{{ money(selected.cost) }}</strong>
            </div>
            <div class="a-divider" />
            <dl class="a-definition">
              <dt>Transcription</dt>
              <dd>{{ money(selected.cost * 0.59) }}</dd>
              <dt>Résumé</dt>
              <dd>{{ money(selected.cost * 0.41) }}</dd>
            </dl>
            <div class="a-divider" />
            <h3>Modèles utilisés</h3>
            <div class="a-list">
              <div class="a-list-item">
                <span class="a-icon-tile blue"
                  ><AdminIcon name="audio" :size="16"
                /></span>
                <div>Voxtral Mini<small>Transcription</small></div>
              </div>
              <div class="a-list-item">
                <span class="a-icon-tile purple"
                  ><AdminIcon name="cpu" :size="16"
                /></span>
                <div>Mistral Large<small>Résumé et compte rendu</small></div>
              </div>
            </div></AdminPanel
          >
        </div>
        <div class="a-grid a-grid-2">
          <AdminPanel title="Étapes du traitement"
            ><template #action
              ><AdminBadge :value="selected.status"
            /></template>
            <ol class="a-timeline">
              <li
                v-for="(step, i) in [
                  'Import de l’audio',
                  'Transcription (Voxtral)',
                  'Rédaction du résumé',
                  'Validation et enregistrement',
                  'Création du document Word',
                ]"
                :key="step"
              >
                <span
                  class="a-step"
                  :class="selected.status === 'Erreur' && i === 2 ? 'red' : ''"
                  >{{ i + 1 }}</span
                >
                <div>
                  <strong>{{ step }}</strong
                  ><small>{{
                    selected.status === "Terminé" || i < 2
                      ? "Terminé"
                      : selected.status === "Erreur" && i === 2
                        ? "Échec · modèle indisponible"
                        : "En attente"
                  }}</small>
                </div>
              </li>
            </ol>
            <button
              v-if="selected.status === 'Erreur'"
              class="a-button a-button-primary"
              @click="
                selected.status = 'En cours';
                notify('Relance simulée : la réunion passe en cours.');
              "
            >
              <AdminIcon name="refresh" :size="14" />Simuler une relance
            </button></AdminPanel
          ><AdminPanel title="Fichiers et résultats"
            ><button
              v-for="file in [
                { name: 'Transcription', kind: 'transcription', ext: 'TXT' },
                { name: 'Résumé structuré', kind: 'resume', ext: 'JSON' },
              ]"
              :key="file.kind"
              class="a-file-item a-button-wide"
              @click="download(file.kind)"
            >
              <span class="a-icon-tile small blue"
                ><AdminIcon name="file" :size="16"
              /></span>
              <div>
                <strong>{{ file.name }}</strong
                ><small>Exemple · {{ file.ext }}</small>
              </div>
              <AdminIcon name="download" :size="15" />
            </button>
            <p class="a-note a-spaced">
              L’audio, le Word et le PDF seront accessibles lors du raccordement
              aux données réelles.
            </p>
            <button
              class="a-button a-button-wide a-spaced"
              @click="tab = 'Logs IA'"
            >
              Consulter les logs d’exemple
            </button></AdminPanel
          >
        </div></template
      >
      <AdminPanel
        v-else-if="tab === 'Transcription'"
        title="Transcription de démonstration"
        ><label class="a-search"
          ><AdminIcon name="search" :size="16" /><input
            v-model="transcriptSearch"
            placeholder="Rechercher dans le texte…"
            aria-label="Rechercher dans le texte"
        /></label>
        <div v-for="row in transcriptRows" :key="row.time" class="a-list-item">
          <AdminBadge :value="row.time" color="blue" />
          <p>{{ row.text }}</p>
        </div>
        <p v-if="!transcriptRows.length" class="a-empty">
          Aucun passage trouvé.
        </p></AdminPanel
      >
      <AdminPanel v-else-if="tab === 'Résumé'" title="Résumé de la réunion"
        ><p>{{ summary }}</p>
        <div class="a-divider" />
        <h3>Décisions prises</h3>
        <ul class="a-check-list a-spaced">
          <li>
            <AdminIcon name="success" :size="15" />Calendrier de travail
            approuvé.
          </li>
          <li>
            <AdminIcon name="success" :size="15" />Budget à finaliser avant
            vendredi.
          </li>
        </ul>
        <div class="a-divider" />
        <h3>Prochaines actions</h3>
        <p class="a-muted a-spaced">
          Chaque responsable partage ses besoins. L’équipe se retrouve lundi
          pour mesurer l’avancement.
        </p></AdminPanel
      >
      <AdminPanel
        v-else-if="tab === 'Documents'"
        title="Télécharger les exemples"
        ><button
          class="a-button a-button-wide"
          @click="download('transcription')"
        >
          <AdminIcon name="download" :size="15" />Transcription (.txt)</button
        ><button
          class="a-button a-button-wide a-spaced"
          @click="download('resume')"
        >
          <AdminIcon name="download" :size="15" />Résumé (.json)
        </button>
        <p class="a-note a-spaced">
          Les documents de cette vue sont fictifs.
        </p></AdminPanel
      >
      <AdminPanel v-else title="Journal IA de démonstration">
        <pre class="a-log">
10:14:00  AUDIO       Fichier reçu
10:14:02  VOXTRAL     Transcription terminée
10:14:09  MISTRAL     {{
            selected.status === "Erreur"
              ? "Échec de rédaction : service indisponible"
              : "Résumé structuré reçu"
          }}
10:14:10  VALIDATION  {{
            selected.status === "Terminé" ? "Contenu validé" : "En attente"
          }}
10:14:11  DOCUMENT    {{
            selected.status === "Terminé" ? "Document prêt" : "En attente"
          }}</pre>
        <a
          class="a-button a-button-primary a-spaced"
          href="https://cloud.langfuse.com"
          target="_blank"
          rel="noopener noreferrer"
          >Ouvrir Langfuse<AdminIcon name="external" :size="14" /></a
      ></AdminPanel>
    </AdminDetail>
  </div>
  <AdminModal
    :open="modal"
    :title="
      editing ? 'Modifier la réunion' : 'Nouvelle réunion de démonstration'
    "
    @close="modal = false"
    ><form class="a-form" @submit.prevent="save">
      <label class="a-field"
        >Titre<input v-model="form.title" required maxlength="120" /></label
      ><label class="a-field"
        >Organisation<select v-model="form.organization">
          <option v-for="org in organisations" :key="org.id">
            {{ org.name }}
          </option>
        </select></label
      ><label class="a-field"
        >Durée (minutes)<input
          v-model.number="form.duration"
          type="number"
          min="1"
          max="480"
          required
      /></label>
      <div class="a-form-footer">
        <button type="button" class="a-button" @click="modal = false">
          Annuler</button
        ><button class="a-button a-button-primary">Enregistrer</button>
      </div>
    </form></AdminModal
  >
</template>
