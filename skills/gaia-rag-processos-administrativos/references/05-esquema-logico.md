# 05 — Taxonomia editorial e modelo lógico de memória

> **IMPORTANTE:** isto é um contrato de conteúdo **na skill**, não mudança de schema na collection Qdrant. A API MCP atual aceita somente um resumo textual e poucos campos. Campos abaixo devem constar em síntese editorial quando úteis; não enviar metadados adicionais como payload MCP.

## Hierarquia lógica

```text
Namespace (o padrão da MCP é chatgpt)
  └── Processo administrativo (process_id real, único)
      ├── assunto: mesas_cadeiras | minimercado_conveniencia | ... (rótulo editorial)
      ├── fato/ato/documento/decisão daquele processo
      ├── estado e pendências do processo
      └── aprendizado originado naquele processo
Conhecimento generalizável
  └── nasce de caso comprovado, mas só é aplicado fora dele se
      mantiver fonte, jurisdição, limites e aprovação humana apropriada
```

## Rótulos editoriais sugeridos

`tipo_editorial`: `caso`, `fundamento`, `procedimento`, `modelo`, `precedente`, `aprendizado`, `pendencia`.
`assunto`: slug controlado (`mesas_cadeiras`, `minimercado_conveniencia`, `alvara_funcionamento`, `uso_espaco_publico`, outros se comprovados).
`jurisdicao`: esfera + UF + município + órgão competente; nunca deduzir.
`estado_evidencia`: `alegado`, `documentado`, `confirmado`, `nao_verificado`, `inaplicavel`, `refutado`.
`fase_processo`: `minuta_interna`, `protocolado`, `em_exigencia`, `em_analise`, `decidido`, `encerrado` (só com evidência).

## Modelo lógico recomendado (NÃO é payload da API)

```yaml
process_id: "PROC-DEMONSTRATIVO-001"
assunto: "mesas_cadeiras"
municipio_uf: "EXEMPLO/XX"
objeto: "Pedido de autorização de mesas e cadeiras"
tipo_editorial: "caso"
fonte_ref: "identificador_documento_real_ou_pendente"
estado_evidencia: "documentado"
fatos_confirmados: []
pendencias: []
fundamentos_verificados: []
resultado_administrativo: "sem_decisao_comprovada"
limites: ["Não reutilizar normas de outro município"]
```

Os exemplos acima são **ficção sintética**, não ID de processo real, não dados para gravar.

## Conteúdo mínimo do resumo MCP

```text
[ASSUNTO: ...] [PROCESSO: ...] [JURISDICAO: ...]
TÍTULO: ...
TIPO: ...
FATO/ATO CONFIRMADO: ...
FONTE: ...
ESTADO DA PROVA: ...
DECISÃO/RESULTADO: ... (somente se comprovado)
PENDÊNCIAS: ...
LIMITES DE USO: ...
DATA DE CONFERÊNCIA: ... (se disponível)
```

## Deduplicação editorial

Para **caso**, comparar `process_id + tipo_editorial + subtema + fonte_ref + versão quando existir`.
Para **método**, comparar `assunto + jurisdição + finalidade + fonte + limites`. Identidade textual/semântica isolada não basta.

A melhoria física (payload indexes, embeddings, shards, namespaces novos) precisa de projeto técnico e autorização distintos. A skill não executa migração ou upsert.


## Ontologia normalizada da habilidade R04 — NÃO esquema físico do Qdrant

**Níveis de identidade**: `tenant_titular` (derivado de autorização do servidor, não do prompt) → `cliente_ref` (identificador interno) → `process_id` (caso único) → `evento_ref` (fonte/ato). Em paralelo, `assunto` e `jurisdicao` classificam o conteúdo; não formam `namespace` novo nem garantem ACL. Não criar coleção por `mesas_cadeiras`.

**Chave editorial de duplicidade:** para eventos do processo, `process_id + tipo + fonte_ref + data_evento + objeto`; para método abstrato, `tipo + assunto + jurisdicao + finalidade + fonte_verificada`. É recomendação editorial de comparação, **não** índice configurado. Registros de clientes diferentes nunca são duplicatas técnicas só porque o texto é parecido.

**Estado de uma memória e estado do caso são ortogonais:** aprovação (`candidata/em_revisao/aprovada`), evidência (`alegada/documentada/confirmada/inaplicavel`), resultado do caso (`sem_protocolo/protocolado/exigencia/decisao/encerrado`), vigência da norma (`confirmada/pendente/superada`). Esses estados são representação de governança, não payload novo inferido.

### Exemplo de objeto local para revisão (NÃO enviar direto à MCP)

```json
{
  "schema_editorial": "gaia-rag/r04",
  "process_id": "DEMO-MESAS-017",
  "assunto": "mesas_cadeiras",
  "jurisdicao": {"municipio": "EXEMPLO", "uf": "XX", "orgao": "ORGAO_FICTICIO"},
  "natureza": "decisao_interna",
  "evidencia": "documentada",
  "status_administrativo": "minuta_aprovada_internamente",
  "texto_sintese": "Minuta aprovada internamente, sem confirmação de protocolo ou deferimento.",
  "fonte_ref": "DEMO/documento-local-validado-001",
  "limites": ["Nao equivale a decisao da Administracao"],
  "autorizado_persistir": false
}
```

**Adaptação ao contrato real:** somente `summary`, `title`, `process_id` e os opcionais `namespace`, `kind`, `source_ref`, `source_type` podem ser enviados a `memory_prepare_after_approval` quando o gatilho estiver satisfeito. Nem `autorizado_persistir`, nem `evidencia`, nem `jurisdicao` são campos aceitos da ferramenta; o `false` do exemplo **não** substitui a autorização do portal.

### Embedding vs metadado

Embedding transforma um texto em representação vetorial para semelhança. Não é partição, nem autoridade, nem base documental. Os filtros por payload só são seguros quando **impostos pelo backend autenticado**; `process_id` na instrução da skill é convenção operacional, não certificação do isolamento do Qdrant. Qdrant: https://qdrant.tech/documentation/deploy-and-scale/multitenant-search/ .
