from functools import cache


@cache
def get_config_cached(config_dict, path: str):
    return get_config(config_dict, path)


def get_config(config_dict, path: str, fail_on_missing=True):
    keys = [x for x in path.strip().split("/") if x != ""]

    value = config_dict
    path = []
    for key in keys:
        path.append(key)
        try:
            value = value[key]
        except KeyError as e:
            if fail_on_missing:
                raise Exception(f"INTERNAL ERROR: Config setting '{'/'.join(path)}' not found in config.")
            else:
                return e
    return value
