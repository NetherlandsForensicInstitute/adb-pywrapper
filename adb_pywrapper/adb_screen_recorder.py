import subprocess
from time import sleep
from uuid import uuid4

from adb_pywrapper import log_error_and_raise_exception, logger, ADB_PATH
from adb_pywrapper.adb_device import AdbDevice


class AdbScreenRecorder:
    def __init__(self, device: AdbDevice, bit_rate: str = '8M'):
        self.device = device
        self._recording_process = None
        self._recording_folder = f'/sdcard/{uuid4()}'
        self._bit_rate = bit_rate
        self.__enter__()

    def __enter__(self):
        # create recording folder:
        self.device.shell(f'mkdir {self._recording_folder}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # stop recording if still in process
        if self.is_recording():
            self._recording_process.kill()
        # remove files on device
        self.device.shell(f'rm -rf {self._recording_folder}')

    def is_recording(self):
        return self._recording_process is not None and self._recording_process.poll() is None

    def start_recording(self):
        if not self.is_recording():
            arguments = f'{ADB_PATH} {self.device.device_command}shell'.split(' ')
            loop = f'i=1; while true; do screenrecord --bit-rate {self._bit_rate} {self._recording_folder}/$i.mp4; let i=i+1; done'
            arguments.append(loop)
            logger.info(f'executing adb command: {arguments}')
            self._recording_process = subprocess.Popen(arguments)

    def _screenrecord_process_active_on_device(self):
        return '' != self.device.shell('ps -A | grep screenrecord').stdout

    def stop_recording(self, output_folder: str) -> [str]:
        if not self.is_recording():
            logger.warning(f"Recording was stopped but the recorder wasn't started")
            return None
        # Stop background process
        logger.info('Stopping screen recorder...')
        self._recording_process.terminate()
        while self._screenrecord_process_active_on_device():
            sleep(0.2)
        self._recording_process = None
        # collect recordings
        video_files = [f'{self._recording_folder}/{file_name}' for file_name in
                       self.device.ls(self._recording_folder)]
        logger.info(f'Copying video files: {video_files}')
        pull_results = self.device.pull_multi(video_files, output_folder)
        failures = [pull_result for pull_result in pull_results if not pull_result.success]
        if len(failures) > 0:
            msg = f"Failed to pull file(s) {[failure.path for failure in failures]}"
            log_error_and_raise_exception(logger, msg)
        # clean up recordings on device
        for video_file in video_files:
            self.device.shell(f'rm -f {video_file}')
        return [pull_result.path for pull_result in pull_results]  # pulled files