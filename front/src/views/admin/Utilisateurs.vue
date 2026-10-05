<script setup>
import { computed, reactive, ref } from "vue";
import {
  AdminAvatar,
  AdminBadge,
  AdminDetail,
  AdminIcon,
  AdminModal,
  AdminPanel,
  AdminStats,
  AdminTable,
  AdminToggle,
} from "../../components/admin";
import {
  users,
  organisations,
  meetings,
  audit,
  money,
  notify,
} from "../../admin/demo";
import { useDemoSelection } from "../../admin/useDemoSelection";
const selected = useDemoSelection(users),
  tab = ref("Informations"),
  modal = ref(false),
  editing = ref(false);
const form = reactive({
  name: "",
  email: "",
  organization: "Ivoir Trips",
  role: "Membre",
});
const permissionsByUser = reactive({});
const permissions = computed(() => {
  const id = selected.value?.id;
  return permissionsByUser[id] ||= { meetings: true, export: true, team: false };
});
const columns = [
  { key: "name", label: "Utilisateur" },
  { key: "organization", label: "Organisation" },
  { key: "role", label: "Rôle" },
  { key: "status", label: "Statut" },
  { key: "lastSeen", label: "Dernière connexion" },
  { key: "meetings", label: "Réunions" },
];
const stats = computed(() => [
  {
    label: "Total utilisateurs",
    value: users.length,
    icon: "users",
    color: "green",
    change: "↗ +18 %",
  },
  {
    label: "Utilisateurs actifs",
    value: users.filter((u) => u.status === "Actif").length,
    icon: "success",
    color: "green",
    change: "↗ +21 %",
  },
  {
    label: "En attente",
    value: users.filter((u) => u.status === "En attente").length,
    icon: "send",
    change: "↗ +40 %",
  },
  {
    label: "Inactifs",
    value: users.filter((u) => u.status === "Inactif").length,
    icon: "clock",
    color: "orange",
    change: "↘ −12 %",
  },
]);
const organization = computed(() =>
  organisations.find((o) => o.name === selected.value?.organization),
);
const userMeetings = computed(() =>
  meetings.filter((m) => m.creator === selected.value?.name),
);
const userActions = computed(() =>
  audit.filter((a) => a.user === selected.value?.name),
);
function openForm(edit = false) {
  editing.value = edit;
  Object.assign(
    form,
    edit
      ? selected.value
      : {
          name: "",
          email: "",
          organization: organisations[0].name,
          role: "Membre",
        },
  );
  modal.value = true;
}
function save() {
  if (!form.name.trim()) return;
  if (editing.value) Object.assign(selected.value, form);
  else {
    const user = {
      ...form,
      id: Date.now(),
      status: "En attente",
      lastSeen: "Jamais",
      meetings: 0,
      date: "30 septembre 2026",
    };
    users.unshift(user);
    selected.value = user;
  }
  modal.value = false;
  notify(
    editing.value
      ? "Profil de démonstration modifié."
      : "Invitation simulée. Aucun message n’a été envoyé.",
  );
}
</script>
<template>
  <div class="a-toolbar">
    <span class="a-muted">Comptes et accès à la plateforme</span
    ><button class="a-button a-button-primary" @click="openForm()">
      <AdminIcon name="plus" :size="17" />Inviter un utilisateur
    </button>
  </div>
  <AdminStats :items="stats" />
  <div class="a-split" :class="{ 'a-no-detail': !selected }">
    <AdminTable
      :rows="users"
      :columns="columns"
      :tabs="['Actif', 'Inactif', 'En attente', 'Suspendu']"
      :filters="[
        { key: 'organization', label: 'Organisation' },
        { key: 'role', label: 'Rôle' },
      ]"
      :selected-id="selected?.id"
      :page-size="10"
      label="utilisateurs"
      search-placeholder="Rechercher un utilisateur, un e-mail…"
      export-name="utilisateurs-demo.csv"
      @select="
        selected = $event;
        tab = 'Informations';
      "
    >
      <template #name="{ row }"
        ><div class="a-identity">
          <AdminAvatar :name="row.name" />
          <div>
            <strong>{{ row.name }}</strong
            ><small>{{ row.email }}</small>
          </div>
        </div></template
      ><template #role="{ value }"><AdminBadge :value="value" /></template
      ><template #status="{ value }"
        ><AdminBadge :value="value" dot
      /></template>
    </AdminTable>
    <AdminDetail
      v-if="selected"
      v-model="tab"
      :title="selected.name"
      :subtitle="`${selected.role} · ${selected.organization}`"
      :status="selected.status"
      :tabs="['Informations', 'Activité', 'Réunions', 'Permissions']"
      @close="selected = null"
    >
      <template v-if="tab === 'Informations'"
        ><AdminPanel title="Informations personnelles"
          ><template #action
            ><button class="a-button a-button-soft" @click="openForm(true)">
              <AdminIcon name="edit" :size="14" />Modifier
            </button></template
          >
          <dl class="a-definition">
            <dt>Nom complet</dt>
            <dd>{{ selected.name }}</dd>
            <dt>E-mail</dt>
            <dd>{{ selected.email }}</dd>
            <dt>Organisation</dt>
            <dd>
              <RouterLink
                :to="`/admin/organisations?id=${organization?.id || 1}`"
                class="a-link"
                >{{ selected.organization }}</RouterLink
              >
            </dd>
            <dt>Rôle</dt>
            <dd><AdminBadge :value="selected.role" /></dd>
            <dt>Statut</dt>
            <dd><AdminBadge :value="selected.status" dot /></dd>
            <dt>Membre depuis</dt>
            <dd>{{ selected.date }}</dd>
            <dt>Dernière connexion</dt>
            <dd>{{ selected.lastSeen }}</dd>
            <dt>Fuseau horaire</dt>
            <dd>Africa/Abidjan</dd>
          </dl></AdminPanel
        >
        <AdminPanel title="Statistiques d’usage"
          ><AdminStats
            :items="[
              {
                label: 'Réunions créées',
                value: selected.meetings,
                icon: 'video',
                color: 'blue',
                note: 'Ce mois-ci',
              },
              {
                label: 'Heures audio',
                value: Math.round(selected.meetings * 1.4) + ' h',
                icon: 'clock',
                color: 'orange',
                note: 'Ce mois-ci',
              },
              {
                label: 'Coût IA estimé',
                value: money(selected.meetings * 487),
                icon: 'database',
                color: 'red',
                note: 'Données fictives',
              },
              {
                label: 'Documents exportés',
                value: Math.floor(selected.meetings / 4),
                icon: 'file',
                color: 'green',
                note: 'Ce mois-ci',
              },
            ]"
        /></AdminPanel>
        <AdminPanel title="Organisation et rôle"
          ><template #action
            ><RouterLink
              :to="`/admin/organisations?id=${organization?.id || 1}`"
              class="a-link"
              >Voir l’organisation</RouterLink
            ></template
          >
          <div class="a-identity">
            <AdminAvatar :name="selected.organization" large />
            <div>
              <strong>{{ selected.organization }}</strong
              ><small>{{ organization?.description }}</small>
            </div>
            <AdminBadge :value="selected.role" /></div></AdminPanel
      ></template>
      <AdminPanel v-else-if="tab === 'Activité'" title="Dernières actions"
        ><div class="a-list">
          <div
            v-for="action in userActions"
            :key="action.id"
            class="a-list-item"
          >
            <AdminIcon name="activity" />
            <div>
              <strong>{{ action.action }}</strong
              ><small>{{ action.date }} · {{ action.time }}</small>
              <p>{{ action.details }}</p>
            </div>
            <AdminBadge :value="action.status" />
          </div>
          <p v-if="!userActions.length" class="a-muted">
            Aucune activité pour ce compte de démonstration.
          </p>
        </div></AdminPanel
      >
      <AdminPanel v-else-if="tab === 'Réunions'" title="Réunions créées"
        ><div class="a-list">
          <RouterLink
            v-for="meeting in userMeetings"
            :key="meeting.id"
            :to="`/admin/reunions?id=${meeting.id}`"
            class="a-list-item"
            ><AdminIcon name="video" />
            <div>
              {{ meeting.title }}<small>{{ meeting.date }}</small>
            </div>
            <AdminBadge :value="meeting.status"
          /></RouterLink>
          <p v-if="!userMeetings.length" class="a-muted">
            Aucune réunion pour cet utilisateur.
          </p>
        </div></AdminPanel
      >
      <AdminPanel v-else title="Permissions de démonstration"
        ><AdminToggle
          v-model="permissions.meetings"
          label="Créer et consulter des réunions"
        /><AdminToggle
          v-model="permissions.export"
          label="Exporter des documents"
        /><AdminToggle
          v-model="permissions.team"
          label="Gérer les membres de l’équipe"
        /><button
          class="a-button a-button-primary a-spaced"
          @click="
            notify('Permissions simulées enregistrées pour cette session.')
          "
        >
          Enregistrer les permissions
        </button></AdminPanel
      >
      <template #footer
        ><button
          class="a-button a-button-danger"
          @click="
            selected.status =
              selected.status === 'Suspendu' ? 'Actif' : 'Suspendu';
            notify('Statut du compte de démonstration modifié.');
          "
        >
          {{
            selected.status === "Suspendu"
              ? "Réactiver le compte"
              : "Suspendre le compte"
          }}</button
        ><button
          class="a-button"
          @click="
            notify('Réinitialisation simulée. Aucun e-mail n’a été envoyé.')
          "
        >
          <AdminIcon name="key" :size="14" />Réinitialiser le mot de passe
        </button></template
      >
    </AdminDetail>
  </div>
  <AdminModal
    :open="modal"
    :title="editing ? 'Modifier l’utilisateur' : 'Inviter un utilisateur'"
    @close="modal = false"
    ><form class="a-form" @submit.prevent="save">
      <label class="a-field"
        >Nom complet<input v-model="form.name" required maxlength="80" /></label
      ><label class="a-field"
        >Adresse e-mail<input
          v-model="form.email"
          type="email"
          required /></label
      ><label class="a-field"
        >Organisation<select v-model="form.organization">
          <option v-for="org in organisations" :key="org.id">
            {{ org.name }}
          </option>
        </select></label
      ><label class="a-field"
        >Rôle<select v-model="form.role">
          <option>Membre</option>
          <option>Administrateur</option>
          <option>Propriétaire</option>
        </select></label
      >
      <div class="a-form-footer">
        <button type="button" class="a-button" @click="modal = false">
          Annuler</button
        ><button class="a-button a-button-primary">
          {{ editing ? "Enregistrer" : "Simuler l’invitation" }}
        </button>
      </div>
    </form></AdminModal
  >
</template>
