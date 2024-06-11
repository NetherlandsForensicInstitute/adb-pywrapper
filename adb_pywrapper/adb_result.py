from subprocess import CompletedProcess


class AdbResult:
    def __init__(self, completed_adb_process: CompletedProcess):
        self.completed_adb_process: CompletedProcess = completed_adb_process
        self.stdout: str = completed_adb_process.stdout.decode()
        self.stderr: str = completed_adb_process.stderr.decode()
        self.success: bool = completed_adb_process.returncode == 0

    def __str__(self) -> str:
        return f'success : "{self.success}", ' \
               f'stdout : "{self.stdout}", ' \
               f'stderr : "{self.stderr}"'

    def __repr__(self) -> str:
        return self.__str__()