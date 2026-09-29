# Incident insights

A Streamlit dashboard for submitted incident reports by branch, incident type, severity, year, and named activity place. The filters in the sidebar apply throughout the dashboard.

## Run locally

Download or clone the whole repository. In Terminal:

```bash
cd path/to/mountaineers-incident-dashboard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`). On Windows, activate with `.venv\Scripts\activate` instead. Stop with Control+C in Terminal.

## Project files

| File | Purpose |
| --- | --- |
| `app.py` | Dashboard and global filters |
| `data/incidents_clean.csv` | Included de-identified report data (1,075 rows) |
| `data/locations.csv` | **Editable list of all 455 named places**, with seven known representative coordinates and blank latitude/longitude for the rest |
| `prepare_data.py` | Refresh cleaned reports and append newly named places without overwriting coordinate edits |
| `tests/` | Data preparation and location lookup checks |
| `CONTRIBUTING.md` | Collaboration and data handling guidance |

### Filter definitions

The export calls Minor, Significant, Near Miss, etc. **Incident Type**; the dashboard calls this **Severity**. The export's **Incident Category** (slip/trip/fall, illness, etc.) is called **Incident type** in the dashboard. The original labels are retained, including Near Miss and Safety Concern, without imposing an unsupported severity ordering.

### Improve the map

Open `data/locations.csv` in Excel or another CSV editor. Find a `place`, fill in **both** `latitude` and `longitude` in decimal degrees, and record `location_precision`, `source_url`, and any caveat in `notes`. Save as a CSV with the same filename, then refresh the running dashboard. Do not alter the `place` text or create duplicate place rows. The map will display every branch covered by the global filters; use the Branch filter for Everett alone. Blank and invalid coordinates remain listed under *Places still needing coordinates*.

The seven initial coordinates are reference locations for Leavenworth, Exit 38, Lake Sammamish State Park, Seattle Program Center, Squamish, The Tooth, and Stevens Pass Ski Area. They are **not incident locations**. See source links and precision notes in the lookup. Some place names cover a city, large recreation area, traverse, or multiple peaks. Leave those unmapped until a useful representative point is confirmed.

### Refresh the report export

Keep the original export **outside** this repository because it includes personal information and narratives. From the repository root:

```bash
python prepare_data.py "/path/to/File an Incident Report-2.csv"
python -m unittest discover -s tests -v
```

This removes exact duplicate rows, selects fields needed for analysis, and preserves edits to `data/locations.csv` while adding new place names. `report_id` is regenerated and is not a stable source identifier.

## Interpretation

- The source has 1,087 rows; 12 exact duplicate rows were removed, leaving 1,075 reports. A report is not necessarily a distinct real-world event.
- Trends use **activity start date**, since an incident occurrence or report submission date is unavailable. An activity spanning years belongs to its start year.
- 2005 and 2018 each have one report. 2026 data end at September 19 and are partial. Reporting completeness may vary by year or branch.
- These are counts, not incident rates. Comparing safety risk requires denominators such as number of activities or participants.
- The included cleaned CSV omits reporter and leader contact details, narrative text, attachments, and activity URLs. Review the dataset and your organization's sharing rules before making a public GitHub repository. A **private** repository is the safer default for initial collaboration.

## Collaborate with GitHub

Create an empty **private** repository on GitHub (do not initialize it with a README, since this project has one). From this folder run:

```bash
git init
git add .
git commit -m "Initial incident dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-REPO.git
git push -u origin main
```

Invite your collaborator under the repository's **Settings → Collaborators**. They can clone the repository, create a branch, and open a pull request. See `CONTRIBUTING.md`.
