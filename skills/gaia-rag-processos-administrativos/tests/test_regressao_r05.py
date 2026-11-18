#!/usr/bin/env python3
"""Testes determinísticos de contrato documental; NÃO executam LLM, MCP ou rede."""
from pathlib import Path
import json, re, unittest, yaml
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parent
SK=(ROOT/'SKILL.md').read_text(encoding='utf8')
class RegressaoR05(unittest.TestCase):
 def test_yaml_real(self):
  self.assertTrue(SK.startswith('---\n'))
  fm=yaml.safe_load(SK.split('---',2)[1]); self.assertEqual(fm['name'],ROOT.name)
  self.assertLessEqual(len(fm['description']),1024)
  self.assertEqual(fm['metadata']['version'],'0.7.0-institutional-assimilation-preview')
 def test_yaml_negativo_rejeitado(self):
  with self.assertRaises(yaml.YAMLError):yaml.safe_load('description: algo: outro: valor')
 def test_dez_modulos_r07(self):
  self.assertEqual(len(list((ROOT/'references').glob('*.md'))),10)
  self.assertTrue(all((ROOT/'references'/(f'{i:02d}-'+name)).is_file() for i,name in enumerate([
   'contexto-e-isolamento.md','recuperacao.md','producao-e-proposta.md','governanca-e-evidencia.md',
   'esquema-logico.md','continuidade-processual.md','contratos-mcp-atual.md',
   'arquitetura-tecnica-nao-mutativa.md','instalacao-e-portabilidade.md',
   'assimilacao-institucional.md'],1)))
 def test_nomes_referenciados(self):
  refs=set(re.findall(r'`(references/[0-9]{2}-[^`]+\.md)`',SK))
  self.assertEqual(len(refs),10)
  self.assertTrue(all((ROOT/r).is_file() for r in refs))
 def test_segundo_gate_de_aprovacao(self):
  self.assertIn('aprovação',SK.lower());self.assertIn('clique humano',SK.lower())
  self.assertIn('memory_prepare_after_approval',(ROOT/'references/03-producao-e-proposta.md').read_text())
  self.assertIn('não grava ponto aprovado',(ROOT/'references/07-contratos-mcp-atual.md').read_text())
 def test_sem_elevacao_automatica(self):
  self.assertIn('não',SK.lower());self.assertIn('deferimento',SK.lower());self.assertIn('namespace=chatgpt',SK)
 def test_contratos_nao_inventados(self):
  c=(ROOT/'references/07-contratos-mcp-atual.md').read_text()
  self.assertIn('não',c.lower());self.assertIn('gaia_memoria_salvar',c)
  self.assertIn('não',c[c.index('gaia_memoria_salvar')-100:c.index('gaia_memoria_salvar')+50].lower())
 def test_escopo_fonte(self):
  for p in ROOT.glob('references/*.md'):self.assertTrue(p.read_text(encoding='utf8').strip(),str(p))
  x=(ROOT/'references/02-recuperacao.md').read_text()
  for phrase in ['memory_list_process','memory_search','memory_find_by_source','memory_get','process_id']:
   self.assertIn(phrase,x)
 def test_examples_sinteticos(self):
  for f in (ROOT/'assets/templates').glob('*.md'):
   t=f.read_text(encoding='utf8')
   self.assertGreater(len(t),500)
   self.assertTrue('DEMO' in t or 'fictíci' in t or 'fictici' in t)
 def test_modelo_nao_e_schema(self):
  txt=(ROOT/'references/05-esquema-logico.md').read_text()
  self.assertIn('não enviar',txt.lower());self.assertIn('autorizado_persistir',txt)
 def test_fonte_institucional(self):
  m=(PROJECT/'MATRIZ_EVIDENCIAS_R04.md').read_text()
  for i in range(1,17):self.assertIn('O%02d'%i,m)
  for i in range(1,15):self.assertIn('F%02d'%i,m)
  for i in range(1,3):self.assertIn('B%02d'%i,m)
 def test_testes_host_nao_homologados(self):
  c=(ROOT/'tests/aceite.md').read_text()
  for gate in ('G06','G07','G08'):self.assertIn(gate,c)
  self.assertIn('NÃO EXECUTADO',c)
 def test_cenarios_ficticios(self):
  x=json.loads((ROOT/'tests/cenarios_r04.json').read_text())
  self.assertEqual(len(x),30)
  self.assertEqual(len(set(z['id'] for z in x)),30)
  self.assertTrue(all(not z['executado_em_host'] for z in x))
  self.assertTrue(all(z['ferramenta_permitida_se_precondicoes'] for z in x))
 def test_json_sintaxe(self):
  for p in ROOT.rglob('*.json'):json.loads(p.read_text(encoding='utf8'))
 def test_governanca_minima(self):
  for x in ('POLITICA_MEMORIA.md','DECISOES_ARQUITETURA.md','MATRIZ_RISCOS.md','FONTES_E_STATUS.md','CHANGELOG.md'):
   self.assertGreater(len((ROOT/'governanca'/x).read_text()),500)
 def test_fluxo_nao_iniciar_gravacao(self):
  self.assertIn('sem alterar infraestrutura',SK.lower())
  self.assertIn('não altera schema', (ROOT/'references/08-arquitetura-tecnica-nao-mutativa.md').read_text().lower())
 def test_politica_lgpd(self):
  a=(ROOT/'governanca/POLITICA_MEMORIA.md').read_text()
  self.assertIn('13.709/2018',a);self.assertIn('necessidade',a)
 def test_documentacao_tecnica_sob_demanda(self):
  self.assertIn('não carregar a arquitetura qdrant',SK.lower())
 def test_schema_editorial_json(self):
  c=(ROOT/'references/05-esquema-logico.md').read_text()
  sample=re.search(r'```json\s*(\{[\s\S]*?\})\s*```',c)
  self.assertIsNotNone(sample);a=json.loads(sample.group(1))
  self.assertFalse(a['autorizado_persistir'])
 def test_regressoes_previa_pendentes(self):
  self.assertTrue((ROOT/'tests/roteiros_llm_sinteticos.json').exists())
  self.assertTrue((ROOT/'tests/resultados_simulacao_llm_r031.md').exists())
 def test_fontes_iso_publicas(self):
  x=(ROOT/'references/04-governanca-e-evidencia.md').read_text()
  for s in ('ISO 30401:2018','ISO 15489-1:2016','ISO 23081-1:2017'):
   self.assertIn(s,x)
 def test_yaml_agents(self):
  a=yaml.safe_load((ROOT/'agents/openai.yaml').read_text())
  self.assertIn('interface',a)
 def test_codificacao(self):
  for p in ROOT.rglob('*'):
   if p.is_file():p.read_text(encoding='utf8')
if __name__=='__main__':unittest.main(verbosity=2)
