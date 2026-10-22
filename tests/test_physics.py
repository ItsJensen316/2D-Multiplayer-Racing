"""Regression tests for shared physics and two-player contacts."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
from collections import defaultdict
import unittest
import tempfile
import pygame
from racing.app import App
from racing.driver import Driver, RacePhysics, contact, resolve_contact

V=pygame.Vector2


class PhysicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.app=App(cls.temp.name)
        cls.track=cls.app.tracks[0]
        cls.keys=[dict(up=pygame.K_UP,down=pygame.K_DOWN,left=pygame.K_LEFT,right=pygame.K_RIGHT),
                  dict(up=pygame.K_w,down=pygame.K_s,left=pygame.K_a,right=pygame.K_d)]

    @classmethod
    def tearDownClass(cls):
        cls.app.audio.close()
        pygame.quit()
        cls.temp.cleanup()

    def pair(self, track=None):
        track=track or self.track
        return [Driver(track,i,self.app.images[f'car{i+1}.png'],self.keys[i]) for i in range(2)]

    def assert_safe(self,cars):
        for car in cars:self.assertTrue(car.track.valid(car.sprite(),car.position))
        self.assertIsNone(contact(*cars))

    def test_classic_uses_same_driver_and_safe_grid(self):
        app=self.app
        app.track_index=next(i for i,t in enumerate(app.tracks) if t.id=='original')
        app.race()
        self.assertTrue(all(type(c) is Driver for c in app.cars))
        self.assert_safe(app.cars)

    def test_fixed_steps_match_at_30_60_144_fps(self):
        states=[]
        keys=defaultdict(bool,{pygame.K_UP:True,pygame.K_w:True})
        for fps in (30,60,144):
            cars=self.pair();world=RacePhysics(cars)
            for _ in range(fps):world.advance(1/fps,keys)
            states.append([(c.position,c.speed) for c in cars])
        for state in states[1:]:
            for (p,s),(q,t) in zip(states[0],state):
                self.assertLess(p.distance_to(q),1e-6)
                self.assertAlmostEqual(s,t)

    def test_rear_end_transfers_momentum(self):
        a,b=self.pair()
        a.position=V(750,180);b.position=V(800,180)
        a.heading=b.heading=0;a.speed=300;b.speed=80
        before=[(c.position.copy(),c.heading) for c in (a,b)]
        self.assertTrue(resolve_contact(a,b,before))
        self.assertLess(a.speed,300);self.assertGreater(b.speed,80)
        self.assert_safe([a,b])

    def test_head_on_rebounds_without_overlap(self):
        a,b=self.pair();a.position=V(750,180);b.position=V(800,180)
        a.heading=0;b.heading=180;a.speed=b.speed=300
        before=[(c.position.copy(),c.heading) for c in (a,b)]
        resolve_contact(a,b,before)
        self.assertLess(a.velocity.x,0);self.assertGreater(b.velocity.x,0)
        self.assert_safe([a,b])

    def test_side_contact_does_not_cross_wall(self):
        a,b=self.pair();a.heading=b.heading=0
        # Top kerb at y~108: first car is safely beside it.
        a.position=V(750,125);b.position=V(750,149)
        a.bump=V(0,-50);b.bump=V(0,-140)
        for _ in range(100):
            world=RacePhysics([a,b]);world.advance(1/120,defaultdict(bool))
            self.assert_safe([a,b])

    def test_high_speed_head_on_does_not_tunnel(self):
        a,b=self.pair();a.position=V(700,180);b.position=V(850,180)
        a.heading=0;b.heading=180;a.speed=b.speed=360
        world=RacePhysics([a,b])
        for _ in range(50):
            world.advance(1/120,defaultdict(bool));self.assert_safe([a,b])
        self.assertGreater(world.contacts,0)
        self.assertLess(a.position.x,b.position.x)

    def test_reverse_can_leave_a_wall(self):
        a=self.pair()[0];a.position=V(750,145);a.heading=270;a.speed=250
        forward=defaultdict(bool,{pygame.K_UP:True})
        for _ in range(50):a.update(1/120,forward)
        self.assertTrue(a.track.valid(a.sprite(),a.position))
        stopped=a.position.copy()
        reverse=defaultdict(bool,{pygame.K_DOWN:True})
        for _ in range(120):a.update(1/120,reverse)
        self.assertGreater(a.position.y,stopped.y+10)
        self.assertTrue(a.track.valid(a.sprite(),a.position))

    def test_finish_stops_at_first_physics_step(self):
        cars=self.pair();world=RacePhysics(cars)
        cars[0].point=1
        self.assertEqual(world.advance(.1,defaultdict(bool),target_laps=1),[1])
        self.assertAlmostEqual(world.elapsed,1/120)
        world.advance(.1,defaultdict(bool),target_laps=1)
        self.assertAlmostEqual(world.elapsed,1/120)


if __name__=='__main__':unittest.main()
