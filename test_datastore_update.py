from app.services.data_store import data_store
from app.database import SessionLocal

# Force update to reload data with enriched lineages
print("Forçando atualização do data_store...")
data_store.update_data()

print("\n=== Primeiros 3 players no data_store ===\n")
for i, p in enumerate(data_store.level_ranking[:3]):
    print(f'Player {i+1}: {p["name"]}')
    print(f'  Celestial Lineage: {p["celestial_lineage"]}')
    print(f'  Subclass Lineage: {p["subclass_lineage"]}')
    print()
