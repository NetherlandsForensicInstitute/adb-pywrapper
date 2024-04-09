from setuptools import setup

setup(
    name="adb_py",
    version="0.9",
    description="adb_py facilitates seamless interaction with Android devices using the Android Debug Bridge (ADB) "
                "directly within Python scripts.",
    author="Netherlands Forensic Institute",
    licence="EUPL-1.2",
    py_modules=["adb_py", "adb_init"],
)
