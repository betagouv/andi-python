# NAF / ROME Link Factory
* Utiliser les diverses données pour calculer une table de correspondance rome / naf
* Initialement conçu dans un notebook Jupyter, d'ou une structure différente des autres composants

## Lancement
Le programme crée un tableau, d'après les ressources dans le répertoire `ressources`, un tableau 
de correspondance dans le répertoire `outputs`.

Sous pipenv:
```bash
$> pipenv install
$> pipenv run ./main.py
```

Sans pipenv:
Initialiser l'environnement d'après `requirements.py`
```bash
$> ./main.py
```


## Autres idées non exploitées:
- pousser certains domaines naf manuellement reliés aux romes
- exploiter les codes OGR (données insuffisantes)
- obtenir des données plus larges, sur une pluse grande durée (cf DPAE)
- intégrer nombre d'entreprises et leur taille moyenne (sur tout le territoire) (cf. sirene/insee)
- plus dynamique: intégrer variance, écart type, ...
- ...

## A vérifier:
- Anomalie des fromagers: NAF-1051C et ROME-A1412, peu de recrutement mais ils y vont en masse
