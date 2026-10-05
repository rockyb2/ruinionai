<script setup>
import { initials } from "../../admin/demo";
defineProps({ name: String, large: Boolean });
const colors = [
  "#334963",
  "#069aba",
  "#367eff",
  "#8b5cf6",
  "#ba4e87",
  "#008878",
];
</script>
<template>
  <span
    class="a-avatar"
    :class="{ 'a-avatar-lg': large }"
    :style="{ background: colors[(name?.charCodeAt(0) || 0) % colors.length] }"
    aria-hidden="true"
    >{{ initials(name) }}</span
  >
</template>
