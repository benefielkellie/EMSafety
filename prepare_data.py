"""Create de-identified report data and maintain an editable place lookup."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

COLUMNS = {
    'Activity Start Date': 'activity_start_date',
    'Activity End Date': 'activity_end_date',
    'Branch': 'branch',
    'Incident Type': 'severity',
    'Incident Category': 'incident_type',
    'Activity Type': 'activity_type',
    'Activity Category': 'activity_category',
    'Time of Day': 'time_of_day',
    'Route/Place Title': 'place',
}
LOCATION_COLUMNS = ['place', 'latitude', 'longitude', 'location_precision', 'source_url', 'notes']


def prepare(source: Path, output: Path, lookup: Path) -> dict:
    raw = pd.read_csv(source, dtype='string', keep_default_na=False)
    absent = set(COLUMNS) - set(raw.columns)
    if absent:
        raise ValueError(f'Missing source columns: {sorted(absent)}')
    duplicates = int(raw.duplicated().sum())
    unique = raw.drop_duplicates().reset_index(drop=True)
    df = unique[list(COLUMNS)].rename(columns=COLUMNS).copy()
    for column in df:
        df[column] = df[column].str.strip().replace('', pd.NA)
    for column in ('branch', 'severity', 'incident_type'):
        df[column] = df[column].fillna('Unknown')
    for column in ('activity_start_date', 'activity_end_date'):
        df[column] = pd.to_datetime(df[column], format='%b %d, %Y', errors='coerce')
    df['year'] = df.activity_start_date.dt.year.astype('Int64')
    df.insert(0, 'report_id', range(1, len(df) + 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False, date_format='%Y-%m-%d')

    places = sorted(df.place.dropna().unique().tolist())
    if lookup.exists():
        existing = pd.read_csv(lookup, dtype='string', keep_default_na=False)
        if not set(LOCATION_COLUMNS).issubset(existing):
            raise ValueError(f'Location lookup needs columns: {LOCATION_COLUMNS}')
        if existing.place.duplicated().any():
            raise ValueError('Location lookup has duplicate place names')
        existing = existing[LOCATION_COLUMNS]
    else:
        existing = pd.DataFrame(columns=LOCATION_COLUMNS)
    additions = pd.DataFrame({'place': [p for p in places if p not in set(existing.place)]})
    for column in LOCATION_COLUMNS[1:]:
        additions[column] = ''
    # Keep prior edits, including old places no longer represented in a refresh.
    locations = pd.concat([existing, additions], ignore_index=True).sort_values('place')
    locations.to_csv(lookup, index=False)
    return {'source_rows':len(raw), 'duplicate_rows_removed':duplicates,
            'reports':len(df), 'named_places':len(places),
            'new_places':len(additions), 'missing_start_dates':int(df.activity_start_date.isna().sum())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Original export; keep it outside the Git repository')
    parser.add_argument('--output', type=Path, default=Path('data/incidents_clean.csv'))
    parser.add_argument('--locations', type=Path, default=Path('data/locations.csv'))
    args = parser.parse_args()
    print(prepare(args.source, args.output, args.locations))
