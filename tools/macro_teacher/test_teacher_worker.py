import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock,patch
from selector import TeacherPolicy
from teacher_worker import ObservedLearner,episode,digest,ordinary
from src.rl.actor_critic import ActorCritic
from src.rl.terran import FEATURES,ACTIONS


class WorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_observer_records_without_changing_command_buffer(self):
        context=SimpleNamespace(gamma=.99,reward_scale=.01,reward_version='combat-kills-v1',macro_seconds=1)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            bot=ObservedLearner(TeacherPolicy(context),False,root/'actions',journal=root/'journal',
                                production=root/'production',commands=root/'commands',macro_seconds=1)
            unit=SimpleNamespace(tag=101,type_id=SimpleNamespace(name='MARINE'))
            command=SimpleNamespace(unit=unit,ability=SimpleNamespace(name='TRAIN_MARINE'),target=None,queue=False)
            bot.state=SimpleNamespace(game_loop=224);bot.actions=[command];bot.decisions=[{}]
            with patch('teacher_worker.JournalLearner.custom_on_step',new=AsyncMock()) as original:
                await bot.custom_on_step(8);original.assert_awaited_once_with(8)
            await bot.on_unit_created(unit)
            bot.production_file.close();bot.command_file.close()
            self.assertEqual(bot.actions,[command])
            record=json.loads((root/'commands').read_text());self.assertEqual(record['queued'][0]['ability'],'TRAIN_MARINE')
            self.assertEqual(json.loads((root/'production').read_text())['event'],'unit_appeared')

    async def test_episode_failure_restores_normal_runner_and_never_fits(self):
        import selector
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'context.npz'
            context=ActorCritic(FEATURES,ACTIONS,seed=7);context.gamma=.99;context.macro_seconds=1
            context.reward_version='combat-kills-v1';context.save(path)
            job={'purpose':'macro-teacher-preflight','mode':'evaluate','game_limit':1200,'macro_seconds':1,
                 'gamma':.99,'reward_scale':.01,'reward_version':'combat-kills-v1','behavior_checkpoint':str(path),
                 'behavior_checkpoint_sha256':digest(path),'checkpoint_role':'context_only_not_teacher_weights',
                 'teacher_source':str(Path(selector.__file__).resolve()),'teacher_source_sha256':digest(selector.__file__),
                 **{key:str(root/key) for key in ['actions','journal','replay','trajectory','production','commands']}}
            before_load,before_bot=ordinary.load_policy,ordinary.TerranLearner
            with patch.object(ordinary,'episode',side_effect=RuntimeError('native failure')):
                with self.assertRaises(RuntimeError):episode(job)
            self.assertIs(ordinary.load_policy,before_load);self.assertIs(ordinary.TerranLearner,before_bot)
            self.assertEqual(digest(path),job['behavior_checkpoint_sha256']);self.assertFalse(Path(job['trajectory']).exists())


if __name__=='__main__':unittest.main()
