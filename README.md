# EcoWaste (WIPE) — intégration Home Assistant

Intégration personnalisée pour les portails de déchets **EcoWaste / WIPE**
(éditeur : OptiWaste SA), utilisés par de nombreuses communes suisses
(`https://wipe.ecowaste.ch/client/<commune>`).

Elle récupère **vos** dépôts de déchets via l'API client officielle et expose
des capteurs dans Home Assistant — sans navigateur headless ni conteneur Docker.

> ⚠️ Projet communautaire non officiel, sans lien avec OptiWaste SA / EcoWaste.
> Vous utilisez **vos propres identifiants** pour accéder à **vos propres
> données**. Respectez les conditions d'utilisation du portail.

## Capteurs créés

Par commune/carte configurée :

| Capteur | Unité | Détail |
|---|---|---|
| Poids total | kg | somme de l'année en cours |
| Coût total | CHF | somme de l'année en cours |
| Nombre de dépôts | dépôts | sur l'année en cours |
| Dernière pesée | kg | + attributs (date, conteneur, carte, flux, coût) |
| Poids carte `<label>` | kg | un par carte détectée |
| Coût carte `<label>` | CHF | un par carte détectée |

Rafraîchissement toutes les 6 h (le jeton d'accès, valable ~12 h, est régénéré
automatiquement).

## Installation

### Via HACS (dépôt personnalisé)
1. HACS → menu ⋮ → **Dépôts personnalisés**.
2. URL : `https://github.com/prophetmaster/ecowaste-ha`, catégorie **Intégration**.
3. Installez « EcoWaste (WIPE) », puis **redémarrez** Home Assistant.

### Manuelle
Copiez `custom_components/ecowaste/` dans le dossier `config/custom_components/`
de votre instance, puis redémarrez.

## Configuration

**Paramètres → Appareils et services → Ajouter une intégration → EcoWaste**.

Trois champs :

- **Commune** : le *slug* présent dans l'URL du portail.
  Ex. pour `https://wipe.ecowaste.ch/client/plateau-de-diesse` → `plateau-de-diesse`.
- **Numéro de carte** : tel que vous le saisissez à l'écran de connexion
  (c.-à-d. l'étiquette *sans* la première partie `AAAA-` si elle est présente).
- **Code / nom** : la valeur demandée au 2e écran de connexion.

L'intégration vérifie les identifiants immédiatement en se connectant à l'API.

## Comment ça marche (technique)

```
POST /ipServer/wise/public/wipe/v1/authenticate
     {"client": "<commune>", "card": "<carte>", "code": "<code>"}
  -> {"access_token": "<JWT ~12h>"}

GET  /ipServer/wise/wipe/v1/waste?year=AAAA
     en-tête  X-Client-Token: <JWT>
  -> [ { timestamp, weight, amount, card:{label}, container:{identifier}, flowType:{name} }, ... ]
```

## Limitations connues

- Les cartes sont découvertes au démarrage ; si une **nouvelle carte** apparaît,
  rechargez l'intégration pour créer ses capteurs.
- Seule l'**année en cours** est remontée (comme le portail). L'historique
  complet reste accessible année par année via l'API.
- API non documentée publiquement : un changement côté OptiWaste peut nécessiter
  une mise à jour.

## Licence
MIT — faites-en bon usage.
