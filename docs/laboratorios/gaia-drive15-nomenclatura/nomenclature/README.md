# Motor de nomenclatura isolado (preview)
Quatro arquivos JavaScript puros preservados em nomenclature/core, sem acesso ao Drive.
As 56 regras estão em rules.snapshot.json, provenientes de RulesData.js.
API: require("./nomenclature").suggestDocumentName({rule_id, clientNNN, provided, rawFields, signals}).
Saída: nome proposto ou PENDENTE_NOMENCLATURA. Nunca renomeia nem move arquivos.
Para testar: node --test nomenclature/tests/naming.test.js
