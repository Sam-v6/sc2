"""Bounded Linux game workers and unique artifact identities."""
import multiprocessing as mp
import os
import signal
import time
import traceback
from uuid import uuid4


def match_id():
    return uuid4().hex


def _child(connection, function, args):
    os.setsid()
    try:
        connection.send(function(*args))
    except BaseException:
        connection.send({'status': 'error', 'result': None, 'error': traceback.format_exc()})
    finally:
        connection.close()


def _stop(process):
    # Only signal the process group established by this worker's setsid().
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    if process.is_alive():
        try:
            group = os.getpgid(process.pid)
            if group == process.pid:
                os.killpg(group, signal.SIGTERM)
            else:
                process.terminate()
        except ProcessLookupError:
            pass
        process.join(2)
        if process.is_alive():
            try:
                if os.getpgid(process.pid) == process.pid:
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            process.join()
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def supervise(function, args, timeout, stop_event=None):
    context = mp.get_context('spawn')
    receive, send = context.Pipe(duplex=False)
    process = context.Process(target=_child, args=(send, function, args))
    start = time.monotonic()
    process.start()
    send.close()
    try:
        while True:
            remaining = timeout - (time.monotonic() - start)
            if stop_event is not None and stop_event.is_set():
                result = {'status': 'cancelled', 'result': None}
                break
            if remaining <= 0:
                result = {'status': 'wall_timeout', 'result': None}
                break
            if receive.poll(min(remaining, .1) if stop_event is not None else remaining):
                try:
                    result = receive.recv()
                except EOFError:
                    result = {'status': 'error', 'result': None, 'error': 'Worker exited without a result'}
                process.join(3)
                break
    finally:
        _stop(process)
        receive.close()
        process.close()
    result['wall_seconds'] = round(time.monotonic() - start, 3)
    return result
