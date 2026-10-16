from pathlib import Path
import unittest,hashlib,json,csv
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

class DataTest(unittest.TestCase):
    def test_source_integrity_and_extraction(self):
        manifest=json.loads((ROOT/'data/source_manifest.json').read_text())
        self.assertEqual(len(manifest),8)
        for m in manifest:
            name=f"{m['year']}_{m['direction']}"
            data=(ROOT/'data/raw'/f'{name}.ods').read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),m['sha256'])
            with (ROOT/'data/processed'/f'{name}.csv').open() as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),m['rows'])
            mismatch=sum(r['Year']!=str(m['year']) for r in rows)
            self.assertEqual(mismatch,2593 if name=='2021_exports' else 0)

    def test_no_false_zero_or_duplicate_observations(self):
        x=pd.read_csv(ROOT/'data/processed/panel.csv',keep_default_na=False,dtype={'iso':str,'hs2':str})
        self.assertEqual(len(x),53161)
        self.assertTrue((x.declared_year==x.source_file_year).all())
        quarantine=pd.read_csv(ROOT/'data/processed/quarantined_year_mismatches.csv',keep_default_na=False)
        self.assertEqual(len(quarantine),2593)
        self.assertTrue((quarantine.source_file_year==2021).all())
        self.assertTrue((quarantine.declared_year==2023).all())
        self.assertFalse(x.duplicated(['iso','hs2','year','direction']).any())
        self.assertTrue((x.iso=='NA').any(),'Namibia ISO code must not become a missing value')
        self.assertTrue((x.used<=x.eligible).all());self.assertTrue((x.eligible>=0).all())

    def test_independent_published_controls(self):
        # DBT 2024 HTML, Tables 1 and 4, values rounded to GBP million.
        # Controls are reported in the primary statistical commentary, independently
        # of this package's ODS extraction and aggregation code.
        x=pd.read_csv(ROOT/'results/partner_statistics.csv')
        controls=[('CH','exports',142,87,61.2),('JP','exports',653,398,61.0),
            ('CH','imports',2888,2384,82.6),('JP','imports',3827,2889,75.5)]
        for iso,direction,e,p,u in controls:
            z=x[(x.iso==iso)&(x.direction==direction)&(x.year==2024)].iloc[0]
            self.assertLessEqual(abs(z.eligible/1e6-e),.5001)
            self.assertLessEqual(abs(z.used/1e6-p),.5001)
            self.assertLessEqual(abs(z.pur*100-u),.0501)

if __name__=='__main__':unittest.main(verbosity=2)
