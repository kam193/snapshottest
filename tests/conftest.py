from configparser import ConfigParser

from pytest import fixture

from snapshottest.config import DEFAULTS

pytest_plugins = "pytester"


@fixture
def make_config():
    def _inner(override: dict = None):
        config = ConfigParser(DEFAULTS)
        config.add_section("snapshottest")
        if override:
            config.read_dict({"snapshottest": override})
        return config

    return _inner
