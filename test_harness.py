"""Run real SparkyFitness integration tests with an isolated temporary account."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests"))
from seed_sparkyfitness import seed


def run(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sparkyfitness-harness", type=Path, default=ROOT.parent / "sparkyfitness-addon-harness")
    args = parser.parse_args()
    harness = args.sparkyfitness_harness.resolve()
    if not (harness / "harness.py").is_file():
        parser.error("Check out sparkyfitness-addon-harness alongside this repository")
    run([sys.executable, str(harness / "harness.py"), "up"])
    for name in ("runtime", "reports"):
        (ROOT / name).mkdir(exist_ok=True)
        (ROOT / name).chmod(0o777)
    stack = ["docker", "compose", "--project-directory", str(harness), "-f", str(harness / "compose.yaml")]
    # Capture rather than print Compose's resolved configuration: it contains secrets.
    resolved = json.loads(run(stack + ["config", "--format", "json"], capture_output=True, text=True).stdout)
    port = resolved["services"]["frontend"]["ports"][0]["published"]
    network = resolved["networks"]["default"]["name"]
    overlay = ROOT / "runtime/test-sparkyfitness.compose.json"
    overlay.write_text(json.dumps({
        "services": {"test": {"networks": ["default", "sparkyfitness-harness"]}},
        "networks": {"sparkyfitness-harness": {"external": True, "name": network}}}), encoding="utf-8")
    compose = ["docker", "compose", "-f", "compose.test.yaml", "-f", str(overlay)]
    credentials = ROOT / "runtime/test-credentials.json"
    email = "strava-connector-it-" + uuid.uuid4().hex + "@example.test"
    try:
        seed("http://localhost:" + str(port), email, "TestOnly-" + uuid.uuid4().hex + "!", credentials)
        credentials.chmod(0o600)
        run(compose + ["build", "test"])
        run(compose + ["up", "-d", "--wait", "mock-strava"])
        run(compose + ["run", "--rm", "test"])
    finally:
        subprocess.run(compose + ["down"], cwd=ROOT, check=False)
        # This email is generated locally above, never supplied by the operator.
        # Delete only that dedicated test account; its owned data cascades.
        cleanup = 'DELETE FROM public."user" WHERE email = ' + "'" + email + "';"
        try:
            run(stack + ["exec", "-T", "db", "psql", "-U", "sparky", "-d", "sparkyfitness", "-v", "ON_ERROR_STOP=1"],
                input=cleanup, text=True)
        finally:
            credentials.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, RuntimeError) as error:
        print(f"Integration harness failed: {error}", file=sys.stderr)
        sys.exit(1)
