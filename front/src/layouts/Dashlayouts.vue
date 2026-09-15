<template>
  <div class="min-h-screen bg-slate-50 px-4 py-3 text-slate-900 sm:px-5">
    <div class="mx-auto flex max-w-[1728px] flex-col gap-4 lg:flex-row">
      <SideBar />
      <main class="min-w-0 flex-1 pb-4">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'

import SideBar from '../components/SideBar.vue'
</script>
