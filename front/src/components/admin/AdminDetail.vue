<script setup>
import AdminIcon from "./AdminIcon.vue";
import AdminAvatar from "./AdminAvatar.vue";
import AdminBadge from "./AdminBadge.vue";
defineProps({
  title: String,
  subtitle: String,
  status: String,
  tabs: { type: Array, default: () => [] },
  modelValue: String,
});
defineEmits(["close", "update:modelValue"]);
</script>
<template>
  <aside class="a-detail a-card" aria-label="Panneau de détails">
    <header class="a-detail-heading">
      <AdminAvatar :name="title" large />
      <div>
        <h2>{{ title }}</h2>
        <p>{{ subtitle }}</p>
        <AdminBadge v-if="status" :value="status" dot />
      </div>
      <button
        class="a-icon-button"
        aria-label="Fermer les détails"
        @click="$emit('close')"
      >
        <AdminIcon name="x" />
      </button>
    </header>
    <div
      v-if="tabs.length"
      class="a-tabs a-detail-tabs"
      aria-label="Sections du détail"
    >
      <button
        v-for="tab in tabs"
        :key="tab"
        :class="{ active: modelValue === tab }"
        @click="$emit('update:modelValue', tab)"
      >
        {{ tab }}
      </button>
    </div>
    <div class="a-detail-body"><slot /></div>
    <footer v-if="$slots.footer" class="a-detail-footer">
      <slot name="footer" />
    </footer>
  </aside>
</template>
