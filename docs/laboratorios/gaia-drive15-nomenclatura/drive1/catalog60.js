'use strict';
const {DRIVE_ID}=require('./config');
const REFERENCE='./reference/CATALOGO_FEDERADO_60_REGRAS_READONLY_20261118.json';
const REVIEW=new Set(['NOM-012','NOM-033','NOM-058','NOM-060']);
function validateCatalog(catalog){
  if(!catalog || catalog.target_drive_id!==DRIVE_ID ||
     catalog.catalog_id!=='GAIA_NOM_FEDERATED_20261117_02' ||
     catalog.status!=='DERIVED_NONCANONICAL_NOT_RELEASED' ||
     catalog.schema_version!=='1.1.0' ||
     catalog.rename_execution_allowed!==false ||
     catalog.source_recheck_before_use!==true)
    throw Error('CATALOG_SOURCE_OR_STATUS_MISMATCH');
  if(!Array.isArray(catalog.rules)||catalog.rules.length!==60)throw Error('CATALOG_RULE_COUNT_MISMATCH');
  const ids=new Set(catalog.rules.map(r=>r.rule_id));
  if(ids.size!==60)throw Error('DUPLICATE_RULE_ID');
  for(let n=1;n<=60;n++){
    const id='NOM-'+String(n).padStart(3,'0');
    if(!ids.has(id))throw Error('MISSING_RULE:'+id);
  }
  return true;
}
function getCatalog(){
  const catalog=require(REFERENCE);
  validateCatalog(catalog);
  return catalog;
}
function gateRule(ruleId,catalog=getCatalog()){
  validateCatalog(catalog);
  const rule=catalog.rules.find(r=>r.rule_id===ruleId);
  if(!rule)return {status:'BLOCKED',reason:'RULE_NOT_IN_CATALOG',ruleId};
  const sourceReview=REVIEW.has(ruleId)||rule.review_blockers?.length>0;
  return {
    status:'REFERENCE_ONLY',ruleId,
    proposedPattern:rule.approved_pattern,sourceType:rule.source_type,
    sourceFileId:rule.source_file_id||null,
    sourceConstraintsPresent:!!rule.source_constraints,
    overlayConstraintsPresent:!!rule.overlay_constraints,
    reviewRequired:sourceReview||rule.review_required===true,
    ruleNeedsCurrentSourceRecheck:true,
    executed:false,
    runtimeSupported:rule.source_type==='BASE' && !REVIEW.has(ruleId)
  };
}
module.exports={validateCatalog,getCatalog,gateRule,REVIEW};
