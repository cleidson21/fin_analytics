import re
from typing import Dict

class BrokerAliasResolver:
    """
    Camada de resolução canônica de corretoras (Broker Alias Layer).
    Mapeia os nomes confusos vindos de integrações externas (B3, notas, etc)
    para o nome canônico salvo no banco de dados.
    """
    
    def __init__(self):
        # Mapa inicial de aliases
        # Chave: Alias limpo (uppercase)
        # Valor: Nome Canônico (como deverá ser achado no banco via LIKE ou match exato)
        self._aliases: Dict[str, str] = {
            "NU INVESTIMENTOS S.A. - CTVM": "NU INVEST",
            "NUBANK": "NUBANK",
            "NU INVEST": "NU INVEST",
            "XP INVESTIMENTOS CCTVM S/A": "XP INVESTIMENTOS",
            "XP INVESTIMENTOS": "XP INVESTIMENTOS",
            "BTG PACTUAL CORRETORA DE TITULOS E VALORES MOBILIARIOS S.A.": "BTG PACTUAL",
            "BTG PACTUAL": "BTG PACTUAL",
            "CLEAR CORRETORA - GRUPO XP": "CLEAR",
            "CLEAR": "CLEAR",
            "RICO INVESTIMENTOS - GRUPO XP": "RICO",
            "RICO": "RICO",
            "BANCO INTER S.A.": "INTER",
            "INTER": "INTER",
        }

    def resolve(self, raw_broker: str) -> str:
        """
        Normaliza e resolve o nome de uma corretora.
        
        Args:
            raw_broker (str): Nome cru fornecido pela origem de dados.
            
        Returns:
            str: O nome canônico resolvido, ou o nome cru limpo se não houver alias.
        """
        if not raw_broker:
            return raw_broker
            
        # Normalização básica da chave de busca (trim, uppercase)
        clean_name = raw_broker.strip().upper()
        # Reduzir espaços múltiplos
        clean_name = re.sub(r'\s+', ' ', clean_name)
        
        # Busca 1: Match exato
        if clean_name in self._aliases:
            return self._aliases[clean_name]
            
        # Busca 2: Fallback via substring (heurística básica)
        for alias_key, canonical_name in self._aliases.items():
            if alias_key in clean_name or clean_name in alias_key:
                # Evita matches curtos demais e falsos positivos
                if len(alias_key) > 4: 
                    return canonical_name

        # Se não achou, retorna o nome limpo para tentar via query de banco
        return clean_name
