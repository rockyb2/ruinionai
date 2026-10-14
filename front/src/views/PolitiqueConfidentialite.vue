<script setup>
import logo from '@/assets/logo.png'

defineProps({
  embedded: { type: Boolean, default: false },
})

const updatedAt = '12 octobre 2026'

const sections = [
  { id: 'responsable', label: 'Responsable du traitement' },
  { id: 'donnees', label: 'Données collectées' },
  { id: 'finalites', label: 'Utilisation des données' },
  { id: 'destinataires', label: 'Destinataires' },
  { id: 'conservation', label: 'Conservation' },
  { id: 'securite', label: 'Sécurité' },
  { id: 'droits', label: 'Vos droits' },
]

function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <main :class="embedded ? 'bg-white text-slate-800' : 'min-h-screen bg-slate-50 text-slate-800'">
    <header v-if="!embedded" class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-5 sm:px-8">
        <RouterLink to="/connexion" class="flex items-center gap-3 font-black text-slate-950">
          <img :src="logo" alt="Ruinion AI" class="h-12 w-auto max-w-[210px] object-contain" />
        </RouterLink>
        <RouterLink to="/connexion" class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 hover:border-blue-200 hover:text-blue-600">
          Retour à la connexion
        </RouterLink>
      </div>
    </header>

    <section :class="embedded ? 'border-b border-slate-100 bg-white' : 'border-b border-blue-100 bg-gradient-to-br from-blue-50 via-white to-indigo-50'">
      <div class="mx-auto max-w-6xl px-5 sm:px-8" :class="embedded ? 'py-8' : 'py-14 sm:py-20'">
        <p class="text-sm font-black uppercase tracking-[0.2em] text-blue-600">Protection des données</p>
        <h1 class="mt-4 max-w-3xl font-black tracking-tight text-slate-950" :class="embedded ? 'text-3xl' : 'text-4xl sm:text-5xl'">Politique de confidentialité</h1>
        <p class="mt-5 max-w-3xl text-lg leading-8 text-slate-600">
          Cette politique explique quelles données Ruinion AI traite pour transcrire et résumer vos réunions, pourquoi elles sont utilisées et comment exercer vos droits.
        </p>
        <p class="mt-5 text-sm font-semibold text-slate-500">Dernière mise à jour : {{ updatedAt }}</p>
      </div>
    </section>

    <div class="mx-auto grid max-w-6xl gap-8 px-5 py-10 sm:px-8" :class="embedded ? '' : 'lg:grid-cols-[240px_minmax(0,1fr)] lg:py-14'">
      <aside v-if="!embedded" class="h-fit rounded-2xl border border-slate-200 bg-white p-5 lg:sticky lg:top-6">
        <strong class="text-sm text-slate-950">Sommaire</strong>
        <nav class="mt-4 grid gap-2" aria-label="Sommaire de la politique">
          <button v-for="section in sections" :key="section.id" type="button" class="rounded-lg px-3 py-2 text-left text-sm font-semibold text-slate-500 hover:bg-blue-50 hover:text-blue-700" @click="scrollToSection(section.id)">
            {{ section.label }}
          </button>
        </nav>
      </aside>

      <article class="min-w-0 space-y-8">
        

        <section id="responsable" class="privacy-card">
          <h2>1. Responsable du traitement</h2>
          <p>Le responsable du traitement est l’entité qui édite et exploite Ruinion AI.</p>
          <dl class="mt-5 grid gap-3 rounded-xl bg-slate-50 p-5 text-sm sm:grid-cols-[180px_1fr]">
            <dt>Identité juridique</dt><dd>Zadi Jonathan Charles David</dd>
            <dt>Adresse</dt><dd>Abidjan</dd>
            <dt>Contact confidentialité</dt><dd>jonathandev225@gmail.com / +225 05 64 21 85 67</dd>
          </dl>
          <p class="mt-5">Lorsqu’une organisation utilise Ruinion AI pour ses propres réunions, elle peut également être responsable des décisions relatives à l’enregistrement de ses participants et aux personnes autorisées à consulter la réunion.</p>
        </section>

        <section id="donnees" class="privacy-card">
          <h2>2. Données que nous traitons</h2>
          <div class="mt-5 grid gap-4 sm:grid-cols-2">
            <div class="privacy-block"><h3>Compte et organisation</h3><p>Nom, prénom, adresse électronique, mot de passe haché, organisation, rôle, statut, invitations et notifications.</p></div>
            <div class="privacy-block"><h3>Réunions</h3><p>Titre, date, organisateur, membres invités, durée et état du traitement.</p></div>
            <div class="privacy-block"><h3>Contenus</h3><p>Fichiers audio, transcription et segments horodatés, résumé, compte rendu et document généré.</p></div>
            <div class="privacy-block"><h3>Sécurité et fonctionnement</h3><p>Routes appelées, résultat HTTP, événements d’authentification, empreinte HMAC de l’adresse IP, modèle utilisé, durée, volume et coût estimé des traitements IA.</p></div>
          </div>
          <p class="mt-5">Un brouillon audio peut aussi rester temporairement dans le stockage local du navigateur jusqu’à son envoi, sa suppression ou le nettoyage des données du navigateur.</p>
        </section>

        <section id="finalites" class="privacy-card">
          <h2>3. Pourquoi ces données sont utilisées</h2>
          <ul class="privacy-list">
            <li>créer et sécuriser les comptes et les espaces d’organisation ;</li>
            <li>enregistrer ou importer un audio à la demande de l’utilisateur ;</li>
            <li>transcrire l’audio, générer un résumé et produire un compte rendu ;</li>
            <li>partager une réunion avec les membres expressément invités ;</li>
            <li>fournir l’historique, les notifications et les documents téléchargeables ;</li>
            <li>prévenir les abus, diagnostiquer les erreurs et tenir un journal d’audit ;</li>
            <li>mesurer les volumes techniques et les coûts des fournisseurs IA.</li>
          </ul>
          <p class="mt-5">Ces traitements sont nécessaires à la fourniture du service demandé, à la sécurité de la plateforme et au respect des obligations applicables. Lorsque le consentement constitue la base appropriée, il peut être retiré pour l’avenir.</p>
        </section>

        <section class="privacy-card">
          <h2>4. Enregistrement des participants</h2>
          <p>L’utilisateur qui lance ou importe un enregistrement doit informer les personnes enregistrées et obtenir leur accord lorsque la loi ou le contexte l’exige. Il doit notamment expliquer la finalité de l’enregistrement, les personnes qui pourront y accéder et sa durée de conservation.</p>
          <p class="mt-4 font-semibold text-slate-950">Ruinion AI ne doit pas être utilisé pour enregistrer une personne à son insu lorsque son information ou son autorisation est requise.</p>
        </section>

        <section id="destinataires" class="privacy-card">
          <h2>5. Qui peut recevoir les données</h2>
          <ul class="privacy-list">
            <li>le créateur de la réunion et les membres qui y ont été invités ;</li>
            <li>les services techniques de Ruinion AI strictement nécessaires au fonctionnement et à la sécurité ;</li>
            <li>Mistral AI/Voxtral pour la transcription et, selon la configuration, la rédaction ;</li>
            <li>OpenRouter et les modèles de secours configurés lorsqu’un premier modèle de rédaction échoue ;</li>
            <li>Langfuse pour les métriques techniques de traçage, notamment le modèle, la durée, la consommation et le coût estimé, sans audio, transcription, résumé ni réponse générée ;</li>
            <li>les prestataires d’hébergement et de stockage nécessaires à l’exploitation.</li>
          </ul>
          <p class="mt-5">Ruinion AI ne vend pas les données de réunion et ne les utilise pas pour de la publicité ciblée. Certains fournisseurs peuvent traiter des données hors de Côte d’Ivoire selon leur infrastructure et leurs engagements contractuels.</p>
        </section>

        <section id="conservation" class="privacy-card">
          <h2>6. Durée de conservation</h2>
          <div class="mt-5 overflow-x-auto">
            <table class="w-full min-w-[620px] border-collapse text-left text-sm">
              <thead><tr><th>Donnée</th><th>Critère actuel de conservation</th></tr></thead>
              <tbody>
                <tr><td>Compte et appartenance à une organisation</td><td>Pendant la durée d’utilisation du compte, puis selon les obligations légales et les demandes valides de suppression.</td></tr>
                <tr><td>Audio, transcription, résumé et document</td><td>Tant que la réunion correspondante est conservée ou jusqu’à une suppression autorisée.</td></tr>
                <tr><td>Invitations</td><td>Jusqu’à expiration, révocation ou acceptation, puis pour la gestion et la preuve de l’invitation.</td></tr>
                <tr><td>Journal d’audit</td><td>Aussi longtemps que nécessaire à la sécurité, à la détection des abus et à la preuve des actions administratives.</td></tr>
                <tr><td>Traces techniques IA</td><td>Selon la durée configurée dans Langfuse et les besoins de suivi des performances et des coûts.</td></tr>
              </tbody>
            </table>
          </div>
          <p class="mt-5 rounded-xl bg-blue-50 p-4 text-sm font-semibold text-blue-950">La suppression automatique des audios après un nombre déterminé de jours n’est pas encore active dans la version actuelle. Une durée configurable doit être mise en place avant de pouvoir annoncer cette fonction.</p>
        </section>

        <section id="securite" class="privacy-card">
          <h2>7. Mesures de sécurité</h2>
          <ul class="privacy-list">
            <li>isolation des réunions par organisation et contrôle des rôles ;</li>
            <li>chiffrement AES-256-GCM des transcriptions, segments, résumés et comptes rendus en base ;</li>
            <li>hachage des mots de passe et limitation des tentatives de connexion ;</li>
            <li>stockage privé des fichiers et restriction de l’accès au contenu des réunions ;</li>
            <li>journalisation des actions administratives sans corps de requête ni adresse IP en clair ;</li>
            <li>réduction des données envoyées à l’outil de traçage IA.</li>
          </ul>
          <p class="mt-5">Aucune mesure ne supprime entièrement les risques. En cas d’incident confirmé, Ruinion AI appliquera les mesures de limitation, d’analyse et de notification requises.</p>
        </section>

        <section id="droits" class="privacy-card">
          <h2>8. Vos droits</h2>
          <p>Conformément à la loi ivoirienne n° 2013-450 du 19 juin 2013 relative à la protection des données à caractère personnel, vous pouvez notamment demander l’accès, la rectification, l’opposition, la limitation ou la suppression des données qui vous concernent, et retirer un consentement lorsqu’il constitue la base du traitement.</p>
          <p class="mt-4">Pour exercer ces droits, utilisez l’adresse de contact confidentialité indiquée à la section 1. Une vérification raisonnable de votre identité pourra être demandée pour éviter de communiquer des données à une autre personne.</p>
          <p class="mt-4">Vous pouvez également vous adresser à l’Autorité de protection des données de Côte d’Ivoire, exercée par l’ARTCI.</p>
          <div class="mt-5 flex flex-wrap gap-3">
            <a class="privacy-link" href="https://www.artci.ci/images/stories/pdf/lois/loi_2013_450.pdf" target="_blank" rel="noopener noreferrer">Consulter la loi ivoirienne</a>
            <a class="privacy-link" href="https://consommateurs.artci.ci/" target="_blank" rel="noopener noreferrer">Contacter l’ARTCI</a>
          </div>
        </section>

        <section class="privacy-card">
          <h2>9. Stockage local et cookies</h2>
          <p>Le navigateur utilise un stockage local ou de session pour maintenir la connexion et mémoriser le contexte de l’organisation. Un stockage IndexedDB peut conserver temporairement les parties d’un enregistrement non encore envoyé. Aucun cookie publicitaire n’est nécessaire au fonctionnement décrit ici.</p>
        </section>

        <section class="privacy-card">
          <h2>10. Évolution de cette politique</h2>
          <p>Cette politique peut évoluer lorsque les fonctionnalités, les fournisseurs ou les durées de conservation changent. La date de mise à jour figurant en haut de la page permet d’identifier la version applicable.</p>
          <RouterLink class="privacy-link mt-5 inline-flex" to="/conditions-d-utilisation">Consulter les conditions d’utilisation</RouterLink>
        </section>
      </article>
    </div>
  </main>
</template>

<style scoped>
.privacy-card { scroll-margin-top: 1.5rem; border: 1px solid rgb(226 232 240); border-radius: 1rem; background: white; padding: 1.5rem; box-shadow: 0 8px 28px rgb(15 23 42 / 0.04); }
.privacy-card h2 { font-size: 1.35rem; font-weight: 900; letter-spacing: -0.02em; color: rgb(15 23 42); }
.privacy-card h3 { font-weight: 850; color: rgb(15 23 42); }
.privacy-card p, .privacy-list { line-height: 1.75; color: rgb(71 85 105); }
.privacy-block { border-radius: .8rem; background: rgb(248 250 252); padding: 1rem; }
.privacy-block p { margin-top: .35rem; font-size: .9rem; }
.privacy-list { margin-top: 1rem; padding-left: 1.25rem; list-style: disc; }
.privacy-list li + li { margin-top: .45rem; }
dt { font-weight: 800; color: rgb(51 65 85); }
dd { color: rgb(71 85 105); }
th, td { border-bottom: 1px solid rgb(226 232 240); padding: .9rem; vertical-align: top; }
th { background: rgb(248 250 252); font-weight: 800; color: rgb(51 65 85); }
.privacy-link { border-radius: .75rem; border: 1px solid rgb(191 219 254); padding: .7rem 1rem; font-size: .85rem; font-weight: 800; color: rgb(37 99 235); }
.privacy-link:hover { background: rgb(239 246 255); }
@media (min-width: 640px) { .privacy-card { padding: 2rem; } }
</style>
