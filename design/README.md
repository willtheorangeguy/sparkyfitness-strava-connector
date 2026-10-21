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
`attach_mock` rejects live URLs. No live Strava photo upload was performed for this
project. Automatic card attachment is outside v0.1.0.

Inter retains its SIL Open Font License. Most artwork is MIT licensed; the adapted
carrier illustration is CC BY-SA 4.0 with its bundled attribution notice.
Comparison masses are illustrative approximate reference values.
