[![Maintenance](https://img.shields.io/badge/Maintained%3F-no-red.svg)](https://GitHub.com/betagouv/andi-docker/graphs/commit-activity)
[![Generic badge](https://img.shields.io/badge/ANDi-toujours-green.svg)](https://shields.io/)
<p align="center">
  <a href="https://andi.beta.gouv.fr">
    <img alt="Début description. Marianne. Fin description." src="https://upload.wikimedia.org/wikipedia/fr/3/38/Logo_de_la_R%C3%A9publique_fran%C3%A7aise_%281999%29.svg" width="90" />
  </a>
</p>
<h1 align="center">
  andi.beta.gouv.fr
</h1>

[ANDi](https://andi.beta.gouv.fr) est une service numérique en développement visant à faciliter l'immersion professionnelle des personnes en situation de handicap.

# 🐍 andi-python
Ensemble d'outils et scripts python utilisés dans le cadre de l'expérimentation ANDi.

Chaque répertoire contient sa propre documentation, dépendances, `requirements` et Makefile s'il y a lieu.

## sirene_import
Ensemble de scripts d'import et de mise à jour de données entreprises (sirene / insee) de différentes sources.

## correspondance_rome_naf
Script initialement sous Jupyter de génération des tableaux de correspondance rome/naf utilisés par l'API ANDi

## lbb_enrich
Script d'extraction de données (flag BOE, contacts divers) de la DB LaBonneBoite (API emploistore pole emploi)

## charting
Génération de funnel / visualisation de données (essai avant de passer sur des notebooks Jupyter).
