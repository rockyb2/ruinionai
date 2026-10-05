<script setup>
defineProps({ modelValue: Boolean, label: String, description: String });
defineEmits(["update:modelValue"]);
</script>
<template>
  <label class="a-toggle-row"
    ><span
      ><strong>{{ label }}</strong
      ><small v-if="description">{{ description }}</small></span
    ><input
      class="a-switch"
      type="checkbox"
      role="switch"
      :checked="modelValue"
      @change="$emit('update:modelValue', $event.target.checked)"
  /></label>
</template>
