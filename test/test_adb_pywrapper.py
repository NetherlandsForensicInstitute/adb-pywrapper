import os.path
import subprocess
import unittest
from unittest.mock import patch, Mock

from adb_pywrapper.adb_device import AdbDevice
from adb_pywrapper.adb_result import AdbResult

PROCESS = subprocess.run('echo hello', shell=True, capture_output=True)
MOCK_SUCCESSFULLY_PULLED_FILE = ['abc.apk', 'bla.jpg']
PRINT_MOCK_DEBUG = False


class MockAdbResult(AdbResult):
    def __init__(self, stdout: str = '', stderr: str = '', success: bool = True):
        super().__init__(PROCESS)
        self.stdout = stdout
        self.stderr = stderr
        self.success = success


# code to mock calls to the adb command
ADB_MOCK_SETTINGS = {
    'MOCK_ADB_RESULTS': [MockAdbResult(stdout='hello world', stderr='hello errworld')],
    'NEXT_MOCK_ADB_RESULT': 0
}
ADB_CALLS_ARGUMENT_HISTORY: [str] = []


def assert_not_called_with(self, *args, **kwargs):
    try:
        self.assert_called_with(*args, **kwargs)
    except AssertionError:
        return
    raise AssertionError('Expected %s to not have been called.' % self._format_mock_call_signature(args, kwargs))


Mock.assert_not_called_with = assert_not_called_with


def mock_adb_call(arguments_string, timeout: int = None):
    """
    Method that will mock a call to the adb command. Instead of executing the adb command, this method will return
    the next mock AdbResult object stored in ADB_MOCK_SETTINGS.
    ADB_MOCK_SETTINGS['MOCK_ADB_RESULTS'] contains a list of mock AdbResults. Each time this method is called, the next
    entry in this list will be returned. When the end of the list is reached, the first entry will be returned again, so
    if you want each adb call to return the sameresult indefinitely, you just need to store 1 AdbResult in
    ADB_MOCK_SETTINGS.
    This method also stores the adb arguments in ADB_CALLS_ARGUMENT_HISTORY, so your tests can check what adb calls are
    done.

    :param arguments_string: the adb command arguments.
    :param timeout: not used here, this mock method returns results immediately.
    :return: the next mock result
    """
    if PRINT_MOCK_DEBUG:
        print(f'mock adb is being called with arguments `{arguments_string}`')
    ADB_CALLS_ARGUMENT_HISTORY.append(arguments_string)
    current_mock_index = ADB_MOCK_SETTINGS['NEXT_MOCK_ADB_RESULT']
    ADB_MOCK_SETTINGS['NEXT_MOCK_ADB_RESULT'] += 1
    ADB_MOCK_SETTINGS['NEXT_MOCK_ADB_RESULT'] %= len(ADB_MOCK_SETTINGS['MOCK_ADB_RESULTS'])
    return ADB_MOCK_SETTINGS['MOCK_ADB_RESULTS'][current_mock_index]


class TestAdb(unittest.TestCase):

    def setUp(self) -> None:
        # For testing we create an AdbDevice in which we mock the _adb_command() method.
        ADB_MOCK_SETTINGS['MOCK_ADB_RESULTS'] = [MockAdbResult(stdout='hello world', stderr='hello errworld')]
        ADB_MOCK_SETTINGS['NEXT_MOCK_ADB_RESULT'] = 0
        self.original_adb_call = AdbDevice._adb_command
        AdbDevice._adb_command = mock_adb_call
        self.device = AdbDevice('fake_device', check_device_exists=False)
        for filename in MOCK_SUCCESSFULLY_PULLED_FILE:
            with open(filename, 'w') as fp:
                pass

    def tearDown(self) -> None:
        AdbDevice._adb_command = self.original_adb_call
        for mock_file in MOCK_SUCCESSFULLY_PULLED_FILE:
            os.remove(mock_file)

    def _mock_adb_results(self, *mock_results: [AdbResult]):
        """
        Sets the mock results _adb_command should return. See mock_adb_call.
        :param mock_results: The mock results, in order, to be returned by _adb_command calls.
        """
        ADB_MOCK_SETTINGS['MOCK_ADB_RESULTS'] = mock_results
        ADB_MOCK_SETTINGS['NEXT_MOCK_ADB_RESULT'] = 0

    def test_adb_device_init(self):
        two_devices_connected = MockAdbResult(
            stdout='List of devices attached\nfake_device\tdevice\nanother_fake_device\tdevice\n')
        self._mock_adb_results(two_devices_connected)

        # no device specified: should never fail
        AdbDevice()
        AdbDevice(check_device_exists=False)
        # device that doesn't exist specified: should not fail only when check_device_exists is False
        with self.assertRaisesRegex(Exception, 'Cannot create adb connection with device.*'):
            AdbDevice('nonexistent_device', check_device_exists=True)
        AdbDevice('nonexistent_device', check_device_exists=False)
        # existing device specified: should succeed
        AdbDevice('another_fake_device', check_device_exists=True)
        AdbDevice('another_fake_device', check_device_exists=False)

    def test_root(self):
        root_success = MockAdbResult(stdout='restarting adbd as root\n')
        root_error = MockAdbResult(stdout='adbd cannot run as root in production builds\n')
        self._mock_adb_results(root_success, root_error)

        self.assertTrue(self.device.root().success)
        self.assertFalse(self.device.root().success)

        # check if calls were correct: to get root on device x you need the parameters 'root' and '-s X'
        self.assertIn('root', ADB_CALLS_ARGUMENT_HISTORY[-1])
        self.assertIn('-s fake_device', ADB_CALLS_ARGUMENT_HISTORY[-1])

    def test_ls(self):
        ls_result = MockAdbResult(stdout='bin\nusr\ntmp\n')
        ls_error = MockAdbResult(stdout='ls: /bla: No such file or directory\n', success=False)
        self._mock_adb_results(ls_result, ls_error)

        self.assertListEqual(['bin', 'usr', 'tmp'], self.device.ls('/'))
        with self.assertRaisesRegex(Exception, 'Could not get contents of path /bla.*'):
            self.device.ls('/bla')

    def test_installed_packages(self):
        success_result = MockAdbResult(stdout='package:com.google.android.networkstack.tethering\n'
                                              'package:com.android.cts.priv.ctsshim\n'
                                              'package:com.google.android.youtube\n')
        error_result = MockAdbResult(stderr='something went wrong!', success=False)
        self._mock_adb_results(success_result, error_result)

        self.assertListEqual(
            ['com.google.android.networkstack.tethering',
             'com.android.cts.priv.ctsshim',
             'com.google.android.youtube'],
            self.device.installed_packages())
        with self.assertRaisesRegex(Exception, 'Could not get installed packages.*'):
            self.device.installed_packages()
        # check if calls were correct: to get the packages on device x you need the parameters 'shell pm list packages' and '-s X'
        self.assertIn('shell pm list packages', ADB_CALLS_ARGUMENT_HISTORY[-1])
        self.assertIn('-s fake_device', ADB_CALLS_ARGUMENT_HISTORY[-1])

    def test_path_package(self):
        success_result = MockAdbResult(
            stdout=
            'package:/data/app/~~AlS-tIsYg8hVknxAW6HAhg==/com.whatsapp-q43OZ5GWzSs2h0SoWXBEnQ==/base.apk\n'
            'package:/data/app/~~AlS-tIsYg8hVknxAW6HAhg==/com.whatsapp-q43OZ5GWzSs2h0SoWXBEnQ==/split_pkg.en.apk\n'
            'package:/data/app/~~AlS-tIsYg8hVknxAW6HAhg==/com.whatsapp-q43OZ5GWzSs2h0SoWXBEnQ==/split_pkg.arm64.apk\n')
        empty_result = MockAdbResult(stdout='')
        failure_result = MockAdbResult(stderr='', success=False)
        self._mock_adb_results(success_result, empty_result, failure_result)

        self.assertListEqual([
            '/data/app/~~AlS-tIsYg8hVknxAW6HAhg==/com.whatsapp-q43OZ5GWzSs2h0SoWXBEnQ==/base.apk',
            '/data/app/~~AlS-tIsYg8hVknxAW6HAhg==/com.whatsapp-q43OZ5GWzSs2h0SoWXBEnQ==/split_pkg.en.apk',
            '/data/app/~~AlS-tIsYg8hVknxAW6HAhg==/com.whatsapp-q43OZ5GWzSs2h0SoWXBEnQ==/split_pkg.arm64.apk'
        ], self.device.path_package('com.whatsapp'))
        self.assertListEqual([], self.device.path_package('com.whatsapp'))
        with self.assertRaisesRegex(Exception, 'Could not locate package com.whatsapp.*'):
            self.device.path_package('com.whatsapp')

    def test_package_versions(self):
        success_result = MockAdbResult(
            stdout='versionName=91.0.4472.114\n'
                   'versionName=91.0.4472.114\n'
        )
        empty_result = MockAdbResult(stdout='')
        failure_result = MockAdbResult(stderr='blablabla', success=False)
        self._mock_adb_results(success_result, empty_result, failure_result)

        expected = ['91.0.4472.114', '91.0.4472.114']
        actual = self.device.package_versions('com.whatsapp')
        self.assertListEqual(expected, actual)

        self.assertListEqual([], self.device.package_versions('com.whatsapp'))
        with self.assertRaisesRegex(Exception, 'Could not locate package com.whatsapp.*'):
            self.device.package_versions('com.whatsapp')

    def test_pull(self):
        success_result = MockAdbResult(
            stdout='pull successfull! (we don\'t stdout so I can put anything I want here. poop.)')
        failure_result = MockAdbResult(stderr='adb gods are angry', success=False)

        # pull goes well: we 'pull' a file to this exact location to pretend the pull was successful
        self._mock_adb_results(success_result)
        pull_result = self.device.pull(MOCK_SUCCESSFULLY_PULLED_FILE[0], '.')
        self.assertTrue(pull_result.success)
        self.assertEqual(f'./{MOCK_SUCCESSFULLY_PULLED_FILE[0]}', pull_result.path)
        # pull goes well according to adb, but the resulting file is not present so the result should be a failure
        pull_result = self.device.pull('bla', 'folder_for_testing_purposes')
        self.assertFalse(pull_result.success)
        self.assertTrue(os.path.isdir('folder_for_testing_purposes'))  # destination fodler should be created
        os.rmdir('folder_for_testing_purposes')
        # pull goes wrong
        self._mock_adb_results(failure_result)
        with self.assertRaisesRegex(Exception, 'Could not pull file bla.*'):
            self.device.pull('bla', '.')
        # adb pull can sometimes fail for no good reason! The pull method should be resiliant against that
        self._mock_adb_results(failure_result, failure_result, success_result)
        pull_result = self.device.pull(MOCK_SUCCESSFULLY_PULLED_FILE[0], '.')
        self.assertTrue(pull_result.success)
        self.assertEqual(f'./{MOCK_SUCCESSFULLY_PULLED_FILE[0]}', pull_result.path)

    def test_pull_package(self):
        package_paths_result = MockAdbResult(
            stdout=
            f'package:/data/apks/{MOCK_SUCCESSFULLY_PULLED_FILE[0]}\n'
            f'package:/data/apks/{MOCK_SUCCESSFULLY_PULLED_FILE[1]}')
        success_pull_result = MockAdbResult(stdout='pull success')

        # successful pull:
        self._mock_adb_results(package_paths_result, success_pull_result, success_pull_result)
        pull_package_result = self.device.pull_package('com.whatsapp', '.')
        self.assertListEqual([f'./{MOCK_SUCCESSFULLY_PULLED_FILE[0]}', f'./{MOCK_SUCCESSFULLY_PULLED_FILE[1]}'],
                             [pull_result.path for pull_result in pull_package_result])
        last_three_commands = '; '.join(ADB_CALLS_ARGUMENT_HISTORY[-3:])
        self.assertIn('pm path com.whatsapp', last_three_commands)
        self.assertIn(f'pull /data/apks/{MOCK_SUCCESSFULLY_PULLED_FILE[0]}', last_three_commands)
        self.assertIn(f'pull /data/apks/{MOCK_SUCCESSFULLY_PULLED_FILE[1]}', last_three_commands)

    def test_open_intent(self):
        intent_success = MockAdbResult(stdout='Starting: Intent { act=android.intent.action.VIEW dat=bla }')
        intent_failure = MockAdbResult(stdout='Starting: Intent { act=android.intent.action.VIEW dat=bla }',
                                       stderr='Error: Activity not started, unable to resolve Intent { '
                                              'act=android.intent.action.VIEW dat=bla flg=0x10000000 }')
        self._mock_adb_results(intent_success, intent_failure)

        self.assertTrue(self.device.open_intent('First call will succees').success)
        self.assertFalse(self.device.open_intent('Second call will fail').success)

    def test_list_devices(self):
        no_device_connected = MockAdbResult(stdout='List of devices attached\n')
        one_device_connected = MockAdbResult(stdout='List of devices attached\nfake_device\tdevice\n')
        two_devices_connected = MockAdbResult(
            stdout='List of devices attached\nfake_device\tdevice\nanother_fake_device\tdevice\n')
        error_in_adb_command = MockAdbResult(stderr='bla', success=False)

        self._mock_adb_results(no_device_connected, one_device_connected, two_devices_connected, error_in_adb_command)

        self.assertListEqual(AdbDevice.list_devices(), [])
        self.assertListEqual(AdbDevice.list_devices(), ['fake_device'])
        self.assertListEqual(AdbDevice.list_devices(), ['fake_device', 'another_fake_device'])
        self.assertRaisesRegex(Exception, '.*Could not get list of available adb devices.*', AdbDevice.list_devices)

    def test_get_device_status(self):
        two_devices_connected = MockAdbResult(
            stdout='List of devices attached\noffline_fake_device\toffline\nonline_fake_device\tdevice\n')
        error_in_adb_command = MockAdbResult(stderr='bla', success=False)

        self._mock_adb_results( two_devices_connected, two_devices_connected, two_devices_connected, error_in_adb_command)

        self.assertEqual(AdbDevice.get_device_status('offline_fake_device'), 'offline')
        self.assertEqual(AdbDevice.get_device_status('online_fake_device'), 'device')
        self.assertRaisesRegex(Exception, '.*Could not get status from device*',lambda: AdbDevice.get_device_status('non_existing_device'))
        self.assertRaisesRegex(Exception, '.*Could not get list of available adb devices.*',lambda: AdbDevice.get_device_status('offline_fake_device'))

    def test_get_prop(self):
        value = 'some value!'
        prop_has_value = MockAdbResult(stdout=value)
        prop_no_value = MockAdbResult(stdout='')
        self._mock_adb_results(prop_has_value, prop_no_value)

        # first property should be fine
        self.assertEqual(self.device.get_prop('some.property'), value)
        # third call: not cached, so this wil lbe the second adb call, and this should return None
        self.assertIsNone(self.device.get_prop('second.property.has.no.value'))

    def test_emulator_emu_avd(self):
        # Define mock results for emulator_emu_avd
        happy_flow = MockAdbResult(stdout='avd_device')
        not_an_emulator = MockAdbResult(success=False)
        invalid_command = MockAdbResult(success=False)

        # Mock the _mock_adb_results method to set expected results
        self._mock_adb_results(happy_flow, not_an_emulator, invalid_command)

        # Happy flow: a regular command like adb emu avd name giving the expected result
        result = self.device.emulator_emu_avd('name')
        self.assertTrue(result.success)
        self.assertIn('avd_device', result.stdout)

        # Scenario when the device is not an emulator
        result = self.device.emulator_emu_avd('name')
        self.assertFalse(result.success)

        # Scenario where the emu avd command is invalid (e.g., a typo: snapsht)
        result = self.device.emulator_emu_avd('snapsht')
        self.assertFalse(result.success)

    def test_get_state(self):
        # Define mock results for get_state
        state_online = MockAdbResult(stdout='device')
        state_offline = MockAdbResult(stdout='offline')
        state_unauthorized = MockAdbResult(stdout='unauthorized')
        invalid_command = MockAdbResult(stderr="Invalid command", success=False)

        # Mock the _mock_adb_results method to set expected results
        self._mock_adb_results(state_online, state_offline, state_unauthorized, invalid_command)

        # Test the case when the device is 'device'
        result = self.device.get_state()
        self.assertTrue(result.success)
        self.assertEqual(result.stdout, 'device')

        # Test the case when the device is 'offline'
        result = self.device.get_state()
        self.assertTrue(result.success)
        self.assertEqual(result.stdout, 'offline')

        # Test the case when the device is 'unauthorized'
        result = self.device.get_state()
        self.assertTrue(result.success)
        self.assertEqual(result.stdout, 'unauthorized')

        # Test the case when the command is invalid
        result = self.device.get_state()
        self.assertFalse(result.success)
        self.assertIn('Invalid command', result.stderr)

    @patch('adb_pywrapper.adb_device.AdbDevice._snapshot_command')
    def test_emulator_snapshots_list(self, mock_snapshot_command):
        # Test emulator_snapshots_list function
        snapshot_list_output = """List of snapshots present on all disks:
ID        TAG                 VM SIZE                DATE       VM CLOCK
--        snap_2023-11-23_13-13-02   130M 2023-11-23 13:13:02   00:02:08.739
--        snap_2023-12-05_12-56-56   130M 2023-12-05 12:56:56   00:01:17.073
OK
"""
        mock_snapshot_command.return_value = MockAdbResult(stdout=snapshot_list_output)
        result = self.device.emulator_snapshots_list()

        mock_snapshot_command.assert_called_once_with('list')
        self.assertEqual(result, ['snap_2023-11-23_13-13-02', 'snap_2023-12-05_12-56-56'])

    @patch('adb_pywrapper.adb_device.AdbDevice._snapshot_exists')
    @patch('adb_pywrapper.adb_device.AdbDevice._snapshot_command')
    def test_emulator_snapshot_load_existing(self, mock_snapshot_command, mock_snapshot_exists):
        # Test emulator_snapshot_load function with an existing snapshot
        mock_snapshot_exists.return_value = True
        mock_snapshot_command.return_value = MockAdbResult(success=True)

        self.device.emulator_snapshot_load('snapshot1')

        mock_snapshot_exists.assert_called_once_with('snapshot1')
        mock_snapshot_command.assert_called_once_with('load', 'snapshot1')

    @patch('adb_pywrapper.adb_device.AdbDevice._snapshot_exists')
    def test_emulator_snapshot_load_non_existing(self, mock_snapshot_exists):
        # Test emulator_snapshot_load function with a non-existing snapshot
        mock_snapshot_exists.return_value = False

        result = self.device.emulator_snapshot_load('non_existing_snapshot')

        mock_snapshot_exists.assert_called_once_with('non_existing_snapshot')
        self.assertFalse(result.success)

    @patch('adb_pywrapper.adb_device.AdbDevice._snapshot_exists')
    @patch('adb_pywrapper.adb_device.AdbDevice._snapshot_command')
    def test_emulator_snapshot_save(self, mock_snapshot_command, mock_snapshot_exists):
        # Test emulator_snapshot_save function
        mock_snapshot_exists.return_value = False
        mock_snapshot_command.return_value = MockAdbResult(success=True)

        self.device.emulator_snapshot_save('snapshot1')

        mock_snapshot_exists.assert_called_once_with('snapshot1')
        mock_snapshot_command.assert_called_once_with('save', 'snapshot1')

    @patch('adb_pywrapper.adb_device.AdbDevice.emulator_snapshots_list', return_value=['snapshot1', 'snapshot2'])
    @patch('adb_pywrapper.adb_device.AdbDevice._snapshot_exists')
    @patch('adb_pywrapper.adb_device.AdbDevice._snapshot_command')
    def test_emulator_snapshot_delete(self, mock_snapshot_command, mock_snapshot_exists, mock_emulator_snapshots_list):
        # Test emulator_snapshot_delete function
        mock_snapshot_exists.return_value = True  # Existing snapshots
        mock_snapshot_command.return_value = MockAdbResult(success=True)

        result_contains_faulty = self.device.emulator_snapshot_delete(delete=['snapshot1', 'snapshot3'])
        self.assertFalse(result_contains_faulty.success)

        mock_emulator_snapshots_list.assert_called_once()
        mock_snapshot_command.assert_called_with('del', 'snapshot1')
        mock_snapshot_command.assert_not_called_with('del', 'snapshot2')  # snapshot2 is not in the delete list

        result_faulty = self.device.emulator_snapshot_delete(delete=['snapshot3'])
        self.assertFalse(result_faulty.success)

        result_correct = self.device.emulator_snapshot_delete(delete=['snapshot1', 'snapshot2'])
        self.assertTrue(result_correct)


if __name__ == '__main__':
    unittest.main()
