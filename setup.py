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
    version="0.4.0",
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
        "python-json-logger>=4.0.0",
        "graypy>=2.1.0",
        "pytz>=2025.0",
        "toml>=0.10.2",
        "msgpack>=1.1.1",
        "psutil>=7.1.0",
        "requests>=2.32.0",
        "urllib3>=1.26.0,<3.0.0",
        "charset-normalizer>=3.4.0",
        # Database handlers
        "psycopg2-binary>=2.9.10",  # PostgreSQL
        "pymongo>=4.10.0",          # MongoDB
        "redis>=6.1.0",            # Redis
        # Message queue handlers
        "pika>=1.3.2",             # RabbitMQ
        "kafka-python>=2.2.0",     # Kafka
        # Cloud service handlers
        "boto3>=1.37.0",           # AWS CloudWatch
        "elasticsearch>=9.0.0",    # Elasticsearch
        # Network handlers
        "websockets>=13.0.0",      # WebSocket support
        # System handlers (Windows only - will be skipped on other platforms)
        "pywin32>=306; sys_platform == 'win32'",  # Windows Event Log
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
            "bandit>=1.7.10",
            "safety>=3.6.2",
            "tomli-w>=1.0.0",
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
