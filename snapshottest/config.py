from configparser import ConfigParser

DEFAULTS = {"allow_create": True, "allow_unvisited": True}

_config = None


def get_global_config() -> ConfigParser:
    global _config
    if not _config:
        _config = ConfigParser(DEFAULTS)
        _config.add_section("snapshottest")
        _config.read("snapshottest.cfg")
    return _config
