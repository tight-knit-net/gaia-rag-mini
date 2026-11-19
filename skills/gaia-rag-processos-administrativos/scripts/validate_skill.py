#!/usr/bin/env python3
"""Validação estrutural independente, sem rede/sem mutação do GAIA RAG."""
from pathlib import Path
import re, json, sys, yaml
root=Path(__file__).resolve().parents[1]
errors=[]
def err(m): errors.append(m)
sk=root/'SKILL.md'
if not sk.is_file(): err('SKILL.md ausente')
else:
 text=sk.read_text(encoding='utf8')
 m=re.match(r'\A---\s*\n(.*?)\n---\s*\n',text,re.S)
 if not m: err('YAML frontmatter ausente/não fechado')
 else:
  try: fm=yaml.safe_load(m.group(1))
  except yaml.YAMLError as e: fm={};err('YAML invalido: '+str(e))
  if not isinstance(fm,dict): err('frontmatter nao e mapa');fm={}
  name=fm.get('name')
  if not isinstance(name,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name) or len(name)>64 or name!=root.name:err('name invalido/nao corresponde a pasta')
  desc=fm.get('description')
  if not isinstance(desc,str) or not 1<=len(desc)<=1024:err('description invalida (1..1024)')
  if 'metadata' in fm and (not isinstance(fm['metadata'],dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in fm['metadata'].items())):err('metadata invalida')
  if len(text.split())>5000: err('SKILL.md excede recomendacao de 5000 palavras')
  # All explicitly referenced local resources (code spans and markdown links)
  for rel in set(re.findall(r'`((?:references|tests|assets|agents|governanca|scripts)/[^`\n ]+\.(?:md|json|yaml|py))`',text)):
   if not (root/rel).is_file():err('Recurso nao encontrado: '+rel)
for path in root.rglob('*'):
 if not path.is_file():continue
 rel=path.relative_to(root).as_posix()
 if path.suffix in ('.md','.yaml','.yml','.json','.py'):
  try: c=path.read_text(encoding='utf8')
  except UnicodeError:err('Codificacao invalida: '+rel);continue
  for pattern in (r'-----BEGIN [A-Z ]*PRIVATE KEY-----',r'(?i)api[_-]?key\s*[:=]\s*[\"\']?[A-Za-z0-9_-]{25,}'):
   if re.search(pattern,c):err('Suspeita de segredo: '+rel)
  if path.suffix=='.json':
   try:json.loads(c)
   except Exception as e:err('JSON invalido: '+rel+' '+str(e))
  if path.suffix in ('.yaml','.yml'):
   try:yaml.safe_load(c)
   except Exception as e:err('YAML invalido: '+rel+' '+str(e))
  if path.suffix=='.py':
   try:compile(c,rel,'exec')
   except Exception as e:err('Python invalido: '+rel+' '+str(e))
# Cross-check table of contents, no external execution
refs=list((root/'references').glob('*.md'))
if len(refs)<9:err('referencias esperadas ausentes')
if not (root/'tests/fixtures_sinteticas.json').is_file():err('fixtures ausentes')
print('STATUS:', 'OK' if not errors else 'FALHA', '| arquivos:',sum(p.is_file() for p in root.rglob('*')))
for e in errors:print('ERRO:',e)
sys.exit(0 if not errors else 1)
