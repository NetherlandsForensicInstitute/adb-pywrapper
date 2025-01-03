1.0.3
-----

- 23: Fix broken parsing of snapshot list when partial snapshots exist

1.0.2
-----

- 20: correctly pull files when name contains a space

1.0.1
-----

- implemented optionally specified wait time for wait_for_device functionality

1.0.0
-----

- Change name to adb-pywrapper and add action to release to PyPi

0.8
---

- Removed lru_cache function that caused get_prop output to be cached which is not advisable since these properties can
  change

0.7
---

- Improved the documentation of all the functions and the README.md

0.6
---

- Introduced get_device_status functionality to get the device status using a static function

0.5
---

- Introduced snapshot_list, load, save and delete for emulator snapshot interaction

0.4
---

- Introduced get-state function to get the current status of a connected device. Example: device, offline, fastboot

0.3
---

- Introduced emu avd function for emulator communication trough adb

0.2
---

- Introduced get_prop function from OSS project

0.1
---

- Initial release based on ADB functions introduced in the Appium project    
