import inspect
import unittest

from .diff import PrettyDiff
from .error import UnvisitedSnapshotsLeftError
from .module import SnapshotModule, SnapshotTest
from .reporting import diff_report


class UnitTestSnapshotTest(SnapshotTest):
    def __init__(self, test_class, test_id, test_filepath, should_update, assertEqual):
        self.test_class = test_class
        self.test_id = test_id
        self.test_filepath = test_filepath
        self.assertEqual = assertEqual
        self.should_update = should_update
        super(UnitTestSnapshotTest, self).__init__()

    @property
    def module(self):
        return SnapshotModule.get_module_for_testpath(self.test_filepath)

    @property
    def update(self):
        return self.should_update

    def assert_equals(self, value, snapshot):
        self.assertEqual(value, snapshot)

    @property
    def test_name(self):
        class_name = self.test_class.__name__
        test_name = self.test_id.split(".")[-1]
        return "{}::{} {}".format(class_name, test_name, self.curr_snapshot)


# Inspired by https://gist.github.com/twolfson/13f5f5784f67fd49b245
class TestCase(unittest.TestCase):

    snapshot_should_update = False
    final_registered = False

    @classmethod
    def final(cls):
        for module in SnapshotModule.get_modules():
            try:
                module.validate_before_close()
            except UnvisitedSnapshotsLeftError:
                # Temporary implementation to present the idea
                if module.config.getboolean("list_unvisited"):
                    print("-" * 80)
                    print("Following snaphots left unvisited:")
                    for _module in SnapshotModule.get_modules():
                        unvisited = "\n".join(_module.unvisited_snapshots)
                        if unvisited:
                            print(unvisited)
                    print("-" * 80)
                raise

    @classmethod
    def setUpClass(cls):
        """On inherited classes, run our `setUp` method"""
        cls._snapshot_tests = []
        cls._snapshot_file = inspect.getfile(cls)

        if cls is not TestCase and cls.setUp is not TestCase.setUp:
            orig_setUp = cls.setUp
            orig_tearDown = cls.tearDown

            def setUpOverride(self, *args, **kwargs):
                TestCase.setUp(self)
                return orig_setUp(self, *args, **kwargs)

            def tearDownOverride(self, *args, **kwargs):
                TestCase.tearDown(self)
                return orig_tearDown(self, *args, **kwargs)

            cls.setUp = setUpOverride
            cls.tearDown = tearDownOverride

        if not cls.final_registered:
            setattr(unittest.TestResult, "stopTestRun", cls.final)
            cls.final_registered = True

        super(TestCase, cls).setUpClass()

    def comparePrettyDifs(self, obj1, obj2, msg):
        if not (obj1 == obj2):
            raise self.failureException("\n".join(diff_report(obj1, obj2)))

    @classmethod
    def tearDownClass(cls):
        if cls._snapshot_tests:
            module = SnapshotModule.get_module_for_testpath(cls._snapshot_file)
            module.save()
        super(TestCase, cls).tearDownClass()

    def setUp(self):
        """Do some custom setup"""
        self.addTypeEqualityFunc(PrettyDiff, self.comparePrettyDifs)
        self._snapshot = UnitTestSnapshotTest(
            test_class=self.__class__,
            test_id=self.id(),
            test_filepath=self._snapshot_file,
            should_update=self.snapshot_should_update,
            assertEqual=self.assertEqual,
        )
        self._snapshot_tests.append(self._snapshot)
        SnapshotTest._current_tester = self._snapshot

    def tearDown(self):
        """Do some custom setup"""
        SnapshotTest._current_tester = None
        self._snapshot = None

    def assert_match_snapshot(self, value, name=""):
        self._snapshot.assert_match(value, name=name)

    assertMatchSnapshot = assert_match_snapshot


def tearDownModule():
    print("module")
