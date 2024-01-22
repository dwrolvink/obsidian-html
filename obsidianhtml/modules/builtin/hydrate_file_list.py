import os
import yaml

from pathlib import Path

from ...lib import pushd, WriteFileLog

from ...core.NetworkTree import NetworkTree
from ...core.FileObject import FileObject


from ..base_classes import ObsidianHtmlModule


class HydrateFileListModule(ObsidianHtmlModule):
    """
    This module will take the index/files.json file, determine properties per file, and write these to index/files_annotated.json
    """

    @staticmethod
    def friendly_name():
        return "hydrate_file_list"    

    @staticmethod
    def requires():
        return tuple(["index/files.json", "config.yml"])

    @staticmethod
    def provides():
        return tuple(["index/files_annotated.json"])

    @staticmethod
    def alters():
        return tuple()


    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def get_annotated_file(self, file_str):
        af = {
            "path": file_str,
            "is_note": False,
            "is_video": False,
            "is_audio": False,
            "is_embeddable": False,
            "is_includable_file": False,
            "is_parsable_note": False,
        }

        gc = self.gc
        file_path = Path(file_str)
        suffix = file_path.suffix[1:].lower()

        if suffix == "md":
            af["is_note"] = True
        if suffix in gc("included_file_suffixes"):
            af["is_includable_file"] = True
        if suffix in gc("video_format_suffixes"):
            af["is_video"] = True
        if suffix in gc("audio_format_suffixes"):
            af["is_audio"] = True
        if suffix in gc("embeddable_file_suffixes"):
            af["is_embeddable"] = True

        if file_path.exists() and af["is_note"]:
            af["is_parsable_note"] = True

        return af

    def run(self):
        # get files
        files = self.modfile("index/files.json").read().from_json()
        
        # annotate
        annotated_files = []
        for file in files:
            annotated_files.append(self.get_annotated_file(file))

        # write output
        self.modfile("index/files_annotated.json", annotated_files).to_json().write()

        exit()

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass
