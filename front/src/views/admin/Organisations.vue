<script setup>
import { computed, reactive, ref } from "vue";
import {
  AdminAvatar,
  AdminBadge,
  AdminChart,
  AdminDetail,
  AdminIcon,
  AdminModal,
  AdminPanel,
  AdminStats,
  AdminTable,
} from "../../components/admin";
import {
  organisations,
  users,
  meetings,
  plans,
  money,
  duration,
  notify,
} from "../../admin/demo";
import { useDemoSelection } from "../../admin/useDemoSelection";
const selected = useDemoSelection(organisations);
const tab = ref("Vue d’ensemble"),
  modal = ref(false),
  editing = ref(false);
const form = reactive({ name: "", email: "", description: "", plan: "Pro" });
const columns = [
  { key: "name", label: "Organisation" },
  { key: "plan", label: "Plan" },
  { key: "members", label: "Membres" },
  { key: "meetings", label: "Réunions" },
  { key: "hours", label: "Heures audio" },
  { key: "cost", label: "Coût IA" },
  { key: "status", label: "Statut" },
];
const stats = computed(() => [
  {
    label: "Total organisations",
    value: organisations.length,
    icon: "building",
    change: "↗ +12 %",
  },
  {
    label: "Organisations actives",
    value: organisations.filter((o) => o.status === "Actif").length,
    icon: "users",
    color: "green",
    change: "↗ +15 %",
  },
  {
    label: "En période d’essai",
    value: organisations.filter((o) => o.status === "En essai").length,
    icon: "clock",
    color: "orange",
    change: "↘ −25 %",
  },
  {
    label: "Suspendues",
    value: organisations.filter((o) => o.status === "Suspendu").length,
    icon: "failure",
    color: "red",
    change: "→ 0 %",
  },
]);
const plan = computed(
  () => plans.find((p) => p.name === selected.value?.plan) || plans[0],
);
const orgUsers = computed(() =>
  users.filter((u) => u.organization === selected.value?.name),
);
const orgMeetings = computed(() =>
  meetings.filter((m) => m.organization === selected.value?.name),
);
function openForm(edit = false) {
  editing.value = edit;
  Object.assign(
    form,
    edit
      ? selected.value
      : { name: "", email: "", description: "", plan: "Pro" },
  );
  modal.value = true;
}
function save() {
  if (!form.name.trim()) return;
  if (editing.value) {
    const previousName = selected.value.name;
    for (const user of users) {
      if (user.organization === previousName) user.organization = form.name.trim();
    }
    for (const meeting of meetings) {
      if (meeting.organization === previousName) meeting.organization = form.name.trim();
    }
    Object.assign(selected.value, { ...form, name: form.name.trim() });
  } else {
    const org = {
      ...form,
      name: form.name.trim(),
      id: Date.now(),
      status: "Actif",
      members: 0,
      meetings: 0,
      hours: 0,
      cost: 0,
      date: "30/09/2026",
    };
    organisations.unshift(org);
    selected.value = org;
  }
  modal.value = false;
  notify("Organisation enregistrée dans la démonstration.");
}
function toggleStatus() {
  selected.value.status =
    selected.value.status === "Suspendu" ? "Actif" : "Suspendu";
  notify("Statut de démonstration mis à jour.");
}
</script>
<template>
  <div class="a-toolbar">
    <span class="a-muted">Répertoire des organisations</span
    ><button class="a-button a-button-primary" @click="openForm()">
      <AdminIcon name="plus" :size="17" />Nouvelle organisation
    </button>
  </div>
  <AdminStats :items="stats" />
  <div class="a-split" :class="{ 'a-no-detail': !selected }">
    <AdminTable
      :rows="organisations"
      :columns="columns"
      :tabs="['Actif', 'En essai', 'Suspendu']"
      :filters="[{ key: 'plan', label: 'Plan' }]"
      :selected-id="selected?.id"
      label="organisations"
      search-placeholder="Rechercher une organisation…"
      export-name="organisations-demo.csv"
      :page-size="10"
      @select="
        selected = $event;
        tab = 'Vue d’ensemble';
      "
    >
      <template #name="{ row }"
        ><div class="a-identity">
          <AdminAvatar :name="row.name" /><strong>{{ row.name }}</strong>
        </div></template
      ><template #plan="{ value }"><AdminBadge :value="value" /></template
      ><template #hours="{ value }">{{ value }} h</template
      ><template #cost="{ value }">{{ money(value) }}</template
      ><template #status="{ value }"><AdminBadge :value="value" /></template>
    </AdminTable>
    <AdminDetail
      v-if="selected"
      v-model="tab"
      :title="selected.name"
      :subtitle="selected.description"
      :status="selected.status"
      :tabs="['Vue d’ensemble', 'Utilisateurs', 'Réunions', 'Abonnement']"
      @close="selected = null"
    >
      <template v-if="tab === 'Vue d’ensemble'">
        <div class="a-grid a-grid-2">
          <AdminPanel title="Informations générales"
            ><template #action
              ><button class="a-link" @click="openForm(true)">
                <AdminIcon name="edit" :size="13" />Modifier
              </button></template
            >
            <dl class="a-definition">
              <dt>Nom</dt>
              <dd>{{ selected.name }}</dd>
              <dt>Description</dt>
              <dd>{{ selected.description }}</dd>
              <dt>E-mail</dt>
              <dd>{{ selected.email }}</dd>
              <dt>Adresse</dt>
              <dd>Abidjan, Côte d’Ivoire</dd>
              <dt>Créée le</dt>
              <dd>{{ selected.date }}</dd>
              <dt>Statut</dt>
              <dd><AdminBadge :value="selected.status" /></dd></dl
          ></AdminPanel>
          <AdminPanel title="Plan et quotas"
            ><template #action
              ><button class="a-link" @click="tab = 'Abonnement'">
                Voir le plan
              </button></template
            >
            <div class="a-toolbar">
              <AdminBadge :value="plan.name" /><strong
                >{{ money(plan.price) }} / mois</strong
              >
            </div>
            <div
              v-for="quota in [
                {
                  label: 'Utilisateurs',
                  value: selected.members,
                  max: plan.users,
                },
                {
                  label: 'Heures audio',
                  value: selected.hours,
                  max: plan.hours,
                },
              ]"
              :key="quota.label"
              class="a-quota"
            >
              <div>
                <span>{{ quota.label }}</span
                ><span>{{ quota.value }} / {{ quota.max }}</span>
              </div>
              <div class="a-progress">
                <span
                  :style="{
                    width: Math.min(100, (quota.value / quota.max) * 100) + '%',
                    background: quota.value > quota.max ? '#ff3d60' : undefined,
                  }"
                />
              </div>
            </div>
            <ul class="a-check-list">
              <li
                v-for="feature in [
                  'Export Word et PDF',
                  'Transcription IA',
                  'Résumé intelligent',
                  'Support prioritaire',
                ]"
                :key="feature"
              >
                <AdminIcon name="success" :size="14" />{{ feature }}
              </li>
            </ul></AdminPanel
          >
        </div>
        <AdminStats
          :items="[
            {
              label: 'Réunions',
              value: selected.meetings,
              icon: 'video',
              color: 'blue',
              note: 'Ce mois-ci',
            },
            {
              label: 'Heures audio',
              value: selected.hours + ' h',
              icon: 'clock',
              color: 'orange',
              note: 'Ce mois-ci',
            },
            {
              label: 'Coût IA',
              value: money(selected.cost),
              icon: 'database',
              color: 'red',
              note: 'Estimation fictive',
            },
            {
              label: 'Membres',
              value: selected.members,
              icon: 'users',
              color: 'green',
              note: 'Dans l’organisation',
            },
          ]"
        />
        <div class="a-grid a-grid-2">
          <AdminPanel title="Usage des 6 derniers mois"
            ><AdminChart
              kind="monthly"
              :values="[24, 38, 52, 64, 81, selected.hours]"
              :labels="['Avr.', 'Mai', 'Juin', 'Juil.', 'Août', 'Sept.']"
              title="Heures audio sur six mois" /></AdminPanel
          ><AdminPanel title="Dernières réunions"
            ><template #action
              ><button class="a-link" @click="tab = 'Réunions'">
                Voir toutes
              </button></template
            >
            <div class="a-list">
              <RouterLink
                v-for="meeting in orgMeetings.slice(0, 3)"
                :key="meeting.id"
                :to="`/admin/reunions?id=${meeting.id}`"
                class="a-list-item"
                ><span class="a-icon-tile blue"
                  ><AdminIcon name="video" :size="15"
                /></span>
                <div>
                  {{ meeting.title
                  }}<small
                    >{{ duration(meeting.duration) }} ·
                    {{ meeting.date }}</small
                  >
                </div></RouterLink
              >
              <p v-if="!orgMeetings.length" class="a-muted">
                Aucune réunion dans cet exemple.
              </p>
            </div></AdminPanel
          >
        </div>
      </template>
      <AdminPanel
        v-else-if="tab === 'Utilisateurs'"
        title="Membres de l’organisation"
        ><div class="a-list">
          <RouterLink
            v-for="user in orgUsers"
            :key="user.id"
            :to="`/admin/utilisateurs?id=${user.id}`"
            class="a-list-item"
            ><AdminAvatar :name="user.name" />
            <div>
              <strong>{{ user.name }}</strong
              ><small>{{ user.email }}</small>
            </div>
            <AdminBadge :value="user.role"
          /></RouterLink>
          <p v-if="!orgUsers.length" class="a-muted">
            Aucun membre dans cet exemple.
          </p>
        </div></AdminPanel
      >
      <AdminPanel
        v-else-if="tab === 'Réunions'"
        title="Réunions de l’organisation"
        ><div class="a-list">
          <RouterLink
            v-for="meeting in orgMeetings"
            :key="meeting.id"
            :to="`/admin/reunions?id=${meeting.id}`"
            class="a-list-item"
            ><AdminIcon name="video" />
            <div>
              {{ meeting.title
              }}<small
                >{{ meeting.date }} · {{ duration(meeting.duration) }}</small
              >
            </div>
            <AdminBadge :value="meeting.status"
          /></RouterLink>
          <p v-if="!orgMeetings.length" class="a-muted">
            Aucune réunion dans cet exemple.
          </p>
        </div></AdminPanel
      >
      <AdminPanel v-else title="Abonnement actuel"
        ><dl class="a-definition">
          <dt>Plan</dt>
          <dd><AdminBadge :value="plan.name" /></dd>
          <dt>Prix mensuel</dt>
          <dd>{{ money(plan.price) }}</dd>
          <dt>Prochaine facture</dt>
          <dd>1 octobre 2026</dd>
          <dt>Quota audio</dt>
          <dd>{{ plan.hours }} heures / mois</dd>
        </dl>
        <RouterLink
          :to="`/admin/abonnements?id=${selected.id}`"
          class="a-button a-button-primary a-spaced"
          >Gérer l’abonnement<AdminIcon name="arrow" :size="15" /></RouterLink
      ></AdminPanel>
      <template #footer
        ><button
          class="a-button"
          :class="selected.status === 'Suspendu' ? '' : 'a-button-danger'"
          @click="toggleStatus"
        >
          {{
            selected.status === "Suspendu" ? "Réactiver" : "Suspendre"
          }}</button
        ><button class="a-button" @click="openForm(true)">
          <AdminIcon name="edit" :size="15" />Modifier</button
        ><a
          class="a-button a-button-primary"
          href="https://cloud.langfuse.com"
          target="_blank"
          rel="noopener noreferrer"
          >Ouvrir Langfuse<AdminIcon name="external" :size="14" /></a
      ></template>
    </AdminDetail>
  </div>
  <AdminModal
    :open="modal"
    :title="editing ? 'Modifier l’organisation' : 'Nouvelle organisation'"
    @close="modal = false"
    ><form class="a-form" @submit.prevent="save">
      <label class="a-field"
        >Nom de l’organisation<input
          v-model="form.name"
          required
          maxlength="80" /></label
      ><label class="a-field"
        >E-mail de contact<input
          v-model="form.email"
          type="email"
          required /></label
      ><label class="a-field"
        >Description<textarea
          v-model="form.description"
          maxlength="240"
        /></label
      ><label class="a-field"
        >Plan<select v-model="form.plan">
          <option v-for="p in plans" :key="p.name">{{ p.name }}</option>
        </select></label
      >
      <div class="a-form-footer">
        <button type="button" class="a-button" @click="modal = false">
          Annuler</button
        ><button class="a-button a-button-primary">Enregistrer</button>
      </div>
    </form></AdminModal
  >
</template>
