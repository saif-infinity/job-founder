# Job Founder

**Assistant graphique de recherche d’emploi pour Linux.** Importez votre CV, confirmez votre profil, examinez les offres et préparez vos candidatures depuis une seule interface de bureau.

> **État : prototype MVP.** La recherche peut maintenant interroger des tableaux publics de carrières Greenhouse et Lever configurés par l’utilisateur. Les annonces visibles au premier lancement restent fictives jusqu’à la configuration d’au moins une source.

## Aperçu du prototype

L’application PySide6 est organisée comme un centre de contrôle : navigation latérale, liste filtrable des offres et panneau d’analyse. L’interface est en français et ne présente pas de terminal à l’utilisateur final.

Fonctionnalités disponibles dans ce prototype :

- Import local de CV PDF, DOCX ou TXT et formulaire de vérification du profil et de la ville.
- Configuration graphique de tableaux carrières Greenhouse/Lever publics ; interrogation en arrière-plan, normalisation et déduplication des offres, filtrées selon la ville confirmée.
- Offres de démonstration au premier lancement, puis offres récupérées depuis les sources configurées ; filtres par texte, score, contrat, localisation et mode de travail.
- Panneau de détails avec compétences, score, état, lien et points à vérifier.
- Analyse à la demande d’une page avec Playwright : détection du type de site, du lien de candidature, des champs requis, des formulaires à étapes, et de certains blocages.
- Préparation locale d’un dossier exemple dans `~/Candidatures` et suivi manuel des offres.

Au premier lancement, les liens sont fictifs (`example.org`). Pour activer une recherche réelle : ouvrez **Sources**, ajoutez une ligne par tableau de carrières, puis cliquez sur **Rechercher**. Formats acceptés : `greenhouse:identifiant-du-tableau` et `lever:identifiant-du-site` (le slug de l’employeur dans l’URL officielle, par exemple `boards.greenhouse.io/acme` → `greenhouse:acme`, ou `jobs.lever.co/acme` → `lever:acme`). Les connecteurs interrogent uniquement les API publiques de ces fournisseurs, sans scraping générique ni identifiants de connexion. La distance n’est pas géocodée dans ce MVP et reste inconnue ; le filtrage par rayon ne peut donc pas calculer une distance réelle. Le score actuel est indicatif et basé sur les compétences saisies dans le profil.

## Installation pour le développement

L’application cible Linux et Python 3.10+. Ces commandes sont réservées au développement ; elles ne sont pas l’interface du produit final.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python -m job_founder
```

Les distributions graphiques futures devront intégrer/configurer Chromium et démarrer l’application depuis une icône. Pour l’extraction de CV, `pypdf` et `python-docx` sont utilisés. L’OCR des images n’est pas encore disponible.

## Tests

Les tests du diagnostic de pages peuvent être exécutés sans lancer l’interface graphique :

```bash
python -m unittest discover -s tests -v
```

Le lancement de l’interface nécessite les bibliothèques graphiques Qt/OpenGL de Linux, notamment `libGL.so.1`.

## Confidentialité et limites de sécurité

- Le CV est traité localement par le prototype ; il n’est pas envoyé à un service externe.
- L’analyse des pages est en lecture seule : aucun formulaire n’est soumis.
- Aucun contournement de CAPTCHA, de connexion ou de protection anti-robot n’est effectué.
- Les actions sensibles et l’envoi d’une candidature restent sous le contrôle de la personne.
- Les documents générés sont des brouillons à vérifier ; le prototype ne doit pas inventer de faits ni prétendre avoir postulé.

## Architecture actuelle

- `job_founder/app.py` — fenêtre principale PySide6 et interactions graphiques.
- `job_founder/sources.py` — connecteurs d’API Greenhouse et Lever, normalisation et score par compétences.
- `job_founder/navigation.py` — diagnostic des pages et adaptateur Playwright.
- `tests/` — tests unitaires des sources, classifications et blocages.

## Prochaines étapes

1. Ajouter d’autres API officielles et des tests d’intégration contrôlés.
2. Géocoder les lieux pour calculer distance et rayon correctement.
3. Persister profil, offres, blocages et historique dans SQLite.
4. Améliorer l’extraction structurée du CV et le score explicable.
5. Préparer le packaging Linux (AppImage/Flatpak), Chromium et les mises à jour.
