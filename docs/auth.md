# Authentification - V1

Cette V1 utilise une authentification JWT simple pour isoler les donnees par organisation.

## Fichiers

- `agent_résumé/auth/security.py` : hash des mots de passe et creation des JWT.
- `agent_résumé/auth/dependencies.py` : recuperation de l'utilisateur connecte.
- `agent_résumé/auth/routes.py` : routes `register`, `login` et `me`.
- `agent_résumé/routes/meetings.py` : routes protegees par organisation.

## Flux D'inscription

`POST /auth/register`

```json
{
  "first_name": "Jonathan",
  "last_name": "Doe",
  "email": "jonathan@example.com",
  "password": "motdepassefort",
  "organization_name": "RuinionAI"
}
```

Ce endpoint cree :

- un utilisateur dans `users`
- une organisation dans `organizations`
- un lien admin dans `organization_members`
- un JWT pour connecter directement l'utilisateur

## Flux De Connexion

`POST /auth/login`

```json
{
  "email": "jonathan@example.com",
  "password": "motdepassefort"
}
```

Reponse :

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

## Utilisateur Courant

`GET /auth/me`

Header :

```http
Authorization: Bearer <access_token>
```

Ce endpoint retourne l'utilisateur, son organisation courante et son role.

## Regle Multi-Organisation

Les routes `/meetings` ne lisent plus `organization_id` depuis le body.

L'organisation vient du token :

```text
token -> user -> organization_members -> organization_id
```

Ainsi, un utilisateur ne peut acceder qu'aux reunions de son organisation.

## Variables D'environnement

Pour la production, definir :

```env
SECRET_KEY=une_longue_cle_aleatoire
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

En developpement, le backend a une valeur par defaut pour `SECRET_KEY`, mais elle ne doit pas etre utilisee en production.
