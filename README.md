# 📊 Screener Nasdaq 100 — Version Cloud (Mobile)

Screener d'actions automatisé, déployé gratuitement sur GitHub Pages.
Le moteur Python tourne tous les soirs après la clôture US, les résultats
sont publiés sur une page web consultable depuis votre smartphone.

---

## 🚀 Mise en place (15 minutes)

### Étape 1 — Créer un compte GitHub (si vous n'en avez pas)

Rendez-vous sur [github.com](https://github.com) et créez un compte gratuit.

### Étape 2 — Créer le dépôt

1. Cliquez sur le **+** en haut à droite → **New repository**
2. Nom : `screener-nasdaq` (ou ce que vous voulez)
3. Cochez **Public** (obligatoire pour GitHub Pages gratuit)
4. Cliquez **Create repository**

### Étape 3 — Uploader les fichiers

Sur la page de votre dépôt vide, cliquez **uploading an existing file**.
Glissez-déposez tous les fichiers de ce dossier :
- `screener.py`
- `index.html`
- `requirements.txt`
- `.gitignore`
- Le dossier `.github/` avec son contenu (glissez le dossier entier)

⚠️ **Attention** : GitHub cache les dossiers commençant par `.`. Si vous
n'arrivez pas à uploader le dossier `.github/workflows/`, créez-le via
l'interface web :
1. **Add file** → **Create new file**
2. Dans le nom, tapez : `.github/workflows/screener.yml`
3. Collez le contenu du fichier fourni
4. Commit directement sur `main`

Puis cliquez **Commit changes**.

### Étape 4 — Activer GitHub Pages

1. Dans le dépôt, onglet **Settings**
2. Menu de gauche → **Pages**
3. Source : sélectionnez **GitHub Actions**
4. C'est tout, pas besoin de configurer davantage.

### Étape 5 — Lancer le premier screening

1. Onglet **Actions** en haut du dépôt
2. Cliquez sur **Screener Nasdaq 100** à gauche
3. Bouton **Run workflow** à droite → **Run workflow**
4. Attendez ~5 minutes (le moteur télécharge et analyse les 100 actions)

Vous verrez le workflow passer au vert ✅ quand c'est terminé.

### Étape 6 — Accéder depuis votre mobile

L'URL de votre dashboard sera :
```
https://VOTRE-USERNAME.github.io/screener-nasdaq/
```

(Remplacez `VOTRE-USERNAME` par votre nom d'utilisateur GitHub et
`screener-nasdaq` par le nom de votre dépôt.)

L'URL exacte est affichée dans **Settings → Pages** une fois le déploiement terminé.

### Étape 7 — Ajouter à l'écran d'accueil (mobile)

**iPhone (Safari)** :
1. Ouvrez l'URL dans Safari
2. Bouton **Partager** en bas
3. **Sur l'écran d'accueil**
4. Renommez "Screener" → **Ajouter**

**Android (Chrome)** :
1. Ouvrez l'URL
2. Menu ⋮ en haut à droite
3. **Ajouter à l'écran d'accueil**

L'icône apparaît comme une app native, sans barre de navigation.

---

## ⏰ Automatisation

Le workflow est configuré pour tourner **automatiquement chaque soir
à 00h30 (heure de Paris), du lundi au vendredi** — juste après la clôture
du marché américain.

Pour changer l'heure, éditez `.github/workflows/screener.yml` :
```yaml
schedule:
  - cron: '30 22 * * 1-5'  # 22h30 UTC = 00h30 Paris
```

Le format est : `minute heure jour-du-mois mois jour-de-la-semaine` en UTC.
Exemples :
- `0 13 * * 1-5` → 13h00 UTC = 15h00 Paris (ouverture US à 15h30)
- `0 20 * * 1-5` → 20h00 UTC = 22h00 Paris (mid-session US)

Vous pouvez aussi **lancer manuellement** à tout moment depuis l'onglet
**Actions** de votre dépôt.

---

## 📁 Structure des fichiers

```
screener-nasdaq/
├── .github/workflows/screener.yml   # Automatisation GitHub Actions
├── screener.py                      # Moteur d'analyse technique
├── index.html                       # Dashboard web (responsive mobile)
├── requirements.txt                 # Dépendances Python
├── .gitignore
└── README.md
```

Les fichiers `results_swing.json` et `results_position.json` sont générés
dans le dossier `public/` au moment du déploiement (pas commités dans le dépôt).

---

## 🎯 Stratégie d'analyse

Pour chaque action, **score composite (-100 à +100)** pondéré :

| Catégorie | Poids max | Détails |
|---|---|---|
| Patterns de chandeliers | ±20 | Marteau, étoile filante, doji, engulfing, morning/evening star |
| Volume anormal + breakout | ±25 | Volume > 1.5× moyenne 20j + cassure plus haut/bas 20 séances |
| Divergences RSI | ±20 | Prix nouveau high mais RSI plus bas (et inverse) |
| Croisements MM | ±15 | EMA rapide × lente, position vs EMA tendance |
| Survente / Surachat | ±25 | RSI<30 ou >70, bonus hors bandes de Bollinger |

**Classification** :
- Score ≥ +40 → 🟢🟢 Achat fort
- Score ≥ +20 → 🟢 Achat
- Score ∈ [-20, +20] → ⚪ Neutre
- Score ≤ -20 → 🔴 Vente
- Score ≤ -40 → 🔴🔴 Vente fort

---

## 🛠 Utilisation locale (optionnel)

Si vous voulez tester sur votre PC avant de déployer :

```bash
pip install -r requirements.txt
python screener.py --horizon swing --limit 10     # Test rapide
python screener.py --horizon all --output-dir .   # Tous les horizons
```

Puis ouvrez `index.html` dans votre navigateur (il chargera automatiquement
les `results_*.json` du même dossier).

---

## 💰 Coûts

**Zéro euro.** Tout est gratuit :
- GitHub (dépôt public + Pages)
- GitHub Actions (2000 min/mois gratuits, ce screener utilise ~5 min/jour × 22 jours = 110 min/mois)
- yfinance (données Yahoo Finance)

---

## ⚠️ Avertissement

Cet outil est **une aide à la décision**, pas un conseil en investissement.
Les signaux techniques doivent être croisés avec l'analyse fondamentale,
le contexte macro et votre propre gestion de risque.

## 🔧 Personnalisation

- **Modifier la watchlist** : éditez `NASDAQ100` dans `screener.py`
- **Ajuster les pondérations** : dans `analyze_ticker()`, section scoring
- **Ajouter des patterns** : fonction `detect_patterns()`
- **Changer les seuils de zones** : dans `analyze_ticker()`, section classification
