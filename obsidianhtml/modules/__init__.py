from . import builtin
from .base_classes import ObsidianHtmlModule

import json, sys
import inspect, importlib
from pkgutil import iter_modules

# Get all classes that extend parent_class defined in given module or its submodules
def get_builtin_module_aliases(module, parent_class):
    builtin_module_aliases = {}

    # find submodules and recurse for those
    if hasattr(module, '__path__'):
        for submodule in iter_modules(module.__path__):            
            # import submodule and then get reference
            importlib.import_module('.'+submodule.name, module.__name__)
            submodule = sys.modules[f'{module.__name__}.{submodule.name}']

            # recurse and merge output
            _builtin_module_aliases = get_builtin_module_aliases(submodule, parent_class)
            for key in _builtin_module_aliases:
                builtin_module_aliases[key] = _builtin_module_aliases[key]
        
    # find classes in current (sub)module
    all_members = inspect.getmembers(module)
    for name, obj in all_members:
        if inspect.isclass(obj):
            # test that the found class is a subclass of parent_class
            if issubclass(obj, parent_class) and parent_class != obj:
                builtin_module_aliases[obj.friendly_name()] = obj

    return builtin_module_aliases

    # defined_functions = [obj for name, obj in all_members if inspect.isfunction(obj) and inspect.getmodule(obj) == module]
    # return defined_functions

builtin_module_aliases = get_builtin_module_aliases(builtin, ObsidianHtmlModule)

