# Rome=>Naf in functions
import pandas as pd


# Deprecated
def rome2nafz_v1(rome, df_in, output_size=15):
    """
    Generate naf list using input rome code and specific dataframe:
    ['rome', 'naf', 'embauches', 'embauches_total_n', 'embauches_total_r', 'ratio_naf', 'ratio_rome']

    - First a table is generated listing the naf codes who employ the highest percentage
    (from their total recruitments) of the specified rome code, a score is specified with
    a binning technique
    - Then the NAF codes who also appear in the list of where the specified rome code tends
    to work at are boosted
    - Finaly the result is filtered keeping only those with a score of 1 or higher, and from those
    only the first 15 are kept (can be changed by parameter)
    """
    df_nf = (
        df_in.loc[df_in.rome == rome]
             .sort_values(by=['ratio_naf'], ascending=False)
    )
    df_nf['cumsum'] = 100 - df_nf['ratio_rome'].cumsum()
    df_nf = df_nf.loc[df_nf['cumsum'] > 25]
    df_nf['score'] = pd.to_numeric(pd.cut(
        df_nf['ratio_naf'],
        bins=[1, 2, 5, 10, 50, 100],
        labels=[0, 1, 2, 3, 4]
    ))
    df_nf['score_rome'] = pd.to_numeric(pd.cut(
        df_nf['ratio_rome'],
        bins=[1, 2, 5, 10, 50, 100],
        labels=[0, 1, 2, 3, 4]
    ))

    df_rs = (
        df_in.loc[df_in.rome == rome]
             .sort_values(by=['ratio_rome'], ascending=False)
    )
    df_rs['cumsum'] = 100 - df_rs['ratio_rome'].cumsum()
    df_rs = df_rs.head(10)

    df_nf.loc[df_nf['naf'].isin(df_rs['naf']), 'score'] += 1
    df_nf = df_nf.loc[df_nf['score'].ge(1)]

    return (
        df_nf.sort_values(by=['score'], ascending=False)
             .head(output_size)
    )[['rome', 'naf', 'score']]


# Rome=>Naf in function form
# Latest
def rome2nafz_v2(rome, df_in, output_size=15):
    """
    Generate naf list using input rome code and specific dataframe:
    ['rome', 'naf', 'embauches', 'embauches_total_n', 'embauches_total_r', 'ratio_naf', 'ratio_rome']

    - Two scores are generated (rome & naf), resulting in 5 bins scored 5 to 1 according to custom thresholds.
    These are then weighed into a single binned score, following the same rules (5 bins scored 5 to 1)
    - Finaly only the first 15 are kept (can be changed by parameter)
    """
    df_nf = (
        df_in.loc[df_in.rome == rome]
             .sort_values(by=['ratio_naf'], ascending=False)
    )
    df_nf['cumsum'] = 100 - df_nf['ratio_rome'].cumsum()
    # df_nf = df_nf.loc[df_nf['cumsum'] > 25]
    df_nf['score_naf'] = pd.to_numeric(pd.cut(
        df_nf['ratio_naf'],
        bins=[0, 2, 5, 10, 50, 100],
        labels=[0, 1, 2, 3, 4]
    ))
    df_nf['score_rome'] = pd.to_numeric(pd.cut(
        df_nf['ratio_rome'],
        bins=[0, 2, 5, 10, 50, 100],
        labels=[0, 1, 2, 3, 4]
    ))

    df_nf = df_nf.loc[df_nf['score_naf'].ge(1) | df_nf['score_rome'].ge(1)]
    df_nf['score'] = df_nf['score_naf'] * 4 + df_nf['score_rome']
    df_nf['score'] = pd.cut(
        df_nf['score_naf'] * 3 + df_nf['score_rome'],
        bins=5,
        labels=[1, 2, 3, 4, 5]
    )

    return (
        df_nf.sort_values(by=['score'], ascending=False)
             .head(output_size)
    )[['rome', 'naf', 'score']]
