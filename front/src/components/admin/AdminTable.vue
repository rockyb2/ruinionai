<script setup>
import { computed, ref, watch } from "vue";
import { exportCsv, normalize, notify } from "../../admin/demo";
import AdminIcon from "./AdminIcon.vue";
const props = defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  filters: { type: Array, default: () => [] },
  tabs: { type: Array, default: () => [] },
  tabKey: { type: String, default: "status" },
  selectedId: [Number, String],
  pageSize: { type: Number, default: 8 },
  label: { type: String, default: "éléments" },
  searchPlaceholder: { type: String, default: "Rechercher…" },
  compact: Boolean,
  exportName: { type: String, default: "export-demo.csv" },
});
const emit = defineEmits(["select"]);
const query = ref(""),
  activeTab = ref(""),
  selectedFilters = ref({}),
  page = ref(1),
  sortKey = ref(""),
  sortDirection = ref(1);
const filtered = computed(() =>
  props.rows
    .filter(
      (row) =>
        (!activeTab.value || row[props.tabKey] === activeTab.value) &&
        Object.entries(selectedFilters.value).every(
          ([key, value]) => !value || String(row[key]) === value,
        ) &&
        (!query.value ||
          normalize(Object.values(row).join(" ")).includes(
            normalize(query.value),
          )),
    )
    .sort((a, b) =>
      !sortKey.value
        ? 0
        : sortDirection.value *
          (typeof a[sortKey.value] === "number"
            ? a[sortKey.value] - b[sortKey.value]
            : String(a[sortKey.value] ?? "").localeCompare(
                String(b[sortKey.value] ?? ""),
                "fr",
                { numeric: true },
              )),
    ),
);
const pageCount = computed(() =>
  Math.max(1, Math.ceil(filtered.value.length / props.pageSize)),
);
const displayed = computed(() =>
  filtered.value.slice(
    (page.value - 1) * props.pageSize,
    page.value * props.pageSize,
  ),
);
watch(
  [query, activeTab, selectedFilters, sortKey, sortDirection],
  () => {
    page.value = 1;
  },
  { deep: true },
);
watch(pageCount, (value) => {
  page.value = Math.min(page.value, value);
});
function sort(key) {
  if (sortKey.value === key) sortDirection.value *= -1;
  else {
    sortKey.value = key;
    sortDirection.value = 1;
  }
}
function download() {
  exportCsv(filtered.value, props.columns, props.exportName);
  notify("Export des données de démonstration téléchargé.");
}
</script>
<template>
  <section class="a-card a-data-table" :class="{ 'a-table-compact': compact }">
    <div v-if="!compact" class="a-table-toolbar">
      <div class="a-tabs" aria-label="Filtrer les résultats">
        <button :class="{ active: !activeTab }" @click="activeTab = ''">
          Tous <span>{{ rows.length }}</span></button
        ><button
          v-for="tab in tabs"
          :key="tab"
          :class="{ active: activeTab === tab }"
          @click="activeTab = tab"
        >
          {{ tab }}
          <span>{{ rows.filter((row) => row[tabKey] === tab).length }}</span>
        </button>
      </div>
      <button class="a-button" @click="download">
        <AdminIcon name="download" :size="15" />Exporter
      </button>
    </div>
    <div v-if="!compact" class="a-filters">
      <label class="a-search"
        ><AdminIcon name="search" :size="17" /><input
          v-model="query"
          :aria-label="searchPlaceholder"
          :placeholder="searchPlaceholder"
          type="search"
      /></label>
      <label v-for="filter in filters" :key="filter.key" class="a-field"
        ><span>{{ filter.label }}</span
        ><select
          :value="selectedFilters[filter.key] || ''"
          :aria-label="filter.label"
          @change="selectedFilters[filter.key] = $event.target.value"
        >
          <option value="">Tous</option>
          <option
            v-for="option in filter.options || [
              ...new Set(rows.map((row) => row[filter.key])),
            ]"
            :key="option"
            :value="option"
          >
            {{ option }}
          </option>
        </select></label
      >
    </div>
    <div class="a-table-scroll" tabindex="0" :aria-label="`Tableau : ${label}`">
      <table>
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              :aria-sort="
                sortKey === column.key
                  ? sortDirection === 1
                    ? 'ascending'
                    : 'descending'
                  : 'none'
              "
            >
              <button @click="sort(column.key)">
                {{ column.label
                }}<AdminIcon
                  v-if="sortKey === column.key"
                  :name="sortDirection === 1 ? 'down' : 'upload'"
                  :size="12"
                />
              </button>
            </th>
            <th><span class="a-sr-only">Détails</span></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in displayed"
            :key="row.id"
            :class="{ 'a-selected-row': row.id === selectedId }"
            @click="emit('select', row)"
          >
            <td v-for="column in columns" :key="column.key">
              <slot :name="column.key" :row="row" :value="row[column.key]">{{
                row[column.key]
              }}</slot>
            </td>
            <td>
              <button
                class="a-icon-button"
                :aria-label="`Voir les détails de ${row.name || row.title || row.id}`"
                @click.stop="emit('select', row)"
              >
                <AdminIcon name="more" :size="17" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!filtered.length" class="a-empty">
        <AdminIcon name="search" :size="30" /><strong>Aucun résultat</strong>
        <p>Essayez une autre recherche ou modifiez les filtres.</p>
        <button
          class="a-button"
          @click="
            query = '';
            activeTab = '';
            selectedFilters = {};
          "
        >
          Réinitialiser les filtres
        </button>
      </div>
    </div>
    <footer v-if="!compact" class="a-pagination">
      <span
        >{{ filtered.length ? (page - 1) * pageSize + 1 : 0 }}–{{
          Math.min(page * pageSize, filtered.length)
        }}
        sur {{ filtered.length }} {{ label }}</span
      >
      <nav aria-label="Pagination">
        <button
          class="a-icon-button"
          aria-label="Page précédente"
          :disabled="page === 1"
          @click="page--"
        >
          <AdminIcon name="left" :size="16" /></button
        ><button
          v-for="p in pageCount"
          :key="p"
          class="a-page-button"
          :class="{ active: p === page }"
          :aria-current="p === page ? 'page' : undefined"
          :aria-label="`Page ${p}`"
          @click="page = p"
        >
          {{ p }}</button
        ><button
          class="a-icon-button"
          aria-label="Page suivante"
          :disabled="page === pageCount"
          @click="page++"
        >
          <AdminIcon name="right" :size="16" />
        </button>
      </nav>
    </footer>
  </section>
</template>
