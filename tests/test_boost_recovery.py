import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile
import unittest
from collections import defaultdict
import pygame
from racing.app import App
from racing.driver import Driver,RacePhysics,contact,MAX_SPEED,BOOST_SPEED


class BoostRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.app=App(cls.temp.name)

    @classmethod
    def tearDownClass(cls):
        cls.app.stop();pygame.quit();cls.temp.cleanup()

    def race(self,track=0):
        a=self.app;a.track_index=track;a.race();a.change('race');return a

    def test_boost_accelerates_and_decays_after_release(self):
        a=self.race();car=a.cars[0];car.speed=300
        held=defaultdict(bool,{pygame.K_UP:True,pygame.K_RSHIFT:True})
        car.update(.35,held)
        self.assertGreater(car.speed,MAX_SPEED);self.assertLessEqual(car.speed,BOOST_SPEED)
        self.assertLess(car.boost,1)
        release=defaultdict(bool,{pygame.K_UP:True})
        # Test deceleration without running into a corner by resetting position.
        for _ in range(150):
            car.position=pygame.Vector2(750,180);car.heading=0;car.update(1/120,release)
        self.assertAlmostEqual(car.speed,MAX_SPEED)
        self.assertLessEqual(car.boost,1)

    def test_empty_boost_requires_release_and_recharges(self):
        a=self.race();car=a.cars[0]
        held=defaultdict(bool,{pygame.K_UP:True,pygame.K_RSHIFT:True})
        for _ in range(300):
            car.position=pygame.Vector2(750,180);car.heading=0;car.update(1/120,held)
        self.assertEqual(car.boost,0);self.assertTrue(car.boost_locked)
        car.update(.1,held);self.assertFalse(car.boosting)
        for _ in range(250):
            car.position=pygame.Vector2(750,180);car.heading=0;car.update(1/120,defaultdict(bool))
        self.assertGreater(car.boost,.3);self.assertFalse(car.boost_locked)

    def test_boost_does_not_enable_in_reverse_or_braking(self):
        a=self.race();car=a.cars[0];car.speed=-80
        car.update(.1,defaultdict(bool,{pygame.K_DOWN:True,pygame.K_RSHIFT:True}))
        self.assertFalse(car.boosting)
        self.assertEqual(car.boost,1)

    def test_recovery_safe_on_all_tracks_preserves_progress_and_boost(self):
        a=self.app
        for index in range(len(a.tracks)):
            a=self.race(index);car=a.cars[0]
            car.next_gate=4;car.point=1;car.boost=.2
            self.assertTrue(a.physics.recover(0),car.track.name)
            self.assertTrue(car.track.valid(car.sprite(),car.position))
            self.assertIsNone(contact(*a.cars))
            self.assertEqual(car.next_gate,4);self.assertEqual(car.point,1)
            self.assertEqual(car.boost,.2)
            self.assertEqual(car.recovery_time,2)
            self.assertFalse(a.physics.recover(0))

    def test_recovery_penalty_counts_time_and_blocks_input(self):
        a=self.race();self.assertTrue(a.physics.recover(0));car=a.cars[0]
        position=car.position.copy();keys=defaultdict(bool,{pygame.K_UP:True,pygame.K_RSHIFT:True})
        for _ in range(120):a.physics.advance(1/120,keys)
        self.assertAlmostEqual(a.physics.elapsed,1)
        self.assertAlmostEqual(car.recovery_time,1)
        self.assertEqual(car.position,position)
        self.assertEqual(car.speed,0)
        self.assertEqual(car.point,0)

    def test_pause_freezes_recovery_and_restart_resets(self):
        a=self.race();a.physics.recover(0);a.change('paused');a.update(.2)
        self.assertEqual(a.cars[0].recovery_time,2)
        a.race();self.assertEqual(a.cars[0].boost,1)
        self.assertEqual(a.cars[0].recovery_time,0)

    def test_recovery_rejects_blocked_candidates_without_penalty(self):
        from unittest.mock import patch
        a=self.race();car=a.cars[0];position=car.position.copy();heading=car.heading
        with patch.object(car.track,'valid',return_value=False):
            self.assertFalse(a.physics.recover(0))
        self.assertEqual(car.position,position);self.assertEqual(car.heading,heading)
        self.assertEqual(car.recovery_time,0)

    def test_bindings_and_render(self):
        a=self.race();self.assertEqual(a.cars[0].keys['boost'],pygame.K_RSHIFT)
        self.assertEqual(a.cars[1].keys['boost'],pygame.K_LSHIFT)
        a.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
        self.assertEqual(a.cars[0].recovery_time,2)
        a.handle(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_r))
        # The second car either finds a safe position or leaves the first undisturbed.
        self.assertTrue(a.cars[0].track.valid(a.cars[0].sprite(),a.cars[0].position))
        self.assertIsNone(contact(*a.cars));a.draw();a.present()


if __name__=='__main__':unittest.main()
