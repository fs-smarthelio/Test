"""Access the meta DB hosted by Ants."""
import math

import pandas as pd
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


SENSOR_SYMBOL = 'SENS'
INVERTER_SYMBOL = 'INV'
COMBINER_SYMBOL = 'CMB'
MPPT_SYMBOL = 'MPPT'
STRING_SYMBOL = 'STRG'
INVERTER_NAME = 'inv'


class MetadataAPI:
    get_plant_info_from_plant_id_cache = {}
    get_company_info_from_company_id_cache = {}
    get_base_url_from_plant_id_cache = {}
    get_credentials_from_plant_id_cache = {}
    get_credentials_id_cache = {}
    get_service_id_cache = {}
    get_api_type_cache = {}
    get_api_keys_from_plant_id_cache = {}
    get_company_id_from_company_name_cache = {}
    get_plant_infra_cache = {}

    def __init__(self, base_url, options):
        self.base_url = base_url

        if "ACCESS_TOKEN" not in options:
            raise Exception("ACCESS_TOKEN needs to be present in the options object!")

        self.options = options

    def retry_session(self, url, retries=3, backoff_factor=3, allowed_request_type=['GET','POST']):
        if allowed_request_type is None:
            raise Exception("Empty allowed_request_type param received!")
        session = requests.Session()
        retry = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[502, 503, 504],
            method_whitelist=frozenset(allowed_request_type)
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount(url, adapter)
        return session


    def get_plants_ids_by_company_name(self, company_name):
        # Step 0 - Get CompanyId using Company Name
        company_id = self.get_company_id_from_company_name(company_name)

        # Step 1 - Get all plants of a given CompanyId
        plant_dataframe = self.get_plant_infra(
            plant_id='',
            param_exists=False,
            param_name='plant'
        )

        # filtering plant_df on company_ID
        plant_dataframe = plant_dataframe[plant_dataframe.company_id == company_id]

        return list(plant_dataframe.plant_id.values)

    def get_company_id_from_company_name(self, company_name):
        if company_name in self.get_company_id_from_company_name_cache:
            return self.get_company_id_from_company_name_cache[company_name]

        for pageNum in range(1, 100):
            data = {
                "pageNum": pageNum,
                "pageSize": self.options['PAGE_SIZE']
            }
            url = self.base_url + 'company/list'
            session = self.retry_session(url)
            response = session.post(url, json=data)
            output = response.json()
            company_list = output['body']['records']

            for company in company_list:
                if company['company_name'] == company_name:
                    self.get_company_id_from_company_name_cache[company_name] = company['company_id']
                    return company['company_id']

    def get_plant_infra(self, plant_id, param_exists, param_name):
        if plant_id in self.get_plant_infra_cache:
            if param_name in self.get_plant_infra_cache[plant_id]:
                return self.get_plant_infra_cache[plant_id][param_name]

        """
        Get the info. of a specific piece of infrastructure for one plant.
        Parameters
        ----------
        plant_id: str
            The plant ID in the meta DB.
        param_exists: bool
            True if there's any query string to send in the API request.
        param_name: str
            The piece of infrastructure. Examples are mppt, string, etc.
        """
        full_table = pd.DataFrame()

        # We have set a flexible limit of 100 pages of inputs
        for pageNum in range(1, 100):
            data = {"pageNum": pageNum, "pageSize": self.options['PAGE_SIZE']}
            url = self.base_url + '{}/list'.format(param_name)
            session = self.retry_session(url)
            if param_exists:
                params = {'plant_id': plant_id}
                response = session.post(url, params=params, json=data)
            else:
                response = session.post(url, json=data)

            output = response.json()
            small_piece = pd.DataFrame(output['body']['records'])
            full_table = pd.concat([full_table, small_piece])

            total_inputs = output['count']['records'][0]['totalcount']
            if math.ceil(total_inputs / self.options['PAGE_SIZE']) == pageNum: break

        if not plant_id in self.get_plant_infra_cache:
            self.get_plant_infra_cache[plant_id] = {}

        self.get_plant_infra_cache[plant_id][param_name] = full_table

        return full_table

    # Functions calling metaDB
    def get_plant_info_from_plant_id(self, plant_id):
        if plant_id in self.get_plant_info_from_plant_id_cache:
            return self.get_plant_info_from_plant_id_cache[plant_id]

        """Get plant-related information."""
        url = self.base_url + 'plant/{}'.format(plant_id)
        session = self.retry_session(url)
        response = session.get(url)
        output = response.json()
        gen_inf = pd.DataFrame(output['body']['records'])

        self.get_plant_info_from_plant_id_cache[plant_id] = gen_inf

        return gen_inf

    def get_plants(self):

        """Get plant-related information."""
        url = self.base_url + 'plant/list'
        session = self.retry_session(url)
        response = session.post(url)
        output = response.json()
        plants = pd.DataFrame(output['body']['records'])

        return plants

    def get_company_info_from_company_id(self, company_id):
        if company_id in self.get_company_info_from_company_id_cache:
            return self.get_company_info_from_company_id_cache[company_id]

        """Get the name of the company for its ID."""
        url = self.base_url + 'company/{}'.format(company_id)
        session = self.retry_session(url)
        response = session.get(url)
        output = response.json()
        company_info = pd.DataFrame(output['body']['records'])

        self.get_company_info_from_company_id_cache[company_id] = company_info

        return company_info

    def get_inverters_info(self):
        """Get information of all inverters."""
        # Intentionally set plant_id as empty as there's no query string
        plant_id = ''
        inverters_info = self.get_plant_infra(plant_id, param_exists=False,
                                              param_name='inverters')
        return inverters_info

    def get_credentials_from_plant_id(self, plant_id):
        if plant_id in self.get_credentials_from_plant_id_cache:
            return self.get_credentials_from_plant_id_cache[plant_id]

        """Get credentials from plant ID."""
        gen_inf = self.get_plant_info_from_plant_id(plant_id)
        credentials_id = gen_inf.loc[0, 'credentials_id']

        url = self.base_url + 'credential/{}'.format(credentials_id)
        headers = {
            'Authorization': self.options['ACCESS_TOKEN']
        }
        session = self.retry_session(url)
        response = session.get(url, headers=headers)
        output = response.json()
        creds = output['body']['records'][0]

        self.get_credentials_from_plant_id_cache[plant_id] = creds

        return creds

    def get_credentials_id(self, plant_id):
        if plant_id in self.get_credentials_id_cache:
            return self.get_credentials_id_cache[plant_id]

        plant_df = self.get_plant_infra(plant_id, param_name='plant', param_exists=False)
        credentials_id = plant_df[plant_df.plant_id == int(plant_id)]['credentials_id'].values[0]

        self.get_credentials_id_cache[plant_id] = credentials_id

        return credentials_id

    def get_service_id(self, plant_id, cred_id):
        if cred_id in self.get_service_id_cache:
            return self.get_service_id_cache[cred_id]

        creds = self.get_credentials_from_plant_id(plant_id)
        service_id = creds['service']

        self.get_service_id_cache[cred_id] = service_id

        return service_id

    def get_api_type(self, plant_id):
        if plant_id in self.get_api_type_cache:
            return self.get_api_type_cache[plant_id]

        credentials_id = self.get_credentials_id(plant_id)

        self.get_api_type_cache[plant_id] = self.get_service_id(plant_id, credentials_id)

        return self.get_api_type_cache[plant_id]

    def get_api_keys_from_plant_id(self, plant_id):
        if plant_id in self.get_api_keys_from_plant_id_cache:
            return self.get_api_keys_from_plant_id_cache[plant_id]

        """Get API keys from plant ID."""
        creds = self.get_credentials_from_plant_id(plant_id)
        auth_key = creds['authorization']
        api_key = creds['api_key']

        headers = {
            'Authorization': auth_key,
            'X-API-KEY': api_key
        }

        self.get_api_keys_from_plant_id_cache[plant_id] = headers

        return headers

    def get_base_url_from_plant_id(self, plant_id):
        if plant_id in self.get_base_url_from_plant_id_cache:
            return self.get_base_url_from_plant_id_cache[plant_id]

        """Get Base URL from plant ID."""
        creds = self.get_credentials_from_plant_id(plant_id)
        base_url = creds['base_url']

        self.get_base_url_from_plant_id_cache[plant_id] = base_url

        return base_url

    def get_panel_info(self, panel_id):
        """Get information of panels."""
        url = self.base_url + 'panel/{}'.format(panel_id)
        session = self.retry_session(url)
        response = session.get(url)
        output = response.json()
        panel_info = pd.DataFrame(output['body']['records'])

        panel_info.iloc[:, 3:-1] = panel_info.iloc[:, 3:-1].apply(pd.to_numeric)
        return panel_info

    def get_orientation_info(self, orient_id, plant_id):
        """Get information of orientations."""
        params = {'plant_id': plant_id}
        url = self.base_url + 'orientation/{}'.format(orient_id)
        session = self.retry_session(url)
        response = session.get(url, params=params)
        output = response.json()

        orient_info = pd.DataFrame(output['body']['records'])
        return orient_info

    # Functions that don't need base URL
    def do_strings_exist(self, plant_id):
        """Do strings exist? Yes/No."""
        gen_inf = self.get_plant_info_from_plant_id(plant_id)
        string_exist = bool(gen_inf.loc[0, 'string_exists'])
        return string_exist

    def do_sensors_exist(self, plant_id):
        """Do sensors exist? Yes/No."""
        gen_inf = self.get_plant_info_from_plant_id(plant_id)
        sensor_exist = bool(gen_inf.loc[0, 'sensor_exists'])
        return sensor_exist

    def get_system_key(self, plant_id):
        """Get system key as found in Meteocontrol."""
        gen_inf = self.get_plant_info_from_plant_id(plant_id)
        system_key = gen_inf.loc[0, 'system_key']
        return system_key

    def get_company_name(self, plant_id):
        """Get the name of the company associated with that plant ID."""
        # Get company ID from plant ID
        gen_inf = self.get_plant_info_from_plant_id(plant_id)
        company_id = gen_inf.loc[0, 'company_id']

        # Get company name from company ID
        company_inf = self.get_company_info_from_company_id(company_id)
        company_name = company_inf.loc[0, 'company_name']

        return company_name

    # Plant infra dependent functions
    def get_mppts(self, plant_id):
        """Get all the MPPTs present in a plant."""
        mppt_table = self.get_plant_infra(plant_id, param_exists=True,
                                          param_name='mppt')
        return mppt_table

    def get_strings(self, plant_id):
        """Get all the strings present in a plant."""
        string_table = self.get_plant_infra(plant_id, param_exists=True,
                                            param_name='string')
        return string_table

    def get_combiners(self, plant_id):
        """Get all the combiner boxes present in a plant."""
        combiner_table = self.get_plant_infra(plant_id, param_exists=True,
                                              param_name='combiner')
        return combiner_table

    def get_inverters(self, plant_id):
        """Get all the inverters present in a plant."""
        inverter_table = self.get_plant_infra(plant_id, param_exists=True,
                                              param_name='inverter')
        return inverter_table

    def get_sensors(self, plant_id):
        """Get all the sensors present in a plant."""
        sensor_table = self.get_plant_infra(plant_id, param_exists=True,
                                            param_name='sensor')
        return sensor_table

    def get_plant_attributes(self, plant_id):
        """Get all the plant attributes in a plant."""
        plant_attributes = self.get_plant_infra(plant_id, param_exists=True,
                                                param_name='plant-attributes')
        return plant_attributes

    def get_sensor_ids(self, sensor_table):
        """Get list of sensor IDs."""
        sensor_info = sensor_table['sensor_id_fk'].astype(int)
        sensor_ids = list(sensor_info.astype(str).unique())
        return sensor_ids

    def get_inv_map(self, inverter_table):
        """Map inverters to their foreign key IDs."""
        inv_table = inverter_table.copy()
        inv_table['inv_id'] = INVERTER_NAME + inv_table[
            'inv_id'].astype(str)
        inv = inv_table[['inv_id_fk', 'inv_id']].copy()
        inv_map = dict(inv.values)
        return inv_map

    def get_cb_inv_mapping(self, combiner_table, inverter_table):
        """Get all Combiner box IDs for a particular inverter."""
        mapping = combiner_table.merge(inverter_table, on='inv_id')[['cb_id', 'inv_id_fk']]
        mapping['cb_id'] = mapping['cb_id'].astype(int).astype(str)

        # What if each MPPT has its own CB ID?
        # Ref: SO Q.No 22219004
        dfJesus = mapping.groupby('inv_id_fk')[
            'cb_id'].apply(list).to_frame().reset_index()
        cb_map_inv = dict(dfJesus.values)
        return cb_map_inv

    def get_sensor_inv_mapping(self, sensor_table):
        """Get all sensor IDs for a particular inverter."""
        sens = sensor_table.copy()
        sens['inv_id'] = INVERTER_NAME + sens['inv_id'].astype(str)
        sens['sensor_id_fk'] = sens['sensor_id_fk'].astype(int).astype(str)
        sens = sens[['inv_id', 'sensor_id_fk']].copy()

        # What if each MPPT has its own sensor ID?
        dfJesus = sens.groupby('inv_id')[
            'sensor_id_fk'].apply(list).to_frame().reset_index()
        Sensor_inv_dict = dict(dfJesus.values)
        return Sensor_inv_dict

    def get_mppt_str_comb(self, mppt_table, string_table):
        """Get no. of strings are attached to each MPPT for every inverter."""
        infra = string_table[['string_id', 'mppt_id', 'inv_id']].merge(
            mppt_table[['mppt_id', 'mppt_id_fk', 'inv_id']])
        infra['mppt_id'] = infra.mppt_id_fk.replace(to_replace='U_DC',
                                                    value='M', regex=True)

        mppt_str_count = pd.DataFrame()

        for inverter in infra['inv_id'].unique():
            analysis = infra[infra.inv_id == inverter]
            temp_count = analysis.groupby(['mppt_id'])[
                'string_id'].count().to_frame().reset_index()
            str_inv = 'inv' + str(inverter)
            temp_count['inverter'] = str_inv
            mppt_str_count = pd.concat([mppt_str_count, temp_count])

        mppt_str_count.set_index(['inverter'], inplace=True)
        return mppt_str_count
