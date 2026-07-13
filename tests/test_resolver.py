from backend.domains.investments.repositories.broker_alias_resolver import BrokerAliasResolver

resolver = BrokerAliasResolver()

test_cases = [
    "NU INVESTIMENTOS S.A. - CTVM",
    "NUBANK",
    "Nu Invest",
    "NU INVEST",
    "XP INVESTIMENTOS",
    "BTG PACTUAL",
    "CORRETORA INEXISTENTE S.A.",
    "INVEST" # Ambiguidade
]

print("--- TESTE BROKER ALIAS RESOLVER ---")
for raw in test_cases:
    resolved = resolver.resolve(raw)
    print(f"Raw: '{raw}' -> Resolved: '{resolved}'")
