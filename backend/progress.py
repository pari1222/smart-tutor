import json
import os

PROGRESS_FILE = "user_progress.json"


def load_progress():

    if not os.path.exists(PROGRESS_FILE):
        return {}

    with open(PROGRESS_FILE, "r") as file:
        return json.load(file)


def save_progress(data):

    with open(PROGRESS_FILE, "w") as file:
        json.dump(
            data,
            file,
            indent=4
        )