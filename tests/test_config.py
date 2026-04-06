from unittest.mock import patch
from gitai.config import load_config, save_config, DEFAULT_CONFIG


# --- load_config ---

def test_returns_defaults_when_no_file(tmp_path):
    config_path = tmp_path / ".gitai.toml"
    with patch("gitai.config.CONFIG_PATH", config_path):
        config = load_config()
    assert config == DEFAULT_CONFIG

def test_creates_config_file_when_missing(tmp_path):
    config_path = tmp_path / ".gitai.toml"
    with patch("gitai.config.CONFIG_PATH", config_path):
        load_config()
    assert config_path.exists()

def test_merges_partial_user_config_with_defaults(tmp_path):
    config_path = tmp_path / ".gitai.toml"
    config_path.write_bytes(b'model = "gpt-4o"\n')
    with patch("gitai.config.CONFIG_PATH", config_path):
        config = load_config()
    assert config["model"] == "gpt-4o"
    assert config["provider"] == DEFAULT_CONFIG["provider"]
    assert config["ollama_url"] == DEFAULT_CONFIG["ollama_url"]

def test_user_provider_overrides_default(tmp_path):
    config_path = tmp_path / ".gitai.toml"
    config_path.write_bytes(b'provider = "anthropic"\n')
    with patch("gitai.config.CONFIG_PATH", config_path):
        config = load_config()
    assert config["provider"] == "anthropic"

def test_user_emoji_true_overrides_default(tmp_path):
    config_path = tmp_path / ".gitai.toml"
    config_path.write_bytes(b'emoji = true\n')
    with patch("gitai.config.CONFIG_PATH", config_path):
        config = load_config()
    assert config["emoji"] is True


# --- save_config / roundtrip ---

def test_save_and_load_roundtrip(tmp_path):
    config_path = tmp_path / ".gitai.toml"
    custom = {**DEFAULT_CONFIG, "model": "mistral", "emoji": True}
    with patch("gitai.config.CONFIG_PATH", config_path):
        save_config(custom)
        loaded = load_config()
    assert loaded["model"] == "mistral"
    assert loaded["emoji"] is True

def test_save_writes_all_default_keys(tmp_path):
    config_path = tmp_path / ".gitai.toml"
    with patch("gitai.config.CONFIG_PATH", config_path):
        save_config(DEFAULT_CONFIG)
        loaded = load_config()
    assert set(loaded.keys()) == set(DEFAULT_CONFIG.keys())

def test_save_creates_file(tmp_path):
    config_path = tmp_path / ".gitai.toml"
    with patch("gitai.config.CONFIG_PATH", config_path):
        save_config(DEFAULT_CONFIG)
    assert config_path.exists()


# --- max_diff_chars default ---

def test_default_config_includes_max_diff_chars():
    assert "max_diff_chars" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["max_diff_chars"] == 12000

def test_load_config_includes_max_diff_chars_when_missing_from_file(tmp_path):
    config_path = tmp_path / ".gitai.toml"
    config_path.write_bytes(b'model = "gpt-4o"\n')
    with patch("gitai.config.CONFIG_PATH", config_path):
        config = load_config()
    assert config["max_diff_chars"] == 12000

def test_user_max_diff_chars_overrides_default(tmp_path):
    config_path = tmp_path / ".gitai.toml"
    config_path.write_bytes(b'max_diff_chars = 5000\n')
    with patch("gitai.config.CONFIG_PATH", config_path):
        config = load_config()
    assert config["max_diff_chars"] == 5000


# --- key validation ---

def test_unknown_key_prints_warning(tmp_path, capsys):
    config_path = tmp_path / ".gitai.toml"
    config_path.write_bytes(b'provder = "ollama"\n')
    with patch("gitai.config.CONFIG_PATH", config_path):
        load_config()
    captured = capsys.readouterr()
    assert "provder" in captured.out

def test_known_keys_produce_no_warning(tmp_path, capsys):
    config_path = tmp_path / ".gitai.toml"
    config_path.write_bytes(b'model = "gpt-4o"\nprovider = "openai"\n')
    with patch("gitai.config.CONFIG_PATH", config_path):
        load_config()
    captured = capsys.readouterr()
    assert captured.out == ""
