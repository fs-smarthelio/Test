"""Obtain array info and general info from meta DB."""
import pandas as pd
import datetime
from datetime import date, datetime, timedelta
from smarthelio_shared import MetadataAPI


class SystemInfoMetadataAPI:
    def __init__(self, meta_db_api: MetadataAPI):
        self.metadb_client = meta_db_api

    def merge_input_info(self, string_df, mppt_df, plant_attributes, string_exist):
        """
        Merge input information.

        Parameters
        ----------
        string_df: pandas DataFrame
            Dataframe holding string details.
        mppt_df: pandas DataFrame
            Dataframe holding MPPT details.
        plant_attributes: pandas DataFrame
            Dataframe holding plant attribute details.
        string_exist: bool
            True if we can get string-level data from the PV system.

        Returns
        -------
        step_1: pandas DataFrame
            Dataframe containing input info.
        """
        if string_exist:
            # Merge plant attributes with string table
            step_1 = string_df.merge(plant_attributes, on=['string_id', 'mppt_id', 'inv_id', 'combiner_id'])
            col_to_drop = 'string_id_fk'
        else:
            # Merge attributes with MPPT table
            step_1 = mppt_df.merge(plant_attributes, on=['mppt_id', 'inv_id'])
            col_to_drop = 'mppt_id_fk'

        step_1.drop(columns=['attributes_id', 'combiner_id', col_to_drop],
                    inplace=True)
        return step_1

    def merge_panel_info(self, step_df, panel_df):
        """
        Merge panel information to the df from the previous step.

        Parameters
        ----------
        step_df: pandas DataFrame
            Dataframe obtained from the previous step
        panel_df: pandas DataFrame
            Dataframe holding panel specifications.

        Returns
        -------
        step_2: pandas DataFrame
            Dataframe containing panel info as well.
        """
        step_2 = step_df.merge(panel_df, on='panel_id')
        # Drop unnecessary columns
        step_2.drop(columns=['panel_id', 'manufacturer',
                             'model_name', 'wattage'], inplace=True)

        # Perform some calculations
        step_2['number_of_modules'] = step_2['modules_per_string'] * step_2[
            'number_of_strings']
        # The final array_info has the value in Watts, so no dividing by 1000
        step_2['installed_capacity'] = step_2['number_of_modules'] * step_2[
            'i_mpp'] * step_2['v_mpp']
        return step_2

    def get_orientation_col(self):
        """Get the dataframe column holding the correct orientation details."""
        yesterday = date.today() - timedelta(days=1)
        yesterday_mon = yesterday.strftime('%b').lower()

        col_to_keep = yesterday_mon + '_data'
        return col_to_keep

    def merge_orientation_info(self, step_df, orientation_df, orientation_col):
        """
        Merge orientation information to the df from the previous step.

        Parameters
        ----------
        step_df: pandas DataFrame
            Dataframe obtained from the previous step
        orientation_df: pandas DataFrame
            Dataframe holding orientation specifications.
        orientation_col: str
            Name of the column corresponding to correct orientation info.

        Returns
        -------
        step_3: pandas DataFrame
            Dataframe containing orientation info as well.
        """
        orientation_df[['surface_tilt', 'surface_azimuth']] = orientation_df[
            orientation_col].str.split(',', expand=True)
        # Remove the double quotes
        orientation_df.replace(to_replace="\"", value='', regex=True, inplace=True)
        # Make surface tilt and azimuth as an integer
        orientation_df[['surface_tilt', 'surface_azimuth']] = orientation_df[[
            'surface_tilt', 'surface_azimuth']].astype(float)
        orientation_df.drop(columns=[orientation_col], inplace=True)

        step_3 = step_df.merge(orientation_df, on='orientation_id')
        step_3.drop(columns=['orientation_id'], inplace=True)
        return step_3

    def get_num_strings_in_mppt(self, dataframe):
        """Get the number of strings in each MPPT."""
        qwerty = dataframe.groupby(['inv_id', 'mppt_id'])[
            'string_id'].count().reset_index()
        col_name = 'str_in_mppt'
        qwerty.rename(columns={'string_id': col_name}, inplace=True)
        return qwerty, col_name

    def get_num_mppts_in_inverter(self, dataframe):
        """Get the number of MPPTs in each inverter."""
        qwerty = dataframe.groupby(['inv_id'])['mppt_id'].count().reset_index()
        col_name = 'mppt_in_inv'
        qwerty.rename(columns={'mppt_id': col_name}, inplace=True)
        return qwerty, col_name

    def merge_inverter_information(self, step_df, string_exist, inverter_df, mppt_df):
        """
        Merge inverter information to the df from the previous step.
        Parameters
        ----------
        step_df: pandas DataFrame
            Dataframe obtained from the previous step
        string_exist: bool
            True if we can get string-level data from the PV system.
        inverter_df: pandas DataFrame
            Dataframe holding inverter specifications.
        mppt_df: pandas DataFrame
            Dataframe holding MPPT details.
        Returns
        -------
        step_4: pandas DataFrame
            Dataframe containing inverter info as well.
        """
        vol_clns = list(mppt_df.mppt_id_fk.unique())

        if string_exist:
            qwerty, col_name = self.get_num_strings_in_mppt(step_df)
            # Special case - if voltage is same across MPPTs
            if len(vol_clns) == 1:
                qwerty1 = qwerty.groupby(['inv_id'])['mppt_id'].count().reset_index()
                qwerty1.rename(columns={'mppt_id': 'mppt_in_inv'}, inplace=True)
                qwerty = qwerty.merge(qwerty1)
        else:
            qwerty, col_name = self.get_num_mppts_in_inverter(step_df)

        # Merging with inverter spec dataframe
        qwerty = qwerty.merge(inverter_df[['inv_id', 'max_dc_current',
                                           'dc_power_limit', 'inverter_eff', 'inverter_capacity']])

        if len(vol_clns) > 1:
            qwerty['dc_current_limit'] = qwerty.max_dc_current / qwerty[col_name]
            step_4 = step_df.merge(qwerty).drop(columns=[col_name, 'max_dc_current'])
        else:
            if string_exist:
                qwerty['dc_current_limit'] = qwerty.max_dc_current / (
                        qwerty.str_in_mppt * qwerty.mppt_in_inv)
                step_4 = step_df.merge(qwerty).drop(columns=[
                    'str_in_mppt', 'mppt_in_inv', 'max_dc_current'])
            else:
                qwerty['dc_current_limit'] = qwerty.max_dc_current / (qwerty.mppt_in_inv)
                step_4 = step_df.merge(qwerty).drop(columns=['mppt_in_inv', 'max_dc_current'])
        return step_4

    def apply_col_operations(self, general_info):
        """Rename and drop columns."""
        general_info.rename(columns={'plant_id': 'ID',
                                     'plant_id_fk': 'name'}, inplace=True)
        general_info.drop(columns=['mppt_exists', 'cb_exists', 'string_exists'], inplace=True)
        general_info.drop(columns=['sensor_exists', 'system_key', 'company_id'], inplace=True)
        general_info.drop(columns=['is_deleted'], inplace=True)
        general_info.drop(columns=['plant_manager_name', 'plant_manager_email'], inplace=True)
        return general_info

    def create_levels(self, array_info, string_exist):
        """Create columns corresponding to levels in the dataframe."""
        if string_exist:
            array_info['ag_level_2'] = array_info[['inv_id', 'mppt_id']].apply(
                lambda x: '_'.join(x), axis=1)
            array_info['ag_level_1'] = array_info['string_id'].astype(str)
        else:
            array_info['ag_level_2'] = array_info['inv_id']
            array_info['ag_level_1'] = array_info['mppt_id']

        array_info.drop(columns=['inv_id', 'mppt_id'], inplace=True)
        if string_exist:
            array_info.drop(columns=['string_id'], inplace=True)

        array_info['inverter_id'] = array_info['ag_level_2']
        array_info['input_name'] = array_info[['ag_level_2', 'ag_level_1']].apply(
            lambda x: '-'.join(x), axis=1)

        array_info.set_index(['ag_level_2', 'ag_level_1'], inplace=True)
        return array_info

    # Main function
    def gather_inputs(self, plant_id):
        """
        Create the general_info and array_info dataframes holding site and input specific info.
        Parameters
        ----------
        plant_id: int
            The ID of the plant specified in the meta database.
        Returns
        -------
        array_info : pandas MultiIndex DataFrame
            Dataframe containing input-specific information for all inputs in the plant.
        general_info : dictionary
            Dictionary containing site specific information.
        """
        # Get plant table:
        plant_table = self.metadb_client.get_plant_info_from_plant_id(plant_id)
        string_exist = bool(plant_table['string_exists'].iloc[0])

        # Get plant_attributes table:
        plant_attributes = self.metadb_client.get_plant_attributes(plant_id)
        plant_attributes['panel_id'] = plant_attributes['panel_id'].astype(int)
        plant_attributes = plant_attributes.drop_duplicates(keep='first')

        # Remove null columns (change in metadb plant-attributes schema)
        plant_attributes.dropna(axis=1, how='all', inplace=True)

        # Get the input information:
        mppt_df = self.metadb_client.get_mppts(plant_id)
        if string_exist:
            string_df = self.metadb_client.get_strings(plant_id)
        else:
            string_df = pd.DataFrame()  # Empty df

        mppt_df = mppt_df.drop_duplicates(keep='first')
        string_df = string_df.drop_duplicates(keep='first')

        step_1 = self.merge_input_info(string_df, mppt_df, plant_attributes, string_exist)

        # Get the panel information:
        panel_info = pd.DataFrame()
        for panel_id in step_1.panel_id.unique():
            small_panel = self.metadb_client.get_panel_info(panel_id)
            panel_info = pd.concat([panel_info, small_panel])

        # Merge panel information:
        step_2 = self.merge_panel_info(step_1, panel_info)

        # Get latest surface tilt and azimuth:
        orientation_col = self.get_orientation_col()

        orient_info = pd.DataFrame()
        for orient_id in step_2.orientation_id.unique():
            small_orient = self.metadb_client.get_orientation_info(orient_id, plant_id)
            small_orient = small_orient[['orientation_id', orientation_col]].copy()
            orient_info = pd.concat([orient_info, small_orient])

        step_3 = self.merge_orientation_info(step_2, orient_info, orientation_col)

        # Get inverter info.
        inverter_table = self.metadb_client.get_inverters(plant_id)
        inverter_info = self.metadb_client.get_inverters_info()

        full_inverter = pd.DataFrame()
        for inverter in inverter_table.inverters_id.unique():
            small_inverter = inverter_table[inverter_table.inverters_id == inverter]
            # Get specific inverter details from inverter info
            inv_specs = inverter_info[inverter_info.inverters_id == inverter]
            small_inverter = small_inverter.merge(inv_specs[['inverters_id',
                                                             'inverter_eff',
                                                             'max_dc_current',
                                                             'dc_power_limit',
                                                             'inverter_capacity'
                                                             ]],
                                                  on='inverters_id')
            full_inverter = pd.concat([full_inverter, small_inverter])

        step_4 = self.merge_inverter_information(step_3, string_exist, full_inverter, mppt_df)

        # # drop rows with number-of-strings or modules-per-string is zero
        # step_4 = step_4[~((step_4.number_of_strings == 0) | (step_4.modules_per_string == 0))]

        ######################## Building general_info
        gen_inf = plant_table.copy()
        start_date = pd.to_datetime(gen_inf['system_start_date'].iloc[0], dayfirst=True)
        system_age = (datetime.now() - start_date).days / 365

        # Apply operations on columns
        gen_inf = self.apply_col_operations(gen_inf)

        # Timezone
        tz_str = gen_inf['timezone'].iloc[0]
        gen_inf['timezone'] = tz_str

        # Altitude
        altitude = gen_inf['elevation'].iloc[0]
        gen_inf['altitude'] = float(altitude)

        # Longitude
        longitude = gen_inf['longitude'].iloc[0]
        gen_inf['longitude'] = float(longitude)

        # Latitude
        latitude = gen_inf['latitude'].iloc[0]
        gen_inf['latitude'] = float(latitude)

        if tz_str in ["Asia/Kolkata", "Asia/Bangkok"]:
            gen_inf['kg_CO2_per_kWh'] = 0.82
        else:
            gen_inf['kg_CO2_per_kWh'] = 0.075914

        gen_inf['pollution_red_factor'] = 1
        gen_inf['system_age'] = system_age

        ######################## Building the array_info - Lord, help me!
        array_info = step_4.copy()
        array_info[['inv_id', 'mppt_id']] = array_info[['inv_id', 'mppt_id']].astype(str)

        array_info = self.create_levels(array_info, string_exist)

        array_info[['gamma', 'beta', 'alpha']] = 0.01 * array_info[['gamma', 'beta', 'alpha']]
        if system_age > 1:
            array_info['expected_degradation'] = array_info['degrdn_yr1'] + ((
                                                                                     system_age - 1) * array_info[
                                                                                 'degrdn_yr2'])
        else:
            array_info['expected_degradation'] = array_info['degrdn_yr1'] * system_age

        ################################ Last steps to build general_info
        gen_inf['inverter_eff'] = array_info['inverter_eff'].mean()
        gen_inf['expected_degradation'] = array_info['expected_degradation'].mean()
        general_info = gen_inf.iloc[0, :].to_dict()

        return array_info, general_info, string_exist
