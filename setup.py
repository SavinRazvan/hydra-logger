"""
Setup script for Hydra-Logger package.

This module configures the package installation, dependencies, and metadata
for the Hydra-Logger distribution. It includes comprehensive package information,
development dependencies, and entry points for command-line usage.

The setup configuration supports both basic installation and development
environments with appropriate dependency management.
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="hydra-logger",
    version="0.1.0",
    author="Savin Ionut Razvan",
    author_email="razvan.i.savin@gmail.com",
    description="A dynamic, multi-headed logging system for Python applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SavinRazvan/hydra-logger",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Logging",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "python-json-logger>=2.0.0",
        "graypy>=2.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    include_package_data=True,
    package_data={
        "hydra_logger": ["examples/config_examples/*.yaml"],
    },
    entry_points={
        "console_scripts": [
            "hydra-logger=hydra_logger.examples.basic_usage:main",
        ],
    },
)
