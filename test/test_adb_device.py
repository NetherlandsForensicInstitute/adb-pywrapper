import os.path
import shutil
import unittest
from os.path import basename
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch, Mock

from parameterized import parameterized

from adb_pywrapper.adb_device import AdbDevice
from adb_pywrapper.adb_result import AdbResult


class MockAdbResult(AdbResult):
    def __init__(self, stdout: str = '', stderr: str = '', success: bool = True):
        self.completed_adb_process = Mock(CompletedProcess)
        self.stdout = stdout
        self.stderr = stderr
        self.success = success


class TestAdbDevice(unittest.TestCase):

    @parameterized.expand([
        ('/sdcard/test.txt', './foo', 'pull /sdcard/test.txt ./foo'),
        ('/sdcard/test file.txt', './foo', 'pull \'/sdcard/test file.txt\' ./foo'),
        ('/sdcard/test.txt', './foo bar', 'pull /sdcard/test.txt \'./foo bar\''),
        ('/sdcard/test file.txt', './foo bar', 'pull \'/sdcard/test file.txt\' \'./foo bar\'')
    ])
    @patch('adb_pywrapper.adb_device.AdbDevice._adb_command')
    def test_pull(self, file_to_pull, destination, expected_command, mock_adb_command):
        try:
            device = AdbDevice()
            result = device.pull(file_to_pull, destination)

            mock_adb_command.assert_called_once_with(expected_command, None)
            self.assertTrue(os.path.exists(destination))  # destination folder should have bene created
            self.assertFalse(
                result.success)  # this is set to True if the file has been copied to the destination. We didn't copy anything
            expected_result_path = Path(destination) / basename(file_to_pull)
            self.assertEqual(f'./{str(expected_result_path)}', result.path)
        finally:
            shutil.rmtree(destination)

    @patch('adb_pywrapper.adb_device.AdbDevice._adb_command')
    def test_ls(self, mock_adb_command):
        device = AdbDevice()
        # happy flow
        mock_adb_command.return_value = MockAdbResult('foo.txt\nbar.txt', '')
        result = device.ls('/sdcard')
        mock_adb_command.assert_called_once_with('shell ls /sdcard', None)
        self.assertEqual(['foo.txt', 'bar.txt'], result)
        # escape special characters
        device.ls('/sdcard/test folder')
        mock_adb_command.assert_called_with('shell ls \'/sdcard/test folder\'', None)

    @patch('adb_pywrapper.adb_device.AdbDevice._adb_command')
    def test_install(self, mock_adb_command):
        device = AdbDevice()
        result = device.install('/path/to/apk')
        mock_adb_command.assert_called_once_with('install /path/to/apk', None)
        result = device.install('/path/to/other apk')
        mock_adb_command.assert_called_with('install \'/path/to/other apk\'', None)
        result = device.install('/path/to/yet another apk', True)
        mock_adb_command.assert_called_with('install -r \'/path/to/yet another apk\'', None)

    @patch('adb_pywrapper.adb_device.AdbDevice._adb_command')
    def test_install_multiple(self, mock_adb_command):
        device = AdbDevice()
        result = device.install_multiple(['foo.apk', 'bar.apk'])
        mock_adb_command.assert_called_once_with('install-multiple foo.apk bar.apk', None)
        result = device.install_multiple(['foo bar.apk', 'bar foo.apk'])
        mock_adb_command.assert_called_with("install-multiple 'foo bar.apk' 'bar foo.apk'", None)


if __name__ == '__main__':
    unittest.main()
