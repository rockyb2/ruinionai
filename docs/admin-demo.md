# Administration de Ruinion AI

L'espace `/admin` exige une session valide et un compte dont `users.is_super_admin` vaut `true`. Cette autorisation est vérifiée par le backend sur toutes les routes `/admin/*` ; la vérification du frontend sert seulement à présenter une page d'accès refusé propre.

## Pages connectées

Les pages suivantes utilisent la base réelle et proposent le CRUD :

| Page | Adresse | Données gérées |
| --- | --- | --- |
| Organisations | `/admin/organisations` | Paramètres existants, propriétaire initial, membres et statistiques réelles |
| Utilisateurs | `/admin/utilisateurs` | Compte, état actif, mot de passe et appartenances aux organisations |
| Réunions | `/admin/reunions` | Métadonnées, transcription, résumés, audio, Word et relance du traitement |

Les autres pages de l'interface admin restent des maquettes. Elles portent la mention « Interface de démonstration ». Les abonnements n'ont volontairement pas été ajoutés au modèle backend.

## Initialiser le premier administrateur

La migration ajoute le droit sans l'accorder automatiquement à un utilisateur. Cette séparation évite de promouvoir un compte arbitraire pendant un déploiement.

Depuis la racine du projet, après avoir remplacé l'e-mail :

```powershell
docker compose exec backend python admin_cli.py grant utilisateur@example.com
```

Pour retirer ce droit :

```powershell
docker compose exec backend python admin_cli.py revoke utilisateur@example.com
```

La commande refuse un compte inexistant ou inactif et empêche de retirer le dernier super administrateur.

## Règles de protection

- Un propriétaire d'organisation n'est pas automatiquement super administrateur de la plateforme.
- Le dernier propriétaire actif d'une organisation ne peut pas être retiré, désactivé ou supprimé.
- Un administrateur ne peut pas désactiver ou supprimer son propre compte depuis l'interface.
- Une organisation contenant des réunions doit d'abord être vidée de ses réunions ; cela permet de supprimer leurs fichiers explicitement.
- Une réunion en cours de traitement ne peut pas être modifiée ou supprimée.
- Les chemins audio et Word sont vérifiés côté serveur avant lecture ou suppression.
- Les routes admin n'utilisent pas l'en-tête `X-Organization-Id`, car leur portée couvre toute la plateforme.

## Migration et vérifications

```powershell
docker compose run --rm backend alembic upgrade head
cd agent_résumé
python -m unittest discover -s tests -v
cd ../front
npm run build
npm test
node tests/browser-admin.mjs
```

Le test navigateur simule l'API sans écrire dans la base. Il vérifie l'autorisation, les listes, la création d'une organisation, les fiches utilisateur et réunion, la transcription et l'affichage mobile.
