from setuptools import setup

setup(
    name="adb-pywrapper",
    version="1.0.0",
    description="adb-pywrapper facilitates seamless interaction with Android devices using the Android Debug Bridge (ADB) "
                "directly within Python scripts.",
    long_description=f"{open('README.md').read()}",
    long_description_content_type="text/markdown",
    author="Netherlands Forensic Institute",
    author_email="netherlandsforensicinstitute@users.noreply.github.com",
    url="https://github.com/NetherlandsForensicInstitute/adb-pywrapper",
    licence="EUPL-1.2",
    py_modules=["adb-pywrapper", "adb_init"],
    test_suite="test",
)
