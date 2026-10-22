> Release v0.2.0: automatic export cards are implemented. See the main README's automatic cards section for worker setup, durable job status and recovery. Historical preview milestones below describe earlier published releases.

# Experimental SparkyFitness cards

Ported from wger-strava-connector v0.2.1: midnight blue, enlarged muscle diagrams,
30 illustrated weight comparisons, and saved browser login. Preview data is synthetic.

Run `docker compose -f compose.media.yaml run --rm preview` to render four 1080×1080
cards, `concepts.png`, and `comparison-catalog.png` into `design/previews/`.
The renderer uses local artwork/fonts and blocks network requests.

Run `docker compose -f compose.media.yaml run --rm --service-ports media-login` for
the loopback viewer at http://localhost:6080/vnc.html. Use the printed password,
sign in manually, then stop with Ctrl+C to preserve cookies. For remote hosts:
`ssh -N -L 6080:127.0.0.1:6080 user@host`. Profiles are private and exclusively locked.

`compose.media.test.yaml` uses real Chromium against a mock website to test
rendering, persistent login, identity checks, attachment, duplicates, and recovery.
`attach_mock` rejects live URLs. Automatic attachment and source muscle highlighting were verified in the v0.2.0
implementation; see the main README and validation notes.

Inter retains its SIL Open Font License. Most artwork is MIT licensed; the adapted
carrier illustration is CC BY-SA 4.0 with its bundled attribution notice.
Comparison masses are illustrative approximate reference values.
