from setuptools import setup

setup(
    name='lbb_enrich',
    version='1.0',
    description='Database enricher',
    author='Pieterjan Montens',
    author_email='pieterjan.montens@beta.gouv.fr',
    packages=['lbb_enrich'],
    install_requires=['requests', 'click', 'pyyaml', 'psycopg2-binary', 'beautifulsoup4'],
)
