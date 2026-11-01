# Decisões (ADRs curtos)

1. **MVP = Direito de Família.** Valida o fluxo completo com o caso de guarda antes de ampliar.
2. **Python + Supabase (Postgres/pgvector).** Busca híbrida; Supabase já conectado ao ambiente do usuário.
3. **MCP como interface.** Qualquer chat do Claude usa a base como ferramenta; o repo carrega o contexto (`CLAUDE.md`).
4. **Rastreabilidade obrigatória.** Resposta = texto + fonte + URL oficial + status de verificação. Sem isso, não afirma.
5. **Curadoria marcada como não verificada.** O mapa pedido→artigos foi escrito de memória; só vira "verificado" após ingestão do texto oficial + revisão de advogado.
6. **Ingestão fora do sandbox.** O ambiente de desenvolvimento em nuvem não acessa as fontes; usar GitHub Actions/local.
7. **Dados de clientes separados do corpus público** (RLS, nada no repo).
