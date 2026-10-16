"""Acquire dated DBT releases without credentials; retain bytes and SHA-256 provenance."""
from pathlib import Path
from urllib.request import urlopen, Request
from datetime import datetime, timezone
import json, hashlib, re
import xml.etree.ElementTree as ET
from zipfile import ZipFile
import csv

ROOT = Path(__file__).resolve().parents[1]
NS = {k: f'urn:oasis:names:tc:opendocument:xmlns:{v}:1.0' for k,v in
      [('t','table'),('o','office'),('x','text')]}

def fetch(url):
    with urlopen(Request(url,headers={'User-Agent':'Academic replication archive'}),timeout=90) as f:
        return f.read()

def extract(path):
    with ZipFile(path) as z:
        doc = ET.fromstring(z.read('content.xml'))
    tables = doc.findall('.//t:table',NS)
    table = next(t for t in tables if t.get('{'+NS['t']+'}name')=='Table_1')
    records=[]
    header=None
    for row in table.findall('t:table-row',NS):
        vals=[]
        for cell in row:
            n=int(cell.get('{'+NS['t']+'}number-columns-repeated','1'))
            value=cell.get('{'+NS['o']+'}value')
            if value is None:
                value=' '.join(''.join(p.itertext()) for p in cell.findall('x:p',NS))
            vals.extend([value]*min(n,32))
        if vals and vals[0]=='Partner ISO':
            header=vals[:next((i for i,v in enumerate(vals) if not v),len(vals))]
        elif header and len(vals)>3 and vals[3] in ['2021','2022','2023','2024']:
            records.append(dict(zip(header,vals[:len(header)])))
    if header is None or not records:
        raise ValueError(f'Unrecognized source layout: {path}')
    return header,records

def main():
    saved=ROOT/'data/source_manifest.json'
    if saved.exists():
        for m in json.loads(saved.read_text()):
            path=ROOT/'data/raw'/f"{m['year']}_{m['direction']}.ods"
            if hashlib.sha256(path.read_bytes()).hexdigest()!=m['sha256']:
                raise ValueError(f'Archived file changed: {path}')
            header,rows=extract(path)
            with (ROOT/'data/processed'/f"{m['year']}_{m['direction']}.csv").open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=header,lineterminator='\n');writer.writeheader();writer.writerows(rows)
        print('Re-extracted the verified archived vintage; no network access used.')
        return
    manifest=[]
    for year in range(2021,2025):
        page=f'https://www.gov.uk/government/statistics/preference-utilisation-of-uk-trade-in-goods-{year}'
        html=fetch(page).decode()
        for direction in ['imports','exports']:
            urls=set(re.findall(r'https://assets\.publishing\.service\.gov\.uk/[^"<>\s]+\.ods',html))
            matches=[u for u in urls if f'{direction}-pur-database-{year}.ods' in u]
            if len(matches)!=1:
                raise ValueError(f'Expected one database for {year} {direction}: {matches}')
            url=matches[0]; path=ROOT/'data/raw'/f'{year}_{direction}.ods'
            if not path.exists(): path.write_bytes(fetch(url))
            header,rows=extract(path)
            out=ROOT/'data/processed'/f'{year}_{direction}.csv'
            with out.open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=header,lineterminator='\n');writer.writeheader();writer.writerows(rows)
            manifest.append(dict(year=year,direction=direction,page=page,url=url,
                retrieved_utc=datetime.now(timezone.utc).isoformat(),bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),rows=len(rows)))
    (ROOT/'data/source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
