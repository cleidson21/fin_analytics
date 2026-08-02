# ADR-007: MyProfit Session Management
Como não há API oficial, a integração MyProfit ocorrerá via sessão autenticada (cookies). É terminantemente proibido tentar realizar bypass de 2FA ou armazenar senhas em plain text permanentemente sem um cofre. A interação de 2FA requer ação humana, armazenando-se apenas a sessão resultante.
