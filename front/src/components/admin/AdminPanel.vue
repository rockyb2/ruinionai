<script setup>
defineProps({ title: String, subtitle: String });
</script>
<template>
  <section class="a-card a-panel">
    <header v-if="title || $slots.action" class="a-panel-heading">
      <div>
        <h2>{{ title }}</h2>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>
      <slot name="action" />
    </header>
    <slot />
  </section>
</template>
