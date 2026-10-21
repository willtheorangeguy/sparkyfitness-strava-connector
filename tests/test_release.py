"""Prevent publishing mismatched versions or moving stable tags for prereleases."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "release_metadata", Path(__file__).resolve().parents[1] / "scripts/release_metadata.py"
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def test_stable_release_metadata():
    result = release.release_metadata("v0.1.0", False, "0.1.0", "0.1.0", "Example/Connector")
    assert result == {"version": "0.1.0", "minor": "0.1", "stable": "true", "image": "ghcr.io/example/connector"}


def test_prerelease_does_not_get_stable_aliases():
    result = release.release_metadata("v0.2.0-rc.1", True, "0.2.0-rc.1", "0.2.0-rc.1", "owner/repo")
    assert result["stable"] == "false"
    assert result["version"] == "0.2.0-rc.1"


@pytest.mark.parametrize("tag,prerelease,version,source_version", [
    ("0.1.0", False, "0.1.0", "0.1.0"),
    ("v00.1.0", False, "00.1.0", "00.1.0"),
    ("v0.1.0", False, "0.2.0", "0.2.0"),
    ("v0.1.0", False, "0.1.0", "0.2.0"),
    ("v0.1.0", True, "0.1.0", "0.1.0"),
    ("v0.2.0-rc.1", False, "0.2.0-rc.1", "0.2.0-rc.1"),
    ("v0.2.0-rc.01", True, "0.2.0-rc.01", "0.2.0-rc.01"),
    ("v0.1.0\nlatest", False, "0.1.0", "0.1.0"),
])
def test_reject_invalid_release(tag, prerelease, version, source_version):
    with pytest.raises(ValueError):
        release.release_metadata(tag, prerelease, version, source_version, "owner/repo")


@pytest.mark.parametrize("version", ["0.2.0", "0.2.0-rc.1"])
def test_release_downloads_target_actual_image_and_version(tmp_path, version):
    assets_spec = importlib.util.spec_from_file_location(
        "release_assets", Path(__file__).resolve().parents[1] / "scripts/release_assets.py"
    )
    assets = importlib.util.module_from_spec(assets_spec)
    assets_spec.loader.exec_module(assets)
    assets.render("ghcr.io/fork-owner/custom-connector", version, tmp_path)
    assert {p.name for p in tmp_path.iterdir()} == {"docker-compose.yml", "env.example", "docker-compose.sparkyfitness.yml", "sparkyfitness.env.example", "docker-compose.media.yml"}
    for name in ("docker-compose.yml", "docker-compose.sparkyfitness.yml", "docker-compose.media.yml"):
        content = (tmp_path / name).read_text()
        assert "ghcr.io/fork-owner/custom-connector" in content
        assert "CONNECTOR_VERSION:-" + version in content
        assert "build:" not in content and "STRAVA_CONNECTOR_PATH" not in content
        if name != "docker-compose.media.yml":
            assert "command: [watch]" in content
            assert "restart: unless-stopped" in content
    assert 'CONNECTOR_VERSION:-'+version+'}-media' in (tmp_path/'docker-compose.media.yml').read_text()
    assert "CONNECTOR_VERSION=" + version + "\n" in (tmp_path / "env.example").read_text()
    assert "STRAVA_CONNECTOR_VERSION=" + version + "\n" in (tmp_path / "sparkyfitness.env.example").read_text()
