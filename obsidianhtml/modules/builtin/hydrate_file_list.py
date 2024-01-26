import os
import yaml
import platform
import datetime
from dataclasses import dataclass

from pathlib import Path

from ...lib import pushd, WriteFileLog

from ...core.NetworkTree import NetworkTree
from ...core.FileObject import FileObject
from ...core.schema import Schema

from ..base_classes import ObsidianHtmlModule
from ..base_classes.config import Config

@dataclass
class AnnotatedFile(Schema):
    path: str
    is_note: bool
    is_video: bool
    is_audio: bool
    is_embeddable: bool
    is_includable_file: bool
    is_parsable_note: bool
    modified_time: str = None
    creation_time: str = None

    @staticmethod
    def set_times(af):
        times = {}
        af.modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(af.path)).isoformat()
        if platform.system() == "Windows" or platform.system() == "Darwin":
            af.creation_time = datetime.datetime.fromtimestamp(os.path.getctime(af.path)).isoformat()
        return af

    @classmethod
    def from_file_str(cls, gc, file_str):
        af = cls(
            path = file_str,
            is_note = False,
            is_video = False,
            is_audio = False,
            is_embeddable = False,
            is_includable_file = False,
            is_parsable_note = False,
        )

        file_path = Path(file_str)
        suffix = file_path.suffix[1:].lower()

        if suffix == "md":
            af.is_note = True
        if suffix in gc("included_file_suffixes"):
            af.is_includable_file = True
        if suffix in gc("video_format_suffixes"):
            af.is_video = True
        if suffix in gc("audio_format_suffixes"):
            af.is_audio = True
        if suffix in gc("embeddable_file_suffixes"):
            af.is_embeddable = True

        if file_path.exists() and af.is_note:
            af.is_parsable_note = True

        af = cls.set_times(af)

        return af


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

    def run(self):
       
        # get files
        files = self.modfile("index/files.json").read().from_json()
        
        # annotate
        annotated_files = []
        for file in files:
            annotated_files.append(
                AnnotatedFile.from_file_str(self.config.gc, file).normalize()
            )

        # write output
        self.modfile("index/files_annotated.json", annotated_files).to_json().write()


    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass
