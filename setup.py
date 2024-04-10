from setuptools import setup

setup(
    name="adb_py",
    version="0.9",
    description="adb_py facilitates seamless interaction with Android devices using the Android Debug Bridge (ADB) "
                "directly within Python scripts.",
    long_description=f"{open('README.md').read()}",
    author="Netherlands Forensic Institute",
    author_email="netherlandsforensicinstitute@users.noreply.github.com",
    url="https://github.com/NetherlandsForensicInstitute/adb_py",
    licence="EUPL-1.2",
    py_modules=["adb_py", "adb_init"],
    test_suite="test",
)
