# Contributing

1. Create a branch from `main`, make a focused change, and open a pull request.
2. Run `python -m unittest discover -s tests -v` before submitting.
3. Do not commit the original incident export, names, emails, phone numbers, narratives, or attachments. The included report table contains selected fields only, but review additions before publishing.
4. When editing `data/locations.csv`, keep each `place` value exactly as shown, one row per place. Enter decimal latitude and longitude together, with a source URL and a note such as `city center`, `trailhead`, or `summit`. A mapped activity place is not a verified incident point. Leave uncertain places blank.
5. Resolve uncertain or multi-place names with another reviewer before placing a marker. Do not change coordinates merely to make the map look complete.
6. If the source export is refreshed, keep it outside the repository and run `python prepare_data.py /path/to/export.csv` from the repository root. This preserves existing location edits and appends new place names.
