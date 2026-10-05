<script setup>
import { navigation } from "../../admin/demo";
import AdminIcon from "./AdminIcon.vue";
defineEmits(["navigate"]);
</script>
<template>
  <aside class="a-sidebar">
    <RouterLink to="/admin/dashboard" class="a-brand" @click="$emit('navigate')"
      ><AdminIcon name="audio" :size="34" />
      <div>
        <strong>Ruinion AI</strong><span>Super administrateur</span>
      </div></RouterLink
    >
    <div class="a-nav-label">ESPACE ADMINISTRATION</div>
    <nav aria-label="Navigation administrateur">
      <RouterLink
        v-for="item in navigation"
        :key="item.path"
        :to="item.path"
        @click="$emit('navigate')"
        ><AdminIcon :name="item.icon" /><span>{{
          item.label
        }}</span></RouterLink
      >
    </nav>
    <div class="a-sidebar-bottom">
      <a
        href="https://cloud.langfuse.com"
        target="_blank"
        rel="noopener noreferrer"
        class="a-langfuse"
        ><div>
          <span class="a-langfuse-mark">◉</span><strong>Langfuse</strong
          ><AdminIcon name="external" :size="15" />
        </div>
        <p>Les traces et les métriques IA, en détail.</p></a
      ><RouterLink to="/reunion" class="a-back-app"
        ><AdminIcon name="back" :size="16" />Retour à l’application</RouterLink
      >
    </div>
  </aside>
</template>
