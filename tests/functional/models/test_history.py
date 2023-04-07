from datetime import datetime, timedelta
import unittest

from tests.helper import TestHelper


class TestHistory(unittest.TestCase):
    helper = None
    balena = None

    @classmethod
    def setUpClass(cls):
        cls.helper = TestHelper()
        cls.balena = cls.helper.balena

    def tearDown(self):
        # Wipe all apps after every test case.
        self.helper.wipe_application()

    def _test_device_history(self, test_model):
        app_info = self.helper.create_multicontainer_app()

        def check_device_history(device_history):
            device_history.sort(key=lambda entry: entry["created_at"], reverse=True)
            # this entry should be the newest and have no end_timestamp => not ended history record
            self.assertIsNone(device_history[0]["end_timestamp"])
            # now check
            for history_entry in device_history:
                self.assertEqual(
                    history_entry["tracks__device"]["__id"], app_info["device"]["id"]
                )
                self.assertEqual(history_entry["uuid"], app_info["device"]["uuid"])
                self.assertEqual(
                    history_entry["belongs_to__application"]["__id"],
                    app_info["app"]["id"],
                )

        # should set the device to track the current application release.
        self.balena.models.device.set_to_release(
            app_info["device"]["uuid"], app_info["old_release"]["commit"]
        )

        # get by device uuid
        device_history = test_model.get_all_by_device(app_info["device"]["uuid"])
        check_device_history(device_history)

        # get by device id
        device_history = test_model.get_all_by_device(app_info["device"]["id"])
        check_device_history(device_history)

        # get by application id
        device_history = test_model.get_all_by_application(app_info["app"]["id"])
        check_device_history(device_history)

        with self.assertRaises(Exception) as cm:
            test_model.get_all_by_device(app_info["device"]["uuid"] + "toManyDigits")
        self.assertIn("Invalid parameter:", cm.exception.message)

        for test_set in [
            {"method": "get_all_by_device", "by": "device"},
            {"method": "get_all_by_application", "by": "app"},
        ]:
            method_under_test = getattr(test_model, test_set["method"])
            device_history = method_under_test(app_info[test_set["by"]]["id"])

            check_device_history(device_history)

            # set time range to return device history entries
            device_history = method_under_test(
                app_info[test_set["by"]]["id"],
                fromDate=datetime.utcnow() + timedelta(days=-10),
                toDate=datetime.utcnow() + timedelta(days=+1),
            )
            check_device_history(device_history)

            # set time range to return now data
            device_history = method_under_test(
                app_info[test_set["by"]]["id"],
                fromDate=datetime.utcnow() + timedelta(days=-3000),
                toDate=datetime.utcnow() + timedelta(days=-2000),
            )
            self.assertEqual(len(device_history), 0)

            for invalidParameter in [[], {}, "invalid", 1]:
                with self.assertRaises(Exception) as cm:
                    device_history = method_under_test(
                        app_info[test_set["by"]]["id"], fromDate=invalidParameter
                    )
                self.assertIn("Invalid parameter:", cm.exception.message)

                with self.assertRaises(Exception) as cm:
                    device_history = method_under_test(
                        app_info[test_set["by"]]["id"], toDate=invalidParameter
                    )
                self.assertIn("Invalid parameter:", cm.exception.message)

    def test_device_model_get_device_history(self):
        self._test_device_history(self.balena.models.device.history)

    def test_history_model_get_device_history(self):
        self._test_device_history(self.balena.models.history.device_history)


if __name__ == "__main__":
    unittest.main()
