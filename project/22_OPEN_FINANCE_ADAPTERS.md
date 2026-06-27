# 5.10 Open Finance

## Objetivo
Preparar o terreno estrutural para integração futura e direta com APIs bancárias oficiais, substituindo o parsing manual de CSV/PDF.

## Arquitetura
Criar a estrutura passiva de Adapters (Empty Shells) com injeção de dependência via configuração:
- `adapters/openfinance/nubank/`
- `adapters/openfinance/bb/`
- `adapters/openfinance/itau/`
- `adapters/openfinance/inter/`
- `adapters/openfinance/c6/`

## Regras
Inicialmente, todos os adapters permanecerão estritamente VAZIOS. Eles são stubs estruturais reservados para ativação na Fase de Open Finance, somente após as importações passivas (Parsers e CSVs) estarem totalmente operacionais e maduras.
