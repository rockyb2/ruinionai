<script setup>
import AdminIcon from "./AdminIcon.vue";
defineProps({ items: { type: Array, required: true } });
</script>
<template>
  <div class="a-stats" :style="{ '--stat-count': items.length }">
    <article v-for="item in items" :key="item.label" class="a-stat a-card">
      <span class="a-icon-tile" :class="item.color || 'purple'"
        ><AdminIcon :name="item.icon" :size="23"
      /></span>
      <div>
        <p class="a-stat-label">{{ item.label }}</p>
        <strong class="a-stat-value">{{ item.value }}</strong>
        <p
          v-if="item.change"
          class="a-stat-change"
          :class="item.negative ? 'a-danger-text' : 'a-success-text'"
        >
          {{ item.change }}
        </p>
        <small>{{ item.note || "vs mois précédent" }}</small>
      </div>
    </article>
  </div>
</template>
