<script setup>
import { computed, ref } from "vue";
import {
  AdminAvatar,
  AdminBadge,
  AdminDetail,
  AdminIcon,
  AdminModal,
  AdminPanel,
  AdminStats,
  AdminTable,
} from "../../components/admin";
import {
  organisations,
  plans,
  money,
  notify,
  exportFile,
} from "../../admin/demo";
import { useDemoSelection } from "../../admin/useDemoSelection";
const selected = useDemoSelection(organisations),
  tab = ref("Abonnement"),
  modal = ref(false),
  planModal = ref(null),
  nextPlan = ref("Pro"),
  orgId = ref(1);
const currentPlan = computed(
  () => plans.find((p) => p.name === selected.value?.plan) || plans[0],
);
const rows = computed(() =>
  organisations.map((org) => {
    const plan = plans.find((p) => p.name === org.plan) || plans[0];
    return {
      ...org,
      price: plan.price,
      quota: plan.hours,
      usage: Math.round((org.hours / plan.hours) * 100),
    };
  }),
);
const columns = [
  { key: "name", label: "Organisation" },
  { key: "plan", label: "Plan" },
  { key: "price", label: "Prix mensuel" },
  { key: "quota", label: "Quota" },
  { key: "usage", label: "Utilisation" },
  { key: "status", label: "Statut" },
];
const stats = computed(() => [
  {
    label: "Revenus mensuels",
    value: money(
      rows.value
        .filter((r) => r.status === "Actif")
        .reduce((s, r) => s + r.price, 0),
    ),
    icon: "credit",
    change: "↗ +18 %",
  },
  {
    label: "Abonnements actifs",
    value: organisations.filter((o) => o.status === "Actif").length,
    icon: "building",
    color: "blue",
    change: "↗ +12 %",
  },
  {
    label: "En période d’essai",
    value: organisations.filter((o) => o.status === "En essai").length,
    icon: "clock",
    color: "orange",
    change: "↘ −25 %",
  },
  {
    label: "Suspendus",
    value: organisations.filter((o) => o.status === "Suspendu").length,
    icon: "failure",
    color: "red",
    change: "→ 0 %",
  },
]);
function openEdit() {
  orgId.value = selected.value?.id || organisations[0].id;
  nextPlan.value = selected.value?.plan || "Pro";
  modal.value = true;
}
function save() {
  const org = organisations.find((o) => o.id === Number(orgId.value));
  org.plan = nextPlan.value;
  selected.value = org;
  modal.value = false;
  notify("Abonnement de démonstration modifié.");
}
function invoice(month) {
  exportFile(
    `facture-demo-${selected.value.id}-${month}.txt`,
    `FACTURE DE DÉMONSTRATION — SANS VALEUR COMPTABLE\nOrganisation : ${selected.value.name}\nPlan : ${currentPlan.value.name}\nMontant : ${money(currentPlan.value.price)}\nPériode : ${month} 2026`,
  );
}
</script>
<template>
  <div class="a-toolbar">
    <span class="a-muted">Plans et facturation · Septembre 2026</span
    ><button class="a-button a-button-primary" @click="openEdit">
      <AdminIcon name="plus" :size="16" />Créer un abonnement
    </button>
  </div>
  <AdminStats :items="stats" />
  <div class="a-split" :class="{ 'a-no-detail': !selected }">
    <div class="a-stack">
      <AdminPanel title="Plans disponibles"
        ><div class="a-plan-grid">
          <article v-for="plan in plans" :key="plan.name" class="a-plan">
            <span class="a-icon-tile" :class="plan.color"
              ><AdminIcon :name="plan.icon" :size="23"
            /></span>
            <h3>{{ plan.name }}</h3>
            <strong>{{
              plan.price ? money(plan.price) + " / mois" : "Gratuit"
            }}</strong>
            <p>
              Jusqu’à {{ plan.users }} utilisateurs<br />{{ plan.hours }} heures
              / mois
            </p>
            <AdminBadge
              :value="
                organisations.filter((o) => o.plan === plan.name).length +
                ' organisations'
              "
            /><button class="a-button a-button-soft" @click="planModal = plan">
              Voir les détails
            </button>
          </article>
        </div></AdminPanel
      >
      <AdminTable
        :rows="rows"
        :columns="columns"
        :selected-id="selected?.id"
        :tabs="['Actif', 'En essai', 'Suspendu']"
        :filters="[{ key: 'plan', label: 'Plan' }]"
        search-placeholder="Rechercher un abonnement…"
        label="abonnements"
        export-name="abonnements-demo.csv"
        @select="
          selected = organisations.find((o) => o.id === $event.id);
          tab = 'Abonnement';
        "
        ><template #name="{ row }"
          ><div class="a-identity">
            <AdminAvatar :name="row.name" />{{ row.name }}
          </div></template
        ><template #plan="{ value }"><AdminBadge :value="value" /></template
        ><template #price="{ value }">{{ money(value) }}</template
        ><template #quota="{ value }">{{ value }} h</template
        ><template #usage="{ row, value }"
          ><div style="min-width: 90px">
            <small :class="value > 100 ? 'a-danger-text' : ''"
              >{{ row.hours }} / {{ row.quota }} h · {{ value }} %</small
            >
            <div class="a-progress">
              <span
                :style="{
                  width: Math.min(100, value) + '%',
                  background: value > 100 ? '#ff365c' : '#2185ff',
                }"
              />
            </div></div></template
        ><template #status="{ value }"><AdminBadge :value="value" /></template
      ></AdminTable>
    </div>
    <AdminDetail
      v-if="selected"
      v-model="tab"
      :title="selected.name"
      :subtitle="selected.description"
      :status="selected.status"
      :tabs="['Abonnement', 'Facturation', 'Historique', 'Utilisation']"
      @close="selected = null"
    >
      <template v-if="tab === 'Abonnement'"
        ><AdminPanel title="Détails de l’abonnement"
          ><template #action
            ><button class="a-button a-button-soft" @click="openEdit">
              <AdminIcon name="edit" :size="14" />Modifier
            </button></template
          >
          <dl class="a-definition">
            <dt>Plan actuel</dt>
            <dd><AdminBadge :value="selected.plan" /></dd>
            <dt>Prix mensuel</dt>
            <dd>
              <strong>{{ money(currentPlan.price) }}</strong>
            </dd>
            <dt>Date de début</dt>
            <dd>{{ selected.date }}</dd>
            <dt>Prochaine facture</dt>
            <dd>1 octobre 2026</dd>
            <dt>Mode de paiement</dt>
            <dd>Virement bancaire</dd>
            <dt>Statut</dt>
            <dd><AdminBadge :value="selected.status" dot /></dd>
          </dl>
          <button
            class="a-button a-button-danger a-button-wide a-spaced"
            @click="
              selected.status =
                selected.status === 'Suspendu' ? 'Actif' : 'Suspendu';
              notify('Statut de l’abonnement simulé mis à jour.');
            "
          >
            {{
              selected.status === "Suspendu"
                ? "Réactiver l’abonnement"
                : "Suspendre l’abonnement"
            }}
          </button></AdminPanel
        ></template
      >
      <AdminPanel
        v-if="tab === 'Abonnement' || tab === 'Utilisation'"
        title="Quotas et utilisation"
        ><div
          v-for="q in [
            {
              label: 'Utilisateurs',
              value: selected.members,
              max: currentPlan.users,
              icon: 'users',
            },
            {
              label: 'Heures audio',
              value: selected.hours,
              max: currentPlan.hours,
              icon: 'clock',
            },
            { label: 'Stockage (jours)', value: 12, max: 30, icon: 'database' },
          ]"
          :key="q.label"
          class="a-quota"
        >
          <div>
            <span class="a-identity"
              ><AdminIcon :name="q.icon" :size="17" />{{ q.label }}</span
            ><span>{{ q.value }} / {{ q.max }}</span>
          </div>
          <div class="a-progress">
            <span
              :style="{
                width: Math.min(100, (q.value / q.max) * 100) + '%',
                background: q.value > q.max ? '#ff365c' : undefined,
              }"
            />
          </div>
          <small :class="q.value > q.max ? 'a-danger-text' : ''"
            >{{ Math.round((q.value / q.max) * 100) }} % utilisés</small
          >
        </div></AdminPanel
      >
      <AdminPanel v-if="tab === 'Abonnement'" title="Fonctionnalités incluses"
        ><ul class="a-check-list">
          <li
            v-for="feature in [
              'Transcription IA (Voxtral)',
              'Résumé intelligent (Mistral Large)',
              'Export Word et PDF',
              'Historique des réunions (30 jours)',
              'Support prioritaire',
            ]"
            :key="feature"
          >
            <AdminIcon name="success" :size="16" />{{ feature }}
          </li>
        </ul></AdminPanel
      >
      <AdminPanel v-if="tab === 'Facturation'" title="Factures de démonstration"
        ><div
          v-for="month in ['Septembre', 'Août', 'Juillet']"
          :key="month"
          class="a-list-item"
        >
          <AdminIcon name="credit" />
          <div>
            <strong>{{ month }} 2026</strong
            ><small>{{ money(currentPlan.price) }} · Payée</small>
          </div>
          <button
            class="a-icon-button"
            :aria-label="`Télécharger la facture de ${month}`"
              @click="invoice(month)"
          >
            <AdminIcon name="download" :size="16" />
          </button>
        </div>
        <p class="a-note a-spaced">
          Les fichiers exportés sont des exemples sans valeur comptable.
        </p></AdminPanel
      >
      <AdminPanel v-if="tab === 'Historique'" title="Historique de l’abonnement"
        ><ol class="a-timeline">
          <li
            v-for="event in [
              'Abonnement créé le ' + selected.date,
              'Plan actuel : ' + selected.plan,
              'Renouvellement prévu le 1 octobre 2026',
            ]"
            :key="event"
          >
            <span class="a-step"><AdminIcon name="check" :size="12" /></span>
            <div>
              <strong>{{ event }}</strong
              ><small>Événement de démonstration</small>
            </div>
          </li>
        </ol></AdminPanel
      >
    </AdminDetail>
  </div>
  <AdminModal
    :open="modal"
    title="Configurer un abonnement"
    @close="modal = false"
    ><form class="a-form" @submit.prevent="save">
      <label class="a-field"
        >Organisation<select v-model="orgId">
          <option v-for="org in organisations" :key="org.id" :value="org.id">
            {{ org.name }}
          </option>
        </select></label
      ><label class="a-field"
        >Plan<select v-model="nextPlan">
          <option v-for="plan in plans" :key="plan.name">
            {{ plan.name }}
          </option>
        </select></label
      >
      <div class="a-form-footer">
        <button type="button" class="a-button" @click="modal = false">
          Annuler</button
        ><button class="a-button a-button-primary">Enregistrer</button>
      </div>
    </form></AdminModal
  >
  <AdminModal
    :open="!!planModal"
    :title="`Plan ${planModal?.name || ''}`"
    @close="planModal = null"
    ><template v-if="planModal"
      ><p>
        {{ money(planModal.price) }} / mois · {{ planModal.hours }} heures audio
      </p>
      <p class="a-muted a-spaced">
        Jusqu’à {{ planModal.users }} utilisateurs, transcription, résumé et
        export des documents.
      </p>
      <button
        class="a-button a-button-primary a-spaced"
        @click="
          nextPlan = planModal.name;
          orgId = selected?.id || organisations[0].id;
          planModal = null;
          modal = true;
        "
      >
        Choisir ce plan
      </button></template
    ></AdminModal
  >
</template>
