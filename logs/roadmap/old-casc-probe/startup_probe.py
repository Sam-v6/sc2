"""Bounded old-engine startup and protocol ping, with process-group cleanup."""
import asyncio,json,os,sys,resource
from pathlib import Path
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE.parents[2]))
os.environ['SC2PATH']=str(BASE.parent/'runtime-4.9.3')
from src.runtime import supervise
async def probe():
 from sc2.sc2process import SC2Process
 from s2clientprotocol import sc2api_pb2 as pb
 async with SC2Process(base_build='Base75025',data_hash='C305368C63621480462F8F516FB64374') as server:
  packet=await server._execute(ping=pb.RequestPing())
  result={'status':'ping_succeeded','game_version':packet.ping.game_version,'data_version':packet.ping.data_version,'base_build':packet.ping.base_build}
  await server.quit()
  return result
def child():
 resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 return asyncio.run(probe())
if __name__=='__main__':
 result=supervise(child,(),60)
 (BASE/'startup-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
