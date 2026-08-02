> [!IMPORTANT]
> A pasta docs/ é a única fonte oficial de documentação do projeto. É proibido criar documentação fora dela. Toda nova implementação deve ler os documentos existentes em docs/, atualizá-los quando necessário e registrar decisões arquiteturais por meio de ADRs antes de prosseguir.

# MyProfit - Referência Técnica

**Data da Consulta:** 18 de Julho de 2026.
**Acesso:** ✗ Sem API pública oficial. Integração via scraping web inferido.

## Estratégia de Autenticação
- **Login e Senha:** [CONFIRMADO] MyProfit exige login web padrão.
- **2FA:** [CONFIRMADO] Envio de token via email/app.
- **Persistência de Sessão:** [VALIDADO] Será feito via cookies guardados.
- **Bypass Automatizado:** [CONFIRMADO] Proibido/Impossível.

## Informações
### [CONFIRMADO]
- O sistema da MyProfit é um portal web.
- Integração requer fluxo de sessão interativo com 2FA.

### [INFERIDO]
- É possível exportar CSVs por dentro do portal após o login.
- É possível raspar o DOM para pegar o portfólio.

### [DESCONHECIDO]
- Duração exata do cookie de sessão.
- Alterações futuras no DOM que possam quebrar parsers.
- Rate limits da proteção anti-bot.
