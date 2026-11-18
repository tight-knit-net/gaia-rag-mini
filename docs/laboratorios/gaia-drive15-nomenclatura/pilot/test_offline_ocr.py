import importlib.util, tempfile, pathlib, json, hashlib, unittest
from unittest.mock import patch
p=pathlib.Path(__file__).with_name('offline_ocr.py')
s=importlib.util.spec_from_file_location('gaiaofflineocr',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestOCR(unittest.TestCase):
 def fixture(self):
  tmp=tempfile.TemporaryDirectory();root=pathlib.Path(tmp.name)
  (root/'reports').mkdir();(root/'raw').mkdir()
  (root/'manifest.json').write_text(json.dumps({'schema':'gaia.drive1.pilot.v1','mode':'READ_ONLY','driveId':'0ALBFaLnE8ZPHUk9PVA','clientId':'009','batchId':'test_009','copies':[]}),encoding='utf-8')
  return tmp,root
 def test_rejects_no_copies(self):
  tmp,root=self.fixture()
  try:
   with self.assertRaisesRegex(ValueError,'COPIES_MISSING'):m.process(root,'t001')
  finally:tmp.cleanup()
 def test_rejects_invalid_output_label(self):
  tmp,root=self.fixture()
  try:
   with self.assertRaisesRegex(ValueError,'INVALID_OUTPUT_LABEL'):m.process(root,'../../evil')
  finally:tmp.cleanup()
 def test_rejects_reuse(self):
  tmp,root=self.fixture();(root/'reports'/'ocr_local_t001').mkdir()
  try:
   with self.assertRaisesRegex(ValueError,'COPIES_MISSING'):m.process(root,'t001')
  finally:tmp.cleanup()
 def test_rejects_modified_file(self):
  tmp,root=self.fixture(); fid='1AbCdEfGh0123';b=b'%PDF-test-payload';(root/'raw'/(fid+'.pdf')).write_bytes(b)
  mf=json.loads((root/'manifest.json').read_text());mf['copies']=[{'fileId':fid,'storedAs':fid+'.pdf','sha256':'0'*64,'bytes':len(b)}];(root/'manifest.json').write_text(json.dumps(mf))
  try:
   with self.assertRaisesRegex(ValueError,'SHA256_OR_SIZE_MISMATCH'):m.process(root,'t001')
  finally:tmp.cleanup()
 def test_rejects_invalid_drive(self):
  tmp,root=self.fixture();mf=json.loads((root/'manifest.json').read_text());mf['driveId']='bad';(root/'manifest.json').write_text(json.dumps(mf))
  try:
   with self.assertRaisesRegex(ValueError,'PILOT_MANIFEST_INVALID'):m.process(root,'t001')
  finally:tmp.cleanup()
 def test_rejects_page_limit(self):
  with self.assertRaisesRegex(ValueError,'MAX_PAGES_OUT_OF_RANGE'):m.process(pathlib.Path('.'),'safe_label',31)
 def test_local_real_scanned_pdf_ocr(self):
  try:
   import fitz
  except ImportError:self.skipTest('fitz for test fixture absent')
  tmp,root=self.fixture();fid='1AbCdEfGh0123'
  try:
   # Generate a scanned PDF: rendered text converted into pixels, then image-only PDF.
   doc=fitz.open();page=doc.new_page(width=595,height=842);page.insert_text((72,160),'CERTIDAO DE TESTE GAIA 009 2026',fontsize=25)
   pix=page.get_pixmap(matrix=fitz.Matrix(2,2));imagepdf=fitz.open();p2=imagepdf.new_page(width=595,height=842);p2.insert_image(p2.rect,stream=pix.tobytes('png'));b=imagepdf.tobytes();doc.close();imagepdf.close()
   f=root/'raw'/(fid+'.pdf');f.write_bytes(b);sha=hashlib.sha256(b).hexdigest()
   mf=json.loads((root/'manifest.json').read_text());mf['copies']=[{'fileId':fid,'storedAs':fid+'.pdf','sha256':sha,'bytes':len(b)}];(root/'manifest.json').write_text(json.dumps(mf))
   r=m.process(root,'t001');self.assertEqual(r['driveWrites'],0);self.assertEqual(r['results'][0]['status'],'TEXT_EXTRACTED_REVIEW_REQUIRED');self.assertEqual(r['results'][0]['ocrPages'],1)
   text=(root/'reports'/'ocr_local_t001'/(fid+'.txt')).read_text();self.assertIn('GAIA',text)
   with self.assertRaisesRegex(ValueError,'REPORT_ALREADY_EXISTS'):m.process(root,'t001')
  finally:tmp.cleanup()
if __name__=='__main__':unittest.main()
