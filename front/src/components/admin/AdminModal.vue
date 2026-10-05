<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from "vue";
import AdminIcon from "./AdminIcon.vue";
const props = defineProps({ open: Boolean, title: String });
const emit = defineEmits(["close"]);
const dialog = ref(null);
let previousFocus;
watch(
  () => props.open,
  async (value) => {
    if (value) {
      previousFocus = document.activeElement;
      await nextTick();
      dialog.value?.showModal();
    } else {
      dialog.value?.close();
      previousFocus?.focus();
    }
  },
);
onBeforeUnmount(() => dialog.value?.close());
</script>
<template>
  <dialog
    ref="dialog"
    class="a-modal"
    @cancel.prevent="emit('close')"
    @click="
      (event) => {
        if (event.target === dialog) emit('close');
      }
    "
  >
    <header>
      <h2>{{ title }}</h2>
      <button
        class="a-icon-button"
        aria-label="Fermer la fenêtre"
        @click="emit('close')"
      >
        <AdminIcon name="x" />
      </button>
    </header>
    <p class="a-demo-hint">
      Démonstration · Les changements restent dans cette session.
    </p>
    <slot />
  </dialog>
</template>
