"""
    This module takes the index/files_annotated.json file and determines the following extra values:
      - input_path: original path as found in the source file
      - rel_path: This is derived from the input_path and input_folder, but will be overwritten in some cases (e.g. index.md)
      - note_path: the path of the obsidian vault, will be None if we take markdown as input
      - markdown_path: the path for the generated markdown file, will use updated rel_path
      - html_path: the file path for the generated html file, will use updated rel_path
"""

import os
import yaml
import platform
import datetime
from dataclasses import dataclass

from pathlib import Path

from ...lib import pushd, WriteFileLog

from ...core.NetworkTree import NetworkTree
from ...core.schema import Schema

from ..base_classes import ObsidianHtmlModule
from ..base_classes.config import Config

from .hydrate_file_list import AnnotatedFile

@dataclass
class MappedFile(Schema):
    original_rel_path: str
    rel_path: str
    rel_path_html: str

    input_path: str
    note_path: str | None
    md_path: str
    html_path: str 

    annotations: AnnotatedFile

    @staticmethod
    def convert_md_to_hmtl(rel_path):
        # ensure Path input
        input_was_str = False
        if not isinstance(rel_path, Path):
            input_was_str = True
            rel_path = Path(rel_path)

        # get rel path posix str
        rel_path_posix = rel_path.as_posix()

        # .md -> .html
        if rel_path_posix[-3:] == ".md":
            rel_path_posix = rel_path_posix[:-3] + ".html"

        # output as str if input was str, otherwise output Path
        if input_was_str:
            return rel_path_posix

        return Path(rel_path_posix)

    @classmethod
    def from_dict(cls, d):
        return cls(
            original_rel_path = d["original_rel_path"],
            rel_path = d["rel_path"],
            rel_path_html = d["rel_path_html"],
            input_path = d["input_path"],
            note_path = d["note_path"],
            md_path = d["md_path"],
            html_path = d["html_path"],
            annotations = AnnotatedFile.from_dict(d["annotations"]),
        )
    @classmethod
    def from_annotated_file(cls, gc, paths, file):
        # determine rel_path
        # ---
        original_rel_path = Path(file.path).relative_to(paths["input_folder"]).as_posix()

        # overwrite rel_path if entrypoint
        # ---
        rel_path = original_rel_path
        if file.is_entrypoint:
            rel_path = 'index.md'

        rel_path_html = cls.convert_md_to_hmtl(rel_path)
        
        # set note and md paths
        # ---
        if gc("toggles/compile_md"):
            # if we compile md, then the input path will be the note path
            note_path = file.path
            md_path = Path(paths["md_folder"]).joinpath(rel_path).as_posix()
        else:
            note_path = None
            # if we don't compile md, the the input path will be the md path
            md_path = file.path
        html_path = Path(paths["html_output_folder"]).joinpath(rel_path_html).as_posix()


        # return obj
        # ---
        return cls(
            original_rel_path = original_rel_path,
            rel_path = rel_path,
            rel_path_html = rel_path_html,

            input_path = file.path,
            note_path = note_path,
            md_path = md_path,
            html_path = html_path,

            annotations = file,
        )


class FileMapperModule(ObsidianHtmlModule):

    @staticmethod
    def friendly_name():
        return "file_mapper"    

    @staticmethod
    def requires():
        return tuple(["index/files_annotated.json","paths.json"])

    @staticmethod
    def provides():
        return tuple(["index/files_mapped.json"])

    @staticmethod
    def alters():
        return tuple()


    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        return

    def run(self):
        # config
        config = Config()
        paths = self.modfile("paths.json").read().from_json()
       
        # get files
        files = self.modfile("index/files_annotated.json").read().from_json()
        
        # determine output locations
        mapped_files = []
        for file in files:
            mapped_files.append(
                MappedFile.from_annotated_file(config.gc, paths, AnnotatedFile.from_dict(file)).normalize()
            )

        # write output
        self.modfile("index/files_mapped.json", mapped_files).to_json().write()


    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass
