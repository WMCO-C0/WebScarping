import json
import csv
import os
from datetime import datetime


def save_results(files, output_dir, filename=None):
    """Guarda los resultados en JSON y CSV."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if filename:
        # Limpiar nombre de archivo
        filename = filename.strip()
        filename = filename.replace('.json', '').replace('.csv', '')
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results_{timestamp}"
    
    # Guardar en JSON
    json_path = os.path.join(output_dir, f"{filename}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(files, f, indent=2, ensure_ascii=False)
    
    # Guardar en CSV
    csv_path = os.path.join(output_dir, f"{filename}.csv")
    if files:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=files[0].keys())
            writer.writeheader()
            writer.writerows(files)
    
    print(f"\nResultados guardados en:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")
    
    return json_path, csv_path


def load_results(json_path):
    """Carga resultados desde un archivo JSON."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)