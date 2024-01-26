import os, yaml
from pathlib import Path
from dataclasses import dataclass
from functools import cache

from ..lib import hash_wrap
from .. import handlers

@dataclass
class Config:
    config: dict = None

    def __post_init__(self):
        # the module data location is found by setup_module, this contains the config.yml
        mdf_path = os.getenv("OBS_MODULE_DATA_FOLDER")
        if mdf_path is None:
            raise Exception("ENV var OBS_MODULE_DATA_FOLDER was not set, this is expected to be the case when this module is run")

        with open(Path(mdf_path).joinpath("config.yml"), 'r') as f:
            self.config = yaml.safe_load(f.read())
        
    def gc(self, path: str, config=None, cached=False):
        """This function makes is easier to get deeply nested config values by allowing path/to/nested/value instead of ["path"]["to"]["nested"]["value"].
        It also handles errors in case of key not found."""
        if config is None:
            config = self.config
        if cached:
            return handlers.config.get_config_cached(hash_wrap(config), path)
        return handlers.config.get_config(config, path)

    def get_dict(self):
        return self.config

    """ Test if key is set in config """
    def has(self, path):
        res = handlers.config.get_config(self.config, path, fail_on_missing=False)
        if type(res) is KeyError:
            return False
        return True