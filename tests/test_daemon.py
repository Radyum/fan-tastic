import getpass
import json
import logging
import os
import tempfile
import threading
import unittest

from fantastic import daemon, i18n
from fantastic.client import Client, DaemonError
from fantastic.daemon import DEFAULT_CONFIG, FanService, ServiceError, make_server
from fantastic.hardware import Hardware

from fakesys import build_desktop

NCT_PWM1 = "nct6798@nct6775.656/pwm1"
KRAKEN_PUMP = "x53@usb-1-5/pwm1"


def setUpModule():
    logging.disable(logging.CRITICAL)


def tearDownModule():
    logging.disable(logging.NOTSET)


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self._tmp.name, "sys")
        self.fs, self.chips = build_desktop(self.root)
        self.state = os.path.join(self._tmp.name, "state.json")
        self.service = self._new_service()

    def tearDown(self):
        self._tmp.cleanup()

    def _new_service(self, **config):
        cfg = {**DEFAULT_CONFIG, "allowed_users": [getpass.getuser()], **config}
        return FanService(Hardware(sysfs_root=self.root, use_nvidia=False), cfg, self.state)

    def nct(self, attr):
        return self.fs.read(f"{self.chips['nct']}/{attr}")

    def test_set_records_original_and_persists(self):
        self.assertEqual(self.service.set_speed(NCT_PWM1, 40), 40)
        self.assertEqual((self.nct("pwm1"), self.nct("pwm1_enable")), ("102", "1"))
        with open(self.state) as f:
            state = json.load(f)
        self.assertEqual(state["targets"], {NCT_PWM1: 40})
        self.assertEqual(state["originals"], {NCT_PWM1: 5})

    def test_auto_restores_original_mode(self):
        self.service.set_speed(NCT_PWM1, 40)
        self.service.set_auto(NCT_PWM1)
        self.assertEqual(self.nct("pwm1_enable"), "5")
        self.assertEqual(self.service.targets, {})

    def test_target_is_clamped_to_minimum(self):
        self.assertEqual(self.service.set_speed(KRAKEN_PUMP, 5), 20)
        self.assertEqual(self.service.set_speed(NCT_PWM1, 150), 100)

    def test_set_all_respects_minimums(self):
        applied, errors = self.service.set_all(10)
        self.assertEqual(errors, {})
        # The EC fan is read-only, the pump is bounded to 20%.
        self.assertEqual(applied, {NCT_PWM1: 10, "nct6798@nct6775.656/pwm2": 10, KRAKEN_PUMP: 20})
        self.assertEqual(self.service.set_all(100)[0][KRAKEN_PUMP], 100)

    def test_auto_all(self):
        self.service.set_all(100)
        self.assertEqual(self.service.auto_all(), {})
        self.assertEqual(self.service.targets, {})
        self.assertEqual(self.nct("pwm1_enable"), "5")
        self.assertEqual(self.fs.read(f"{self.chips['kraken']}/pwm1_enable"), "2")

    def test_hide_and_unhide(self):
        self.service.set_hidden("asusec@asus-ec-sensors/fan1", True)  # read-only fans can be hidden too
        self.service.set_hidden(NCT_PWM1, True)
        hidden = {f["id"] for f in self.service.status()["fans"] if f["hidden"]}
        self.assertEqual(hidden, {NCT_PWM1, "asusec@asus-ec-sensors/fan1"})
        self.service.set_hidden(NCT_PWM1, False)
        self.assertEqual(self.service.hidden, {"asusec@asus-ec-sensors/fan1"})
        self.assertEqual(self.service.unhide_all(), 1)
        self.assertEqual(self.service.hidden, set())
        with self.assertRaises(ServiceError):
            self.service.set_hidden("missing/pwm9", True)

    def test_hidden_fans_are_skipped_by_set_all_but_not_auto_all(self):
        self.service.set_speed(NCT_PWM1, 40)
        self.service.set_hidden(NCT_PWM1, True)
        applied, _ = self.service.set_all(100)
        self.assertNotIn(NCT_PWM1, applied)
        self.assertEqual(self.nct("pwm1"), "102")  # the hidden fan's setting is unchanged
        self.service.auto_all()
        self.assertEqual(self.nct("pwm1_enable"), "5")

    def test_profiles(self):
        self.service.set_speed(NCT_PWM1, 40)
        self.service.save_profile("Quiet")
        self.service.set_speed(NCT_PWM1, 100)
        self.service.set_auto(KRAKEN_PUMP)
        self.service.set_speed("nct6798@nct6775.656/pwm2", 70)
        self.assertEqual(self.service.apply_profile("Quiet"), {})
        # fan 1 back to 40%, fan 2 and the pump back to what they were when saved (automatic)
        self.assertEqual((self.nct("pwm1"), self.nct("pwm1_enable")), ("102", "1"))
        self.assertEqual(self.nct("pwm2_enable"), "5")
        self.assertEqual(self.service.targets, {NCT_PWM1: 40})
        self.assertEqual(self.service.status()["profiles"], ["Quiet"])
        self.assertEqual(self._new_service().profiles["Quiet"][NCT_PWM1], 40)  # persisted
        self.service.delete_profile("Quiet")
        self.assertEqual(self.service.profiles, {})

    def test_profile_validation(self):
        for bad in ("", "   ", "x" * 11, None, 5):
            with self.assertRaises(ServiceError):
                self.service.save_profile(bad)
        self.service.save_profile("1234567890")  # exactly 10 characters is fine
        with self.assertRaises(ServiceError):
            self.service.apply_profile("nope")
        with self.assertRaises(ServiceError):
            self.service.delete_profile("nope")
        for i in range(daemon.MAX_PROFILES - 1):
            self.service.save_profile(f"p{i}")
        with self.assertRaises(ServiceError):
            self.service.save_profile("one more")
        self.service.save_profile("p0")  # overwriting an existing profile is still allowed

    def test_hidden_persists(self):
        self.service.set_hidden(NCT_PWM1, True)
        self.assertEqual(self._new_service().hidden, {NCT_PWM1})

    def test_read_only_and_unknown_fans_are_rejected(self):
        with self.assertRaises(ServiceError):
            self.service.set_speed("asusec@asus-ec-sensors/fan1", 50)
        with self.assertRaises(ServiceError):
            self.service.set_speed("missing/pwm9", 50)

    def test_lost_setting_is_reapplied(self):
        self.service.set_speed(NCT_PWM1, 40)
        self.fs.write(f"{self.chips['nct']}/pwm1_enable", 5)  # e.g. the BIOS takes over after a suspend
        self.service.tick()
        self.assertEqual(self.nct("pwm1_enable"), "1")
        self.assertEqual(self.service.originals[NCT_PWM1], 5)

    def test_failsafe(self):
        self.service.set_speed(NCT_PWM1, 30)
        self.fs.write(f"{self.chips['k10']}/temp1_input", 92000)
        self.service.tick()
        self.assertTrue(self.service.failsafe)
        self.assertEqual(self.nct("pwm1"), "255")
        self.fs.write(f"{self.chips['k10']}/temp1_input", 85000)  # hysteresis: still active
        self.service.tick()
        self.assertTrue(self.service.failsafe)
        self.fs.write(f"{self.chips['k10']}/temp1_input", 70000)
        self.service.tick()
        self.assertFalse(self.service.failsafe)
        self.assertEqual(self.nct("pwm1"), "76")

    def test_settings_survive_restart(self):
        self.service.set_speed(NCT_PWM1, 40)
        self.service.rename(NCT_PWM1, "  Radiator  ")
        self.service.restore_all()
        self.assertEqual(self.nct("pwm1_enable"), "5")
        service = self._new_service()
        service.tick()
        self.assertEqual((self.nct("pwm1"), self.nct("pwm1_enable")), ("102", "1"))
        fan = next(f for f in service.status()["fans"] if f["id"] == NCT_PWM1)
        self.assertEqual((fan["name"], fan["target"]), ("Radiator", 40))


class SocketTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = os.path.join(self._tmp.name, "sys")
        self.fs, self.chips = build_desktop(root)
        config = {**DEFAULT_CONFIG, "allowed_users": [], "allowed_groups": []}
        self.service = FanService(Hardware(sysfs_root=root, use_nvidia=False), config,
                                  os.path.join(self._tmp.name, "state.json"))
        self.path = os.path.join(self._tmp.name, "fantastic.sock")
        self.server = make_server(self.path, self.service)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.client = Client(self.path)

    def tearDown(self):
        self.client.close()
        self.server.shutdown()
        self.server.server_close()
        self._tmp.cleanup()

    def test_status_is_public(self):
        data = self.client.call("status")
        self.assertIn(NCT_PWM1, [f["id"] for f in data["fans"]])
        self.assertEqual(data["authorized"], os.geteuid() == 0)

    @unittest.skipIf(os.geteuid() == 0, "root is always authorized")
    def test_writes_require_authorization(self):
        with self.assertRaises(DaemonError):
            self.client.call("set", fan=NCT_PWM1, percent=50)
        self.service.config["allowed_users"] = [getpass.getuser()]
        self.client.close()  # authorization is evaluated on connection
        self.assertEqual(self.client.call("set", fan=NCT_PWM1, percent=50)["applied"], 50)

    def test_invalid_request(self):
        with self.assertRaises(DaemonError):
            self.client.call("unknown")

    def test_texts_follow_the_requested_language(self):
        self.client.close()
        sock = Client(self.path)
        try:
            for lang, device_name, pump, error in (
                    ("en", "Motherboard (Nuvoton NCT6798)", "Pump", "unknown command: nope"),
                    ("fr", "Carte mère (Nuvoton NCT6798)", "Pompe", "commande inconnue : nope")):
                i18n.set_language(lang)
                data = sock.call("status")
                names = {d["id"]: d["name"] for d in data["devices"]}
                fans = {f["id"]: f for f in data["fans"]}
                self.assertEqual(names["nct6798@nct6775.656"], device_name)
                self.assertEqual(fans[KRAKEN_PUMP]["label"], pump)
                with self.assertRaises(DaemonError) as caught:
                    sock.call("nope")
                self.assertEqual(str(caught.exception), error)
        finally:
            i18n.set_language("en")
            sock.close()


if __name__ == "__main__":
    unittest.main()
