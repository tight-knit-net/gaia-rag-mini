/* GAIA Drive 1 — gate de nomenclatura ANTES do MOVE, v1.0.0.
 * Funcoes PURAS, sem Google API/DriveApp/rede, sem MOVE/RENAME.
 * Originais e regras NOM permanecem imutaveis. Requer estado vivo recebido do
 * conector nativo + autorizacao exata; executor deve falhar fechado.
 */
(function (global) {
  'use strict';
  var DRIVE1 = '0ALBFaLnE8ZPHUk9PVA';
  function block(code) { return {status:'BLOCKED',reason:code,allowMove:false}; }
  function validId(x) { return typeof x === 'string' && /^\d{3}$/.test(x); }
  function nonempty(x) { return typeof x === 'string' && x.length > 0 && x === x.trim(); }
  function exactPrefix(name,id) {
    return typeof name === 'string' && name.startsWith(id+'_') &&
      name.length > id.length+1 && !/^\d{3}_/.test(name.slice(4));
  }
  function approvedTemplate(rule, choice) {
    var s=rule && rule.source_constraints || {};
    var templates=[rule && rule.approved_pattern, s.approved_pattern_when_consolidated];
    var subs=s.approved_subtypes || {};
    Object.keys(subs).forEach(function(k){ templates.push(subs[k].resulting_pattern); });
    return nonempty(choice) && templates.includes(choice);
  }
  function renderApproved(template, values) {
    var ok=true, vals=values||{};
    var name=template.replace(/DD-MM-AAAA|<[^<>]+>|\bAAAA\b/g,function(tok){
      var key=tok==='DD-MM-AAAA'||tok==='AAAA'?tok:tok.slice(1,-1);
      var v=vals[key];
      if (!nonempty(v) || /[\/\\<>\r\n]/.test(v)) { ok=false; return ''; }
      if (tok==='DD-MM-AAAA') {
        var m=/^(\d{2})-(\d{2})-(\d{4})$/.exec(v);
        if(!m || Number(m[3])<1900 || Number(m[3])>2200 ||
           new Date(Date.UTC(+m[3],+m[2]-1,+m[1])).toISOString().slice(0,10)!==
           m[3]+'-'+m[2]+'-'+m[1]) ok=false;
      }
      if(tok==='AAAA' && !/^\d{4}$/.test(v)) ok=false;
      if(key==='UNIDADE_IPTU' && !/^\d{3}$/.test(v)) ok=false;
      return v;
    });
    return ok && !/<[^>]+>|DD-MM-AAAA/.test(name) ? name : null;
  }
  function candidate(ctx) {
    var c=ctx.client||{}, f=ctx.file||{}, d=ctx.destination||{}, n=ctx.nom||{};
    if (ctx.driveId!==DRIVE1 || f.driveId!==DRIVE1 || d.driveId!==DRIVE1) return block('WRONG_DRIVE');
    if (!validId(c.id) || !nonempty(c.rootId) || c.indexVerified!==true ||
        c.manifestVerified!==true || c.indexId!==c.id || c.manifestId!==c.id ||
        c.indexRootId!==c.rootId || c.manifestRootId!==c.rootId) return block('CLIENT_IDENTITY_UNVERIFIED');
    if (!nonempty(f.id)||!nonempty(f.parentId)||!nonempty(f.revision)||!nonempty(f.name) ||
        f.triageProven!==true || f.isFolder===true) return block('SOURCE_OR_REVISION_UNVERIFIED');
    if (!nonempty(d.id) || d.id===c.rootId || !Array.isArray(d.ancestorIds) ||
        !d.ancestorIds.includes(c.rootId) || !Array.isArray(d.existingFiles) ||
        d.liveListingVerified!==true) return block('DESTINATION_NOT_VERIFIED_IN_CLIENT_TREE');
    if (ctx.sanitizationVerified!==true || ctx.affiliationVerified!==true ||
        ctx.fileFormatReviewed!==true || ctx.documentRiskCleared!==true) return block('DOCUMENT_EVIDENCE_MISSING');
    if (/^\d{3}_/.test(f.name) && !f.name.startsWith(c.id+'_')) return block('WRONG_CLIENT_PREFIX');
    if (f.name.startsWith(c.id+'_') && !exactPrefix(f.name,c.id)) return block('DUPLICATED_OR_EMPTY_PREFIX');
    var base = f.name.startsWith(c.id+'_') ? f.name.slice(4) : f.name;
    var chosen;
    if (n.mode==='NOM_POSITIVE') {
      var rule=n.ruleRecord||{};
      if (!/^NOM-\d{3}$/.test(n.ruleId||'') || rule.rule_id!==n.ruleId ||
          rule.runtime_release_allowed!==false || n.catalogIsNonReleased!==true ||
          n.humanReviewApproved!==true || n.sourceCurrentVerified!==true ||
          n.sourceConstraintsVerified!==true || n.variablesProven!==true ||
          n.extensionProven!==true || n.signatureGateCleared!==true ||
          n.patternReviewed!==true || !approvedTemplate(rule,n.selectedTemplate))
        return block('NOM_POSITIVE_NOT_PROVEN');
      chosen=renderApproved(n.selectedTemplate,n.provenVariables);
      if (!chosen || chosen!==n.resolvedApprovedPattern)
        return block('NOM_PATTERN_OR_VARIABLE_MISMATCH');
    } else if (n.mode==='PREFIX_ONLY_NO_NOM') {
      if (n.sourceCurrentVerified!==true || n.noPositiveNomVerified!==true ||
          n.basenameSanitizedVerified!==true || n.sanitizedBasename!==base)
        return block('NO_NOM_FALLBACK_NOT_PROVEN');
      chosen=base; // nao muda caracteres, extensao nem texto original.
    } else return block('NOM_UNKNOWN_OR_CONFLICT');
    var proposed=c.id+'_'+chosen;
    if (!exactPrefix(proposed,c.id)) return block('PROPOSED_NAME_INVALID');
    if (d.existingFiles.some(function(x){return x && x.id!==f.id && x.name===proposed;}))
      return block('COLLISION_DISTINCT_DRIVE_FILE_ID');
    return {status:'PREVIEW_ONLY',allowMove:false,proposedName:proposed,
      renameRequired:f.name!==proposed,ruleId:n.mode==='NOM_POSITIVE'?n.ruleId:null,
      mode:n.mode,originalName:f.name,fileId:f.id,sourceParentId:f.parentId,
      targetParentId:d.id};
  }
  function beforeMove(ctx) {
    var proposal=candidate(ctx);
    if (proposal.status==='BLOCKED') return proposal;
    var a=ctx.authorization||{}, r=ctx.readback||{}, f=ctx.file||{};
    if (a.approved!==true || !nonempty(a.ref) || a.fileId!==f.id ||
        a.sourceParentId!==f.parentId || a.destinationId!==ctx.destination.id ||
        a.clientId!==ctx.client.id || a.exactName!==proposal.proposedName ||
        a.originalRevision!==f.revision) return block('EXACT_MOVE_AUTHORIZATION_MISSING');
    if (r.provider!=='NATIVE_GOOGLE_DRIVE' || r.verified!==true ||
        r.id!==f.id || r.name!==proposal.proposedName ||
        r.parentId!==f.parentId || r.driveId!==DRIVE1 ||
        !nonempty(r.revision) || r.revision!==a.approvedPostRenameRevision)
      return block('RENAME_READBACK_REQUIRED_BEFORE_MOVE');
    // Deve ser invocado pelo executor IMEDIATAMENTE antes do MOVE; sem isso nao ha enforcement.
    return {status:'READY_FOR_MOVE',allowMove:true,verifiedName:r.name,
      fileId:f.id,sourceParentId:f.parentId,targetParentId:ctx.destination.id,
      verifiedRevision:r.revision,authorizationRef:a.ref,ruleId:proposal.ruleId};
  }
  function verifyAfterMove(ready,readback) {
    if (!ready || ready.status!=='READY_FOR_MOVE' || ready.allowMove!==true)
      return block('PREMOVE_GATE_NOT_PASSED');
    var r=readback||{};
    if (r.provider!=='NATIVE_GOOGLE_DRIVE'||r.verified!==true ||
        r.id!==ready.fileId||r.name!==ready.verifiedName||
        r.parentId!==ready.targetParentId || r.driveId!==DRIVE1)
      return {status:'EXECUTION_UNCERTAIN',allowMove:false,reason:'POST_MOVE_READBACK_MISMATCH'};
    return {status:'MOVED_VERIFIED',allowMove:false,fileId:ready.fileId,
      name:r.name,targetParentId:r.parentId,authorizationRef:ready.authorizationRef};
  }
  var API={candidate:candidate,beforeMove:beforeMove,verifyAfterMove:verifyAfterMove};
  if (typeof module!=='undefined' && module.exports) module.exports=API;
  global.GAIA_NOM_GATE=API;
})(typeof globalThis!=='undefined'?globalThis:this);
