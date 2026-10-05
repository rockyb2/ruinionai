<script setup>
import { tone } from "../../admin/demo";
defineProps({ value: [String, Number], color: String, dot: Boolean });
</script>
<template>
  <span class="a-badge" :class="color || tone(value)"
    ><span v-if="dot" class="a-dot" />{{ value }}<slot
  /></span>
</template>
