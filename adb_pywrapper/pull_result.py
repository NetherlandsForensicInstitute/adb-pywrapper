import os

from adb_pywrapper.adb_result import AdbResult


class PullResult:
    """
    A class to represent the result of an adb pull. it contains three properties:
        path: the path on which the pulled file should be available if the pull was successful
        completed_adb_process: the result of the completed adb process
        success: True if the pull was successful and the file in path exists
    """

    def __init__(self, result_path: str, adb_result: AdbResult):
        self.completed_adb_process = adb_result
        self.path = result_path
        self.success = os.path.exists(result_path)

    def __str__(self) -> str:
        return f'path : "{self.path}", ' \
               f'completed_adb_process : [{self.completed_adb_process.__str__()}]"'

    def __repr__(self) -> str:
        return self.__str__()