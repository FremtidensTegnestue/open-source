"""Atomic JSON report output that preserves models, inputs and original sources."""
import json
import os
from pathlib import Path
import tempfile

ROOT=Path(__file__).resolve().parent

def write_report(value, destination, protected_paths=()):
    target=Path(destination).expanduser().resolve()
    protected={Path(p).expanduser().resolve() for p in protected_paths if p is not None}
    if target in protected:
        raise ValueError('Report output would overwrite a source model, request, binding or database')
    if any(target.is_relative_to(ROOT/relative) for relative in ('data/raw','archive','unpacked','upstream')):
        raise ValueError('Report output cannot overwrite the original-source archive')
    if target.suffix.casefold()!='.json':
        raise ValueError('JSON reports require a .json output path')
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=target.parent,prefix=target.name+'.',suffix='.tmp',delete=False) as stream:
            temporary=Path(stream.name);stream.write(text)
        os.replace(temporary,target)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
