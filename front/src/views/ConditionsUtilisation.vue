<script setup>
import logo from '@/assets/logo.png'

defineProps({
  embedded: { type: Boolean, default: false },
})

const updatedAt = '12 octobre 2026'
</script>

<template>
  <main :class="embedded ? 'bg-white text-slate-700' : 'min-h-screen bg-slate-50 text-slate-700'">
    <header v-if="!embedded" class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-4xl items-center justify-between gap-4 px-5 py-5 sm:px-8">
        <RouterLink to="/connexion" class="flex items-center gap-3 font-black text-slate-950">
          <img :src="logo" alt="Ruinion AI" class="h-12 w-auto max-w-[210px] object-contain" />
        </RouterLink>
        <RouterLink to="/connexion" class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold hover:border-blue-200 hover:text-blue-600">Retour à la connexion</RouterLink>
      </div>
    </header>

    <article class="mx-auto max-w-4xl px-5 sm:px-8" :class="embedded ? 'py-8' : 'py-12 sm:py-16'">
      <p class="text-sm font-black uppercase tracking-[0.2em] text-blue-600">Cadre d’utilisation</p>
      <h1 class="mt-4 font-black tracking-tight text-slate-950" :class="embedded ? 'text-3xl' : 'text-4xl sm:text-5xl'">Conditions d’utilisation</h1>
      <p class="mt-4 text-sm font-semibold text-slate-500">Version {{ updatedAt }}</p>

      

      <div class="mt-8 space-y-6">
        <section class="terms-card"><h2>1. Éditeur du service</h2><p>Ruinion AI est exploité par <strong>Jonathan Zadi Charles</strong>, situé à <strong>Abidjan</strong> et joignable à <strong>jonathandev225@gmail.com ou +225 05 64 21 85 67</strong>.</p></section>
        <section class="terms-card"><h2>2. Objet du service</h2><p>Ruinion AI permet d’enregistrer ou d’importer un audio, de le transcrire, de produire un résumé et un compte rendu, puis de partager ces résultats avec les membres autorisés d’une organisation.</p></section>
        <section class="terms-card"><h2>3. Création et sécurité du compte</h2><p>L’utilisateur fournit des informations exactes, protège son mot de passe et informe sans délai Ruinion AI de toute utilisation non autorisée. Les actions réalisées avec son compte sont présumées avoir été réalisées par lui jusqu’au signalement d’un incident.</p></section>
        <section class="terms-card"><h2>4. Enregistrement des réunions</h2><p>L’utilisateur est responsable de la licéité de l’enregistrement. Avant de démarrer ou d’importer un audio, il informe les participants de l’enregistrement, de sa finalité, de ses destinataires et de sa conservation, puis obtient leur accord lorsque celui-ci est requis.</p></section>
        <section class="terms-card"><h2>5. Utilisations interdites</h2><ul><li>enregistrer illégalement ou à l’insu d’une personne ;</li><li>téléverser un contenu que l’utilisateur n’est pas autorisé à traiter ;</li><li>utiliser le service pour nuire, frauder, harceler ou violer les droits d’un tiers ;</li><li>contourner les contrôles d’accès, perturber la plateforme ou rechercher une vulnérabilité sans autorisation ;</li><li>partager ses accès ou tenter d’accéder aux données d’une autre organisation.</li></ul></section>
        <section class="terms-card"><h2>6. Résultats générés par l’intelligence artificielle</h2><p>Les transcriptions et résumés peuvent contenir des erreurs ou des omissions. L’utilisateur doit vérifier les résultats avant toute décision, diffusion ou utilisation professionnelle. Ruinion AI ne remplace pas un conseil juridique, médical, financier ou professionnel qualifié.</p></section>
        <section class="terms-card"><h2>7. Données et confidentialité</h2><p>Le traitement des données est décrit dans la <RouterLink class="font-bold text-blue-600" to="/politique-de-confidentialite">politique de confidentialité</RouterLink>. L’utilisateur choisit les personnes invitées à une réunion et doit respecter la confidentialité des contenus auxquels il accède.</p></section>
        <section class="terms-card"><h2>8. Disponibilité et évolution</h2><p>Le service peut être interrompu pour maintenance, sécurité ou incident fournisseur. Les fonctionnalités, modèles IA et limites techniques peuvent évoluer. Les modifications importantes des conditions feront l’objet d’une nouvelle version.</p></section>
        <section class="terms-card"><h2>9. Suspension et suppression</h2><p>Un compte peut être suspendu en cas de risque de sécurité, d’utilisation interdite ou de violation de ces conditions. L’utilisateur peut demander la suppression de ses données conformément à la politique de confidentialité et aux droits applicables.</p></section>
        <section class="terms-card"><h2>10. Droit applicable</h2><p>Ces conditions sont régies par le droit ivoirien, sous réserve des règles impératives applicables. Les parties chercheront d’abord une solution amiable avant de saisir la juridiction compétente.</p></section>
      </div>
    </article>
  </main>
</template>

<style scoped>
.terms-card { border: 1px solid rgb(226 232 240); border-radius: 1rem; background: white; padding: 1.5rem; box-shadow: 0 8px 28px rgb(15 23 42 / .04); }
.terms-card h2 { font-size: 1.25rem; font-weight: 900; color: rgb(15 23 42); }
.terms-card p, .terms-card ul { margin-top: .8rem; line-height: 1.75; }
.terms-card ul { padding-left: 1.25rem; list-style: disc; }
.terms-card li + li { margin-top: .4rem; }
@media (min-width: 640px) { .terms-card { padding: 2rem; } }
</style>
