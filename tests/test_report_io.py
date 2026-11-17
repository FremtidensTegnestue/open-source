import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from report_io import write_report

ROOT=Path(__file__).resolve().parents[1]

class ReportTests(unittest.TestCase):
    def test_input_and_symlink_alias_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'request.json';src.write_text('original')
            alias=Path(td)/'alias.json';alias.symlink_to(src)
            for out in [src,alias]:
                with self.assertRaises(ValueError):write_report({'changed':True},out,[src])
                self.assertEqual(src.read_text(),'original')
            out=Path(td)/'report.json';write_report({'value':1},out,[src]);self.assertEqual(json.loads(out.read_text()),{'value':1})
    def test_cli_cannot_write_over_model(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'copy.sc';src.write_bytes((ROOT/'examples/models/solidcraft/solid-wood.sc').read_bytes());before=src.read_bytes()
            for tool,args in [('materials.py',['extract',str(src),'--software','solidcraft']),('adapters/solidcraft.py',[str(src)])]:
                reply=subprocess.run([sys.executable,str(ROOT/tool),*args,'--out',str(src)],capture_output=True,text=True)
                self.assertNotEqual(reply.returncode,0);self.assertEqual(src.read_bytes(),before)
    def test_nonfinite_output_does_not_replace_existing_report(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'report.json';p.write_text('original')
            with self.assertRaises(ValueError):write_report({'bad':float('nan')},p)
            self.assertEqual(p.read_text(),'original')

if __name__=='__main__':unittest.main()
