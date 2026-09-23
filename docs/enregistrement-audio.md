# Enregistrement audio avec pause, reprise et écoute

Le bouton micro démarre l’enregistrement. **Pause** conserve la partie en cours
et libère le micro ; le lecteur permet de l’écouter et de se déplacer dans
l’ensemble des parties. **Reprendre** arrête la lecture et ajoute une nouvelle
partie. **Terminer** autorise le bouton **Générer les résumés**. Il reste possible
de reprendre un enregistrement terminé avant son envoi.

Les fichiers importés disposent également d’un lecteur. Pour importer un fichier
à la place d’une note vocale, supprimer d’abord la note ; pour enregistrer après
un import, retirer d’abord le fichier.

## Fichiers du code

- `front/src/components/AudioRecorder.vue` : commandes et niveau réel du micro.
- `front/src/composables/useAudioRecorder.js` : acquisition, chronomètre,
  finalisation des parties, libération du micro et restauration du brouillon.
- `front/src/components/AudioPreview.vue` : lecteur commun, enchaînement et recherche.
- `front/src/service/audioDraft.js` : sauvegarde IndexedDB, séparée par compte.
- `front/src/views/Reunion.vue` : intégration et validation avant traitement.
- `agent_résumé/audio_processing.py` : normalisation et assemblage FFmpeg.
- `agent_résumé/routes/meetings.py` : réception des parties puis transcription.

Chaque pause termine un vrai fichier audio : les fichiers WebM/M4A indépendants
ne sont pas simplement collés avec `new Blob()`. Le serveur décode chaque partie
en PCM mono 16 kHz, les assemble dans l’ordre, puis crée un MP3 64 kbit/s pour
la transcription avec ElevenLabs Scribe v2. La clé `ELEVENLABS_API_KEY` du `.env`
à la racine est transmise au conteneur backend par Docker Compose.

## Lancement

FFmpeg est ajouté au Dockerfile du backend. Depuis la racine du projet :

```powershell
docker compose up -d --build backend frontend
```

Sans Docker, installer FFmpeg et rendre la commande `ffmpeg` disponible dans le
PATH du processus Python. Le micro nécessite HTTPS ou localhost et l’autorisation
du navigateur. Le format est choisi parmi les formats acceptés par le navigateur ;
l’extension du fichier suit le type réellement enregistré.

## Contrat API

`POST /meetings/{id}/audio` accepte exclusivement l’une de ces formes multipart :

- `file` : un fichier importé, contrat existant conservé.
- `files` répété : les parties enregistrées, dans leur ordre chronologique.

L’autorisation sur la réunion reste vérifiée avant tout traitement. L’ensemble
des fichiers est limité à 500 Mo, les enregistrements à 100 parties et 4 heures.
Les fichiers temporaires sont supprimés à la fin du traitement, y compris en cas
d’erreur. Les pauses et écoutes locales ne déclenchent aucun appel de transcription.

## Brouillons et limites

Le brouillon est enregistré **à chaque pause et à la fin**, dans le navigateur
du compte connecté. Il est restauré sur cette page après un rechargement, puis
effacé après une génération réussie ou une suppression explicite. En cas d’erreur
de traitement, il est conservé pour réessayer.

Le stockage est IndexedDB, base `ruinionai-audio`, magasin `drafts`. Retrouver le
brouillon nécessite le même navigateur, profil, compte et adresse du site.
Sous le lecteur, **Télécharger l’audio** permet de sauvegarder le fichier sur
l’appareil. Si des pauses ont créé plusieurs parties, **Télécharger les N parties**
propose chaque fichier séparément, numéroté dans l’ordre. Télécharger toutes les
parties pour conserver l’enregistrement complet. Ces téléchargements utilisent
les fichiers locaux, sans appel au serveur ni au service de transcription.

La partie encore en cours n’est pas garantie après fermeture ou plantage. Faire
des pauses régulières pour sauvegarder une longue réunion. Un avertissement du
navigateur est demandé si la page est fermée pendant une capture. Le stockage
local peut manquer d’espace ou être effacé par le navigateur ; ce n’est pas une
sauvegarde sur le serveur. Les titres et participants ne font pas partie de ce
brouillon audio.

Tester les autorisations micro, le verrouillage de l’écran et les interruptions
sur les appareils mobiles visés : un navigateur peut suspendre la capture en
arrière-plan. Le lecteur enchaîne les parties sans promesse de lecture sans délai
entre deux fichiers ; le MP3 final est assemblé côté serveur.

## Vérification

```powershell
cd front
npm test
npm run build
node tests/browser-audio.mjs
```

Le test navigateur utilise Edge invisible, un profil temporaire, un micro simulé
et une API simulée. Il ne contacte pas les fournisseurs IA. Pour un autre chemin
d’installation, définir `EDGE_PATH`. Les fichiers de test du navigateur sont sous
`front/node_modules/.cache/audio-smoke` (ignorés par Git).

Depuis `agent_résumé`, dans un environnement disposant des dépendances Python et
de FFmpeg :

```powershell
python -m unittest discover -s tests -v
```

Les tests contrôlent notamment la conservation et l’ordre de deux sons après
assemblage WebM/M4A, la validation multipart et l’absence d’appels IA lors d’un
upload invalide. Aucune requête payante n’est réalisée.
