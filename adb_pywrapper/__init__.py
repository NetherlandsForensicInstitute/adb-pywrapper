import logging
import subprocess
from datetime import datetime
from os import makedirs, environ
from os.path import dirname, abspath, isdir, expanduser
from sys import stdout


logger = logging.getLogger(__name__)

###########################
# ADB INITIALISATION CODE #
###########################

def get_sdk_root():
    """
    Used to initialize ANDROID_SDK_ROOT, should not be called, use ANDROID_SDK_ROOT instead!
    This method looks for the location of your Android SDK. it does so by looking for commonly used environmental
    values and commonly used directories.
    If none of these guesses yield a result, an error is logged and the program terminates.
    :return: Our best guess as to the location of the Android SDK
    """
    # list of env values and paths that we look for the Android SDK. envs are checked before paths.
    environmental_values = ['ANDROID_SDK_ROOT', 'ANDROID_HOME']
    possible_paths = ['~/Android/Sdk']

    for key in environmental_values:
        value = environ.get(key)
        if value:
            logger.info(f'Using environmental value {key} for Android SDK ROOT {value}')
            return value
    for path in possible_paths:
        if '~' in path:
            path = expanduser(path)
        if isdir(path):
            logger.info(f'Using Android SDK ROOT {path}')
            return path
    logger.warning(
        f'Could not determine Android SDK ROOT. Define it in one of these env values: {environmental_values},'
        f'or install the Sdk in one of these locations: {possible_paths}. For now using f{possible_paths[0]} '
        f'as Android SDK ROOT.')
    return possible_paths[0]


ADB_PATH = None
ANDROID_SDK_HOME = get_sdk_root()
# initialize adb path: first check if adb is installed and available as a command
# if not, use the ANDROID_SDK_HOME detected in __init__
if 'Android Debug Bridge version' in subprocess.getoutput('adb --version'):
    ADB_PATH = 'adb'
else:
    ADB_PATH = f'{ANDROID_SDK_HOME}/platform-tools/adb'
if 'Android Debug Bridge version' not in subprocess.getoutput(f'{ADB_PATH} --version'):
    logger.warning(
        f'Could not locate ADB. expected it available as "{ADB_PATH}" '
        f'but checking the version gives unexpected output: {subprocess.getoutput(f"{ADB_PATH} --version")}. '
        f'We are assuming the command `adb` works for now even though it doesn\'t seem to work...')
    ADB_PATH = 'adb'


#####################
# LOGGING INIT CODE #
#####################

# define needed folders
PROJECT_ROOT = dirname(dirname(abspath(__file__)))
LOG_FOLDER = f'{PROJECT_ROOT}/logs'
makedirs(LOG_FOLDER, exist_ok=True)
CACHE_FOLDER = f'{PROJECT_ROOT}/cache'
makedirs(CACHE_FOLDER, exist_ok=True)


# logging helpers
def configure_default_logging():
    now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    logging.basicConfig(
        handlers=[
            logging.FileHandler(f'{LOG_FOLDER}/{now}.log'),
            logging.StreamHandler(stdout)
        ],
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')


def log_error_and_raise_exception(logger, msg):
    logger.error(msg)
    raise Exception(msg)
