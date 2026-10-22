import os
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
from collections import defaultdict
import pygame
from racing.audio import Audio

class EngineAudioTests(unittest.TestCase):
    def setUp(self):
        pygame.mixer.pre_init(22050,-16,2,512);pygame.init();self.audio=Audio()
    def tearDown(self):self.audio.close();pygame.quit()
    def test_precomputed_loops(self):
        self.assertEqual(len(self.audio.engines),32)
        for sound in self.audio.engines:self.assertAlmostEqual(sound.get_length(),.4,places=3)
    def test_pitch_changes_crossfade(self):
        class Car:
            speed=0
            keys={'down':pygame.K_DOWN}
        car=Car();keys=defaultdict(bool);a=self.audio
        a.update(.01,'race',[car],keys);car.speed=490;a.update(.01,'race',[car],keys)
        self.assertIsNotNone(a.fades[0])
        self.assertTrue(pygame.mixer.Channel(0).get_busy())
        self.assertTrue(pygame.mixer.Channel(1).get_busy())
        a.update(.1,'race',[car],keys)
        self.assertEqual(a.indices[0],31)
        self.assertIsNone(a.fades[0])
    def test_silence_stops_all_reserved_channels(self):
        self.audio.silence()
        for i in range(6):self.assertFalse(pygame.mixer.Channel(i).get_busy())
    def test_loops_start_at_zero(self):
        from array import array
        for sound in self.audio.engines:self.assertEqual(array('h',sound.get_raw())[0],0)
