# Job Founder

**Assistant graphique de recherche d’emploi pour Linux.** Importez votre CV, confirmez votre profil, examinez les offres et préparez vos candidatures depuis une seule interface de bureau.

> **État : prototype MVP.** L’interface et le diagnostic de pages sont en cours de développement. Les annonces affichées sont fictives ; aucune recherche d’emploi réelle ni collecte auprès de sources n’est encore intégrée.

## Aperçu du prototype

L’application PySide6 est organisée comme un centre de contrôle : navigation latérale, liste filtrable des offres et panneau d’analyse. L’interface est en français et ne présente pas de terminal à l’utilisateur final.

Fonctionnalités disponibles dans ce prototype :

- Import local de CV PDF, DOCX ou TXT et formulaire de vérification du profil et de la ville.
- Offres de démonstration filtrables par texte, score, contrat, localisation, rayon et mode de travail.
- Panneau de détails avec compétences, score, état, lien et points à vérifier.
- Analyse à la demande d’une page avec Playwright : détection du type de site, du lien de candidature, des champs requis, des formulaires à étapes, et de certains blocages.
- Préparation locale d’un dossier exemple dans `~/Candidatures` et suivi manuel des offres.

**Les liens et annonces actuels sont des exemples fictifs (`example.org`).** Le bouton de recherche n’interroge pas encore de sources réelles. Pour utiliser l’analyse Playwright sur des offres réelles, il faudra d’abord connecter des sources autorisées.

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
- `job_founder/navigation.py` — diagnostic des pages et adaptateur Playwright.
- `tests/test_navigation.py` — tests unitaires des classifications et blocages.

## Prochaines étapes

1. Connecter des sources d’offres autorisées et remplacer les annonces fictives.
2. Persister profil, offres, blocages et historique dans SQLite.
3. Améliorer l’extraction structurée du CV et le score explicable.
4. Étendre les adaptateurs de sites, l’assistance humaine et la génération de documents.
5. Préparer le packaging Linux (AppImage/Flatpak) et les mises à jour.
