from __future__ import annotations

from setuptools import find_packages, setup

setup(
    name="kotor-diff",
    version="1.0.0",
    description="KotOR Diff Tool",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pykotor",
        "utility",
        # Add any other dependencies here
    ],
)
from setuptools import find_packages, setup

setup(
    name="kotor-diff",
    version="1.0.0",
    description="KotOR Diff",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pykotor",
        "utility",
    ],
)