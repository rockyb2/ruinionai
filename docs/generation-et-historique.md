# Génération et historique

La réunion est la tâche persistante : son identifiant ne change pas entre les demandes, les actualisations de page et les relances. La migration `e31a62b904fc` ajoute les états de traitement et les références aux audios sans supprimer les anciennes données.

## Parcours

1. `POST /meetings/{id}/audio` conserve les fichiers dans l’ordre, puis met la réunion en attente (HTTP 202). Une nouvelle transmission pour la même réunion réutilise l’audio déjà accepté.
2. Le worker du cycle de vie FastAPI réserve atomiquement une réunion. Les autres workers et requêtes ne peuvent pas la traiter simultanément.
3. Les étapes sont `queued`, `preparing`, `transcribing`, `writing`, `building`, puis `completed` ou `failed`.
4. FFmpeg assemble/normalise l’audio en MP3. Le résultat, sa durée, la transcription et les segments horodatés sont conservés en base/fichiers privés.
5. Un appel direct au modèle produit du JSON validé par Pydantic. Le serveur construit les six sections, puis sauvegarde les deux résumés dans une transaction **avant** de créer le Word avec `BuildWord`.
6. `POST /meetings/{id}/summary` retrouve la tâche active, renvoie le résultat terminé ou relance les étapes restantes. Après un échec du Word, les textes restent consultables et seule la création du document est relancée.
7. L’interface suit l’état avec `GET /meetings/{id}`. Elle peut être fermée pendant le traitement.

## Délais, concurrence et redémarrage

Chaque appel IA est exécuté dans un processus indépendant, arrêté et attendu après 90 secondes. Les tentatives automatiques du SDK sont désactivées. La rédaction essaie au maximum deux modèles distincts. Sans choix explicite, Mistral est essayé avant OpenRouter : le modèle OpenRouter gratuit par défaut ne prend pas en charge `response_format`. Pour ce modèle gratuit, le serveur demande du JSON dans le texte puis vérifie lui-même le résultat. La limite de sortie est de 3 000 jetons. `OPENROUTER_MODEL` reste un alias de `OPENROUTER_MODEL_ID`.

Pour choisir les deux modèles et leur ordre dans Docker, définissez **dans le `.env` à la racine du projet** : `SUMMARY_MODEL_IDS=mistral/mistral-small-2603,openrouter/nvidia/nemotron-3.5-lightning:free`. Les modèles définis seulement dans `agent_résumé/.env` sont utilisés en lancement Python local, mais Docker passe les variables de son propre fichier `.env` racine et ses valeurs par défaut. Un code 429 signale une limite du fournisseur : le serveur conserve la transcription, indique quel modèle a échoué et permet une relance ; il ne peut pas augmenter le quota du compte. Le modèle gratuit OpenRouter a des limites et une disponibilité différentes du modèle standard, selon sa [fiche officielle](https://openrouter.ai/blog/insights/nemotron-3-5-lightning/).

La préparation audio dispose de 330 secondes au total et le Word de 60 secondes. Un échec ne déclenche pas une boucle de tentatives. Une relance explicite reprend les étapes non sauvegardées. Chaque écriture vérifie le jeton de réservation ; un ancien worker ne peut pas écraser le résultat d’un nouveau traitement. À l’arrêt normal, le processus enfant est arrêté et la réunion passe en échec relançable. Après un arrêt brutal, le worker détecte l’expiration de la réservation (délai d’étape + 30 secondes) et expose le même état.

Un worker traite une réunion à la fois par processus serveur. La file reste dans PostgreSQL, sans dépendance Redis. Si le serveur est arrêté, les réunions en attente attendent son redémarrage.

## Audio et historique

`AUDIO_DIR` vaut `/app/storage/audio` dans Docker, sur le volume local `storage`. Les fichiers sont rangés par organisation, réunion et identifiant de dépôt. Ne supprimez pas ce volume pour mettre l’application à jour.

L’endpoint audio exige la même authentification et la même organisation que les autres endpoints de réunion. Le navigateur le charge avec les en-têtes d’authentification, puis utilise une URL Blob locale pour la lecture et la navigation. L’audio MP3 est chargé en mémoire avant lecture ; il n’y a aucun jeton d’accès dans l’URL. L’URL Blob est libérée à la fermeture de la vue.

Les anciens enregistrements jamais sauvegardés ne peuvent pas être récupérés. Leurs textes restent accessibles, avec une indication d’audio absent. Les horodatages ne sont affichés que lorsqu’ils proviennent réellement du fournisseur.

Mistral demande `timestamp_granularities=["segment"]` avec détection automatique de langue : ce paramètre ne se combine pas avec `language`, selon la [documentation Mistral](https://docs.mistral.ai/studio/audio/speech_to_text/offline_transcription). La rédaction du résumé reste en français. Configuration : `MISTRAL_API_KEY`, `MISTRAL_AUDIO_MODEL` (défaut `voxtral-mini-latest`).

Le menu Historique présente des cartes avec recherche, filtres d’état et tri. Dans une réunion : transcription/résumé/compte rendu à gauche, audio à droite, horodatages cliquables, recherche dans le texte, vitesse de lecture et téléchargements. Sur mobile les panneaux s’empilent. Les invitations restent exclusivement dans l’application.

## Vérifications et lancement

Les tests HTTP utilisent une base isolée. Les fournisseurs IA sont simulés ; la création du Word, les transactions et les contrôles d’accès sont réels. Les tests navigateur utilisent un audio synthétique et une API locale fictive.

Depuis `agent_résumé` : `.venv/Scripts/python.exe -m unittest discover -s tests -v`.
Depuis `front` : `npm test`, `npm run build`, `node tests/browser-history.mjs`, `node tests/browser-meeting-invitations.mjs`, `node tests/browser-audio.mjs` (Edge requis).

`docker compose up -d --build backend frontend` applique les migrations au démarrage et lance le worker. Docker inclut FFmpeg pour les tests audio et l’assemblage en production.
