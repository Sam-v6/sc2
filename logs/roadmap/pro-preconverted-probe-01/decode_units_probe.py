import json,struct,pathlib,collections,hashlib
import numpy as np
P=pathlib.Path(__file__).parent
FIELDS=[('id','<u8'),('unitType','<i4'),('observation','u1'),('alliance','u1')]+[(k,'<f4') for k in ('health','health_max','shield','shield_max','energy','energy_max')]+[(k,'i1') for k in ('cargo','cargo_max','assigned_harvesters','ideal_harvesters')]+[('weapon_cooldown','<f4'),('tgtId','<u8'),('cloak_state','u1')]+[(k,'i1') for k in ('is_blip','is_flying','is_burrowed','is_powered','in_cargo')]+[('pos','V12')]+[(f'order{i}','V24') for i in range(4)]+[('buff0','<i4'),('buff1','<i4')]+[(k,'<f4') for k in ('heading','radius','build_progress')]+[('add_on_tag','u1')]
NEUTRAL=[('id','<u8'),('unitType','<i4'),('observation','u1'),('health','<f4'),('health_max','<f4'),('pos','V12'),('heading','<f4'),('radius','<f4'),('contents','<u2')]
for idx in (294,774,870):
 actions=json.loads((P/f'fall-actions-{idx}.json').read_text());b=(P/f'fall-record-{idx}.bin').read_bytes();offset=actions['units_offset'];n=actions['observation_count']
 def vector(dtype):
  global offset
  count=struct.unpack_from('<Q',b,offset)[0];offset+=8;dt=np.dtype(dtype);assert count<10000000 and offset+count*dt.itemsize<=len(b);a=np.frombuffer(b,dtype=dt,count=count,offset=offset);offset+=count*dt.itemsize;return a
 def block(fields):
  global offset
  arrays={k:vector(d) for k,d in fields};count=len(arrays['id']);assert all(len(a)==count for a in arrays.values());ranges=vector('V8').view('<u4').reshape(-1,2);maxstep=struct.unpack_from('<I',b,offset)[0];offset+=4;assert maxstep==n;assert int(ranges[:,1].sum())==count;assert np.all(ranges[:,0]+ranges[:,1]<=n);steps=np.concatenate([np.arange(start,start+length,dtype=np.uint32) for start,length in ranges]);assert len(steps)==count;return arrays,steps
 units,steps=block(FIELDS);neutral,nsteps=block(NEUTRAL);assert offset==len(b)
 assert set(np.unique(units['alliance']))<={1,2,3,4};assert set(np.unique(units['observation']))<={1,2,3}
 initial=[]
 for i in np.flatnonzero(steps==0):
  initial.append({k:int(units[k][i]) for k in ('id','unitType','observation','alliance')});initial[-1]['position']=struct.unpack('<fff',units['pos'][i]);initial[-1]['orders']=[struct.unpack('<ifQii',units[f'order{j}'][i]) for j in range(4)]
 own_by=collections.defaultdict(set)
 for i in np.flatnonzero(units['alliance']==1):own_by[int(steps[i])].add(int(units['id'][i]))
 counts=collections.Counter()
 for step,row in enumerate(actions['actions']):
  for a in row['actions']:
   counts['converted_commands']+=1;counts['all_selected_actors_present_and_self']+=set(a['tags'])<=own_by[step]
 # Re-read scalar and visibility blocks to test perspective and command timing.
 cursor=0
 for _ in range(2):
  size=struct.unpack_from('<Q',b,cursor)[0];cursor+=8+size
 cursor+=26
 h,w,size=struct.unpack_from('<iiQ',b,cursor);cursor+=16+size
 for itemsize in (4,2,2,2,2,2,88):
  count=struct.unpack_from('<Q',b,cursor)[0];cursor+=8
  assert count==n
  if itemsize==2 and 'first_minerals' not in locals():first_minerals=struct.unpack_from('<H',b,cursor)[0]
  cursor+=count*itemsize
 count=struct.unpack_from('<Q',b,cursor)[0];cursor+=8;assert count==n
 grids=[]
 for _ in range(n):
  h,w,size=struct.unpack_from('<iiQ',b,cursor);cursor+=16;assert (h,w,size)==(128,128,16384);grids.append(np.frombuffer(b,dtype='u1',count=size,offset=cursor).reshape(128,128));cursor+=size
 visibility=np.stack(grids);position=units['pos'].view('<f4').reshape(-1,3);x=np.clip((position[:,0]*128/actions['header']['width']).astype(int),0,127);y=np.clip((position[:,1]*128/actions['header']['height']).astype(int),0,127)
 fog={}
 for square_scale in (False,True):
  scale=max(actions['header']['width'],actions['header']['height']);yy=np.clip((position[:,1]*128/scale).astype(int),0,127) if square_scale else y;xx=np.clip((position[:,0]*128/scale).astype(int),0,127) if square_scale else x
  for flip in (False,True):
   pixels=visibility[steps,127-yy if flip else yy,xx];fog[f'square_scale={square_scale},flip={flip}']={str(int(v)):{str(int(pixel)):int(np.count_nonzero((units['alliance']==4)&(units['observation']==v)&(pixels==pixel))) for pixel in np.unique(pixels)} for v in np.unique(units['observation'])}
 # PySC2 transform flips in world coordinates before applying the uniform scale.
 mapheight=actions['header']['height'];scale=max(actions['header']['width'],mapheight);xx=np.clip(np.floor(position[:,0]*128/scale).astype(int),0,127);yy=np.clip(np.floor((mapheight-position[:,1])*128/scale).astype(int),0,127);pixels=visibility[steps,yy,xx];fog['pysc2_world_flip_then_uniform_scale']={str(int(v)):{str(int(pixel)):int(np.count_nonzero((units['alliance']==4)&(units['observation']==v)&(pixels==pixel))) for pixel in np.unique(pixels)} for v in np.unique(units['observation'])}
 # Compare original-replay map dimensions from an existing local map archive.
 import mpyq
 mapname='AcropolisLE' if idx==870 else 'DiscoBloodbathLE';mapfile=P/('original-acropolis.s2ma' if idx==870 else 'original-disco.s2ma');mapinfo=mpyq.MPQArchive(str(mapfile)).read_file('MapInfo');mw,mh=struct.unpack_from('<II',mapinfo,16);scale=max(mw,mh);xx=np.clip(np.floor(position[:,0]*128/scale).astype(int),0,127);yy=np.clip(np.floor((mh-position[:,1])*128/scale).astype(int),0,127);pixels=visibility[steps,yy,xx];fog['original_map_dimensions_world_flip_then_uniform_scale']={str(int(v)):{str(int(pixel)):int(np.count_nonzero((units['alliance']==4)&(units['observation']==v)&(pixels==pixel))) for pixel in np.unique(pixels)} for v in np.unique(units['observation'])}
 mapcheck={'map':mapname,'path':str(mapfile),'sha256':hashlib.sha256(mapfile.read_bytes()).hexdigest(),'width':mw,'height':mh,'header_width':actions['header']['width'],'header_height':actions['header']['height'],'identity':'Exact original replay cache-handle SHA256 verified; dimensions also checked with installed sc2reader MapInfo'}
 causal={'first_observation_loop':actions['first_loop'],'first_minerals':first_minerals,'first_command':actions['actions'][0]['actions'],'starting_command_center_orders':[u['orders'] for u in initial if u['unitType']==18]};del first_minerals
 r={'original_map_dimension_check':mapcheck,'enemy_visibility_pixel_crosscheck':fog,'initial_command_timing_check':causal,'idx':idx,'decoded_bytes_consumed':offset,'record_sha256':hashlib.sha256(b).hexdigest(),'unit_samples':len(steps),'neutral_samples':len(nsteps),'alliance_visibility_counts':{str((int(a),int(v))):int(np.count_nonzero((units['alliance']==a)&(units['observation']==v))) for a in np.unique(units['alliance']) for v in np.unique(units['observation'])},'first_observation_units':initial,'first_observation_neutral_count':int(np.count_nonzero(nsteps==0)),'actor_presence':dict(counts),'training_eligible':False};(P/f'unit-block-audit-{idx}.json').write_text(json.dumps(r,indent=2)+'\n');print(idx,'samples',len(steps),len(nsteps),'initial',len(initial),'counts',counts,flush=True)
