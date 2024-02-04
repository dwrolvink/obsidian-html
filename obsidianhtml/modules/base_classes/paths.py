import os, json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Paths:
    paths: dict = None

    def __post_init__(self):
        # the module data location is found by setup_module, this contains the config.yml
        mdf_path = os.getenv("OBS_MODULE_DATA_FOLDER")
        if mdf_path is None:
            raise Exception("ENV var OBS_MODULE_DATA_FOLDER was not set, this is expected to be the case when this module is run")

        with open(Path(mdf_path).joinpath("paths.json"), "r") as f:
            self.paths = json.loads(f.read())

    def get_dict(self):
        return self.paths
