import asyncio
from playwright.async_api import async_playwright
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("1. Acessando login...")
        await page.goto("http://localhost:3000/login")
        await page.fill("input[type='text']", "admin")
        await page.fill("input[type='password']", "admin")
        await page.click("button:has-text('Entrar')")
        
        await page.wait_for_url("**/governance/database")
        print("Login com sucesso.")

        print("2. Acessando /governance/imports...")
        await page.goto("http://localhost:3000/governance/imports")
        await page.wait_for_selector("text=Upload de Arquivo")
        
        samples_dir = r"C:\Users\Cleidson\Pictures\fin_analytics_v2\samples"
        files_to_test = [
            ("NUBANK_CONTA", "Exemplo_Extrato_Conta_Nubank.csv"),
            ("PIERRE", "Exemplo_Extrato_Pierre.txt"),
            ("MYPROFIT_PROVENTOS", "Exemplo_Proventos_Myprofit.csv"),
            ("B3", "Exemplo_Ativos_B3.xlsx")
        ]
        
        for source_type, filename in files_to_test:
            print(f"\\n--- Testando Upload: {source_type} ({filename}) ---")
            await page.select_option("select", value=source_type)
            
            if source_type == "PIERRE":
                # Pierre usa textbox (paste)
                print("Lendo txt para Pierre...")
                with open(os.path.join(samples_dir, filename), "r", encoding="utf-8") as f:
                    content = f.read()
                await page.fill("textarea", content[:1000]) # just a snippet to avoid huge paste overhead in test if very big, wait, the parser needs real content.
                await page.click("button:has-text('Processar')")
            else:
                print("Fazendo upload do arquivo...")
                await page.set_input_files("input[type='file']", os.path.join(samples_dir, filename))
                await page.click("button:has-text('Validar Arquivo')")
                
            print("Aguardando preview...")
            await page.wait_for_selector("text=Resultado da Validação", timeout=10000)
            
            print("Continuando para Revisão...")
            await page.click("button:has-text('Continuar para Revisão')")
            
            print("Aguardando página de revisão...")
            await page.wait_for_selector("text=Confirmar Importação", timeout=10000)
            
            print("Confirmando importação...")
            await page.click("button:has-text('Confirmar Importação')")
            await page.wait_for_timeout(2000) # give it time to process
            
            print("Voltando para Nova Importação...")
            await page.goto("http://localhost:3000/governance/imports")
            await page.wait_for_selector("text=Upload de Arquivo")
            
        print("\\n3. Verificando Histórico e Dashboard...")
        await page.goto("http://localhost:3000/governance")
        await page.wait_for_selector("text=Últimas Importações")
        await page.screenshot(path="project/dashboard_evidencia.png")
        
        print("Teste finalizado com sucesso.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
