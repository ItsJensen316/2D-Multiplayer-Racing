"""Run: python -m unittest discover -s tests -v (headless, no extra packages)."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import unittest
import tempfile
import math
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile
import pygame
from racing.app import App
from racing.driver import Driver


class TrackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.app = App(cls.temp.name)
        cls.tracks = cls.app.tracks
        cls.keys = dict(up=pygame.K_UP, down=pygame.K_DOWN, left=pygame.K_LEFT, right=pygame.K_RIGHT)

    @classmethod
    def tearDownClass(cls):
        cls.app.audio.close()
        pygame.quit()
        cls.temp.cleanup()

    def driver(self, track, player=0):
        return Driver(track, player, self.app.images[f'car{player+1}.png'], self.keys)

    def test_difficulty_order_and_selection(self):
        self.assertEqual([t.difficulty for t in self.app.tracks], [1,2,3,3,4,5])
        self.app.track_index = 0
        self.app.select_track(-1)
        self.assertEqual(self.app.selected_track.difficulty, 5)
        self.app.select_track(1)
        self.assertEqual(self.app.selected_track.difficulty, 1)

    def test_both_grids_and_entire_centerline_fit_car(self):
        for track in self.tracks:
            for player in range(2):
                car = self.driver(track, player)
                self.assertTrue(track.valid(car.sprite(),car.position), track.name)
            for i in range(0,len(track.path),4):
                tangent = track.path[(i+2)%len(track.path)]-track.path[i-2]
                heading = math.degrees(math.atan2(tangent.y,tangent.x))
                sprite = pygame.transform.rotate(car.car_img1, 180-heading)
                self.assertTrue(track.valid(sprite,track.path[i]), f'{track.name}: {i}')

    def test_one_complete_lap_and_partial_lap(self):
        for track in self.tracks:
            car = self.driver(track)
            # Cross start without visiting sectors: no free lap.
            p,t = track.gates[0]
            car.progress(p-t*8,p+t*8)
            self.assertEqual(car.point,0)
            # Walk full centerline twice, crossing gate 0 only after all others.
            for lap in range(2):
                for a,b in zip(track.path,track.path[1:]+track.path[:1]):
                    car.progress(a,b)
                # Last sample to path[0] lands exactly on finish.
                self.assertEqual(car.point,lap+1,track.name)

    def test_reverse_and_skipped_sectors_do_not_count(self):
        for track in self.tracks:
            car = self.driver(track)
            p,t = track.gates[car.next_gate]
            car.progress(p+t*8,p-t*8)
            self.assertEqual(car.next_gate,1)
            p,t = track.gates[0]
            for _ in range(4):car.progress(p-t*8,p+t*8)
            self.assertEqual(car.point,0)

    def test_collision_is_independent_of_artwork(self):
        for track in self.tracks:
            car = self.driver(track)
            valid = track.valid(car.sprite(),car.position)
            saved = track.image.copy()
            track.image.fill('white')
            self.assertEqual(track.valid(car.sprite(),car.position),valid)
            self.assertFalse(track.valid(car.sprite(),pygame.Vector2(3,3)))
            track.image.blit(saved,(0,0))

    def test_straight_movement_similar_at_60_and_120_hz(self):
        track=self.tracks[0]
        a,b=self.driver(track),self.driver(track)
        pressed=defaultdict(bool,{pygame.K_UP:True})
        for _ in range(60):a.update(1/60,pressed)
        for _ in range(120):b.update(1/120,pressed)
        self.assertLess(a.position.distance_to(b.position),.01)
        self.assertAlmostEqual(a.speed,b.speed)

    def test_all_tracks_lifecycle(self):
        app=self.app
        for i,track in enumerate(app.tracks):
            app.track_index=i
            app.preview=track.preview
            app.change('setup');app.draw()
            app.race();app.draw()
            self.assertIs(app.active_track,track)
            app.update(3.1);self.assertEqual(app.state,'race')
            app.update(.01);app.draw()
            app.change('paused');elapsed=app.elapsed;app.update(.3)
            self.assertEqual(app.elapsed,elapsed)
            app.change('race');app.cars[0].point=app.laps
            app.update(.01);self.assertEqual(app.state,'results');app.draw()
            app.race();self.assertTrue(all(c.point==0 for c in app.cars))
            app.change('menu');app.draw()


if __name__=='__main__':unittest.main()
