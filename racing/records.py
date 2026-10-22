"""Local race records and audio preferences, saved atomically outside the game folder."""
import json
import math
import os
from pathlib import Path
import tempfile
import time


def data_directory():
    override = os.environ.get('APEX_RACING_DATA_DIR')
    if override: return Path(override)
    if os.name == 'nt': return Path(os.environ.get('APPDATA', Path.home())) / 'ApexRacing'
    return Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share')) / 'apex-racing'


def valid_time(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value > 0


def format_time(value):
    if value is None: return '--:--.---'
    milliseconds = round(max(0,value)*1000)
    minutes, remainder = divmod(milliseconds,60000)
    seconds, milliseconds = divmod(remainder,1000)
    return f'{minutes:02}:{seconds:02}.{milliseconds:03}'


class Records:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory else data_directory()
        self.path = self.directory/'records.json'
        self.data = {'version':1,'tracks':{},'audio':{'volume':.5,'muted':False}}
        self.error = ''
        try:
            raw=json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(raw,dict) or raw.get('version') != 1: raise ValueError('Unsupported records format')
            for track,values in raw.get('tracks',{}).items():
                if not isinstance(values,dict): continue
                clean={}
                for key,value in values.items():
                    if valid_time(value): clean[key]=value
                self.data['tracks'][track]=clean
            audio=raw.get('audio',{})
            volume=audio.get('volume',.5)
            if isinstance(volume,(int,float)) and math.isfinite(volume):
                self.data['audio']['volume']=max(0,min(1,volume))
            self.data['audio']['muted']=audio.get('muted') is True
        except FileNotFoundError: pass
        except (ValueError,TypeError,AttributeError):
            try:
                self.path.rename(self.path.with_name(f'records-unreadable-{time.time_ns()}.json'))
            except OSError: self.error='Records could not be recovered.'
        except OSError: self.error='Records could not be read.'

    def best(self, track, key='lap'):
        return self.data['tracks'].get(track,{}).get(key)

    def update_best(self,track,key,value):
        if not valid_time(value): return False
        values=self.data['tracks'].setdefault(track,{})
        if key not in values or value < values[key]:
            values[key]=value
            return True
        return False

    def lap(self,track,player,value):
        changed=self.update_best(track,'lap',value)
        personal=self.update_best(track,f'p{player}_lap',value)
        if changed or personal: self.save()
        return changed

    def race(self,track,player,laps,value):
        # Separate distances: a one-lap race never replaces a three-lap record.
        changed=self.update_best(track,f'race_{laps}',value)
        personal=self.update_best(track,f'p{player}_race_{laps}',value)
        if changed or personal:self.save()
        return changed

    def audio(self,volume,muted):
        self.data['audio']={'volume':max(0,min(1,volume)),'muted':bool(muted)}
        self.save()

    def save(self):
        temporary=None
        try:
            self.directory.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=self.directory,delete=False) as file:
                temporary=Path(file.name)
                json.dump(self.data,file,indent=2,allow_nan=False)
            temporary.replace(self.path)
            self.error=''
            return True
        except (OSError,ValueError):
            self.error='Records could not be saved.'
            return False
        finally:
            if temporary:
                try:temporary.unlink(missing_ok=True)
                except OSError:pass
