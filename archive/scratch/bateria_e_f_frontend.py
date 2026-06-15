import os
import re

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "src")
if not os.path.exists(FRONTEND_DIR):
    FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

def check_frontend():
    print("Iniciando Bateria E e F - Performance e Console Zero (Frontend)...")
    
    issues_found = 0
    console_logs = []
    hooks_without_callback = []
    
    # regex to find hooks
    # Look for export function use*
    
    for root, dirs, files in os.walk(FRONTEND_DIR):
        if "node_modules" in root or ".next" in root or "dist" in root:
            continue
            
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                path = os.path.join(root, file)
                
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    
                # Check console.log
                for i, line in enumerate(lines):
                    if "console.log(" in line and not line.strip().startswith("//"):
                        console_logs.append(f"{path}:{i+1} -> {line.strip()}")
                        
                # Check if it's a hook file (useWealthData, useTransactions)
                if "hooks" in root and file.startswith("use"):
                    content = "".join(lines)
                    # Simple heuristic: if it returns functions, are they wrapped in useCallback?
                    # This is just a warning mechanism
                    if "return {" in content or "return [" in content:
                        if "useCallback" not in content and ("=>" in content or "function " in content):
                            hooks_without_callback.append(path)

    print("\n[BATERIA E] Console Zero:")
    if not console_logs:
        print("  [OK] Nenhum console.log residual encontrado.")
    else:
        print(f"  [X] Encontrados {len(console_logs)} console.log(s):")
        for log in console_logs[:5]:
            print(f"      {log}")
        if len(console_logs) > 5:
            print("      ...")
        issues_found += len(console_logs)

    print("\n[BATERIA F] Performance (useCallback em Hooks):")
    if not hooks_without_callback:
        print("  [OK] Hooks customizados parecem ok ou não possuem funções expostas sem memoização visível.")
    else:
        print(f"  [!] Alerta: {len(hooks_without_callback)} hook(s) não utilizam useCallback, mas expõem lógica.")
        for hook in hooks_without_callback[:5]:
            print(f"      {hook}")
        if len(hooks_without_callback) > 5:
            print("      ...")
        # Apenas um alerta para revisar, não falha direto se não for crasso

    print("\n--- RESUMO BATERIA E E F ---")
    if issues_found == 0:
        print("RESULTADO: SUCESSO. Front-end limpo.")
    else:
        print(f"RESULTADO: FALHA. Remover os console.log para aprovação na Bateria E.")

if __name__ == "__main__":
    check_frontend()
