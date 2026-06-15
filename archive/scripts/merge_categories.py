import os

base_dir = r"C:\Users\Cleidson\Pictures\fin_analytics_v2"

arch_files = [
    "V2_DOMAIN_ARCHITECTURE.md",
    "V2_DATABASE_ARCHITECTURE.md",
    "V2_BACKEND_ARCHITECTURE.md",
    "V2_FRONTEND_ARCHITECTURE.md",
    "V2_MIGRATION_PLAN.md",
    "V2_DEBT_ELIMINATION_PLAN.md"
]

gov_files = [
    "SYSTEM_FREEZE_REPORT.md",
    "BRANCH_GOVERNANCE.md",
    "REBUILD_EXECUTION_PLAN.md",
    "REBUILD_PIPELINE.md",
    "MERGE_POLICY.md",
    "REBUILD_RISKS.md",
    "V2_BOOTSTRAP_REPORT.md",
    "V2_DATABASE_BACKLOG.md"
]

def merge_files(output_name, file_list, title):
    output_path = os.path.join(base_dir, output_name)
    with open(output_path, 'w', encoding='utf-8') as outf:
        outf.write(f"# {title}\n\n")
        outf.write("Este documento consolida as diretrizes da respectiva categoria da Fase 10.\n\n")
        for fname in file_list:
            fpath = os.path.join(base_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as inf:
                    outf.write(inf.read())
                    outf.write("\n\n---\n\n")
                os.remove(fpath)

merge_files("V2_ARCHITECTURE_MASTER_PLAN.md", arch_files, "FIN ANALYTICS V2 - ARCHITECTURE MASTER PLAN")
merge_files("V2_GOVERNANCE_AND_BOOTSTRAP.md", gov_files, "FIN ANALYTICS V2 - GOVERNANCE AND BOOTSTRAP")

print("Merge completed successfully.")
