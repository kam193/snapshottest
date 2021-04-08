import os

import pytest

from snapshottest import Snapshot
from snapshottest.config import get_global_config
from snapshottest.error import SnapshotError
from snapshottest.module import SnapshotModule


class TestSnapshotModuleLoading(object):
    def test_load_not_yet_saved(self, tmpdir):
        filepath = tmpdir.join("snap_new.py")
        assert not filepath.check()  # file does not exist
        module = SnapshotModule("tests.snapshots.snap_new", str(filepath))
        snapshots = module.load_snapshots()
        assert isinstance(snapshots, Snapshot)

    def test_load_missing_package(self, tmpdir):
        filepath = tmpdir.join("snap_import.py")
        filepath.write_text("import missing_package\n", "utf-8")
        module = SnapshotModule("tests.snapshots.snap_import", str(filepath))
        with pytest.raises(ImportError):
            module.load_snapshots()

    def test_load_corrupted_snapshot(self, tmpdir):
        filepath = tmpdir.join("snap_error.py")
        filepath.write_text("<syntax error>\n", "utf-8")
        module = SnapshotModule("tests.snapshots.snap_error", str(filepath))
        with pytest.raises(SyntaxError):
            module.load_snapshots()


class TestSnapshotModuleSaving:
    def test_save_file_and_init_not_exists(self, tmpdir):
        filepath = tmpdir.join("new_dir", "snap_new.py")
        assert not filepath.check()
        module = SnapshotModule("tests.snapshots.snap_new", str(filepath))
        module["test_snapshot"] = "new value"

        module.save()

        assert filepath.check()
        assert tmpdir.join("new_dir", "__init__.py").check()

    def test_save_file_not_exists(self, tmpdir):
        filepath = tmpdir.join("a_dir", "snap_new.py")
        os.mkdir(str(tmpdir.join("a_dir")))
        module = SnapshotModule("tests.snapshots.snap_new", str(filepath))
        module["test_snapshot"] = "new value"

        module.save()

        assert filepath.check()
        assert tmpdir.join("a_dir", "__init__.py").check()

    def test_save_and_load_snapshot(self, tmpdir):
        filepath = tmpdir.join("snap_new.py")
        module = SnapshotModule("tests.snapshots.snap_new", str(filepath))
        module["test_snapshot"] = "new_value"
        module.save()

        file_moved = tmpdir.join("snap_moved.py")
        os.rename(str(filepath), str(file_moved))
        module_2 = SnapshotModule("tests.snapshots.snap_moved", str(file_moved))
        assert module_2["test_snapshot"] == "new_value"

    def test_fail_on_validating_before_close_when_unvisited_disabled(
        self, tmpdir, make_config
    ):
        filepath = tmpdir.join("snap_new.py")
        config = make_config({"allow_unvisited": False})
        module = SnapshotModule(
            "tests.snapshots.snap_new", str(filepath), config=config
        )
        module["test_snapshot"] = "new_value"

        with pytest.raises(SnapshotError):
            module.validate_before_close()


class TestSnapshotModuleBeforeWriteCallback(object):
    def test_callback_are_applied_to_data(self, tmpdir):
        filepath = tmpdir.join("snap_module.py")

        SnapshotModule.register_before_file_write_callback(
            lambda data: "# a comment \n{}".format(data)
        )
        SnapshotModule.register_before_file_write_callback(
            lambda data: "# and another \n{}".format(data)
        )

        module = SnapshotModule("tests.snapshots.snap_module", str(filepath))
        module["my_test"] = "result"

        module.save()

        with open(str(filepath)) as snap_file:
            result = snap_file.read()

        assert result.startswith("# and another \n# a comment")
        assert "my_test" in result

    def test_can_clear_callback(self, tmpdir):
        filepath = tmpdir.join("snap_module.py")

        SnapshotModule.register_before_file_write_callback(
            lambda data: "# a comment \n{}".format(data)
        )

        module = SnapshotModule("tests.snapshots.snap_module", str(filepath))
        module["my_test"] = "result"

        SnapshotModule.clear_before_file_write_callbacks()
        module.save()

        with open(str(filepath)) as snap_file:
            result = snap_file.read()

        assert "# a comment" not in result
        assert "my_test" in result


class TestSnapshotModuleConfig:
    def test_loads_default_config(self):
        module = SnapshotModule("a", "b")
        assert module.config is get_global_config()["snapshottest"]

    def test_load_passed_config(self, make_config):
        module = SnapshotModule("", "", make_config({"test_config": "value"}))
        assert module.config["test_config"] == "value"
