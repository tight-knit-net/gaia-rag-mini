'use strict';
/** Remove APENAS cópias locais do sandbox após relatório aprovado.
 * Não toca Google Drive, GitHub, Dropbox ou documentos originais.
 */
const fs=require('fs'),path=require('path');
const BASE=process.env.GAIA_PILOT_BASE||'/home/ubuntu/gaia-test-lab-homologacao/pilots';
function safeRunId(runId){return /^[a-z0-9][a-z0-9_-]{7,70}$/.test(runId||'')}
function safeDirectory(runId){
 if(!safeRunId(runId))throw Error('INVALID_RUN_ID');
 const p=path.join(path.resolve(BASE),runId);
 if(path.dirname(p)!==path.resolve(BASE))throw Error('OUTSIDE_SAFE_BASE');
 return p;
}
function setup(runId,clientId){
 const p=safeDirectory(runId);
 if(!/^\d{3}$/.test(clientId||''))throw Error('INVALID_CLIENT_ID');
 if(fs.existsSync(p))throw Error('PILOT_ALREADY_EXISTS');
 fs.mkdirSync(p,{recursive:true,mode:0o700});
 for(const d of ['raw','reports'])fs.mkdirSync(path.join(p,d),{mode:0o700});
 fs.writeFileSync(path.join(p,'pilot.marker.json'),JSON.stringify({
   schema:'gaia.drive1.pilot-marker.v1',runId,clientId,
   driveId:'0ALBFaLnE8ZPHUk9PVA',rawOnly:true
 },null,2)+'\n',{mode:0o600});
 return p;
}
function purge(runId,{commit=false}={}){
 const p=safeDirectory(runId),marker=path.join(p,'pilot.marker.json');
 if(fs.lstatSync(p).isSymbolicLink()||fs.lstatSync(marker).isSymbolicLink())throw Error('SYMLINK_UNSAFE');
 const m=JSON.parse(fs.readFileSync(marker,'utf8'));
 if(m.schema!=='gaia.drive1.pilot-marker.v1'||m.runId!==runId||m.driveId!=='0ALBFaLnE8ZPHUk9PVA')
   throw Error('INVALID_PILOT_MARKER');
 const reports=path.join(p,'reports');
 if(!fs.existsSync(reports)||!fs.statSync(reports).isDirectory())throw Error('REPORTS_DIR_MISSING');
 const mdFiles=fs.readdirSync(reports).filter(x=>x.endsWith('.md'));
 if(!mdFiles.length)throw Error('NO_REPORT_SAVED_STOP_PURGE');
 const raw=path.join(p,'raw');
 if(!fs.existsSync(raw))return {runId,status:'ALREADY_PURGED'};
 if(fs.lstatSync(raw).isSymbolicLink())throw Error('RAW_SYMLINK_UNSAFE');
 const files=fs.readdirSync(raw,{withFileTypes:true});
 if(files.some(x=>!x.isFile()||x.isSymbolicLink()))throw Error('RAW_TREE_UNEXPECTED_NONFILE');
 const bytes=files.reduce((sum,f)=>sum+fs.statSync(path.join(raw,f.name)).size,0);
 if(!commit)return {runId,status:'DRY_RUN',files:files.length,bytes};
 for(const f of files)fs.unlinkSync(path.join(raw,f.name));
 fs.rmdirSync(raw);
 fs.writeFileSync(path.join(reports,'LOCAL_COPIES_PURGED.json'),JSON.stringify({
   runId,filesDiscarded:files.length,bytesDiscarded:bytes,
   purgePerformedAt:new Date().toISOString(),scope:'LOCAL_SANDBOX_RAW_ONLY',
   drive1Mutations:0,note:'Deletion of local files is not certified physical erasure on SSD.'
 },null,2)+'\n',{mode:0o600});
 return {runId,status:'LOCAL_COPIES_DISCARDED',files:files.length,bytes};
}
if(require.main===module){
 try{
  const [operation,runId,arg]=process.argv.slice(2);
  console.log(JSON.stringify(operation==='setup'?{path:setup(runId,arg)}:
   operation==='purge'?purge(runId,{commit:arg==='--commit'}):
   (()=>{throw Error('USAGE: node pilot/purge.js setup <runid> <NNN> | purge <runid> [--commit]')})(),null,2));
 }catch(e){console.error('PILOT_PURGE_BLOCKED',e.message);process.exitCode=1}
}
module.exports={setup,purge,safeDirectory};
