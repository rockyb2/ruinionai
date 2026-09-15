# Frontend Auth - V1

Le frontend utilise un JWT retourne par le backend pour proteger le dashboard.

## Fichiers

- `front/src/service/api.js` : appels API, stockage du token et header `Authorization`.
- `front/src/route/router.js` : garde de navigation pour les routes privees.
- `front/src/views/Login.vue` : connexion.
- `front/src/views/Signin.vue` : inscription avec creation d'organisation.
- `front/src/components/SideBar.vue` : session courante, organisation, deconnexion.

## Stockage Du Token

Le token est stocke avec la cle :

```text
ruinionai.access_token
```

Si l'utilisateur coche "rester connecte", le token va dans `localStorage`.
Sinon, il va dans `sessionStorage`.

## Routes Publiques

- `/login`
- `/signin`

Un utilisateur deja connecte est redirige vers `/reunion`.

## Routes Protegees

- `/reunion`
- `/historique`
- `/setting`

Sans token, l'utilisateur est redirige vers `/login`.

## Appels API Authentifies

`api.js` ajoute automatiquement :

```http
Authorization: Bearer <token>
```

sur les appels proteges, par exemple :

- `GET /auth/me`
- `GET /meetings/`
- `POST /meetings/`
- `POST /meetings/{id}/audio`
- `POST /meetings/{id}/summary`

Si le backend repond `401`, le token local est supprime.

