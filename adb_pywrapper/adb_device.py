import subprocess
from os import makedirs
from os.path import basename, isfile
from subprocess import CompletedProcess
from time import sleep
from typing import Optional

from adb_pywrapper import logger, log_error_and_raise_exception, ADB_PATH
from adb_pywrapper.adb_result import AdbResult
from adb_pywrapper.pull_result import PullResult


class AdbDevice:
    def __init__(self, device: str = None, check_device_exists: bool = True):
        self.device = device
        if device is not None and check_device_exists:
            connected_devices = AdbDevice.list_devices()
            if device not in connected_devices:
                log_error_and_raise_exception(logger,
                                                       f'Cannot create adb connection with device `{device}` '
                                                       f'as it cannot be found with `adb devices`: {connected_devices}')
        self.device_command = ''
        if device is not None:
            self.device_command += f'-s {device} '

    def __repr__(self) -> str:
        return f"adb_device:{self.device}"

    @staticmethod
    def _adb_command(command: str, timeout: Optional[int] = None) -> AdbResult:
        """
        Executes a given adb command and returns the completed process.
        Optionally executed with a timeout.
        :param command: the string containing the arguments passed to the adb command
        :param timeout: (Optional) A timeout for the command.
        :return: the completed process of '[timeout {timeout}] adb {command}'
        """
        adb_command = f'{ADB_PATH} {command}'
        if timeout:
            adb_command = f'timeout {timeout} {adb_command}'
        completed_process = subprocess.run(adb_command, shell=True, capture_output=True)
        return AdbResult(completed_process)

    def _command(self, command: str, timeout: Optional[int] = None) -> AdbResult:
        """
        Executes a given adb command and returns the completed process.
        Optionally executed with a timeout.
        :param command: the string containing the arguments passed to the adb command
        :param timeout: (Optional) A timeout for the command.
        :return: the completed process of '[timeout {timeout}] adb {command}'
        """
        return AdbDevice._adb_command(f'{self.device_command}{command}', timeout)

    @staticmethod
    def list_devices() -> list[str]:
        """
        Looks for connected adb devices and returns the device names in a list.
        :return: list of adb device names. Example: ['device-5554','AU9AD74','netagfer987']
        """
        result = AdbDevice._adb_command('devices')
        if not result.success:
            log_error_and_raise_exception(logger, f'Could not get list of available adb devices. '
                                                                    f'ADB output: {result.stdout}{result.stderr}')
        devices = [line[:line.index('\t')] for line in result.stdout.splitlines() if '\t' in line]
        return devices

    @staticmethod
    def get_device_status(device_name) -> str:
        """
        Get the status corresponding to the device_name. This uses the 'adb devices' command.
        :param device_name: the device adb name/identifier.
        :return: a string with the status of the given device. Example: 'offline', 'device' or 'unauthorized'
        """
        result = AdbDevice._adb_command('devices')
        if not result.success:
            log_error_and_raise_exception(logger, f'Could not get list of available adb devices. '
                                                                    f'ADB output: {result.stdout}{result.stderr}')
        for line in result.stdout.splitlines():
            if line.startswith(device_name):
                return line.split('\t')[1]

        log_error_and_raise_exception(logger, f'Could not get status from device {device_name}')

    def root(self) -> AdbResult:
        """
        Restarts adb with root privileges.
        :return: AdbResult containing the completed process of `adb root`
        """
        result = self._command('root')
        # process exits with code 0 even if root could not be obtained. We fix that here
        if 'adbd cannot run as root' in result.stdout:
            result.success = False
        return result

    def wait_for_device(self) -> AdbResult:
        """
        Waits for a maximum of 120 seconds until the Android Debug Bridge with the device is available.
        :return: AdbResult containing the completed process of `adb wait-for-device`
        """
        return self._command('wait-for-device', 120)

    def shell(self, command: str) -> AdbResult:
        """
        Executes a command on the shell of the device like: `adb shell {command}`
        :param command: the command to run on the shell of the connected device.
        :return: AdbResult containing the completed process of `adb shell {command}`
        """
        return self._command(f'shell {command}')

    def emulator_emu_avd(self, command: str) -> AdbResult:
        """
        Executes a command with the `adb emu avd` for emulator communication. Examples: name, snapshot
        :param command: the command to run with the emu avd prefix of the connected device.
        :return: AdbResult containing the completed process of `adb emu avd {command}`
        """
        return self._command(f'emu avd {command}')

    def get_state(self) -> AdbResult:
        """
        Executes a command to fetch the state of a certain ADB device. Examples: `offline` or `device`
        :return: AdbResult instance with either `success=True and stdout='{device_status}'` or `success=False and stderr='ADB error'`
        """
        return self._command(f'get-state')

    def get_prop(self, property: str) -> str:
        """
        Retrieves the value of a given property through the `adb getprop method`
        :param property: the property from which the value is needed
        :return: the value of the property, or None if the property doesn't exist
        """
        value = self.shell(f"getprop {property}").stdout
        if value == "":
            value = None
        return value

    def ls(self, path: str) -> Optional[list[str]]:
        """
        Lists the contents of a given path on the device
        :param path: the path on the device
        :return: a list containing the contents of the given path
        """
        adb_result = self.shell(f'ls {path}')
        if not adb_result.success:
            log_error_and_raise_exception(logger,
                                                   f'Could not get contents of path {path} on device {self.device}. '
                                                   f'adb stderr: {adb_result.stderr}')
        return adb_result.stdout.splitlines()

    def installed_packages(self) -> list[str]:
        """
        Lists all installed packages on the device.
        :return: a list with all installed packages
        """
        adb_result = self.shell(f'pm list packages')
        if not adb_result.success:
            log_error_and_raise_exception(logger,
                                                   f'Could not get installed packages on device {self.device}. '
                                                   f'adb stderr: {adb_result.stderr}')
        return [line[line.index(':') + 1:] for line in adb_result.stdout.splitlines() if line.startswith('package:')]

    def path_package(self, package_name: str) -> list[str]:
        """
        Returns the location of an installed package.
        The result is a list, because applications can be installed using split packages, splitting the apk across
        multiple files.
        If the app is not installed, an exception is thrown
        :param package_name: the package to be located
        :return: a list containing the installation location(s) of said package
        """
        adb_result = self.shell(f'pm path {package_name}')
        if not adb_result.success:
            log_error_and_raise_exception(logger,
                                                   f'Could not locate package {package_name} on device {self.device}. '
                                                   f'adb stderr: {adb_result.stderr}')
        return [line[line.index(':') + 1:] for line in adb_result.stdout.splitlines() if line.startswith('package:')]

    def package_versions(self, package_name: str) -> list[str]:
        """
        Get the list of version of an installed package.
        Returns a list as split apks each have their own versionName record.
        :param package_name: Full name of the package
        :return: list of versions for the package
        """
        adb_result = self.shell(f"dumpsys package {package_name} | grep versionName")
        if not adb_result.success:
            log_error_and_raise_exception(logger,
                                                   f'Could not locate package {package_name} on device {self.device}. '
                                                   f'adb stderr: {adb_result.stderr}')
        result = adb_result.stdout.splitlines()
        return [line.split("=")[-1] for line in result]

    def _pull(self, remote: str, local: Optional[str] = None, a: bool = False) -> AdbResult:
        """
        Raw call to adb_pull. Recommended use is pull(), not _pull()
        :param remote: the file or folder to copy
        :param local: (optional) the location to copy {remote} to
        :param a: copy with timestamp and mode
        :return: the completed process of 'adb pull [-a] {remote} [{local}]'
        """
        command = 'pull'
        if a:
            command += ' -a'
        adb_result = self._command(f'{command} {remote}{f" {local}" if local else ""}')
        return adb_result

    def pull(self, file_to_pull: str, destination: str) -> PullResult:
        """
        Copies a file off the device to a given local directory
        :param file_to_pull: complete path to the file to copy from the device
        :param destination: the directory in which the package file(s) are to be located. Will be created if needed.
        :return: A PullResult object with the completed_adb_process of the `adb pull` action, the destination path and a success flag
        """
        if isfile(destination):
            raise Exception()
        makedirs(destination, exist_ok=True)
        for i in range(5):  # sometimes pull fails, trying a few times doesn't hurt
            pull_result = self._pull(file_to_pull, local=destination)
            if pull_result.success:
                break
            sleep(1)
        if not pull_result.success:
            log_error_and_raise_exception(logger,
                                                   f'Could not pull file {file_to_pull} on device {self.device}, '
                                                   f'adb output: {pull_result.stdout}{pull_result.stderr}')

        result_file_path = f'{destination}/{basename(file_to_pull)}'
        return PullResult(result_file_path, pull_result)

    def pull_multi(self, files_to_pull: [str], destination: str) -> list[PullResult]:
        return [self.pull(file_to_pull, destination) for file_to_pull in files_to_pull]

    def pull_package(self, package_name: str, destination: str) -> list[PullResult]:
        """
        Pulls the apk (or multiple apks if the app uses split packages) from a given package off the devices.
        :param package_name: The package name of the app, eg com.whatsapp
        :param destination: the local directory to store the apk(s)
        :return: a list of PullResult objects with the completed_adb_process of the `adb pull` action, the destination
                 path and a success flag
        """
        result = []
        files_to_pull = self.path_package(package_name)
        if len(files_to_pull) == 0:
            log_error_and_raise_exception(logger,
                                                   f'Could not locate any package files for package {package_name} on '
                                                   f'device {self.device}. Is it installed on the device?')
        for file_to_pull in files_to_pull:
            result.append(self.pull(file_to_pull, destination))
        return result

    def install(self, apk_path: str, r: bool = False) -> AdbResult:
        """
        Installs a given apk on the connected device.
        :param apk_path: the location of the apk file on the local machine
        :param r: -r option: replace already installed application. This is needed on physical devices or
                             if you get an error that the application already exists and should be uninstalled first.
        :return: the completed process of 'adb install [-r] {apk_path}'
        """
        command = 'install'
        if r:
            command += ' -r'
        return self._command(f'{command} {apk_path}')

    def install_multiple(self, apk_paths: [str], r: bool = False) -> AdbResult:
        """
        Calls the adb install-multiple command, used for installing split packages.
        According to adb documentation can only be used for split packages, not for multiple apps!
        :param apk_paths: list of split packages to install
        :param r: -r option: replace already installed application. This is needed on physical devices or
                             if you get an error that the application already exists and should be uninstalled first.
        :return: the completed process of 'adb install-multiple [-r] {apk_paths}'
        """
        command = 'install-multiple'
        if r:
            command += ' -r'
        return self._command(f'{command} {" ".join(apk_paths)}')

    def open_intent(self, url: str) -> AdbResult:
        """
        Opens a given url on the device by starting an intent. If a default app is associated with this URL, this will
        result in the app being opened.
        :param url: The URL to open
        :return: the completed process of adb shell am start -a android.intent.action.VIEW -d '{url}'
        """
        adb_result = self.shell(f"am start -a android.intent.action.VIEW -d '{url}'")
        # When the intent could not be opened stderr contains an error message
        adb_result.success = adb_result.stderr == ''
        return adb_result

    def _snapshot_exists(self, snapshot_name: str) -> bool:
        """
        Check if the snapshot exists on the emulator.
        :param snapshot_name: The name of the snapshot
        :return: boolean
        """
        return snapshot_name in self.emulator_snapshots_list()

    def _snapshot_command(self, subcommand: str, snapshot_name: Optional[str] = None) -> AdbResult:
        """
        Executes the adb command emu avd snapshot with a given subcommand. (run $adb emu avd snapshot --help for the full
        documentation)
        :param subcommand: One of the following: list, save, load, del, get
        :param snapshot_name: Name of the snapshot to perform the action on
        :return:
        """
        allowed_subcommands = ["list", "save", "load", "del", "get"]
        if not subcommand in allowed_subcommands:
            log_error_and_raise_exception(logger,
                                                   f"Could not execute snapshot subcommand {subcommand}, should be one of {', '.join(allowed_subcommands)}")
        if subcommand not in ["list", "get"] and snapshot_name is None:
            logger.warning(logger, f"Snapshot subcommand requires a snapshot_name, None is given.")
        return self.emulator_emu_avd(f' snapshot {subcommand} {snapshot_name}')

    def emulator_snapshots_list(self) -> list:
        """
        Get a list of snapshots from the emulator.
        :return: A list of snapshot names.
        """
        output = self._snapshot_command("list").stdout
        output_lines = output.splitlines()
        return [line.split()[1] for line in output_lines[2:-1]]

    def emulator_snapshot_load(self, snapshot_name: str) -> AdbResult:
        """
        Load a snapshot of the emulator.
        :param snapshot_name: The name of the snapshot.
        :return: AdbResult object with stdout, stderr if applicable and success True/False.
        """
        logger.info(f"Loading snapshot: {snapshot_name} for {self.device}...")

        if self._snapshot_exists(snapshot_name):
            return self._snapshot_command("load", snapshot_name)
        else:
            return AdbResult(CompletedProcess(args=[], returncode=1, stdout=b'',
                                              stderr=f'Snapshot with name {snapshot_name} does not exists. So it '
                                                     f'was not loaded'.encode()))

    def emulator_snapshot_save(self, snapshot_name: str) -> AdbResult:
        """
        Create a snapshot of the current state of the emulator.
        :param snapshot_name: The name of the snapshot.
        :return: AdbResult object with stdout, stderr if applicable and success True/False.
        """
        if self._snapshot_exists(snapshot_name):
            logger.error(f'A snapshot with the name {snapshot_name} already exists')
            return AdbResult(CompletedProcess(args=[], returncode=1, stdout=b'',
                                              stderr=f'A snapshot with the name {snapshot_name} already exists'.encode()))

        save_state = self._snapshot_command("save", snapshot_name)
        if save_state.success:
            logger.info(f"Saved snapshot {snapshot_name} of emulator {self.device}")
        return save_state

    def emulator_snapshot_delete(self, delete: list[str] = None) -> AdbResult:
        """
            Delete snapshots based on a list.
            If some but not all provided snapshots are removed success will be False, and an error message including a
            list of invalid snapshots is passed as a stderr.
            :param delete: a list containing snapshot names (str) to be deleted. Example: ['snap_name_1','snap_name_3']
            :return: AdbResult object with stdout, stderr if applicable and success True/False
        """
        verified_snapshots: list[str] = []

        if delete is not None:
            for snapshot_name in self.emulator_snapshots_list():
                if snapshot_name in delete:
                    verified_snapshots.append(snapshot_name)

            if not verified_snapshots:
                return AdbResult(
                    CompletedProcess(args=[], returncode=1, stdout=b'', stderr=f"None of the snapshots provided "
                                                                               f"exist".encode())
                )

            for s in verified_snapshots:
                self._snapshot_command('del', s)

            # if at least one snapshot but not all provided snapshots are removed.
            if len(delete) > len(verified_snapshots):
                return AdbResult(
                    CompletedProcess(args=[], returncode=1, stdout=b'',
                                     stderr=f"The snapshot(s) [{list(set(delete) - set(verified_snapshots))}] provided "
                                            f"do not exist...".encode())
                )
            return AdbResult(
                CompletedProcess(args=[], returncode=0, stdout=f'All provided snapshots were deleted '
                                                               f'successfully'.encode(), stderr=b'')
            )
