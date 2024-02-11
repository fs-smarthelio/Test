import pandas as pd
import os
import awswrangler as wr
from heliolib.data_extraction_service import TimestreamDataExtractor
from heliolib.data_transformation_service import TimestreamPivotTransformer
from heliolib.feature_engineering_service import ExpectedParametersGenerator
from heliolib.metadata_extraction_service import SystemInfoMetadataAPI, MetadataAPI

metadb_functions = MetadataAPI(
    f'{os.environ["METADATA_API_URL"]}',
    {"PAGE_SIZE": 100, "ACCESS_TOKEN": os.environ["METADATA_ACCESS_TOKEN"]},
)


def function_to_call(start_date, end_date, plants_ids: list, cycle_of_data: str):
    # start_date = (
    #     "2024-02-01"  # st.date_input("Enter start date:", value=datetime.today().date()
    # )
    # end_date = (
    #     "2024-02-07"  # st.date_input("Enter end date:", value=datetime.today().date())  #
    # )
    # plants_ids = [1]

    output = pd.DataFrame(
        [],
        index=pd.to_datetime(pd.date_range(start=start_date, end=end_date, freq='1T').date.tolist()),
    )
    output = output.resample(cycle_of_data).sum()

    plant_ids_not_containing_actual_power_parameter = []

    for plant_id in plants_ids:  # [i for i in range(1, 10)] + [i for i in range(30, 53)]:
        print("plant: ", plant_id)

        company_name = "Daystar"

        system_info = SystemInfoMetadataAPI(metadb_functions)
        array_info, plant_table = system_info.get_plant_meta_data(
            plant_id, reference_date=start_date
        )

        timestream_client = wr.timestream

        data_extractor = TimestreamDataExtractor(
            timestream_client, plant_id, metadata_api_object=metadb_functions
        )

        timestream_data = data_extractor.fetch_data(
            start_datetime=pd.to_datetime(start_date),
            end_datetime=pd.to_datetime(end_date),
        )

        transformer = TimestreamPivotTransformer(data=timestream_data)
        inverter_data, meteo_data = transformer.transform()

        expect = ExpectedParametersGenerator(
            meteo_data=meteo_data,
            array_info=array_info,
            irradiance_key="G",
            system_age=plant_table["system_age"].values[0],
        )
        parameters = expect.generate_expected_features()

        try:
            inv_actual_1 = pd.DataFrame(
                inverter_data.xs("P", level="curve", axis=1).sum(axis=1)
            )
        except Exception as e:
            plant_ids_not_containing_actual_power_parameter.append(plant_id)
            continue
        inv_actual_1 = inv_actual_1 * (5 / 60000)
        inv_actual_1 = inv_actual_1.resample(cycle_of_data).sum()
        # inv_actual_1["datetime_1"] = inv_actual_1.index.date
        # inv_actual_1 = inv_actual_1.groupby("datetime_1", axis=0).sum()

        inv_expected_1 = pd.DataFrame(
            parameters.xs("P_exp_noct_degradation", level="curve", axis=1).sum(axis=1)
        )
        inv_expected_1 = inv_expected_1 * (5 / 60000)
        inv_expected_1 = inv_expected_1.resample(cycle_of_data).sum()
        # inv_expected_1["datetime_1"] = inv_expected_1.index.date
        # inv_expected_1 = inv_expected_1.groupby("datetime_1", axis=0).sum()

        output.loc[
            list(map(lambda x: str(x), inv_actual_1.index.tolist())),
            "plant_" + str(plant_id) + "/ACTUAL",
        ] = inv_actual_1.values
        output.loc[
            list(map(lambda x: str(x), inv_expected_1.index.tolist())),
            "plant_" + str(plant_id) + "/EXPECTED",
        ] = inv_expected_1.values

    return output

# result = function_to_call("2024-02-01", "2024-02-07", [1], "W")
