'use strict';
const {resolveNome} = require('./core/GaiaOffice.js');
const rules = require('./rules.snapshot.json');
const PENDING = 'PENDENTE_NOMENCLATURA';
const pending = (reason, extra={}) => ({status:PENDING,reason,...extra,write_performed:false});
function validDate(s) {
  if(typeof s!=='string'||!/^\d{2}-\d{2}-\d{4}$/.test(s)) return false;
  const [d,m,y]=s.split('-').map(Number);
  if(y<100||m<1||m>12)return false;
  const dt=new Date(Date.UTC(y,m-1,d));
  return dt.getUTCFullYear()===y && dt.getUTCMonth()===m-1 && dt.getUTCDate()===d;
}
function suggestDocumentName(input) {
  if(!input||typeof input!=='object'||Array.isArray(input))return pending('ENTRADA_INVALIDA');
  const output=resolveNome(rules,input);
  if(output.status!=='OK')return {...output,write_performed:false};
  const rule=rules.find(r=>r.rule_id===output.rule_id);
  if(!rule)return pending('REGRA_INEXISTENTE');
  for(const v of rule.variables||[]) {
    if(v.format==='DD-MM-AAAA'&&!validDate(input.provided?.[v.name]))
      return pending('DATA_CALENDARIO_INVALIDA',{field:v.name});
  }
  const n=output.finalFilename;
  if(typeof n!=='string'||n.length===0||/[\\/:*?"<>|\x00-\x1f]/.test(n)||n.includes('..')||/[. ]$/.test(n)||Buffer.byteLength(n,'utf8')>240)
    return pending('NOME_INSEGURO');
  return {...output,mode:'PREVIEW_ONLY',write_performed:false};
}
module.exports={suggestDocumentName, rules, validDate};

