# Auditoria de documentação técnica de fornecedores — GAIA Document MCP

**Verificação de fontes públicas realizada em 18/11/2026.** Natureza: aderência conceitual e documentação; nenhum serviço de fornecedor foi instalado ou homologado por este relatório.

| Sistema | Fontes canônicas inspecionadas | Recurso documentado | Ressalva/gate |
|---|---|---|---|
| Stirling-PDF | https://docs.stirlingpdf.com/Server/Install/Docker/ ; https://docs.stirlingpdf.com/Developers/API/ ; https://docs.stirlingpdf.com/Configuration/Operations/OCR/ | Docker padrão com LibreOffice/Tesseract/OCRmyPDF; API REST e OCR `/api/v1/misc/ocr-pdf` | API e quotas por plano; `latest-ultra-lite` não inclui OCR; pin de digest/imagem, memória, limites de páginas e integração precisos precisam de homologação |
| DocuSeal | https://www.docuseal.com/docs/api ; https://www.docuseal.com/developers | Templates, submissões, preenchimento de campos, documentos assinados e webhooks | Validar licença/plano para API/self-hosting, webhook autêntico, idempotência, titularidade e validade jurídica; não é editor geral de texto arbitrário no PDF |
| GroqCloud | https://console.groq.com/docs/tool-use/remote-mcp ; https://console.groq.com/docs/tool-use/overview ; https://console.groq.com/docs/your-data | Tool calling e acesso a servidores MCP remotos por modelos compatíveis | Remote MCP identificado como beta; risco de contexto sensível; política de retenção/ZDR e termos exigem revisão antes de clientes |
| MCP | https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization ; https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations | Perfil OAuth para transporte HTTP e requisitos de recursos protegidos | Autenticidade, issuer/audience/scope, autorização em nível de ferramenta/objeto, sem token passthrough ou MCP interno exposto |
| Google Workspace | https://developers.google.com/workspace/drive/api/reference/rest/v3 ; https://developers.google.com/workspace/drive/api/guides/folder ; https://developers.google.com/workspace/docs/api/reference/rest ; https://developers.google.com/workspace/sheets/api/reference/rest | Leitura e atualização Drive, documentos Docs, planilhas Sheets; shared drives suportados | Regras IAM/OAuth, `supportsAllDrives`, operações atômicas e readback, rate limit, versões e quotas |
| Python | https://docs.python.org/3.12/library/unittest.html | Testes unitários `unittest` sem dependências | Não cobre provedores nem compliance |
| GAIA R06/R07 | Branches e código privados deste repositório | Busca memória por processo, R07 preview, proposta R06 com aprovação documental | Não confundir CI com runtime conectado nem com aprovação de memória |

## Correções de afirmações informais anteriores
1. **"Sem limite de arquivos"** não deve ser reproduzido como promessa de API ilimitada. A documentação atual do Stirling-PDF diferencia créditos/allowance em uso de API, conforme plano, e devolve 402 quando esgotado; capacidade própria depende dos recursos e da licença.
2. **OCR automático** não prova que o documento foi reconhecido com qualidade nem que os campos foram validados. O mecanismo requer teste com PDF imagem real de laboratório, idiomas `por`/`eng`, página e comparação com gabarito.
3. **DocuSeal** resolve formulários e assinaturas; não substitui editor de conteúdo PDF. Para editar texto solto, usar fluxo específico com transformação/versão e aprovação; não presumir fidelidade PDF↔DOCX.
4. **Groq** com Q é provedor de inferência; não é o **Grok** da xAI. Groq Remote MCP não equivale a um servidor próprio instalado na máquina.
5. **MCP do Stirling** e **MCP do DocuSeal** podem ser aproveitados, mas o núcleo GAIA deve controlar política de ferramentas e não confiar implicitamente na autorização de um MCP de terceiro.
6. **"Aprendizado automático"** significa captura operacional e prévia editorial. Persistência de memória Qdrant segue exclusivamente a R06 e seus controles humanos.
7. A coleção Qdrant **não é** substituto de banco operacional de jobs, logs ou arquivos; SQL full-text de OCR também **não é** RAG vetorial.

## Matriz de auditoria
- **Aderência de capacidades documentadas**: VERIFICADA nas fontes listadas, sem invocação de APIs reais.
- **Compatibilidade de versão de imagens e licenças**: NÃO VERIFICADA no ambiente GAIA.
- **Autenticidade das credenciais e tokens**: NÃO INSPECIONADA (não necessário nesta fase).
- **Tratamento LGPD, retenção, suboperadores e transferência internacional**: PENDENTE de avaliação jurídica/organizacional e teste operacional.
- **OCR com Stirling + integração NOM/R07**: PLANEJADO, não integrado.
- **DocuSeal assinatura em fluxo GAIA**: PLANEJADO, sem evento real ou webhook verificado.
- **Groq em documento de cliente**: BLOQUEADO por padrão; aprovação e controle de dados necessários.
- **Memória persistente automática sem revisão**: NÃO AUTORIZADA pela política vigente.

## Fontes privativas e precedência
A árvore do GitHub é a fonte para afirmar "código existente". O Google Drive/manifesto canônico é a fonte documental do cliente. Evidência operacional exige host, versão, timestamp e recibos. Documentos versionados neste diretório **não criam automaticamente implantação ou habilitação de ferramenta**.

