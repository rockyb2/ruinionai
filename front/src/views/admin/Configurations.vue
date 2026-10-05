<script setup>
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  AdminAvatar,
  AdminBadge,
  AdminIcon,
  AdminPanel,
  AdminToggle,
} from "../../components/admin";
import { organisations, money, notify, exportFile } from "../../admin/demo";
import { defaults, demoSettings } from "../../admin/settings";
const route = useRoute(),
  active = ref(route.query.tab || "Général"),
  form = reactive({ ...demoSettings }),
  importInput = ref(null),
  logoInput = ref(null),
  logo = ref("");
const tabs = [
  ["Général", "settings"],
  ["Réunions", "calendar"],
  ["IA & fournisseurs", "cpu"],
  ["Facturation", "credit"],
  ["E-mail & notifications", "mail"],
  ["Sécurité", "shield"],
  ["Intégrations", "network"],
  ["Stockage", "folder"],
  ["Personnalisation", "edit"],
];
const org = computed(() => organisations[0]);
const changed = computed(
  () => JSON.stringify(form) !== JSON.stringify(demoSettings),
);
watch(
  () => route.query.tab,
  (value) => {
    if (value && tabs.some((t) => t[0] === value)) active.value = value;
  },
);
const show = (section) =>
  active.value === "Général" || active.value === section;
function save() {
  Object.assign(demoSettings, form);
  notify("Paramètres de démonstration enregistrés pour cette session.");
}
function exportSettings() {
  exportFile(
    "configuration-demo.json",
    JSON.stringify({ demo: true, settings: form }, null, 2),
    "application/json",
  );
}
async function importSettings(event) {
  try {
    const file = event.target.files?.[0];
    if (!file) return;
    if (file.size > 100000) throw new Error();
    const data = JSON.parse(await file.text());
    if (!data.settings || typeof data.settings !== "object") throw new Error();
    for (const key of Object.keys(defaults)) {
      if (typeof data.settings[key] === typeof defaults[key])
        form[key] = data.settings[key];
    }
    notify(
      "Configuration importée dans le formulaire. Enregistrez pour la conserver dans cette session.",
    );
  } catch {
    notify(
      "Fichier invalide : sélectionnez un export JSON de cette démonstration.",
    );
  } finally {
    event.target.value = "";
  }
}
function setLogo(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  if (
    !["image/png", "image/jpeg", "image/webp"].includes(file.type) ||
    file.size > 2000000
  ) {
    notify("Choisissez une image PNG, JPEG ou WebP de moins de 2 Mo.");
    return;
  }
  if (logo.value) URL.revokeObjectURL(logo.value);
  logo.value = URL.createObjectURL(file);
}
onBeforeUnmount(() => {
  if (logo.value) URL.revokeObjectURL(logo.value);
});
</script>
<template>
  <div class="a-tabs a-setting-tabs" aria-label="Sections des paramètres">
    <button
      v-for="[label, icon] in tabs"
      :key="label"
      :class="{ active: active === label }"
      @click="active = label"
    >
      <AdminIcon :name="icon" :size="15" />{{ label }}
    </button>
  </div>
  <form class="a-stack" @submit.prevent="save">
    <div class="a-settings-banner">
      <span class="a-icon-tile purple"
        ><AdminIcon name="settings" :size="24"
      /></span>
      <div>
        <h2>Paramètres de la plateforme</h2>
        <p>
          Configurez les préférences de cet espace de démonstration.
          {{ changed ? "Modifications non enregistrées." : "" }}
        </p>
      </div>
      <button class="a-button a-button-primary">
        <AdminIcon name="save" :size="16" />Enregistrer les modifications
      </button>
    </div>
    <div v-if="active === 'Général'" class="a-grid a-grid-3">
      <AdminPanel
        title="Informations de la plateforme"
        subtitle="Informations générales de votre instance Ruinion AI."
        ><div class="a-form">
          <label class="a-field"
            >Nom de la plateforme<input
              v-model="form.name"
              required
              maxlength="80" /></label
          ><label class="a-field"
            >Description<textarea
              v-model="form.description"
              maxlength="300"
            /></label
          ><label class="a-field"
            >URL de la plateforme<input v-model="form.url" type="url" required
          /></label></div></AdminPanel
      ><AdminPanel
        title="Paramètres régionaux"
        subtitle="Langue, fuseau horaire et formats par défaut."
        ><div class="a-form-grid">
          <label class="a-field"
            >Langue par défaut<select v-model="form.language">
              <option>Français</option>
              <option>Anglais</option>
            </select></label
          ><label class="a-field"
            >Fuseau horaire<select v-model="form.timezone">
              <option>Africa/Abidjan (GMT+0)</option>
              <option>Africa/Dakar (GMT+0)</option>
              <option>Europe/Paris</option>
            </select></label
          ><label class="a-field"
            >Format de date<select v-model="form.dateFormat">
              <option>JJ/MM/AAAA</option>
              <option>AAAA-MM-JJ</option>
            </select></label
          ><label class="a-field"
            >Format d’heure<select v-model="form.timeFormat">
              <option>24 heures</option>
              <option>12 heures</option>
            </select></label
          ><label class="a-field"
            >Monnaie<select v-model="form.currency">
              <option>XOF (FCFA)</option>
              <option>EUR (€)</option>
              <option>USD ($)</option>
            </select></label
          >
        </div></AdminPanel
      ><AdminPanel title="Organisation actuelle"
        ><div class="a-identity">
          <AdminAvatar :name="org.name" large />
          <div>
            <h3>{{ org.name }}</h3>
            <small>{{ org.description }}</small>
          </div>
          <AdminBadge :value="org.status" />
        </div>
        <RouterLink
          :to="`/admin/organisations?id=${org.id}`"
          class="a-button a-button-soft a-button-wide a-spaced"
          >Voir le profil<AdminIcon name="external" :size="14"
        /></RouterLink>
        <dl class="a-definition a-spaced">
          <dt>Plan actuel</dt>
          <dd><AdminBadge :value="org.plan" /></dd>
          <dt>Membres</dt>
          <dd>{{ org.members }}</dd>
          <dt>Prochaine facture</dt>
          <dd>1 octobre 2026</dd>
          <dt>Heures audio</dt>
          <dd>{{ org.hours }} h</dd>
          <dt>Coût IA</dt>
          <dd>{{ money(org.cost) }}</dd>
        </dl></AdminPanel
      >
    </div>
    <div class="a-grid a-grid-3">
      <AdminPanel
        v-if="show('Personnalisation')"
        title="Fonctionnalités"
        subtitle="Activez ou désactivez les modules de démonstration."
        ><AdminToggle
          v-for="[key, label, description] in [
            [
              'transcription',
              'Transcription audio (Voxtral)',
              'Transcription automatique des réunions',
            ],
            [
              'summary',
              'Résumé intelligent (LLM)',
              'Résumés et comptes rendus',
            ],
            ['documents', 'Export de documents', 'Word, PDF et autres formats'],
            ['teams', 'Gestion des équipes', 'Organisations et membres'],
            [
              'integrations',
              'Intégrations externes',
              'Calendriers et outils de réunion',
            ],
            ['publicApi', 'API publique', 'Accès pour les développeurs'],
          ]"
          :key="key"
          v-model="form[key]"
          :label="label"
          :description="description"
      /></AdminPanel>
      <AdminPanel
        v-if="show('Réunions')"
        title="Paramètres par défaut des réunions"
        subtitle="Valeurs utilisées dans cette prévisualisation."
        ><div class="a-form-grid">
          <label class="a-field"
            >Langue principale<select v-model="form.language">
              <option>Français</option>
              <option>Anglais</option>
            </select></label
          ><label class="a-field"
            >Modèle de transcription<select v-model="form.audioModel">
              <option>Voxtral Mini</option>
              <option>Whisper</option>
            </select></label
          ><label class="a-field"
            >Modèle de résumé<select v-model="form.summaryModel">
              <option>Mistral Large</option>
              <option>Modèle de secours</option>
            </select></label
          ><label class="a-field"
            >Format d’export<select v-model="form.exportFormat">
              <option>Word (.docx)</option>
              <option>PDF (.pdf)</option>
            </select></label
          >
        </div>
        <label class="a-field a-spaced"
          >Modèle de compte rendu<select v-model="form.template">
            <option>Structure professionnelle</option>
            <option>Synthèse courte</option>
            <option>Suivi des actions</option>
          </select></label
        ><AdminToggle
          v-model="form.diarization"
          label="Détection automatique des locuteurs" /><AdminToggle
          v-model="form.removeSilence"
          label="Suppression des silences" /><AdminToggle
          v-model="form.translation"
          label="Traduction automatique"
      /></AdminPanel>
      <AdminPanel
        v-if="show('Sécurité')"
        title="Sécurité et accès"
        subtitle="Préférences d’authentification de démonstration."
        ><AdminToggle
          v-model="form.twoFactor"
          label="Authentification à deux facteurs (2FA)"
        /><AdminToggle
          v-model="form.google"
          label="Connexion avec Google"
        /><AdminToggle
          v-model="form.microsoft"
          label="Connexion avec Microsoft"
        /><AdminToggle
          v-model="form.inviteLinks"
          label="Liens d’invitation (7 jours)"
        /><label class="a-field a-spaced"
          >Expiration des sessions<select v-model="form.sessionDuration">
            <option>1 jour</option>
            <option>7 jours</option>
            <option>30 jours</option>
          </select></label
        ><label class="a-field a-spaced"
          >Politique de mot de passe<select v-model="form.passwordPolicy">
            <option>Standard</option>
            <option>Renforcée</option>
          </select></label
        ></AdminPanel
      >
      <AdminPanel
        v-if="show('E-mail & notifications')"
        title="Notifications"
        subtitle="Préférences simulées : aucun envoi n’est effectué."
        ><AdminToggle
          v-model="form.emailNotifications"
          label="Notifications par e-mail" /><AdminToggle
          v-model="form.securityAlerts"
          label="Alertes de sécurité" /><AdminToggle
          v-model="form.weeklyReport"
          label="Rapports d’usage hebdomadaires"
      /></AdminPanel>
      <AdminPanel
        v-if="show('Stockage')"
        title="Stockage et données"
        subtitle="Paramètres de conservation et de stockage."
        ><div class="a-form-grid">
          <label class="a-field"
            >Conservation des réunions<select v-model="form.retention">
              <option>6 mois</option>
              <option>12 mois</option>
              <option>18 mois</option>
            </select></label
          ><label class="a-field"
            >Suppression automatique<select v-model="form.autoDelete">
              <option>Jamais</option>
              <option>Après 18 mois</option>
              <option>Après 12 mois</option>
            </select></label
          >
        </div>
        <AdminToggle
          v-model="form.keepOriginal"
          label="Conserver les fichiers originaux" /><AdminToggle
          v-model="form.compress"
          label="Compresser les fichiers audio"
      /></AdminPanel>
      <AdminPanel
        v-if="active === 'Facturation'"
        title="Paramètres de facturation"
        ><div class="a-form">
          <label class="a-field"
            >Mode de paiement<select v-model="form.paymentMethod">
              <option>Virement bancaire</option>
              <option>Carte bancaire</option>
              <option>Mobile Money</option>
            </select></label
          ><label class="a-field"
            >Préfixe des factures<input
              v-model="form.invoicePrefix"
              required
              maxlength="10" /></label
          ><label class="a-field"
            >Délai de paiement<select v-model="form.paymentDelay">
              <option>À réception</option>
              <option>15 jours</option>
              <option>30 jours</option>
            </select></label
          ><label class="a-field"
            >TVA (%)<input
              v-model.number="form.vat"
              type="number"
              min="0"
              max="100"
              required
          /></label></div
      ></AdminPanel>
      <AdminPanel
        v-if="active === 'IA & fournisseurs'"
        title="Modèles de la plateforme"
        ><div class="a-form">
          <label class="a-field"
            >Transcription<select v-model="form.audioModel">
              <option>Voxtral Mini</option>
              <option>Whisper</option>
            </select></label
          ><label class="a-field"
            >Résumé<select v-model="form.summaryModel">
              <option>Mistral Large</option>
              <option>Modèle de secours</option>
            </select></label
          ><RouterLink class="a-button a-button-soft" to="/admin/aifournisseurs"
            >Gérer les fournisseurs<AdminIcon name="arrow" :size="15"
          /></RouterLink></div
      ></AdminPanel>
      <AdminPanel v-if="active === 'Intégrations'" title="Intégrations externes"
        ><AdminToggle
          v-model="form.langfuse"
          label="Langfuse"
          description="Traces et suivi des appels IA"
        /><AdminToggle
          v-model="form.googleMeet"
          label="Google Meet"
          description="Réunions et calendrier"
        /><AdminToggle
          v-model="form.teamsIntegration"
          label="Microsoft Teams"
          description="Réunions et collaboration"
        />
        <p class="a-note a-spaced">
          Les connexions sont simulées dans cette interface.
        </p></AdminPanel
      >
      <AdminPanel v-if="active === 'Personnalisation'" title="Identité visuelle"
        ><div class="a-identity">
          <img
            v-if="logo"
            :src="logo"
            alt="Aperçu du logo"
            style="width: 60px; height: 60px; object-fit: contain"
          /><span v-else class="a-icon-tile blue"
            ><AdminIcon name="audio" :size="30" /></span
          ><button type="button" class="a-button" @click="logoInput.click()">
            Changer le logo</button
          ><input
            ref="logoInput"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            hidden
            @change="setLogo"
          />
        </div>
        <label class="a-field a-spaced"
          >Couleur principale<select v-model="form.accent">
            <option>Violet</option>
            <option>Bleu</option>
          </select></label
        ><label class="a-field a-spaced"
          >Densité d’affichage<select v-model="form.density">
            <option>Confortable</option>
            <option>Compacte</option>
          </select></label
        >
        <p class="a-note a-spaced">
          Préférences enregistrées comme exemples ; le thème de la maquette
          reste celui des interfaces fournies.
        </p></AdminPanel
      >
      <AdminPanel v-if="active === 'Général'" title="Actions avancées"
        ><div class="a-form">
          <button type="button" class="a-button" @click="exportSettings">
            <AdminIcon name="download" :size="16" />Exporter la configuration</button
          ><button type="button" class="a-button" @click="importInput.click()">
            <AdminIcon name="upload" :size="16" />Importer une configuration</button
          ><input
            ref="importInput"
            type="file"
            accept=".json,application/json"
            hidden
            @change="importSettings"
          /><button
            type="button"
            class="a-button a-button-danger"
            @click="
              Object.assign(form, defaults);
              notify('Valeurs par défaut rétablies dans le formulaire.');
            "
          >
            <AdminIcon name="refresh" :size="16" />Rétablir les valeurs par
            défaut
          </button>
          <p class="a-note">
            Les modifications sont temporaires et n’affectent aucune
            organisation réelle.
          </p>
        </div></AdminPanel
      >
    </div>
  </form>
</template>
