# adb-pywrapper
A python wrapper for the Android Debug Bridge enabling interaction with Android devices and emulators.

<img src="adb-pywrapper_logo.jpg" alt="adb-pywrapper logo" width="500"/>


## AdbDevice: Interacting with Android Devices using ADB in Python

The `AdbDevice` class in the `adb-pywrapper` Python package facilitates seamless interaction with Android devices using the Android Debug Bridge (ADB) directly within Python scripts.

Installation
------------

To install the `adb-pywrapper` package from the internal Nexus PyPI server, you can use `pip`:

```bash
pip install adb-pywrapper
```

Before using `adb-pywrapper`, ensure that ADB is installed on your machine and added to PATH. You can download and install the Android SDK, which includes ADB, from the official Android developer website.

If running the below in a terminal gives you an output, you are ready to go!

```bash
adb --version
```

## Getting Started

Import the necessary modules:

```python
from adb_pywrapper.adb_device import AdbDevice
from adb_pywrapper.adb_result import AdbResult
from adb_pywrapper.pull_result import PullResult
```

## Listing Connected Devices

You can list all connected devices using the `list_devices` method (this can be done before creating an instance):

Looks for connected adb devices and returns the device names in a list.    
`:return:` list of adb device names. Example: `['device-5554','AU9AD74','netagfer987']`
```python
devices = AdbDevice.list_devices()
```

### get_device_status
After which you can also get the status of said device without having initialized AdbDevice since this way you can see if the device might be `offline` or `unauthorized`

Get the status corresponding to the device_name. This uses the 'adb devices' command.  
`:param device_name:` the device adb name/identifier.  
`:return:` a string with the status of the given device. Example: 'offline', 'device' or 'unauthorized'
```python
status = AdbDevice.get_device_status('your_device_identifier')
```

# Creating an ADB Device Instance

To interact with a specific Android device, create an instance of the `AdbDevice` class. You can specify the device identifier as an argument (obtained from either Adb using `adb devices`).

```python
adb_device = AdbDevice(device='your_device_identifier')
```

## ADB Commands
All the commands below can be called once a device instance has been initiated. This is exemplified by the `adb_device` variable.

## getting root privileges
You can gain root privilages using the `root` method:

Restarts adb with root privileges.  
`:return:` AdbResult containing the completed process of `adb root`
```python
adb_device.root()
```
- Expected result: AdbResult instance with either `success=True and stdout='{device_status}'` or `success=False and stderr='ADB error'`

## Executing Shell Commands
You can excecute shell commands on the device using the `shell` method:

Executes a command on the shell of the device like: `adb shell {command}`  
`:param command:` the command to run on the shell of the connected device.  
`:return:` AdbResult containing the completed process of `adb shell {command}`
```python
shell_result = adb_device.shell(command="dumpsys activity")
```

## Pulling Files from the Device
You can pull files from the device using the `pull` method:

Copies a file off the device to a given local directory  
`:param file_to_pull:` complete path to the file to copy from the device  
`:param destination:` the directory in which the package file(s) are to be located. Will be created if needed.  
`:return:` A PullResult object with the completed_adb_process of the `adb pull` action, the destination path and a success flag

```python
pull_result = adb_device.pull(file_to_pull='/path/on/device/file', destination='/local/path')

#example usage
if pull_result.success:
    print(f"File pulled to: {pull_result.path}")
else:
    print(f"File pull failed. See {pull_result.completed_adb_process}.")
```

## Installing APKs

You can install APK files on the device using the `install` method:

Installs a given apk on the connected device.  
`:param apk_path:` the location of the apk file on the local machine  
`:param r: -r option:` replace already installed application. This is needed on physical devices or if you get an error that the application already exists and should be uninstalled first.  
`:return:` the completed process of 'adb install [-r] {apk_path}'  

```python
install_result = adb_device.install(apk_path='/local/path/to/apk')
if install_result.success:
    print("APK installed successfully.")
else:
    print("APK installation failed.")
```

## Opening Intents
You can open intents on the device using the `open_intent` method. This is useful for opening URLs:

Opens a given url on the device by starting an intent. If a default app is associated with this URL, this will  
result in the app being opened.  
`:param url:` The URL to open  
`:return:` the completed process of adb shell and start -a android.intent.action.VIEW -d '{url}'  
```python
intent_result = adb_device.open_intent(url='http://example.com')
if intent_result.success:
    print("Intent opened successfully.")
else:
    print("Failed to open intent.")
```

## Getting properties

You can get properties from the device using the `get_prop` method:

Retrieves the value of a given property through the `adb getprop method`  
`:param property:` the property from which the value is needed  
`:return:` the value of the property, or None if the property doesn't exist  
```python
intent_result = adb_device.open_intent(url='http://example.com')
if intent_result.success:
    print("Intent opened successfully.")
else:
    print("Failed to open intent.")
```

## Overview

We cannot cover everything in detail here, but here is a more general overview of all the functionality

#### Initialization and Connection:  
* AdbDevice(device=None, check_device_exists=True)  
* get_device_status(device_name)  

#### General Information:  
* get_device_status(device_name)  
* get_state()  

#### Executing Shell Commands:  
* shell(command, timeout=None)  
* root()  
* wait_for_device()  
* emu_avd(command)  

#### Management of Installed Packages:  
* installed_packages()  
* path_package(package_name)  
* package_versions(package_name)  

#### File Management:  
ls(path)  
* pull(file_to_pull, destination)  
* pull_multi(files_to_pull, destination)  

#### APK Management:  
* pull_package(package_name, destination)  
* install(apk_path, r=False)  
* install_multiple(apk_paths, r=False)

#### Intent and URL Handling:  
* open_intent(url)

#### Emulator Snapshot Management:  
* snapshots_list()  
* snapshot_exists(snapshot_name)  
* snapshot_load(snapshot_name)  
* snapshot_save(snapshot_name)  
* snapshot_delete(delete=None)  

## Error Handling
Be sure to handle errors gracefully in your code, as various operations may fail, adb-pywrapper tries to provide information where possible on success or failure in the `AdbResult` and `PullResult` objects.

## Contributing
Contributions to the adb-pywrapper package are welcome. If you encounter any issues, have suggestions, or want to contribute, feel free to open an issue or PR. Find our contribution guidelines [here](CONTRIBUTING.md).
