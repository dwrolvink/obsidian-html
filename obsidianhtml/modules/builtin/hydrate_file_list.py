"""
    This module takes the index/files.json file paths and for each path create an AnnotatedFile object
    This object is just the path plus some derived properties, such as if a file is a video file, etc.

    This module *also* adds the files that will be created by the program, such as the "not_created.md" file.
    These files will get is_generated:true 
"""

import os
import yaml
import platform
import datetime
from dataclasses import dataclass

from pathlib import Path

from ...core.schema import Schema

from ..base_classes import ObsidianHtmlModule
from ..base_classes.config import Config

@dataclass
class AnnotatedFile(Schema):
    path: str
    is_entrypoint: bool
    is_note: bool
    is_video: bool
    is_audio: bool
    is_embeddable: bool
    is_includable_file: bool
    is_parsable_note: bool
    is_generated: bool = False
    modified_time: str = None
    creation_time: str = None

    @staticmethod
    def set_times(af):
        times = {}

        # file does not exist yet, just give current time
        if af.is_generated:
            af.modified_time = datetime.datetime.now().isoformat()
            af.creation_time = datetime.datetime.now().isoformat()
            return af

        # look up modified time 
        af.modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(af.path)).isoformat()
        
        # created time not available (consistently) on linux
        if platform.system() == "Windows" or platform.system() == "Darwin":
            af.creation_time = datetime.datetime.fromtimestamp(os.path.getctime(af.path)).isoformat()
        return af

    @staticmethod
    def check_is_entrypoint(gc, paths, file_path):
        # get rel_path
        rel_path = file_path.relative_to(paths["input_folder"])

        # test is entrypoint
        if gc("toggles/compile_md"):
            if rel_path.as_posix() == paths["rel_obsidian_entrypoint"]:
                return True
            return False
        else:
            if rel_path.as_posix() == paths["rel_md_entrypoint_path"]:
                return True
            return False

    @classmethod
    def from_dict(cls, d):
        return cls(
            path = d["path"],
            is_entrypoint = d["is_entrypoint"],
            is_note = d["is_note"],
            is_video = d["is_video"],
            is_audio = d["is_audio"],
            is_embeddable = d["is_embeddable"],
            is_includable_file = d["is_includable_file"],
            is_parsable_note = d["is_parsable_note"],
        )

    @classmethod
    def from_file_str(cls, gc, paths, file_str, is_generated=False):
        af = cls(
            path = file_str,
            is_entrypoint = False,
            is_note = False,
            is_video = False,
            is_audio = False,
            is_embeddable = False,
            is_includable_file = False,
            is_parsable_note = False,
            is_generated = is_generated,
        )

        file_path = Path(file_str)
        suffix = file_path.suffix[1:].lower()

        af.is_entrypoint = cls.check_is_entrypoint(gc, paths, file_path)

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
        return tuple(["index/files.json", "paths.json"])

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
        # get input
        paths = self.modfile("paths.json").read().from_json()
        files = self.modfile("index/files.json").read().from_json()
        
        # annotate
        annotated_files = []
        for file in files:
            annotated_files.append(
                AnnotatedFile.from_file_str(self.config.gc, paths, file).normalize()
            )

        # add in generated files
        input_folder = Path(paths["input_folder"])
        annotated_files.append(
            AnnotatedFile.from_file_str(self.config.gc, paths, input_folder.joinpath("not_created.md"), is_generated=True).normalize()
        )

        # check that we have only one entrypoint
        eps = []
        for af in annotated_files:
            if af["is_entrypoint"]:
                eps.append(af["path"])
        if len(eps) == 0:
            raise Exception("No files were found that match the entrypoint defined!")
        if len(eps) > 1:
            raise Exception(f"Multiple entrypoints were found when one was expected: {eps}")
        
        # write output
        self.modfile("index/files_annotated.json", annotated_files).to_json().write()


    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass
