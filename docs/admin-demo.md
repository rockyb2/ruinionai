# Interfaces administrateur — démonstration

Les dix interfaces reprennent les maquettes fournies : menu bleu nuit, sélection violette, cartes de statistiques, tableaux, graphiques et panneaux de détail. Elles fonctionnent uniquement dans le navigateur.

## Ouvrir les pages

Depuis `front`, lancer `npm run dev`, puis ouvrir `/admin`. Cette adresse redirige vers `/admin/dashboard`.

| Page | Adresse |
| --- | --- |
| Vue d’ensemble | `/admin/dashboard` |
| Organisations | `/admin/organisations` |
| Utilisateurs | `/admin/utilisateurs` |
| Réunions | `/admin/reunions` |
| Abonnements | `/admin/abonnements` |
| Usage et coûts | `/admin/usage` |
| IA et fournisseurs | `/admin/aifournisseurs` |
| Incidents | `/admin/incidents` |
| Audit et sécurité | `/admin/audit` |
| Configuration | `/admin/configurations` |

## Fonctionnement des exemples

- Les tableaux permettent de rechercher, filtrer, trier, changer de page et exporter les résultats filtrés au format CSV.
- Un clic sur une ligne ouvre sa fiche. Les liens entre les vues peuvent sélectionner une fiche avec `?id=...`.
- Les formulaires créent ou modifient les exemples en mémoire. Les actions de suspension, d’invitation, de relance et de résolution sont simulées.
- Les préférences de configuration sont conservées pendant la navigation. Le rechargement du navigateur rétablit les exemples initiaux. Un export et un import JSON sont disponibles.
- Les graphiques et indicateurs sont des illustrations, sans mesure des services réels.
- Aucun appel aux API du backend ou aux fournisseurs IA n’est effectué. Aucun e-mail n’est envoyé. Les clés API affichées sont fictives ; aucune clé réelle n’est demandée.
- Le lien Langfuse ouvre son interface générale. Les journaux et les coûts présentés ici sont des exemples, pas des données récupérées de Langfuse.
- Les téléchargements de réunion sont des exemples TXT et JSON. Aucun Word, PDF ou fichier audio réel n’est généré.

## Organisation du code

- `front/src/layouts/DashAdminLayouts.vue` : en-tête commun, notifications fictives, navigation mobile et messages de confirmation.
- `front/src/components/admin/SideBar.vue` : menu des dix rubriques.
- `front/src/components/admin/` : composants réutilisables pour les tableaux, statistiques, graphiques, badges, fenêtres et fiches.
- `front/src/views/admin/` : composition et interactions propres à chaque page.
- `front/src/admin/demo.js` : jeux de données fictifs, formats et téléchargements.
- `front/src/admin/settings.js` : paramètres de démonstration et valeurs par défaut.
- `front/src/admin/admin.css` : style de l’espace administrateur et adaptation aux écrans mobiles.

Les routes de cette maquette sont accessibles sans connexion pour permettre la prévisualisation. Les routes existantes de l’application conservent leur authentification. Avant de connecter des données réelles, les routes administrateur devront recevoir une vérification du rôle côté interface **et côté serveur**.

## Vérifications

```bash
cd front
npm run build
node tests/browser-admin.mjs
```

Le test utilise le navigateur Edge local, comme les autres tests navigateur du projet. Il vérifie les dix pages sur ordinateur et mobile, plusieurs actions simulées et l’absence d’appels au backend. Les captures sont écrites dans `front/node_modules/.cache/admin-smoke/`.
