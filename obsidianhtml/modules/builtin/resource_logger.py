import json
from datetime import datetime

from ..base_classes import ObsidianHtmlModule


class ResourceLoggerMetaModule(ObsidianHtmlModule):
    """
    This module keeps track of the resource states, and logs them to `log.resources`
    """

    @property
    def requires(self):
        return tuple(["config.yml", "log.resources"])

    @property
    def provides(self):
        return tuple(["log.resources"])

    @property
    def alters(self):
        return tuple()

    def new_resource_listing(self, state):
        return {"history": [], "state": state}

    def new_resource_history_listing(self, module_name, action, result):
        return {"datetime": datetime.now().isoformat(), "module_name": module_name, "action": action, "result": result}

    def setup(self):
        if not hasattr(self, "resources"):
            self.resources = {}

    def run(self, module, result):
        # ensure self.resources exists
        self.setup()

        # don't apply this post-run on own normal run
        if module.module_class_name == self.module_class_name:
            return

        # Update resource listing
        resource_state = "present"
        module_result = "succeeded"
        if result is not None:
            resource_state = "failed"
            module_result = "failed"

        for record in module.read_files.log:
            resource_rel_path = record["resource_rel_path"]

            if resource_rel_path not in self.resources.keys():
                print(f"ERROR: Resource read but not yet written: {resource_rel_path} according to history. This points to a bug.")
                self.resources[resource_rel_path] = self.new_resource_listing(state="error")

            hist = self.new_resource_history_listing(module_name=module.module_name, action="read", result="succeeded")
            hist["datetime"] = record["datetime"]

            self.resources[resource_rel_path]["history"].append(hist)

        for record in module.written_files.log:
            resource_rel_path = record["resource_rel_path"]

            # create resourcelisting
            action = "alter"
            if resource_rel_path not in self.resources.keys():
                self.resources[resource_rel_path] = self.new_resource_listing(state=resource_state)
                action = "create"

            hist = self.new_resource_history_listing(module_name=module.module_name, action=action, result=module_result)
            hist["datetime"] = record["datetime"]

            self.resources[resource_rel_path]["history"].append(hist)

    def finalize(self):
        self.setup()

        verb = {"alter": "altered", "create": "created", "read": "read"}
        output = []
        output.append("Resource log:\n-------------")
        output.append("(arguments.yml, config.yml, and user_config.yml created by setup module)\n")

        # merge all history listings together, so that we can sort on time for chronological order
        all_hist = []
        for resource_path in self.resources.keys():
            for hist in self.resources[resource_path]["history"]:
                hist["resource_path"] = resource_path
                all_hist.append(hist)

        # sort
        all_hist_sorted = sorted(all_hist, key=lambda d: d["datetime"])  # , reverse=True)

        # compile log
        for hist in all_hist_sorted:
            if hist["action"] == "failed":
                output.append(f"[{hist['datetime']}] {hist['module_name']:20} failed;    {hist['resource_path']} [state=FAILED]")
            else:
                output.append(f"[{hist['datetime']}] {hist['module_name']:20} {verb[hist['action']]:10} {hist['resource_path']:20}")

        # write to resource
        output.append("\n(log.resources created by resource_logger module)")
        self.modfile("log.resources", contents="\n".join(output)).write()

        if self.verbose_enough("debug", self.verbosity):
            output = ["writing to `log.resources`:\n"] + output + [""]
            self.print("DEBUG", "\n".join(output), force=True)

    def allow_post_module(self, meta_module):
        """Return True if post module is allowed to run after this one, else return False"""
        if meta_module.module_class_name == self.module_class_name:
            return False
        return True
