"""Utility functions for SmartHelio's use."""

import pandas as pd

inv_const = 'Inv'
combiner_const = 'CMB'
mppt_const = 'MPPT'
string_const = 'String'


def melt_multiindex_to_simple_index(curve_levels, dataframe, tagged_df, level_name):
    """Converts a multiindex dataframe to a single-index one."""
    for index, curve in enumerate(curve_levels):
        df = dataframe.xs(curve, axis = 1, level = level_name)
        df.columns = df.columns.map('-'.join)

        temp = df.reset_index()
        df = temp.melt(id_vars = ['datetime'],
                       value_vars = list(df.columns),
                       value_name = curve, var_name = 'tag')

        if index == 0:
            tagged_df = df
        else:
            tagged_df = tagged_df.merge(df, on = ['datetime', 'tag'])

    tagged_df.set_index('datetime', inplace=True)
    return tagged_df


def split_tag(tagged_df, string_exist):
    """Split tags into finer granularity."""
    if string_exist == True:
        tagged_df[['Level1', 'Level2']] = tagged_df.tag.str.split("-", expand=True)
        tagged_df[[inv_const, mppt_const]] = tagged_df.Level1.str.split("_", expand=True)
        tagged_df.rename(columns={'Level2': string_const}, inplace=True)
        tagged_df.drop(columns=['tag', 'Level1'], inplace=True)
    else:
        tagged_df[[inv_const, mppt_const]] = tagged_df.tag.str.split("-", expand=True)
        tagged_df.drop(columns=['tag'], inplace=True)
    return tagged_df


# Function to get the dataframe in required format:
def timestream_transform(df, string_exist, level_name, split_tags):
    """
    Transform a multi-index df to Timestream-acceptable format.
    
    Parameters
    ----------
    df: Pandas dataframe
        A multi-index input-based dataframe.
    string_exist: bool
        True if we can extract string-level data from the plant.
    level_name: str
        Name of the parameter being analyzed. Can be either 'loss' or 'curve'.
    split_tags: bool
        True if we want to split the tags into finer pieces.
        
    Returns
    -------
    final: Pandas dataframe
        A single-index tagged dataframe.
    """
    data = df.copy()
    final = pd.DataFrame()
    try:
        curve_levels = sorted(list(set(data.columns.get_level_values(2))))
    except IndexError:
        return final

    # Convert multi-index df to single index
    final = melt_multiindex_to_simple_index(curve_levels, data, final,
                                            level_name)
    if split_tags:
        final = split_tag(final, string_exist)
    return final


def transform_kpi_to_timestream(df, key):
    """
    Transform a multi-index df holding KPI data to Timestream-acceptable format.

    Parameters
    ----------
    data: Pandas dataframe
        A multi-index input-based dataframe.
    key: str
        Name of the parameter being analyzed.
        
    Returns
    -------
    df: Pandas dataframe
        A single-index tagged dataframe.
    """
    data = df.copy()
    # This means today's data 12 am is there
    if data.shape[0] > 1:
        data.drop(data.index[-1:], inplace=True)

    data.columns = data.columns.map('-'.join)
    temp = data.reset_index()

    df = temp.melt(id_vars = ['datetime'],
                   value_vars = list(temp.columns),
                   value_name = key, var_name = 'tag')
    return df
