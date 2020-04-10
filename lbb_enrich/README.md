## Script d'enrichissement données LBB
Ce script utilise une API de [l'Emploi Store](https://www.emploi-store-dev.fr/portail-developpeur-cms/home.html) de [Pôle Emploi](https://www.pole-emploi.fr/accueil/).

[L'API La Bonne Boite V1](https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api/api-la-bonne-boite-v1.html) met à disposition
des données d'un intérêt particulier par la DB d'entreprises d'ANDi. Ce script en assure l'importation progressive et non-abusive.

Un partie du script s'est inspiré du [client python](https://github.com/bayesimpact/python-emploi-store), de l'emploi store, en y ajoutant une gestion plus poussée des tokens.

## Installation et usage
- créer, à partir de env.default.sh, un fichier env avec les paramêtres qui conviennent à votre situatio
- instantier l'environnement pipenv nécessaire (pipenv ou requirements.txt

## Tests
lbb_enrich utilise behave pour tester certains composants. Après avoir initié l'environnement (`. env.sh`):
```bash
# Pour tous les tests
make tests

# Pour behave
make behave

# Ou directemement, par exemple
pipenv run behave tests/behave/features/tokenmaster.feature --logging-level DEBUG
```


## Utilisation
```bash
Usage: enrich.py [OPTIONS] COMMAND [ARGS]...

Options:
  --debug
  --help   Show this message and exit.

Commands:
  run     Run the enricher !
    Options:
      --dry-run                 Dry run (no writes)
      --limit-run INTEGER       Number of companies to query
      --limit-distance INTEGER  Max distance of search query
      --help                    Show this message and exit.

  target  Specify company Siret to force update
    Options:
      --dry-run     Dry run (no writes)
      --siret TEXT  Target company siret
      --help        Show this message and exit.

  test    Some tests that can be run
    Options:
      --company-list        Test company list generator
      --naf-to-rome         Test rome obtention from naf code
      --contact-extraction  Test contact extraction
      --help                Show this message and exit.
```

## Exemples
```bash
$ ./lbb_enrich/enrich.py --debug run --dry-run
$ ./lbb_enrich/enrich.py --debug target --siret [siret]
```
