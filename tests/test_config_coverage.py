import pytest
from unittest.mock import patch, MagicMock
from hydra_logger.config import (
    load_config,
    create_log_directories,
    LoggingConfig,
    LogLayer,
    LogDestination,
)


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/tmp/does_not_exist.yaml")


def test_load_config_unsupported_extension(tmp_path):
    file = tmp_path / "config.unsupported"
    file.write_text("foo: bar")
    with pytest.raises(ValueError, match="Unsupported config file format"):
        load_config(file)


def test_load_config_empty_yaml(tmp_path):
    file = tmp_path / "empty.yaml"
    file.write_text("")
    with pytest.raises(ValueError, match="empty or invalid"):
        load_config(file)


def test_load_config_yaml_parse_error(tmp_path):
    file = tmp_path / "bad.yaml"
    file.write_text("foo: [unclosed")
    with pytest.raises(ValueError, match="Failed to parse YAML"):
        load_config(file)


def test_load_config_toml_parse_error(tmp_path):
    file = tmp_path / "bad.toml"
    file.write_bytes(b"invalid =")
    with patch("hydra_logger.config.tomllib") as mock_tomllib:
        mock_tomllib.load.side_effect = Exception("TOML parse error")
        with pytest.raises(ValueError, match="Failed to load configuration"):
            load_config(file)


def test_load_config_general_exception(tmp_path):
    file = tmp_path / "bad.yaml"
    file.write_text("foo: bar")
    with patch("hydra_logger.config.yaml.safe_load", side_effect=Exception("fail")):
        with pytest.raises(ValueError, match="Failed to load configuration"):
            load_config(file)


def test_create_log_directories_oserror(tmp_path):
    config = LoggingConfig(
        layers={
            "LAYER": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(type="file", path=str(tmp_path / "logs/app.log"))
                ],
            )
        }
    )
    with patch("os.makedirs", side_effect=OSError("fail")):
        with pytest.raises(OSError, match="Failed to create log directory"):
            create_log_directories(config)


def test_tomllib_import_logic(monkeypatch):
    """Test TOML import fallback logic."""
    # Test that the module can be imported and has the expected attributes
    import hydra_logger.config as config_mod

    assert hasattr(config_mod, "tomllib")
    assert hasattr(config_mod, "TOMLDecodeError")

    # Test that we can access the tomllib module
    assert config_mod.tomllib is not None


def test_toml_decode_error_handling(tmp_path):
    """Test TOML decode error handling."""
    file = tmp_path / "bad.toml"
    file.write_bytes(b"invalid =")

    with patch("hydra_logger.config.tomllib") as mock_tomllib:
        mock_tomllib.load.side_effect = Exception("TOML decode error")
        with pytest.raises(ValueError, match="Failed to parse TOML"):
            load_config(file)


def test_attribute_error_handling():
    """Test AttributeError handling in TOML import."""
    with patch("hydra_logger.config.tomllib", MagicMock()) as mock_tomllib:
        # Remove TOMLDecodeError attribute
        del mock_tomllib.TOMLDecodeError
        import importlib
        import hydra_logger.config as config_mod

        importlib.reload(config_mod)
        assert hasattr(config_mod, "TOMLDecodeError")
