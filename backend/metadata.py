import json
import os

METADATA_FILE = "document_metadata.json"


def load_metadata():

    if not os.path.exists(METADATA_FILE):
        return {}

    with open(METADATA_FILE, "r") as file:
        return json.load(file)


def save_metadata(data):

    with open(METADATA_FILE, "w") as file:
        json.dump(
            data,
            file,
            indent=4
        )