from smarthelio_shared import MetadataAPI
import os

metadb_functions = MetadataAPI('https://metadata-api.test.smarthelio.cloud/', {
    "PAGE_SIZE": 100,
    "ACCESS_TOKEN": os.environ['ACCESS_TOKEN']
})

creds = metadb_functions.get_credentials_from_plant_id(10)

print(creds)
