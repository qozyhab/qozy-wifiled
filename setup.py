import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md")) as f:
    README = f.read()

requires = [
    "flux_led",
]
setup(
    name="qozy-wifiled",
    version="0.1",
    description="qpzy-WifiLED Plugin",
    long_description=README,
    author="qozy.io",
    author_email="contact@qozy.io",
    url="https://www.qozy.io",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    entry_points={
        "qozy.bridge": [
            "wifiled = qozy_wifiled.bridge:WifiLED",
        ]
    },
)
