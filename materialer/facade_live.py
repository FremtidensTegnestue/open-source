"""Read-only live accounting beside SolidCraft; native edits retain native undo/save semantics."""
import argparse
import copy
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import threading
import time

import facade
import facade_guidance


class Control:
    """SolidCraft's documented authenticated loopback protocol; tokens never leave memory."""
    def __init__(self, directory=None, port=None):
        if directory is None:
            directory=os.environ.get('SOLIDCRAFT_CONTROL_DIR')
        if directory is None:
            if sys.platform=='darwin':
                directory=Path.home()/'Library/Application Support/SolidCraft/control'
            elif os.name=='nt':
                directory=Path(os.environ['LOCALAPPDATA'])/'SolidCraft/control'
            else:
                directory=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'solidcraft/control'
        self.directory=Path(directory)
        self.port=int(port if port is not None else (self.directory/'current.port').read_text().strip())

    def call(self, method, params=None):
        port=self.port
        token=(self.directory/(str(port)+'.token')).read_text().strip()
        request={'id':1,'method':method,'params':params or {},'token':token}
        with socket.create_connection(('127.0.0.1',port),timeout=15) as conn:
            conn.settimeout(30)
            conn.sendall((json.dumps(request)+'\n').encode())
            raw=conn.makefile('rb').readline(32*1024*1024)
        if not raw.endswith(b'\n'):
            raise RuntimeError('Ufuldstændigt svar fra SolidCraft')
        answer=json.loads(raw)
        if answer.get('ok') is not True:
            raise RuntimeError('SolidCraft afviste '+method+': '+str(answer.get('error')))
        return answer['result']

    def snapshot(self):
        before=self.call('document.revision')
        exported=self.call('document.export')
        inspected=self.call('document.inspect',{'measure':True,'timeline':'summary'})
        after=self.call('document.revision')
        if before!=after or exported['revision']!=after['revision']:
            raise ValueError('Modellen ændredes under aflæsning; afventer næste stabile revision')
        return before,exported,inspected


def comparison(reference, current):
    if not reference:
        return None
    same_sources=reference['climate']['snapshot']==current['climate']['snapshot']
    return {'climate_known_delta':current['climate']['known_subtotal']-reference['climate']['known_subtotal'] if same_sources else None,
            'area_delta_m2':current['area_m2']-reference['area_m2'],
            'same_area':abs(current['area_m2']-reference['area_m2'])<1e-9,
            'budget':facade.pricing.compare_reports(reference['budget'],current['budget']),
            'note':'Ændret areal er ændret omfang; forskellen er ikke en gevinst for samme funktion.'}


class LiveFacade:
    def __init__(self, config_path, control=None, climate=None):
        self.config_path=Path(config_path).resolve()
        self.config=json.loads(self.config_path.read_text())
        self.config_sha=facade.file_hash(self.config_path)
        self.directory=Path(self.config['project_directory']).resolve()
        self.directory.mkdir(parents=True,exist_ok=True)
        self.control=control or Control(port=self.config.get('control_port'))
        self.climate=climate or facade.RustClimate(self.config['engine'])
        self.code_hashes={str(Path(x.__file__).resolve()):facade.file_hash(x.__file__) for x in (facade,facade.pricing,facade_guidance)}
        self.code_hashes[str(Path(__file__).resolve())]=facade.file_hash(__file__)
        self.lock=threading.RLock()
        self.state={'status':'waiting','message':'Venter på den tilknyttede facade i SolidCraft'}
        self.result=None;self.snapshot_data=None;self.input_key=None;self.version=None
        self.reference=None;self.reference_export=None
        ref=self.directory/'reference.json'
        if ref.exists():
            saved=json.loads(ref.read_text())
            if saved['config_sha256']!=self.config_sha or saved['code_hashes']!=self.code_hashes:
                raise ValueError('Referencens program-/projektgrundlag er ændret; afstem før genstart')
            self.reference=saved['result'];self.reference_export=saved['model']
        self.stop=threading.Event()
        self.settings_path=self.directory/'maal-og-grundlag.json'
        self.settings=facade_guidance.validate(json.loads(self.settings_path.read_text())) if self.settings_path.exists() else facade_guidance.defaults()
        self.settings_sha=facade.file_hash(self.settings_path) if self.settings_path.exists() else None

    def check_basis(self):
        if facade.file_hash(self.config_path)!=self.config_sha or any(facade.file_hash(k)!=v for k,v in self.code_hashes.items()):
            raise ValueError('Program eller projektgrundlag ændret; genstart og afstem referencen')
        self.climate.verify()
        with self.lock:
            actual=facade.file_hash(self.settings_path) if self.settings_path.exists() else None
            if actual!=self.settings_sha:
                raise ValueError('Mål og grundlag er ændret i filen. Genstart visningen før du gemmer nye ændringer.')

    def tick(self):
        try:
            self.check_basis()
            version=self.control.call('document.revision')
            with self.lock:
                unchanged=version==self.version and self.state['status']=='current'
            if unchanged:
                return
            with self.lock:
                self.state={'status':'calculating','message':'Modellen er ændret — genberegner mængder, klima og overslag'}
            version,exported,inspected=self.control.snapshot()
            sample=facade.collect(exported,inspected,self.config['project_id'])
            key=facade.digest({'sample':sample,'config':self.config_sha,'code':self.code_hashes})
            result=facade.evaluate(sample,self.climate)
            if self.control.call('document.revision')!=version:
                raise ValueError('Resultatet tilhører en tidligere revision; afventer modellen')
            result['model_context']=version
            result['program_hashes']=self.code_hashes
            result['config_sha256']=self.config_sha
            with self.lock:
                if not self.reference:
                    self.reference=copy.deepcopy(result);self.reference_export=copy.deepcopy(exported)
                    self._save_reference()
                self.result=result;self.snapshot_data=exported;self.input_key=key;self.version=version
                self.state={'status':'current','message':'Aktuelt — aflæst fra SolidCraft og beregnet med Rust/Python',
                            'updated_at':datetime.now().astimezone().isoformat()}
        except Exception as error:
            with self.lock:
                self.state={'status':'unavailable','message':str(error)}

    def follow(self):
        while not self.stop.is_set():
            self.tick()
            self.stop.wait(.75)

    def _save_reference(self):
        facade.atomic_json(self.directory/'reference.json',{'config_sha256':self.config_sha,
            'code_hashes':self.code_hashes,'result':self.reference,'model':self.reference_export})

    def view(self):
        # Recheck at the HTTP read boundary: never label a completed old revision current.
        try:
            self.check_basis()
            version=self.control.call('document.revision')
        except Exception:
            version=None
        with self.lock:
            status=copy.deepcopy(self.state)
            valid=status['status']=='current' and version==self.version
            if not valid:
                if status['status']=='current':
                    status={'status':'stale','message':'Modellen er ændret eller frakoblet — afventer genberegning'}
                return {'state':status,'result':None,'reference':None,'comparison':None}
            return {'state':status,'result':copy.deepcopy(self.result),'reference':copy.deepcopy(self.reference),
                    'comparison':comparison(self.reference,self.result),'input_key':self.input_key,
                    'settings':copy.deepcopy(self.settings),
                    'guidance':facade_guidance.overview(self.result,self.reference,self.settings)}

    def update_settings(self, expected_key, settings):
        current=self.view()
        if current.get('input_key')!=expected_key or current['result'] is None:
            raise ValueError('Modellen har ændret sig. Vent på den aktuelle beregning.')
        settings=facade_guidance.validate(settings)
        with self.lock:
            if expected_key!=self.input_key or settings['revision']!=self.settings['revision']:
                raise ValueError('Grundlaget er ændret i en anden visning. Genindlæs før du gemmer.')
            settings['revision']+=1
            facade.atomic_json(self.settings_path,settings)
            self.settings_sha=facade.file_hash(self.settings_path)
            self.settings=settings
        return 'Mål og grundlag gemt. Model og kildeberegning er bevaret.'

    def save(self, expected_key, reference=False):
        view=self.view()
        if view.get('input_key')!=expected_key or view['result'] is None:
            raise ValueError('Visningen er forældet; vent på den aktuelle beregning')
        with self.lock:
            if expected_key!=self.input_key:
                raise ValueError('Input har ændret sig')
            if reference:
                self.reference=copy.deepcopy(self.result);self.reference_export=copy.deepcopy(self.snapshot_data)
                self._save_reference()
            else:
                # A separate complete model snapshot and report; never writes to the active tab.
                facade.atomic_json(self.directory/'gemt-model.json',json.loads(self.snapshot_data['text']))
                facade.atomic_json(self.directory/'gemt-regnskab.json',view)
            return 'Reference fastholdt' if reference else 'Modelkopi og regnskab gemt særskilt'


PAGE=Path(__file__).with_name('facade_page.html').read_text(encoding='utf-8')


def server_for(live, port=0):
    token=secrets.token_urlsafe(24)
    prefix='/'+token
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def reply(self,status,data,kind='application/json'):
            raw=data.encode() if isinstance(data,str) else json.dumps(data,ensure_ascii=False).encode()
            self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8')
            self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Frame-Options','DENY');self.end_headers();self.wfile.write(raw)
        def allowed(self):
            host='127.0.0.1:'+str(self.server.server_port)
            return self.headers.get('Host')==host and self.headers.get('Origin') in (None,'http://'+host)
        def do_GET(self):
            if not self.allowed():return self.reply(403,{'error':'Adgang afvist'})
            if self.path==prefix:return self.reply(200,PAGE,'text/html')
            if self.path==prefix+'/state':return self.reply(200,live.view())
            return self.reply(404,{'error':'Ukendt adresse'})
        def do_POST(self):
            if not self.allowed() or self.path not in (prefix+'/save',prefix+'/reference',prefix+'/settings'):
                return self.reply(403,{'error':'Adgang afvist'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=65536 or not self.headers.get('Content-Type','').startswith('application/json'):
                    raise ValueError('Ugyldig anmodning')
                fields=json.loads(self.rfile.read(length))
                required={'input_key','settings'} if self.path.endswith('/settings') else {'input_key'}
                if not isinstance(fields,dict) or set(fields)!=required:raise ValueError('Ukendte felter')
                if self.path.endswith('/settings'):
                    message=live.update_settings(fields['input_key'],fields['settings'])
                else:
                    message=live.save(fields['input_key'],reference=self.path.endswith('/reference'))
                self.reply(200,{'message':message})
            except (ValueError,KeyError,OSError) as e:self.reply(409,{'error':str(e)})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    return server,'http://127.0.0.1:'+str(server.server_port)+prefix


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config',type=Path)
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    live=LiveFacade(args.config)
    if args.once:
        live.tick();view=live.view()
        facade.atomic_json(live.directory/'kontrol-engang.json',view)
        print(json.dumps({'state':view['state'],'result':None if not view['result'] else
            {'active':view['result']['active'],'area_m2':view['result']['area_m2'],
             'climate':view['result']['climate'],'budget_status':view['result']['budget']['status']}},ensure_ascii=False))
        if not view['result']:raise SystemExit(1)
        return
    server,url=server_for(live)
    facade.atomic_json(live.directory/'forbindelse.json',{'url':url,'pid':os.getpid(),'config':str(args.config.resolve())})
    print(url,flush=True)
    worker=threading.Thread(target=live.follow,daemon=True);worker.start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:live.stop.set();server.server_close()


if __name__=='__main__':main()
