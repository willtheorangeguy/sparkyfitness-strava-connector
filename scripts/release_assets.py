"""Render portable setup downloads for the actual released image and version."""
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def render(image, version, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for source, name in [("docker-compose.yml", "docker-compose.yml"), (".env.example", "env.example"),
                         ("examples/docker-compose.sparkyfitness.yml", "docker-compose.sparkyfitness.yml"),
                         ("examples/sparkyfitness.env.example", "sparkyfitness.env.example"),
                         ("examples/docker-compose.media.yml", "docker-compose.media.yml")]:
        content = (ROOT / source).read_text(encoding="utf-8")
        content = content.replace("ghcr.io/willtheorangeguy/sparkyfitness-strava-connector", image)
        content = re.sub(r"(?m)^((?:STRAVA_)?CONNECTOR_VERSION)=.*$", lambda m: m[1] + "=" + version, content)
        content = re.sub(r"(CONNECTOR_VERSION:-)[^}]+", lambda m: m[1] + version, content)
        (destination / name).write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    render(os.environ["IMAGE"], os.environ["VERSION"], ROOT / "release-assets")
