from pathlib import Path

from ...lib import print_debug

from ..base_classes import ObsidianHtmlModule
from .file_mapper import FileManager, MappedFile


class CreateIndexFromTagsModule(ObsidianHtmlModule):
    """
    This module will take the index/files.json file, determine properties per file, and write these to index/files_annotated.json
    """

    @staticmethod
    def friendly_name():
        return "create_index_from_tags"

    def define_mod_config_defaults(self):
        self.mod_config["enabled"] = {
            "value": False,
            "description": "Whether to run this module",
        }
        self.mod_config["tags"] = {
            "value": [],
            "description": "Tags to show in the index",
        }
        self.mod_config["verbose"] = {
            "value": False,
            "description": "Print debug info when True",
        }
        self.mod_config["rel_output_path"] = {
            "value": "obs.html/tag_index.md",
            "description": "File path relative to md_folder where to write the index note to",
        }
        self.mod_config["homepage_label"] = {
            "value": "index",
            "description": "",
        }
        self.mod_config["use_as_homepage"] = {
            "value": False,
            "description": "",
        }
        self.mod_config["add_links_in_graph_tree"] = {
            "value": True,
            "description": "",
        }
        self.mod_config["match_on_inline_tags"] = {
            "value": False,
            "description": "",
        }
        self.mod_config["styling"] = {
            "value": {
                "include_folder_in_link": False,
            },
            "description": "",
        }
        self.mod_config["sort"] = {
            "value": {
                "method": "none",  # <key_value, creation_time, modified_time, none>    ! created_time not available on Linux!
                "key_path": "",  # empty for top level, use ':' to go down multiple levels
                "value_prefix": "",  # in case of multiple values under key_path, match on this prefix, and then remove prefix
                "reverse": False,  # false/true reverses output
                "none_on_bottom": True,  # will put notes at the bottom that do not have the sort key, otherwise at the top
            },
            "description": "",
        }
        self.mod_config["exclude_paths"] = {
            "value": [".gitignore"],
            "description": "",
        }

    @staticmethod
    def requires():
        return tuple(["index/files_mapped.json", "paths.json", "index/files_annotated.json"])

    @staticmethod
    def provides():
        return tuple(["index/files_mapped.json", "paths.json", "index/files_annotated.json"])

    @staticmethod
    def alters():
        return tuple()

    def accept(self, module_data_folder):
        """This function is run before run(), if it returns False, then the module run is skipped entirely. Any other value will be accepted"""
        enabled = self.value_of("enabled")
        if not enabled:
            return False

        # We'll need to write a file to the obsidian folder
        # This is not good if we don't target the temp folder (copy_vault_to_tempdir = True)
        # Because we don't want to mess around in people's vaults.
        # So disable this feature if that setting is turned off
        if self.config.gc("copy_vault_to_tempdir") is False:
            print_debug(
                "WARNING: The feature 'CREATE INDEX FROM TAGS' needs to write an index file to the obsidian path.",
                "We don't want to write in your vault, so in order to use this feature set 'copy_vault_to_tempdir: True' in your config.",
            )
            return False

    def verbose(self):
        global_verbose = self.config.gc("toggles/verbose_printout", cached=True)
        local_verbose = self.value_of("verbose")
        return global_verbose or local_verbose

    def run(self):
        # get input
        settings = self.mod_config_as_dict()

        # we are creating a new file, make a mapping for this and register it so that other modules know about it
        index_mf = FileManager(self).map_generated_files(target="note", dst_rel_paths=["__tags_index.md"])[0]

        # extract the definitive target path from the MappedFile
        rel_path = index_mf.rel_path
        dst_path = index_mf.input_path

        # overwrite path settings
        if settings["use_as_homepage"]:
            if self.verbose():
                print_debug("\tWill overwrite entrypoints: obsidian_entrypoint, rel_obsidian_entrypoint")

            paths_mf = self.modfile("paths.json")
            paths_mf.insert("obsidian_entrypoint", dst_path)
            paths_mf.insert("rel_obsidian_entrypoint", rel_path)
            paths_mf.write()

            # reload paths
            self.paths(cast=True, reload=True)

            # these path setting affect index/files_annotated.json & index/files_mapped.json, so these need to be recalculated
            FileManager.recalculate(af_modfile=self.modfile("index/files_annotated.json"), mf_modfile=self.modfile("index/files_mapped.json"))

        if self.verbose():
            print_debug("\tWill write the note index to: ", dst_path)

        # finally, create the index page
        self.create_index_from_tags(index_mf)

        exit()

    def create_index_from_tags(self, index_mf):
        # get input
        settings = self.mod_config_as_dict()
        paths = self.paths(cast=True)

        # get markdown for the index page
        md_content, index_dict = self.compile_tag_page_markdown()

        # write content to markdown file
        Path(index_mf.input_path).parent.mkdir(exist_ok=True)
        with open(index_mf.input_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # [TODO]
        # # [17] Build graph node/links
        # if pb.gc("toggles/features/create_index_from_tags/add_links_in_graph_tree", cached=True):
        #     if self.verbose():
        #         print_debug("\tAdding graph links between index.md and the matched notes")

        #     node = pb.index.network_tree.NewNode()
        #     node["name"] = pb.gc("toggles/features/create_index_from_tags/homepage_label").capitalize()

        #     if settings["use_as_homepage"]:
        #         node["id"] = "index"
        #         node["url"] = f'{pb.gc("html_url_prefix")}/index.html'
        #     else:
        #         node["id"] = "tag_index"
        #         node["url"] = fo_index_dst_path.get_link("html")

        #     pb.index.network_tree.add_node(node)
        #     bln = node
        #     for t in index_dict.keys():
        #         for n in index_dict[t]:
        #             node = pb.index.network_tree.NewNode()
        #             node["id"] = n["node_id"]
        #             node["name"] = n["graph_name"]
        #             node["url"] = f'{pb.gc("html_url_prefix")}/{slugify_path(n["md_rel_path_str"][:-3])}.html'
        #             pb.index.network_tree.add_node(node)

        #             link = pb.index.network_tree.NewLink()
        #             link["source"] = bln["id"]
        #             link["target"] = node["id"]
        #             pb.index.network_tree.AddLink(link)

    def compile_tag_page_markdown(self):
        # get input
        settings = self.mod_config_as_dict()
        mapped_files = self.modfile("index/files_mapped.json").read().from_json()

        # shorthand
        method = settings["sort"]["method"]
        key_path = settings["sort"]["key_path"]
        value_prefix = settings["sort"]["value_prefix"]
        sort_reverse = settings["sort"]["reverse"]
        none_on_bottom = settings["sort"]["none_on_bottom"]
        include_folder_in_link = settings["styling"]["include_folder_in_link"]

        if self.verbose():
            print_debug("> FEATURE: CREATE INDEX FROM TAGS: Enabled")

        # Test input
        if not isinstance(settings["tags"], list):
            raise Exception("module_config/create_index_from_tags/tags should be a list")

        if len(settings["tags"]) == 0:
            raise Exception("Feature create_index_from_tags is enabled, but no tags were listed")

        # shorthand
        include_tags = settings["tags"]
        if self.verbose():
            print_debug("\tLooking for tags: ", include_tags)

        # Find notes with given tags
        _files = {}
        index_dict = {}
        for t in include_tags:
            index_dict[t] = []

        for mfd in mapped_files:
            mf = MappedFile.from_dict(mfd)

            # shorthand
            page_path_str = mf.input_path

            # Don't parse if not parsable
            if not mf.annotations.is_parsable_note:
                if self.verbose():
                    print_debug(f"\t\tSkipping file, not parsable note: {page_path_str}")
                continue

            # Determine src file path
            if self.verbose():
                print_debug(f"\t\tParsing note {page_path_str}")

            continue

            # make mdpage object
            md = fo.load_markdown_page("note")  # <---------- [CONTINUE HERE]
            md.StripCodeSections()

            metadata = md.metadata
            node_name = md.GetNodeName()
            node_id = pb.FileFinder.GetNodeId(pb, fo.path["markdown"]["file_relative_path"].as_posix())

            # Skip if not valid
            if not fo.is_valid_note("note"):
                continue

            # Check for each of the tags if its present
            # Skip if none matched
            matched = False
            for t in include_tags:
                if md.HasTag(t):
                    if self.verbose():
                        print_debug(f"\t\tMatched note {k} on tag {t}")
                    matched = True

            if matched is False:
                continue

            # determine sorting value
            sort_value = None
            if method not in ("none", "creation_time", "modified_time"):
                if method == "key_value":
                    # key can be multiple levels deep, like this: level1:level2
                    # get the value of the key
                    key_found = True
                    value = metadata
                    for key in key_path.split(":"):
                        if key not in value.keys():
                            key_found = False
                            break
                        value = value[key]
                    # only continue if the key is found in the current note, otherwise the
                    # default sort value of None is kept
                    if key_found:
                        # for a list find all items that start with the value prefix
                        # then remove the value_prefix, and check if we have 1 item left
                        if isinstance(value, list):
                            items = [x.replace(value_prefix, "", 1) for x in value if x.startswith(value_prefix)]
                            if len(items) == 1:
                                sort_value = items[0]
                                # done
                        if isinstance(value, str):
                            sort_value = value.replace(value_prefix, "", 1)
                        if isinstance(value, bool):
                            sort_value = str(int(value))
                        if isinstance(value, int) or isinstance(value, float):
                            sort_value = str(value)
                        if isinstance(value, datetime.datetime):
                            sort_value = value.isoformat()
                else:
                    raise Exception(f"Sort method {method} not implemented. Check spelling.")

            # Get sort_value from files dict
            if method in ("creation_time", "modified_time"):
                # created time is not really accessible under Linux, we might add a case for OSX
                if method == "creation_time" and platform.system() != "Windows" and platform.system() != "Darwin":
                    raise Exception(f'Sort method of "create_time" under toggles/features/create_index_from_tags/sort/method is not available under {platform.system()}, only Windows.')
                sort_value = fo.metadata[method]

            if self.verbose():
                print_debug(f"\t\t\tSort value of note {k} is {sort_value}")

            # Add an entry into index_dict for each tag matched on this page
            # copy file to temp filetree for checking later
            _files[k] = files[k]

            # Add entry to our index dict so we can parse this later
            # do this once for each tag, so each tag listing gets a link to this note
            for t in include_tags:
                if not md.HasTag(t):
                    continue

                index_dict[t].append(
                    {
                        "file_key": k,
                        "node_id": node_id,
                        "md_rel_path_str": fo.path["markdown"]["file_relative_path"].as_posix(),
                        "graph_name": node_name,
                        "sort_value": sort_value,
                    }  # depr?
                )

        return "bla", "bleh"  # [TODO]

        if len(_files.keys()) == 0:
            raise Exception("No notes found with the given tags.")

        if self.verbose():
            print_debug("\tBuilding index.md")

        index_md_content = ""
        for t in index_dict.keys():
            # Add header
            index_md_content += f"## {t}\n"

            # shorthand
            notes = index_dict[t]

            # fill in none types
            # - get max value
            input_val = ""
            max_val = ""
            for n in notes:
                if n["sort_value"] is None:
                    continue
                if n["sort_value"] > max_val:
                    max_val = n["sort_value"]
            max_val += "Z"

            # - determine if we need to give max val or min val
            if none_on_bottom:
                input_val = max_val
                if sort_reverse:
                    input_val = ""
            else:
                input_val = ""
                if sort_reverse:
                    input_val = max_val

            # - fill in none types
            for n in notes:
                if n["sort_value"] is None:
                    n["sort_value"] = input_val

            # Sort notes
            notes = sorted(index_dict[t], key=lambda note: note["sort_value"], reverse=sort_reverse)

            # Add to index content
            for n in notes:
                # set link name
                link_name = n["file_key"][:-3]
                if not include_folder_in_link:
                    link_name = n["file_key"][:-3].split("/")[-1]

                # Add to index content
                index_md_content += f"- [[{link_name}|{n['graph_name']}]]\n"
            index_md_content += "\n"

        return index_md_content, index_dict

    def integrate_load(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass

    def integrate_save(self, pb):
        """Used to integrate a module with the current flow, to become deprecated when all elements use modular structure"""
        pass
