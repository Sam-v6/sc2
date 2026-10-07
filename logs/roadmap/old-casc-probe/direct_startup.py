"""Capture engine stderr, which BurnySC2's launcher suppresses."""
import json,os,resource,socket,subprocess,time,signal
from pathlib import Path
BASE=Path(__file__).resolve().parent
runtime=BASE.parent/'runtime-4.9.3'
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
args=[str(runtime/'Versions/Base75025/SC2_x64'),'-listen','127.0.0.1','-port',str(port),'-dataDir',str(runtime),'-tempDir',str(BASE),'-displayMode','0','-dataVersion','C305368C63621480462F8F516FB64374','-verbose']
start=time.monotonic();result={'args':args,'status':'wall_timeout'}
with (BASE/'direct-startup.log').open('wb') as log:
 p=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try:
  while time.monotonic()-start<60:
   if p.poll() is not None:result.update(status='engine_exited',exit_code=p.returncode);break
   try:
    with socket.create_connection(('127.0.0.1',port),timeout=.2):result['status']='socket_open';break
   except OSError:time.sleep(.2)
 finally:
  if p.poll() is None:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
result['wall_seconds']=time.monotonic()-start
(BASE/'direct-startup-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
