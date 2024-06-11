from setuptools import setup, find_packages

setup(
    name="adb_pywrapper",
    version="1.0.1",
    packages=find_packages(),
    test_suite="test",

    description="adb_pywrapper facilitates seamless interaction with Android devices using the Android Debug Bridge (ADB) "
                "directly within Python scripts.",
    long_description=f"{open('README.md').read()}",
    long_description_content_type="text/markdown",
    author="Netherlands Forensic Institute",
    author_email="netherlandsforensicinstitute@users.noreply.github.com",
    url="https://github.com/NetherlandsForensicInstitute/adb-pywrapper",
    licence="EUPL-1.2",
)

