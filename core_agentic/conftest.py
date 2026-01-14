import pytest

from src.main.utilities.helper.helper_common import HelperInterface


class TestStatsPlugin:
    def __init__(self):
        self.total_tests = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = 0
        self.executed = 0

    def pytest_collection_finish(self, session):
        """Called after collection is completed"""
        # Filter to only count actual test functions, not fixtures
        test_items = [item for item in session.items if item.nodeid.split("::")[-1].startswith('test_')]
        self.total_tests = len(test_items)

        print(f"\n{'=' * 60}")
        print(f"🚀 STARTING TEST EXECUTION")
        print(f"📊 Total tests to execute: {self.total_tests}")
        print(f"{'=' * 60}")

        if self.total_tests > 0:
            print(f"📋 TEST LIST:")
            for i, item in enumerate(test_items, 1):
                test_name = item.nodeid.split("::")[-1]  # Get just the test function name
                file_path = item.nodeid.split("::")[0]  # Get the file path
                print(f"   {i:2d}. {test_name} ({file_path})")
            print(f"{'=' * 60}")

    def pytest_runtest_logreport(self, report):
        """Called after each test phase (setup, call, teardown)"""
        # Only process the 'call' phase to avoid counting setup/teardown
        # Also ensure we're only counting actual test functions, not fixtures
        if report.when == 'call' and hasattr(report, 'nodeid') and '::test_' in report.nodeid:
            self.executed += 1

            if report.passed:
                self.passed += 1
                status = "✅ PASSED"
                color = "\033[92m"  # Green
            elif report.failed:
                self.failed += 1
                status = "❌ FAILED"
                color = "\033[91m"  # Red
            elif report.skipped:
                self.skipped += 1
                status = "⏭️ SKIPPED"
                color = "\033[93m"  # Yellow
            else:
                self.errors += 1
                status = "💥 ERROR"
                color = "\033[95m"  # Magenta

            reset_color = "\033[0m"

            # Display progress after each test
            progress_bar = self._create_progress_bar()
            print(f"\n{'-' * 60}")
            print(f"{color}{status}: {report.nodeid.split('::')[-1]}{reset_color}")
            print(f"📈 Progress: [{self.executed}/{self.total_tests}] {progress_bar}")
            print(f"📊 Stats: ✅ {self.passed} | ❌ {self.failed} | ⏭️ {self.skipped} | 💥 {self.errors}")
            print(f"{'-' * 60}")

    def _create_progress_bar(self, width=30):
        """Create a visual progress bar"""
        if self.total_tests == 0:
            return "[No tests]"

        progress = self.executed / self.total_tests
        filled = int(progress * width)
        bar = "█" * filled + "▒" * (width - filled)
        percentage = int(progress * 100)
        return f"{bar} {percentage}%"

    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        """Called at the end of the test session"""
        print(f"\n{'=' * 60}")
        print(f"🏁 TEST EXECUTION COMPLETED")
        print(f"{'=' * 60}")
        print(f"📊 FINAL RESULTS:")
        print(f"   Total tests executed: {self.executed}")
        print(f"   ✅ Passed: {self.passed}")
        print(f"   ❌ Failed: {self.failed}")
        print(f"   ⏭️ Skipped: {self.skipped}")
        print(f"   💥 Errors: {self.errors}")

        if self.total_tests > 0:
            success_rate = (self.passed / self.executed * 100) if self.executed > 0 else 0
            print(f"   📈 Success Rate: {success_rate:.1f}%")

        print(f"{'=' * 60}")


# Global instance of the plugin
test_stats_plugin = TestStatsPlugin()


def pytest_configure(config):
    """Register the plugin"""
    config.pluginmanager.register(test_stats_plugin, "test_stats")


# @pytest.fixture(scope="session", autouse=True)
# def setup_once_before_all_tests():
#     print("\n=== Setup before all tests ===")
#     helper = HelperInterface()
#     helper.getLatestTestCases()
#     yield
#     print("\n=== Teardown after all tests ===")
    # Place your teardown code here (optional)
