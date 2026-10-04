"""Render a matching Linux SC2 replay to a portable MP4 after simulation."""
import argparse
import asyncio
from contextlib import suppress
import json
from pathlib import Path
import shutil
import subprocess
import sys

from src.path import SC2_GAME_PATH
from src.runtime import supervise
from src.runner import positive
from sc2.main import get_replay_version
from sc2.sc2process import SC2Process
from s2clientprotocol import sc2api_pb2 as pb


def validate_inputs(replay, game_map):
    for path in (replay, game_map):
        if not Path(path).is_file():
            raise FileNotFoundError(path)
    if not shutil.which('ffmpeg'):
        raise FileNotFoundError('ffmpeg is required; no packages are installed automatically')


def validate_frame(frame, width, height):
    if (frame.size.x, frame.size.y, frame.bits_per_pixel) != (width, height, 24):
        raise ValueError('SC2 returned unexpected RGB dimensions or pixel format')
    if len(frame.data) != width * height * 3:
        raise ValueError('SC2 returned missing or incomplete RGB data')
    return frame.data


def check_encoder(code):
    if code != 0:
        raise RuntimeError(f'ffmpeg failed with exit code {code}')


def check_replay_start(response):
    if response.HasField('error'):
        raise RuntimeError(f'{pb.ResponseStartReplay.Error.Name(response.error)}: {response.error_details}')


def overview_request(width, height):
    return {'obs_action': pb.RequestObserverAction(actions=[pb.ObserverAction(
        camera_move=pb.ActionObserverCameraMove(world_pos={'x': width / 2, 'y': height / 2}, distance=max(width, height)))])}


async def record_frames(server, encoder, job):
    telemetry = []
    ended = False
    for _ in range(job['max_frames']):
        response = await server._execute(observation=pb.RequestObservation())
        if response.status == pb.ended and not response.observation.player_result:
            response = await server._execute(observation=pb.RequestObservation())
            if not response.observation.player_result:
                raise RuntimeError('Replay ended without player results')
        ended = bool(response.observation.player_result)
        observation = response.observation.observation
        if ended and not observation.render_data.map.data:
            break
        encoder.stdin.write(validate_frame(observation.render_data.map, job['width'], job['height']))
        score = observation.score.score_details
        common = observation.player_common
        telemetry.append({'game_time': observation.game_loop / 22.4, 'minerals': common.minerals,
                          'vespene': common.vespene, 'army': common.food_army, 'workers': common.food_workers,
                          'collection_rate_minerals': score.collection_rate_minerals,
                          'collection_rate_vespene': score.collection_rate_vespene})
        if ended:
            break
        await server._execute(step=pb.RequestStep(count=job['step']))
    return telemetry, ended


async def render(job):
    from loguru import logger
    logger.remove()
    logger.add(sys.stderr, level='WARNING')
    validate_inputs(job['replay'], job['map'])
    base_build, data_hash = get_replay_version(job['replay'])
    if not (Path(SC2_GAME_PATH) / 'Versions' / base_build / 'SC2_x64').is_file():
        raise FileNotFoundError(f'Replay requires unavailable SC2 build {base_build}')
    process = SC2Process(base_build=base_build, data_hash=data_hash)
    if job['library']:
        library = Path(job['library'])
        if not library.is_file():
            raise FileNotFoundError(library)
    else:
        library = next((p for p in (Path('/lib/x86_64-linux-gnu/libOSMesa.so.8'), Path('/usr/lib/x86_64-linux-gnu/libOSMesa.so.8')) if p.is_file()), None)
        if library is None:
            raise FileNotFoundError('No OSMesa library found; supply --library')
    process._arguments['-osmesapath'] = str(library)
    width, height = job['width'], job['height']
    telemetry = []
    frames = 0
    output = Path(job['output'])
    temporary = output.with_name(output.stem + '.partial.mp4')
    output.parent.mkdir(parents=True, exist_ok=True)
    async with process as server:
        options = pb.InterfaceOptions(raw=True, score=True)
        options.render.resolution.x, options.render.resolution.y = width, height
        options.render.minimap_resolution.x = options.render.minimap_resolution.y = 128
        response = await server._execute(start_replay=pb.RequestStartReplay(
            replay_data=Path(job['replay']).read_bytes(), map_data=Path(job['map']).read_bytes(),
            observed_player_id=job['player'], options=options, realtime=False, disable_fog=job['omniscient']))
        check_replay_start(response.start_replay)
        if job['camera'] == 'overview':
            info = await server._execute(game_info=pb.RequestGameInfo())
            size = info.game_info.start_raw.map_size
            await server._execute(**overview_request(size.x, size.y))
        encoder = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pixel_format', 'rgb24',
                                    '-video_size', f'{width}x{height}', '-framerate', str(job['fps']), '-i', '-', '-an',
                                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(temporary)], stdin=subprocess.PIPE)
        try:
            telemetry, ended = await record_frames(server, encoder, job)
            encoder.stdin.close()
            check_encoder(encoder.wait(timeout=15))
        except BaseException:
            encoder.kill()
            encoder.wait()
            with suppress(BrokenPipeError):
                encoder.stdin.close()
            raise
        frames = len(telemetry)
        if not frames:
            raise RuntimeError('Replay contained no RGB frames')
        await server.quit()
    temporary.replace(output)
    receipt = {'status': 'completed', 'result': None, 'replay': job['replay'], 'map': job['map'],
               'base_build': base_build, 'frames': frames, 'width': width, 'height': height,
               'fps': job['fps'], 'step': job['step'], 'game_seconds': telemetry[-1]['game_time'],
               'frame_limit_reached': not ended, 'player': job['player'],
               'camera': job['camera'], 'omniscient': job['omniscient'], 'telemetry': telemetry}
    output.with_suffix('.frames.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return {key: value for key, value in receipt.items() if key != 'telemetry'}


def render_job(job):
    return asyncio.run(render(job))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('replay', type=Path)
    p.add_argument('--map-file', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--camera', choices=['base', 'overview'], default='base')
    p.add_argument('--player', type=int, choices=[1, 2], default=1)
    p.add_argument('--omniscient', action='store_true', help='Remove fog in replay viewing only')
    p.add_argument('--width', type=positive, default=640)
    p.add_argument('--height', type=positive, default=480)
    p.add_argument('--fps', type=positive, default=8)
    p.add_argument('--step', type=positive, default=3)
    p.add_argument('--max-frames', type=positive, default=20000)
    p.add_argument('--wall-seconds', type=positive, default=600)
    p.add_argument('--library', default=None)
    args = p.parse_args()
    if args.width % 2 or args.height % 2:
        p.error('Width and height must be even for MP4 encoding')
    if args.output.suffix.lower() != '.mp4':
        p.error('Output must end in .mp4')
    validate_inputs(args.replay, args.map_file)
    job = vars(args).copy()
    job['map'] = str(args.map_file.resolve())
    job['replay'], job['output'] = str(args.replay.resolve()), str(args.output.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipt = supervise(render_job, (job,), args.wall_seconds)
    args.output.with_suffix('.export.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)
    if receipt['status'] != 'completed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
