import pandas as pd, random, datetime as dt, json, os

DATA_DIR = "assets/data"
os.makedirs(DATA_DIR, exist_ok=True)

provinces = ["Gauteng","Free State","Mpumalanga","North West","Limpopo"]
towns = {
  "Gauteng":["Roodepoort","Bronkhorstspruit","Pretoria","Johannesburg"],
  "Free State":["Sasolburg","Welkom","Bloemfontein"],
  "Mpumalanga":["Secunda","Mbombela","Witbank"],
  "North West":["Stilfontein","Rustenburg","Klerksdorp"],
  "Limpopo":["Polokwane","Tzaneen","Mokopane"]
}
sectors = ["Retail","Commercial","Industrial","Governmental","Residential","Community"]

# --- Properties ---
props = []
for i in range(1,151):
    prov = random.choice(provinces); town = random.choice(towns[prov]); sec = random.choice(sectors)
    props.append([f"P{i:03d}",f"{sec} Facility {i}",sec,prov,town,round(-22-random.random()*6,5),round(25+random.random()*6,5)])
pd.DataFrame(props,columns=["property_id","property_name","sector","province","town","lat","lon"]).to_csv(f"{DATA_DIR}/properties.csv",index=False)
print("✅ properties.csv generated")

# --- Assets ---
asset_types=["Pipeline","Warehouse","Office","Truck","CCTV","Depot","Transformer","Fuel Tank"]; assets=[]
for i in range(1,401):
    pid=random.choice(props)[0]; assets.append([f"A{i:04d}",pid,random.choice(asset_types),random.choice(["Low","Medium","High"]),random.randint(5e5,5e7)])
pd.DataFrame(assets,columns=["asset_id","property_id","asset_type","criticality","insured_value"]).to_csv(f"{DATA_DIR}/assets.csv",index=False)
print("✅ assets.csv generated")

# --- Clients ---
clients=[]
for i in range(1,101):
    pid=random.choice(props)[0]; clients.append([f"C{i:03d}",f"Client {i}",random.choice(sectors),f"Manager {i}",f"083{random.randint(1000000,9999999)}",f"client{i}@secureco.co.za",pid])
pd.DataFrame(clients,columns=["client_id","client_name","sector","contact_person","phone","email","property_id"]).to_csv(f"{DATA_DIR}/clients.csv",index=False)
print("✅ clients.csv generated")

# --- Incidents ---
incident_types=["Robbery","Theft","Pipeline breach","Hijacking","Strike","Accident","Tampering","Vandalism","Crowd Control"]; statuses=["Reported","Under investigation","In pursuit","Open","Searching","Solved"]
incidents=[]; 
for i in range(1,801):
    if random.random()<0.12: prov,town,is_t="Transit","Transit",True; lat,lon=-24-random.random()*5,28+random.random()*5; pid=""
    else: pr=random.choice(props); prov,town,pid=pr[3],pr[4],pr[0]; is_t=False; lat,lon=pr[5],pr[6]
    inc_type=random.choice(incident_types)
    incidents.append([1000+i,f"{inc_type} {i}",random.choice(sectors),prov,town,inc_type,random.choice(["Low","Medium","Semi-High","High"]),random.choice(statuses),(dt.date(2023,1,1)+dt.timedelta(days=random.randint(0,650))).strftime("%Y-%m-%d"),f"{random.randint(0,23):02}:{random.randint(0,59):02}",lat,lon,pid,is_t,f"Details for incident {i}"])
pd.DataFrame(incidents,columns=["id","title","sector","province","town","incident_type","severity","status","date","time","lat","lon","property_id","is_transit","notes"]).to_csv(f"{DATA_DIR}/incidents.csv",index=False)
print("✅ incidents.csv generated")

# --- Coverage ---
geo={"type":"FeatureCollection","features":[]}
for prov in provinces:
    geo["features"].append({"type":"Feature","properties":{"province":prov},"geometry":{"type":"Polygon","coordinates":[[[24+random.random(),-22-random.random()*4],[30+random.random(),-22-random.random()*4],[30+random.random(),-26-random.random()*4],[24+random.random(),-26-random.random()*4],[24+random.random(),-22-random.random()*4]]]}})
with open(f"{DATA_DIR}/coverage.geojson","w") as f: json.dump(geo,f)
print("✅ coverage.geojson generated")

print("🎉 All seed data generated in assets/data/")
