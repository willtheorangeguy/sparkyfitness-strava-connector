# Media validation

Validated October 21, 2026 with Docker Desktop Linux containers and real Chromium:
17 media tests passed. Report: `reports/media-tests.xml`.

The inherited suite covers both themes, deterministic rendering, 1080×1080 cards,
comparison artwork and layout, mock attachment, persistent browser login,
wrong-account rejection, duplicate prevention, and uncertain-save recovery.
The temporary headful viewer runs without a host display and shuts down cleanly.

Previews were regenerated with SparkyFitness branding. The renderer uses synthetic
data; production sync does not invoke it. No live Strava login/upload was performed
for this project, and no hosted CI results are claimed. Mock browser behavior does
not establish compatibility with live Strava selectors or photo processing.
