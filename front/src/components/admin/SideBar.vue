<script setup>
import { navigation } from "../../admin/demo";
import AdminIcon from "./AdminIcon.vue";
import logo from "@/assets/logo.png";
defineEmits(["navigate"]);
</script>
<template>
  <aside class="a-sidebar">
    <RouterLink to="/admin/tableau-de-bord" class="a-brand" @click="$emit('navigate')"
      ><div class="a-brand-logo"><img :src="logo" alt="Ruinion AI" /></div>
      <span>Super administrateur</span></RouterLink
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
      ><RouterLink to="/réunion" class="a-back-app"
        ><AdminIcon name="back" :size="16" />Retour à l’application</RouterLink
      >
    </div>
  </aside>
</template>
