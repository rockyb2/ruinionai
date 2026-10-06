<script setup>
import AdminIcon from './AdminIcon.vue'
defineProps({ rows: Array, columns: Array, total: Number, offset: Number, limit: { type: Number, default: 20 }, loading: Boolean, selectedId: Number })
defineEmits(['select', 'page'])
</script>
<template>
  <section class="a-card a-data-table" :aria-busy="loading">
    <div class="a-table-scroll" tabindex="0" aria-label="Résultats">
      <table><thead><tr><th v-for="column in columns" :key="column.key">{{ column.label }}</th><th>Détails</th></tr></thead>
        <tbody><tr v-for="row in rows" :key="row.id" :class="{ 'a-selected-row': row.id === selectedId }">
          <td v-for="column in columns" :key="column.key">{{ column.format ? column.format(row[column.key], row) : row[column.key] }}</td>
          <td><button class="a-icon-button" :aria-label="`Voir ${row.name || row.title}`" @click="$emit('select', row.id)"><AdminIcon name="right" /></button></td>
        </tr></tbody>
      </table>
      <p v-if="loading" class="a-empty" role="status">Chargement…</p>
      <p v-else-if="!rows.length" class="a-empty">Aucun résultat pour ces critères.</p>
    </div>
    <footer class="a-pagination"><span>{{ total ? offset + 1 : 0 }}–{{ Math.min(offset + limit, total) }} sur {{ total }}</span>
      <nav aria-label="Pagination"><button class="a-button" :disabled="loading || offset === 0" @click="$emit('page', Math.max(0, offset - limit))">Précédent</button><button class="a-button" :disabled="loading || offset + limit >= total" @click="$emit('page', offset + limit)">Suivant</button></nav>
    </footer>
  </section>
</template>
