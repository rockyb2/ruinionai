# Tutoriel utilisateur — Ruinion AI V1

Ce guide explique comment utiliser la première version de Ruinion AI, depuis la création d’un espace jusqu’à la consultation d’un compte rendu.

## 1. Ce que permet la V1

Ruinion AI permet de :

- créer un espace de travail pour une organisation ;
- inviter des membres dans une équipe ;
- créer une réunion et choisir les membres invités ;
- enregistrer une réunion avec le microphone du navigateur ;
- importer un fichier audio existant ;
- générer automatiquement une transcription, un résumé court et un compte rendu détaillé ;
- écouter l’audio en suivant la transcription ;
- rechercher un passage dans la transcription ;
- télécharger le compte rendu au format Word ;
- retrouver les anciennes réunions dans l’historique.

## 2. Créer son espace

1. Ouvrez la page de connexion.
2. Cliquez sur **Créer un espace**.
3. Renseignez votre prénom, votre nom, votre adresse e-mail et le nom de votre organisation.
4. Choisissez un mot de passe d’au moins 8 caractères, puis confirmez-le.
5. Cliquez sur **Créer l’espace**.

Le compte et l’organisation sont créés ensemble. Le premier utilisateur devient le responsable initial de cet espace.

Si votre organisation existe déjà, ne créez pas un nouvel espace : demandez plutôt un lien d’invitation à son propriétaire ou à un administrateur autorisé.

## 3. Se connecter

1. Ouvrez la page **Connexion**.
2. Saisissez votre adresse e-mail et votre mot de passe.
3. Cliquez sur **Se connecter**.

Après la connexion, l’application ouvre la page **Nouvelle réunion**.

Le menu principal contient :

- **Nouvelle réunion** : créer et traiter une réunion ;
- **Historique** : retrouver les réunions et leurs résultats ;
- **Équipe** : consulter les membres et gérer les invitations ;
- **Paramètres** : configurer l’organisation.

## 4. Inviter un membre dans l’équipe

Les invitations d’équipe sont accessibles depuis la page **Équipe**.

1. Ouvrez **Équipe** dans le menu.
2. Dans **Inviter un membre**, saisissez l’adresse e-mail de la personne.
3. Choisissez son rôle :
   - **Membre** : peut créer et consulter des réunions ;
   - **Administrateur** : peut également gérer certains accès, si le propriétaire l’autorise.
4. Cliquez sur **Créer l’invitation**.
5. Copiez immédiatement le lien affiché et transmettez-le à la personne invitée.

La V1 n’envoie pas automatiquement ce lien par e-mail. Le lien n’est affiché en clair qu’au moment de sa création.

La personne invitée ouvre le lien puis :

- se connecte si elle possède déjà un compte ;
- ou crée son compte avec l’adresse e-mail invitée.

Une invitation expirée peut être renouvelée depuis l’onglet **Invitations** de la page Équipe.

## 5. Comprendre les rôles

### Propriétaire

Le propriétaire contrôle l’organisation. Il peut notamment modifier les paramètres, gérer les rôles et décider si les administrateurs peuvent envoyer des invitations.

### Administrateur

L’administrateur aide à gérer l’équipe. Ses droits d’invitation dépendent des règles choisies par le propriétaire.

### Membre

Le membre utilise l’espace de réunion, crée des réunions et consulte les contenus auxquels il a accès.

## 6. Créer une réunion

1. Cliquez sur **Nouvelle réunion**.
2. Saisissez un titre clair, par exemple `Réunion commerciale du 7 octobre`.
3. Dans **Inviter des membres de l’équipe**, sélectionnez les personnes concernées.
4. Si vous souhaitez créer immédiatement la réunion et envoyer les invitations internes, cliquez sur **Inviter à la réunion**.

Vous pouvez aussi sélectionner les membres puis lancer directement la génération : la réunion sera créée avec les membres sélectionnés.

Une fois la réunion créée, son titre et ses invités ne peuvent plus être modifiés depuis cet écran.

## 7. Ajouter l’audio

Deux méthodes sont disponibles. Il faut en choisir une seule pour une réunion.

### Méthode A — Enregistrer avec le microphone

1. Cliquez sur **Enregistrer**.
2. Autorisez le navigateur à utiliser votre microphone.
3. Pendant la réunion, utilisez **Mettre en pause** si nécessaire.
4. Cliquez sur **Reprendre** pour continuer.
5. Terminez l’enregistrement.
6. Écoutez l’aperçu pour vérifier que le son est exploitable.

L’enregistrement peut être découpé en plusieurs parties. L’application permet de les écouter et de les télécharger avant l’envoi.

Un brouillon local est conservé sur l’appareil lorsque le navigateur le permet. Tant que l’audio n’a pas été envoyé, utilisez de préférence le même navigateur et le même appareil.

### Méthode B — Importer un fichier audio

1. Cliquez dans la zone **Importer un fichier audio**, ou déposez le fichier dans cette zone.
2. Sélectionnez un fichier audio compatible.
3. Écoutez l’aperçu.
4. Si le fichier n’est pas le bon, cliquez sur **Retirer le fichier** puis choisissez-en un autre.

Formats courants acceptés : MP3, WAV, M4A, MP4, WEBM, OGG, FLAC et AAC. La taille totale ne doit pas dépasser **500 Mo**.

Vous ne pouvez pas importer un fichier pendant qu’un enregistrement au microphone est présent. Supprimez d’abord l’enregistrement si vous souhaitez changer de méthode.

## 8. Lancer la génération

Lorsque l’audio est prêt :

1. vérifiez le titre, les membres invités et l’audio ;
2. cliquez sur **Générer les résumés** ;
3. attendez la fin de l’envoi ;
4. l’application ouvre ensuite automatiquement la réunion dans l’historique.

Le traitement continue en arrière-plan. Vous pouvez quitter la page de détail sans arrêter la génération.

Le pipeline comporte les étapes suivantes :

1. mise en attente ;
2. préparation de l’audio ;
3. transcription ;
4. rédaction du résumé et du compte rendu ;
5. création du document Word ;
6. traitement terminé.

## 9. Utiliser l’historique

Ouvrez **Historique** pour afficher les réunions déjà créées.

Vous pouvez :

- rechercher une réunion par mot-clé ;
- filtrer les réunions selon leur état ;
- voir leur durée et la date de création ;
- ouvrir une réunion pour consulter son contenu ;
- suivre un traitement encore en cours.

Les états principaux sont :

- **En attente** ;
- **Préparation audio** ;
- **Transcription** ;
- **Rédaction** ;
- **Création du Word** ;
- **Terminée** ;
- **À relancer** ou **Échec**.

## 10. Consulter une réunion

La page de détail affiche le texte à gauche et le lecteur audio à droite.

### Onglet Transcription

Cet onglet contient le texte découpé avec des repères temporels.

- Cliquez sur un horaire, par exemple `12:35`, pour déplacer l’audio à ce passage.
- Utilisez **Rechercher dans la transcription** pour retrouver un mot ou une phrase.
- Activez **Suivre la lecture** pour faire défiler automatiquement la transcription pendant l’écoute.
- Utilisez l’icône de copie pour copier la transcription.

### Onglet Résumé

Cet onglet présente une version courte de la réunion pour une lecture rapide. Utilisez l’icône de copie pour récupérer le texte.

### Onglet Compte rendu

Cet onglet présente le document détaillé : points importants, décisions, actions, questions ouvertes et éventuels blocages.

### Lecteur audio

Le lecteur permet de :

- lire ou mettre en pause l’enregistrement ;
- avancer ou reculer dans l’audio ;
- changer la vitesse de lecture de `0,75×` à `2×` ;
- télécharger l’audio lorsqu’il est disponible.

### Document Word

Quand la génération est terminée, cliquez sur **Télécharger le Word** pour obtenir le compte rendu mis en forme.

## 11. Relancer un traitement

Si une étape échoue, un message est affiché sur la réunion.

1. Ouvrez la réunion depuis l’historique.
2. Cliquez sur **Relancer le traitement**.
3. Laissez la page se mettre à jour pendant que le serveur réessaie.

Si le résumé existe déjà mais que le document Word manque, le bouton devient **Recréer le Word**. Cette action conserve le résumé existant et relance uniquement la création du document.

## 12. Utiliser les notifications

La cloche située dans l’en-tête ouvre les notifications internes.

Une notification peut signaler notamment :

- une invitation à une réunion ;
- une activité liée à l’équipe ;
- un changement concernant une réunion.

Cliquez sur une notification associée à une réunion pour ouvrir directement cette réunion. Les notifications peuvent être marquées comme lues individuellement ou toutes ensemble.

## 13. Gérer l’organisation

La page **Paramètres** est principalement destinée au propriétaire.

Elle permet de modifier :

- le nom de l’organisation ;
- sa description ;
- la durée de validité des liens d’invitation ;
- le droit des administrateurs à inviter des membres ;
- les notifications internes liées aux invitations.

Après une modification, cliquez sur **Enregistrer les modifications**.

## 14. Conseils pour obtenir un bon résultat

- Placez le microphone au centre de la table.
- Évitez les conversations simultanées.
- Réduisez les bruits de fond et les notifications sonores.
- Vérifiez l’aperçu avant de lancer la génération.
- Utilisez un titre précis pour retrouver facilement la réunion.
- Pour un long enregistrement, gardez la page ouverte jusqu’à la fin de l’envoi.

## 15. Résolution des problèmes courants

### Le microphone ne fonctionne pas

Vérifiez l’autorisation du microphone dans le navigateur, puis rechargez la page. Assurez-vous également que le bon périphérique d’entrée est sélectionné dans le système.

### Le fichier est refusé

Vérifiez qu’il s’agit bien d’un fichier audio pris en charge, qu’il n’est pas vide et qu’il ne dépasse pas 500 Mo.

### Le bouton de génération est désactivé

Vérifiez que :

- le titre est renseigné ;
- l’enregistrement est terminé ;
- ou qu’un fichier audio valide a été sélectionné ;
- aucun envoi n’est déjà en cours.

### Le traitement prend du temps

Ouvrez l’historique pour suivre son état. Les longues réunions demandent davantage de temps pour la préparation, la transcription et la rédaction.

### L’invitation n’est plus valide

Demandez au propriétaire ou à un administrateur autorisé de générer un nouveau lien depuis la page Équipe.

### Le document Word n’apparaît pas

Ouvrez la réunion et utilisez **Recréer le Word** si le résumé et le compte rendu sont déjà disponibles.

---

**Version du guide :** Ruinion AI V1  
**Public concerné :** propriétaires, administrateurs et membres d’une organisation.
