import os

base_dir = r"C:\Users\Cleidson\Pictures\fin_analytics_v2"
files_to_combine = [
    "FRONTEND_INVENTORY.md",
    "FRONTEND_DEPENDENCY_MAP.md",
    "BACKEND_INVENTORY.md",
    "API_CONTRACT_FREEZE.md",
    "DATABASE_SPEC.md",
    "BUSINESS_RULES.md",
    "FLOW_MAP.md",
    "FEATURE_MATRIX.md",
    "DEAD_CODE_REPORT.md",
    "BUG_TRACEABILITY.md",
    "V2_REQUIREMENTS.md",
    "SYSTEM_REBUILD_SCORE.md"
]

output_file = os.path.join(base_dir, "SYSTEM_REBUILD_PACKAGE.md")

with open(output_file, 'w', encoding='utf-8') as outfile:
    outfile.write("# FIN ANALYTICS V2 - SYSTEM REBUILD PACKAGE\n\n")
    outfile.write("Este documento consolida toda a engenharia reversa e arquitetura extraída durante a Fase 10 (Inventory Freeze).\n\n")
    
    for f in files_to_combine:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
                outfile.write("\n\n---\n\n")
            # Delete the file after combining
            os.remove(path)

print(f"Reports combined into {output_file} and individual files deleted.")
