"""
    This module takes the index/files_annotated.json file and determines the following extra values:
      - input_path: original path as found in the source file
      - rel_path: This is derived from the input_path and input_folder, but will be overwritten in some cases (e.g. index.md)
      - note_path: the path of the obsidian vault, will be None if we take markdown as input
      - markdown_path: the path for the generated markdown file, will use updated rel_path
      - html_path: the file path for the generated html file, will use updated rel_path
"""

import json
from dataclasses import dataclass
from pathlib import Path

from ...core.schema import Schema

from ..base_classes import ObsidianHtmlModule
from ..base_classes.config import Config
from ..base_classes.paths import Paths

from .hydrate_file_list import AnnotatedFile, AnnotatedFileManager


""" Used by other modules when they generate files to get these published correctly in index/files_annotated.json and index/files_mapped.json """
class FileManager:
    """ You can define the files that you will create and get MappedFiles back for each path in dst_rel_paths 
        If register=True, the index/files_annotated.json and index/files_mapped.json modfiles will be updated immediately.
            (This is important if other modules are supposed to know they exist)
        Note that FileManager will use the calling class to access the modfiles, so these will need to have the proper requests/provides set!
    """

    def __init__(self, calling_module):
        self.caller = calling_module  # usage: FileManager(self)

    """ Used by core components to get access to the file list """
    @classmethod
    def get_mapped_files(cls):
        paths = Paths().get_dict()
        with open(Path(paths("module_data_folder")).joinpath("index/files_mapped"), 'r') as f:
            mfs = json.loads(f.read())

        MFs = []
        for mf in mfs:
            MFs.append(MappedFile.from_dict(mf))
        return MFs



    def map_generated_files(self, target, dst_rel_paths, register=True):
        # check args
        if not isinstance(dst_rel_paths, list):
            raise Exception(f'dst_rel_paths should be list of desired paths, got {dst_rel_paths}')

        # Get input
        config = Config()
        paths = Paths().get_dict()

        # Create MappedFiles
        mapped_files = []
        for dst_rel_path in dst_rel_paths:
            # cast target "input" to what was configured as input folder
            if target == "input":
                if config.gc("toggles/compile_md"):
                    target = "note"
                else:
                    target = "md"

            # get paths
            #MappedFile.convert_md_to_html(dst_rel_path)
            targets = {
                "note": Path(paths["obsidian_folder"]),
                "md": Path(paths["md_folder"]),
                "html": Path(paths["html_output_folder"]),
            }

            # build full path
            if target not in targets.keys():
                raise Exception(f'Target {target} is not valid. Valid targets include: {targets.keys()}')
            input_path = targets[target].joinpath(dst_rel_path)

            # Create objects
            # create AnnotatedFile
            af = AnnotatedFile.from_file_str(config.gc, paths, input_path, is_generated=True)

            # create MappedFile
            mapped_files.append(MappedFile.from_annotated_file(config.gc, paths, af))

        # Register MappedFiles
        if register:
            self.register_generated_files(mapped_files)

        return mapped_files

    def register_generated_files(self, mapped_files):
        # get access to modfiles
        af_modfile = self.caller.modfile("index/files_annotated.json")
        mf_modfile = self.caller.modfile("index/files_mapped.json")

        # add annotated files to index/files_annotated.json
        afs = af_modfile.read().from_json()
        for mf in mapped_files:
            afs.append(mf.annotations.normalize())
        af_modfile.contents = afs
        af_modfile.to_json().write()

        # add mapped files to index/files_mapped.json
        mfs = mf_modfile.read().from_json()
        for mf in mapped_files:
            mfs.append(mf.normalize())
        mf_modfile.contents = mfs
        mf_modfile.to_json().write()


    """ Whenever you change settings that affect the generated values in the annotated-/mapped file lists,
        after these lists have already been generated, you should call this function 
    """
    @classmethod
    def recalculate(cls, af_modfile, mf_modfile):
        config = Config()
        paths = Paths().get_dict()

        # update index/files_annotated.json
        AnnotatedFileManager.recalculate(af_modfile)

        # update index/files_mapped.json
        cls.calculate_mapped_files(config.gc, paths, af_modfile, mf_modfile)


    @classmethod
    def calculate_mapped_files(cls, gc, paths, af_modfile, mf_modfile):
        # get files
        files = af_modfile.read().from_json()
        
        # determine output locations
        mapped_files = []
        for file in files:
            mapped_files.append(
                MappedFile.from_annotated_file(gc, paths, AnnotatedFile.from_dict(file)).normalize()
            )

        # write output
        mf_modfile.contents = mapped_files
        mf_modfile.to_json().write()


""" Represents a MappedFile as found in index/files_mapped.json """
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
    def convert_md_to_html(rel_path):
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

    """ Mainly used to get a dict from files_mapped.json and recast them into MappedFiles """
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

    """ Take AnnotatedFile from previous module and cast it into a MappedFile """
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

        rel_path_html = cls.convert_md_to_html(rel_path)
        
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
        FileManager.calculate_mapped_files(
            self.config.gc, self.paths(),
            af_modfile = self.modfile("index/files_annotated.json"),
            mf_modfile = self.modfile("index/files_mapped.json")
        )


    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass
