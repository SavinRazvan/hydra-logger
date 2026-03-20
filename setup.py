"""
Role: Package build and distribution entrypoint.
Used By:
 - `pip`/`setuptools` build and packaging workflows.
Depends On:
 - pathlib
 - setuptools
Notes:
 - Defines package metadata, dependencies, and distribution settings.
"""

from pathlib import Path
import re

from setuptools import find_packages, setup

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")
init_text = (this_directory / "hydra_logger" / "__init__.py").read_text(encoding="utf-8")
version_match = re.search(r'^__version__\s*=\s*"([^"]+)"', init_text, re.MULTILINE)
if not version_match:
    raise RuntimeError("Could not determine package version from hydra_logger/__init__.py")
package_version = version_match.group(1)

setup(
    name="hydra-logger",
    version=package_version,
    author="Savin Ionut Razvan",
    author_email="razvan.i.savin@gmail.com",
    license="MIT",
    description="A dynamic, multi-headed logging system for Python applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SavinRazvan/hydra-logger",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: System :: Logging",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    install_requires=[
        "pydantic>=2.10.0",
        "pyyaml>=6.0.3",
        "aiofiles>=24.0.0",
        "pytz>=2025.0",
        "toml>=0.10.2",
        "requests>=2.32.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.0",
            "pytest-cov>=5.0.0",
            "pytest-mock>=3.14.0",
            "black>=24.8.0",
            "flake8>=7.0.0",
            "isort>=5.13.0",
            "mypy>=1.14.0",
            "types-aiofiles>=24.1.0.20250809",
            "types-psutil>=7.0.0.20250809",
            "types-PyYAML>=6.0.12.20250809",
            "types-pytz>=2025.2.0.20250809",
            "types-requests>=2.32.0.20250328",
            "types-toml>=0.10.8.20240310",
            "pyright>=1.1.400",
            "bandit>=1.7.10",
            "tomli-w>=1.0.0",
            "psutil>=7.1.0",
        ],
        "perf": [
            "psutil>=7.1.0",
        ],
        # Optional: pulls transitive `nltk` (known pip-audit noise until NLTK ships fixes).
        "legacy_safety": [
            "safety>=3.6.2",
        ],
        "database": [
            "psycopg2-binary>=2.9.10",
            "pymongo>=4.10.0",
            "redis>=6.1.0",
        ],
        "cloud": [
            "boto3>=1.37.0",
            "elasticsearch>=9.0.0",
        ],
        "queues": [
            "pika>=1.3.2",
            "kafka-python>=2.2.0",
        ],
        "network": [
            "websockets>=13.0.0",
        ],
        "system": [
            "pywin32>=306; sys_platform == 'win32'",
        ],
        "full": [
            "psycopg2-binary>=2.9.10",
            "pymongo>=4.10.0",
            "redis>=6.1.0",
            "pika>=1.3.2",
            "kafka-python>=2.2.0",
            "boto3>=1.37.0",
            "elasticsearch>=9.0.0",
            "websockets>=13.0.0",
            "pywin32>=306; sys_platform == 'win32'",
        ],
        "all": [
            "psycopg2-binary>=2.9.10",
            "pymongo>=4.10.0",
            "redis>=6.1.0",
            "pika>=1.3.2",
            "kafka-python>=2.2.0",
            "boto3>=1.37.0",
            "elasticsearch>=9.0.0",
            "websockets>=13.0.0",
            "pywin32>=306; sys_platform == 'win32'",
        ],
    },
    include_package_data=False,
    entry_points={
        "console_scripts": [
            "hydra-logger=hydra_logger.cli:main",
        ],
        "hydra_logger.http_encoders": [],
    },
)
