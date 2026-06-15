import os

base_dir = r"C:\Users\Cleidson\Pictures\fin_analytics_v2"
files_to_read = [
    "app/api/services/analytics.py",
    "app/api/services/wealth.py",
    "services/categorizer.py",
    "app/api/services/governance_service.py",
    "etl/classifier.py",
    "etl/reconciler.py"
]

out_path = os.path.join(base_dir, "archive", "source_dump.txt")

with open(out_path, 'w', encoding='utf-8') as outfile:
    for f in files_to_read:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            outfile.write(f"\n{'='*20}\nFILE: {f}\n{'='*20}\n")
            with open(path, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
