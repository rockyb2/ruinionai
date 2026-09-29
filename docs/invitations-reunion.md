# Inviter les membres à une réunion

Dans **Nouvelle réunion**, rechercher et sélectionner les membres actifs de
l’organisation, puis cliquer sur **Inviter à la réunion**. L’audio n’est pas
nécessaire pour envoyer les invitations. Le lancement direct de la génération
crée également la réunion et invite les membres sélectionnés.

L’organisateur est inclus dans les participants. Chaque membre sélectionné reçoit
une notification dans l’application, avec un lien vers cette réunion dans
l’historique. Aucun e-mail n’est envoyé. Les notifications sont accessibles aux
membres, administrateurs et propriétaires ; elles sont rafraîchies à l’ouverture,
au retour dans la fenêtre et toutes les 30 secondes lorsque celle-ci est visible.

Après création, le titre et la sélection sont verrouillés sur la page. La
génération et ses éventuelles relances utilisent la même réunion et ne renvoient
pas les invitations. Cette référence est conservée pendant la présence sur la
page ; comme auparavant, le brouillon audio local ne conserve pas les
informations de réunion après un rechargement.

Les réunions historiques conservent leurs anciens participants en texte. Les
nouvelles réunions enregistrent aussi les identifiants des membres invités.
Les invitations ne changent pas la règle existante de visibilité des réunions
au sein d’une organisation.

## API et stockage

- `GET /meetings/invitees?q=...&offset=0&limit=50` : annuaire limité aux membres
  actifs de l’organisation, hors organisateur et comptes désactivés.
- `POST /meetings/` : `{ "title": "Point projet", "participant_member_ids": [12, 15] }`.
  Les noms libres ne sont plus acceptés. Maximum 100 membres, doublons éliminés.
- La réunion, les liens `meeting_participants` et les notifications
  `meeting_invitation` sont enregistrés dans la même transaction.
- `meeting_id` dans les notifications sert au lien vers la réunion exacte.
  Les alertes des invitations à rejoindre l’organisation restent réservées aux
  administrateurs et soumises au paramètre existant ; les invitations aux réunions
  sont disponibles pour tous les membres actifs.

## Installation et vérification

La migration Alembic `d27f6b8a910c` ajoute les liens participants et le champ des
notifications. Le démarrage Docker applique `alembic upgrade head` automatiquement :

```powershell
docker compose up -d --build backend frontend
```

Tests isolés, sans envoyer de vraies notifications ou appeler une IA :

```powershell
cd agent_résumé
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_meeting_invitations.py -v
cd ../front
npm.cmd run build
node tests/browser-meeting-invitations.mjs
```

Le test navigateur utilise Edge sans interface visible, une API simulée et un
microphone synthétique. Il vérifie la sélection, la recherche, l’envoi avant
l’audio, les erreurs, la réutilisation de la réunion et l’ouverture d’une
notification par un membre.
