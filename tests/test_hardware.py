import os
import tempfile
import unittest

from fantastic import hwmon
from fantastic.hardware import Hardware
from fantastic.i18n import render

from fakesys import FakeSys, build_desktop

NCT_PWM1 = "nct6798@nct6775.656/pwm1"
KRAKEN_PUMP = "x53@usb-1-5/pwm1"


class HardwareTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fs, self.chips = build_desktop(self._tmp.name)
        self.hw = Hardware(sysfs_root=self._tmp.name, use_nvidia=False)

    def tearDown(self):
        self._tmp.cleanup()

    def test_stable_ids_and_identification(self):
        devices = {d["id"]: d for d in self.hw.snapshot("en")["devices"]}
        self.assertEqual(devices["x53@usb-1-5"]["name"], "NZXT Kraken X53 / X63 / X73")
        self.assertEqual(devices["x53@usb-1-5"]["kind"], "aio")
        self.assertIn("USB 1e71:2007", devices["x53@usb-1-5"]["details"])
        self.assertEqual(devices["nct6798@nct6775.656"]["name"], "Motherboard (Nuvoton NCT6798)")
        self.assertIn("ROG STRIX X570-I GAMING", devices["nct6798@nct6775.656"]["details"])
        self.assertIn("k10temp@pci-0000:00:18.3", devices)
        # The AIO comes before the motherboard, then the processor.
        self.assertEqual(list(devices)[0], "x53@usb-1-5")

    def test_fans(self):
        fans = self.hw.fans
        self.assertEqual(set(fans), {NCT_PWM1, "nct6798@nct6775.656/pwm2", KRAKEN_PUMP,
                                     "asusec@asus-ec-sensors/fan1"})
        self.assertTrue(fans[NCT_PWM1].controllable)
        self.assertFalse(fans["asusec@asus-ec-sensors/fan1"].controllable)
        self.assertEqual(render(fans[KRAKEN_PUMP].label, "en"), "Pump")
        self.assertEqual(render(fans[KRAKEN_PUMP].label, "fr"), "Pompe")
        self.assertEqual(fans[KRAKEN_PUMP].min_percent, 20)
        self.assertEqual(fans[NCT_PWM1].read(), {"rpm": 900, "percent": 50, "mode": "auto"})

    def test_read_only_pwm_is_not_controllable(self):
        os.chmod(os.path.join(self._tmp.name, self.chips["nct"], "pwm2"), 0o444)
        self.hw.scan()
        self.assertFalse(self.hw.fans["nct6798@nct6775.656/pwm2"].controllable)

    def test_unplugged_sensor_is_hidden(self):
        self.assertNotIn("asusec@asus-ec-sensors/temp1", self.hw.temps)

    def test_hottest_considers_cpu_and_gpu_only(self):
        # SYSTIN (motherboard, 35 °C) and the coolant (29.6 °C) are ignored: only Tctl counts.
        celsius, source = self.hw.hottest()
        self.assertEqual(celsius, 45.0)
        self.assertTrue(source.endswith("/ Tctl"))

    def test_apply_and_restore(self):
        fan = self.hw.fans[NCT_PWM1]
        fan.apply(40)
        self.assertEqual(self.fs.read(f"{self.chips['nct']}/pwm1"), "102")
        self.assertEqual(self.fs.read(f"{self.chips['nct']}/pwm1_enable"), "1")
        self.assertTrue(fan.is_applied(40))
        self.assertFalse(fan.is_applied(60))
        fan.restore(5)
        self.assertEqual(self.fs.read(f"{self.chips['nct']}/pwm1_enable"), "5")

    def test_full_speed_reported_as_no_control_counts_as_applied(self):
        fan = self.hw.fans[NCT_PWM1]
        fan.apply(100)
        self.fs.write(f"{self.chips['nct']}/pwm1_enable", 0)  # what nct6775 reports at 255 in manual mode
        self.assertTrue(fan.is_applied(100))
        self.assertFalse(fan.is_applied(60))

    def test_restore_never_leaves_nuvoton_at_full_speed(self):
        fan = self.hw.fans[NCT_PWM1]
        fan.apply(40)
        fan.restore(0)  # a bogus "original" recorded while the fan was held at 255
        self.assertEqual(self.fs.read(f"{self.chips['nct']}/pwm1_enable"), "5")

    def test_restore_unknown_original_uses_driver_default(self):
        fan = self.hw.fans[NCT_PWM1]
        fan.apply(40)
        fan.restore(None)
        self.assertEqual(self.fs.read(f"{self.chips['nct']}/pwm1_enable"), "5")

    def test_kraken_auto_programs_curve(self):
        fan = self.hw.fans[KRAKEN_PUMP]
        fan.apply(60)
        fan.restore(0)
        base = self.chips["kraken"]
        self.assertEqual(self.fs.read(f"{base}/pwm1_enable"), "2")
        point = lambda celsius: int(self.fs.read(f"{base}/temp1_auto_point{celsius - 19}_pwm"))
        self.assertEqual(point(20), hwmon.percent_to_raw(30))
        self.assertEqual(point(30), hwmon.percent_to_raw(30))
        self.assertEqual(point(40), hwmon.percent_to_raw(65))
        self.assertEqual(point(59), 255)

    def test_hint_when_superio_driver_missing(self):
        with tempfile.TemporaryDirectory() as root:
            fs = FakeSys(root)
            fs.write("class/dmi/id/board_vendor", "ASUSTeK COMPUTER INC.")
            fs.write("class/dmi/id/board_name", "PRIME B550-PLUS")
            fs.write("class/dmi/id/chassis_type", "3")
            hw = Hardware(sysfs_root=root, use_nvidia=False)
            self.assertEqual(len(hw.hints), 1)
            self.assertEqual(hw.hints[0]["command"], "sudo modprobe nct6775")
        self.assertEqual(self.hw.hints, [])

    def test_interpolate(self):
        curve = [(20, 30), (30, 40), (50, 100)]
        self.assertEqual(hwmon.interpolate(curve, 10), 30)
        self.assertEqual(hwmon.interpolate(curve, 25), 35)
        self.assertEqual(hwmon.interpolate(curve, 40), 70)
        self.assertEqual(hwmon.interpolate(curve, 80), 100)


if __name__ == "__main__":
    unittest.main()
