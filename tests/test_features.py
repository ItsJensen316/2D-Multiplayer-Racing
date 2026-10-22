"""Timing, persistence, synthesized audio and feedback regression checks."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from collections import defaultdict
import pygame
from racing.app import App
from racing.records import Records,format_time
from racing.audio import Audio
from racing.effects import Effects
from racing.driver import Driver,RacePhysics,FIXED_DT


class RecordsTests(unittest.TestCase):
    def test_records_survive_reload_and_keep_distances_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            r=Records(directory)
            self.assertTrue(r.lap('club',1,31.25))
            self.assertFalse(r.lap('club',2,35))
            r.race('club',1,1,31.25);r.race('club',2,3,97)
            r.audio(.3,True)
            r=Records(directory)
            self.assertEqual(r.best('club'),31.25)
            self.assertEqual(r.best('club','p2_lap'),35)
            self.assertEqual(r.best('club','race_1'),31.25)
            self.assertEqual(r.best('club','race_3'),97)
            self.assertEqual(r.data['audio'],{'volume':.3,'muted':True})

    def test_bad_file_preserved_and_invalid_times_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'records.json';p.write_text('broken!')
            r=Records(directory)
            self.assertTrue(list(Path(directory).glob('records-unreadable-*.json')))
            for value in [-1,0,float('nan'),float('inf'),True]:
                self.assertFalse(r.lap('club',1,value))
            self.assertIsNone(r.best('club'))
            self.assertTrue(r.lap('club',1,30))

    def test_unwritable_store_fails_without_crash(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'not-a-directory';p.write_text('test')
            r=Records(p)
            self.assertFalse(r.save())
            self.assertTrue(r.error)

    def test_time_rounding(self):
        self.assertEqual(format_time(59.9996),'01:00.000')
        self.assertEqual(format_time(None),'--:--.---')


class FeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.app=App(cls.temp.name)

    @classmethod
    def tearDownClass(cls):
        cls.app.audio.close();pygame.quit();cls.temp.cleanup()

    def car(self):
        a=self.app
        return Driver(a.tracks[0],0,a.images['car1.png'],dict(up=pygame.K_UP,down=pygame.K_DOWN,left=pygame.K_LEFT,right=pygame.K_RIGHT))

    def cross_finish(self,car,world):
        center,tangent=car.track.gates[0]
        car.position=center-tangent*.5
        car.heading=0
        car.speed=120
        car.next_gate=0
        world.advance(FIXED_DT,defaultdict(bool),target_laps=3)

    def test_lap_timestamp_interpolates_crossing_and_finishes(self):
        car=self.car();world=RacePhysics([car]);world.elapsed=10
        self.cross_finish(car,world)
        self.assertEqual(len(car.lap_times),1)
        self.assertGreater(car.lap_times[0],10)
        self.assertLess(car.lap_times[0],10+FIXED_DT)
        self.assertAlmostEqual(car.lap_start_time,car.lap_times[0])
        world.elapsed=40
        self.cross_finish(car,world)
        self.assertEqual(len(car.lap_times),2)
        self.assertAlmostEqual(sum(car.lap_times),car.lap_start_time)
        car.point=2;world.elapsed=70
        self.cross_finish(car,world)
        self.assertEqual(world.finished,[1])
        self.assertIsNotNone(car.finish_time)
        self.assertAlmostEqual(sum(car.lap_times),car.finish_time)

    def test_pause_does_not_change_lap_clock_or_effects(self):
        a=self.app;a.track_index=0;a.race();a.update(3.1);a.update(.1)
        before=a.elapsed
        a.change('paused');a.update(.2)
        self.assertEqual(a.elapsed,before)
        a.change('race');a.update(.1)
        self.assertAlmostEqual(a.elapsed,before+.1)
        for i in range(4):self.assertFalse(pygame.mixer.Channel(i).get_busy()) if a.audio.muted else None

    def test_lap_event_saves_record_and_unfinished_player_not_saved(self):
        a=self.app;a.track_index=0;a.laps=1;a.race();a.change('race')
        car=a.cars[0];car.position=car.track.finish-car.track.tangent*.5
        car.heading=0;car.speed=120;car.next_gate=0
        a.physics.elapsed=32
        a.update(FIXED_DT)
        self.assertEqual(a.state,'results')
        reloaded=Records(a.records.directory)
        self.assertIsNotNone(reloaded.best(a.active_track.id+'-boost-v1'))
        self.assertIsNotNone(reloaded.best(a.active_track.id+'-boost-v1','p1_race_1'))
        self.assertIsNone(reloaded.best(a.active_track.id+'-boost-v1','p2_race_1'))
        self.assertIsNone(a.cars[1].finish_time)

    def test_synthesized_audio_channels_mute_and_silent_fallback(self):
        audio=Audio(.3,False)
        self.assertTrue(audio.available)
        car=self.car();car.speed=240
        audio.update(.1,'race',[car],defaultdict(bool))
        self.assertTrue(pygame.mixer.Channel(0).get_busy())
        audio.play('hit')
        self.assertGreater(audio.sounds['hit'].get_length(),.1)
        audio.muted=True;audio.update(.1,'race',[car],defaultdict(bool))
        self.assertFalse(pygame.mixer.Channel(0).get_busy())
        audio.muted=False;audio.update(.1,'paused',[car],defaultdict(bool))
        self.assertFalse(pygame.mixer.Channel(0).get_busy())
        audio.close()
        with patch('pygame.mixer.get_init',return_value=None),patch('pygame.mixer.init',side_effect=pygame.error('no device')):
            fallback=Audio();self.assertFalse(fallback.available)
            fallback.play('go');fallback.update(.1,'race',[car],defaultdict(bool));fallback.close()

    def test_feedback_is_bounded_and_clears(self):
        effects=Effects();car=self.car();car.speed=250
        keys=defaultdict(bool,{pygame.K_LEFT:True})
        effects.update(.02,[car],keys)
        car.position.x+=8;effects.update(.02,[car],keys)
        self.assertGreater(len(effects.marks),0)
        for _ in range(50):effects.impact(car.position,300)
        self.assertLessEqual(len(effects.sparks),160)
        effects.update(10,[],keys)
        self.assertFalse(effects.sparks);self.assertFalse(effects.marks)

    def test_new_screens_and_controls(self):
        a=self.app
        for state in ['menu','setup','records','settings','controls','paused','results']:
            if state in ('paused','results'):a.race()
            a.change(state);a.draw();a.present()
        a.audio.volume=.5;a.audio.muted=False
        a.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_m));self.assertTrue(a.audio.muted)
        a.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHTBRACKET));self.assertAlmostEqual(a.audio.volume,.6)
        self.assertTrue(Records(a.records.directory).data['audio']['muted'])
        a.race();self.assertFalse(a.cars[0].lap_times)
        self.assertFalse(a.effects.marks)


if __name__=='__main__':unittest.main()
