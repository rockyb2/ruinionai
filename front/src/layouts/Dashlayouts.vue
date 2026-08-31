<template lang="">
    <div class="flex gap-2 min-h-screen bg-slate-50 px-5 py-2">
        <SideBar />
        <main class="flex-1">
            <RouterView />
        </main>
    </div>
</template>
<script setup>
import { RouterView } from 'vue-router';
import SideBar from '../components/SideBar.vue';
</script>
<style lang="">

</style>