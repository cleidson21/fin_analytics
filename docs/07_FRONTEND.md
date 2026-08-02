# Frontend

Aplica a arquitetura em React/Next.js consumindo a API orientada ao domínio.

## Diretrizes Oficiais do Frontend

O frontend legado (Next.js) passa oficialmente a ser o **frontend definitivo** do projeto. 

**O layout, componentes, organização visual, navegação e experiência do usuário do frontend legado constituem a base oficial da interface do FINANALYTICS.**

Durante as Vertical Slices:
- Nenhuma tela será recriada sem necessidade.
- Sempre reutilizar a página existente.
- Substituir apenas a origem dos dados (substituindo mocks/dados estáticos pelas requisições à nossa nova REST API).
- Adaptar os componentes existentes à nova REST API preservando a mesma experiência.

**Regra de Conflito de Interface:**
Caso existam múltiplos locais possíveis para encaixar uma funcionalidade, a implementação deve ser **interrompida imediatamente**, apresentando as alternativas e aguardando decisão do usuário.
