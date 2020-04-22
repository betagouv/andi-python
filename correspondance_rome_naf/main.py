import pandas as pd
import numpy as np
import csv
import time
from function_lib import (
    rome2nafz_v2 as rome2naf
)

# NAF
naf_labels = pd.read_csv('/ressources/list_NAF_LBB.csv', sep='|', encoding="utf-8")
naf_labels.columns = ['nafdot', 'naf', 'label']
print(f"Obtained {len(naf_labels)} NAF labels")
# display(HTML(naf_labels.head(5).to_html()))

# ROME
rome_labels = pd.read_csv('/ressources/liste_rome_LBB.csv', sep=',', encoding="utf-8")
rome_labels.columns = ['rome', 'rome_1', 'rome_2', 'rome_3', 'label', 'slug']
print(f"Obtained {len(rome_labels)} ROME labels")
# display(HTML(rome_labels.head(5).to_html()))

# Chargement des statistiques d'emploi
emploi_rome_naf = pd.read_csv('/ressources/contrats_30j.csv', sep=',', encoding="utf-8")[['ROME', 'APE700', 'nb_embauches']]
emploi_rome_naf.columns = ['rome', 'naf', 'embauches']


# Calcul des ratios
naf_embauches = emploi_rome_naf[['naf', 'embauches']].groupby('naf').agg(
    embauches_total_n=pd.NamedAgg(column='embauches', aggfunc=sum)
)
rome_embauches = emploi_rome_naf[['rome', 'embauches']].groupby('rome').agg(
    embauches_total_r=pd.NamedAgg(column='embauches', aggfunc=sum)
)


naf_i = (
    emploi_rome_naf.merge(naf_embauches, on='naf')
                   .merge(rome_embauches, on='rome')
)
naf_i['ratio_naf'] = (naf_i.embauches / naf_i.embauches_total_n) * 100
naf_i['ratio_rome'] = (naf_i.embauches / naf_i.embauches_total_r) * 100

naf_i = naf_i.sort_values(by=['ratio_naf'], ascending=False)


# Construction des tableaux
result_table = {}
for index, row in rome_labels.iterrows():
    result_table[row.rome] = rome2naf(str(row.rome), naf_i).to_dict('r')
    print(f"row {index} : {len(result_table[row.rome])} Naf codes for Rome {row.rome} \"{rome_labels.loc[(rome_labels['rome'] == row.rome, 'label')].iloc[0]}\" ")

output = f"/outputs/andi_rome2naf_{time.strftime('%Y%m%d')}.csv"
i = 0
with open(output, 'w') as file:
    writer = csv.DictWriter(
        file,
        delimiter=',',
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        fieldnames=['rome', 'rome_label', 'naf', 'naf_label', 'score']
    )
    writer.writeheader()
    for rome, naflist in result_table.items():
        for data in naflist:
            data['rome_label'] = rome_labels.loc[(rome_labels['rome'] == rome, 'label')].iloc[0]
            data['naf_label'] = naf_labels.loc[(naf_labels['naf'] == data['naf'], 'label')].iloc[0]
            writer.writerow(data)
            i += 1


print(f'Wrote {i} rows to {output}')
