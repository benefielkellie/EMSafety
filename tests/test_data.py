import tempfile
import unittest
from pathlib import Path
import pandas as pd
from prepare_data import prepare, LOCATION_COLUMNS

ROOT = Path(__file__).resolve().parents[1]

class DataChecks(unittest.TestCase):
    def test_included_data_and_lookup(self):
        df = pd.read_csv(ROOT/'data/incidents_clean.csv')
        locations = pd.read_csv(ROOT/'data/locations.csv')
        self.assertEqual(len(df), 1075)
        self.assertEqual(len(locations), df.place.nunique())
        self.assertFalse(locations.place.duplicated().any())
        self.assertEqual(len(df[df.branch.eq('Everett')]),83)
        mapped = df[df.branch.eq('Everett')].merge(locations,on='place',validate='many_to_one')
        self.assertEqual(int(mapped.latitude.notna().sum()),27)
        self.assertTrue(set(LOCATION_COLUMNS).issubset(locations.columns))
        self.assertFalse({'Submitter Email','Incident Narrative','Primary Leader Phone'} & set(df.columns))

    def test_refresh_keeps_manual_coordinates_and_adds_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            raw = pd.DataFrame({
                'Activity Start Date':['Jan 2, 2024','Jan 2, 2024','Jan 3, 2024'],
                'Activity End Date':['Jan 2, 2024']*2+['Jan 3, 2024'],
                'Branch':['Everett']*3, 'Incident Type':['Minor']*3,
                'Incident Category':['Slip, trip, fall']*3,
                'Activity Type':['Climbing']*3, 'Activity Category':['Trip']*3,
                'Time of Day':['Morning']*3, 'Route/Place Title':['Known','Known','New'],
                'Submitter Email':['a@example.com']*3})
            source=tmp/'export.csv'; output=tmp/'clean.csv'; lookup=tmp/'locations.csv'
            raw.to_csv(source,index=False)
            pd.DataFrame([{'place':'Known','latitude':'47.5','longitude':'-121.2',
                'location_precision':'summit','source_url':'https://example.org','notes':'checked'}]).to_csv(lookup,index=False)
            result=prepare(source,output,lookup)
            self.assertEqual(result['duplicate_rows_removed'],1)
            saved=pd.read_csv(lookup).set_index('place')
            self.assertEqual(saved.loc['Known','latitude'],47.5)
            self.assertEqual(saved.loc['Known','notes'],'checked')
            self.assertTrue(pd.isna(saved.loc['New','latitude']))
            self.assertEqual(len(pd.read_csv(output)),2)

if __name__ == '__main__':
    unittest.main()
