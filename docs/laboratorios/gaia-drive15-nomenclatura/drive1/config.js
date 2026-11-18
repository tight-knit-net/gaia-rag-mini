'use strict';
// Pinagem de topologia observada no Drive 1 em 2026-11-18.
// Referências são metadados somente; nenhum token e nenhuma API de escrita.
const DRIVE_ID='0ALBFaLnE8ZPHUk9PVA';
const PATHS=Object.freeze({
  root:DRIVE_ID,
  readme:'1qcZTumNI0IkICDyEvGprSAMeH398x4Ig',
  triage:'1xcVof9_m37MQZCR3Fa2-TL3hwwqY4dj-',
  topology:'1obPrd8IpvOvlFSgx5tGa1lQtt7x6SwEb',
  ocr:'14lBYiStqthQsEWtNzbCpZSeRXGZxR8K_',
  quarantine:'1l0VI0NW8CDRkPbTtmC0CczyzDpXGp6bo',
  governance:'1AckKZsRCyZflTYVmZ_HvSl5-VFZQHuHX',
  tracePermanent:'1HUYGCWM3xhBIuv1vX_rNaZwjC0H3V57y',
  clientIndex:'1E3j-K4GxNfYLEjrDl_OE1jNuQPV9EU_M',
  catalog:'1GEsfv0j87tSZRrqf2YKgyBgXJkUazZeG',
  policy:'1Uh0pm8zmGnbzChLXZFxaRn_IAWxIwITA',
  entrypoint:'19fD-MTNdE38noTejrdIxWkRhpIs-BP19'
});
const TECHNICAL_IDS=new Set([PATHS.topology,PATHS.ocr,PATHS.quarantine,PATHS.policy,'1rQOZ1uEIHl3XEOytSO2nqtqfBrpRQeDc']);
module.exports={DRIVE_ID,PATHS,TECHNICAL_IDS};
