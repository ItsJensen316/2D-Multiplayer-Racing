"""Small synthesized arcade sound bank. No external files or extra dependencies."""
from array import array
import math
import random
import pygame


class Audio:
    def __init__(self,volume=.5,muted=False):
        self.volume=volume
        self.muted=muted
        self.available=False
        self.indices=[-1,-1]
        self.active=[0,0]
        self.fades=[None,None]
        self.cooldowns={}
        self.clock=0
        try:
            if not pygame.mixer.get_init():pygame.mixer.init(22050,-16,2,512)
            self.rate,self.bits,self.channels=pygame.mixer.get_init()
            if self.bits != -16: return
            pygame.mixer.set_num_channels(12)
            pygame.mixer.set_reserved(6)
            self.engines=[self.engine(65+i*7.5) for i in range(32)]
            self.sounds={'tick':self.tone([(510,.09)]),
                         'go':self.tone([(880,.22)]),
                         'lap':self.tone([(660,.08),(880,.12)]),
                         'finish':self.tone([(523,.13),(659,.13),(784,.13),(1047,.32)]),
                         'hit':self.noise(.13,44), 'brake':self.noise(.28,19,True)}
            self.available=True
        except (pygame.error,ValueError):self.available=False

    def sound(self,values):
        data=array('h')
        for sample in values:
            value=round(max(-1,min(1,sample))*26000)
            data.extend([value]*self.channels)
        return pygame.mixer.Sound(buffer=data.tobytes())

    def tone(self,notes):
        samples=[]
        for hz,duration in notes:
            count=int(self.rate*duration)
            for i in range(count):
                envelope=min(1,i/(self.rate*.008),(count-i)/(self.rate*.02))
                samples.append(.34*envelope*math.sin(2*math.pi*hz*i/self.rate))
        return self.sound(samples)

    def engine(self,hz):
        # Whole cycles keep each precomputed loop seamless; no runtime PCM streaming.
        count=round(self.rate*.4)
        cycles=round(hz*count/self.rate)
        return self.sound(.25*math.sin(p)+.13*math.sin(2*p)+.06*math.sin(4*p)
                          for p in (2*math.pi*cycles*i/count for i in range(count)))

    def noise(self,duration,seed,tyre=False):
        rng=random.Random(seed)
        count=int(duration*self.rate)
        samples=[]
        low=0
        for i in range(count):
            white=rng.uniform(-1,1)
            low=.8*low+.2*white
            sound=(white-low)*.16+math.sin(i*2*math.pi*1800/self.rate)*.08 if tyre else low*.85
            samples.append(sound*(1-i/count))
        return self.sound(samples)

    @property
    def gain(self):return 0 if self.muted else self.volume

    def play(self,name):
        if not self.available or not self.gain:return
        delay=.18 if name=='hit' else .1
        if self.clock < self.cooldowns.get(name,0):return
        self.cooldowns[name]=self.clock+delay
        sound=self.sounds[name]
        sound.set_volume(self.gain*.7)
        sound.play()

    def silence(self):
        if self.available:
            for i in range(6):pygame.mixer.Channel(i).stop()
        self.indices=[-1,-1]
        self.active=[0,0]
        self.fades=[None,None]

    def update(self,dt,state,cars,pressed):
        self.clock+=dt
        if not self.available:return
        if state!='race' or not self.gain:
            self.silence()
            return
        for i,car in enumerate(cars):
            index=min(31,round(abs(car.speed)/490*31))
            base=2*i
            current=pygame.mixer.Channel(base+self.active[i])
            if not current.get_busy():
                current.set_volume(0)
                current.play(self.engines[index],loops=-1,fade_ms=20)
                self.indices[i]=index
            if self.fades[i] is None and index!=self.indices[i]:
                incoming=pygame.mixer.Channel(base+1-self.active[i])
                incoming.set_volume(0)
                incoming.play(self.engines[index],loops=-1)
                self.fades[i]=[0.0,index]
            volumes=[0.0,0.0]
            volumes[self.active[i]]=1.0
            fade=self.fades[i]
            if fade is not None:
                fade[0]=min(1,fade[0]+max(0,dt)/.09)
                volumes[self.active[i]]=1-fade[0]
                volumes[1-self.active[i]]=fade[0]
                if fade[0]>=1:
                    current.stop()
                    self.active[i]=1-self.active[i]
                    self.indices[i]=fade[1]
                    self.fades[i]=None
            for slot,weight in enumerate(volumes):
                left,right=(.24,.10) if i==0 else (.10,.24)
                pygame.mixer.Channel(base+slot).set_volume(self.gain*left*weight,self.gain*right*weight)
            brake=pygame.mixer.Channel(i+4)
            braking=car.speed>90 and pressed[car.keys['down']]
            if braking:
                if not brake.get_busy():brake.play(self.sounds['brake'],loops=-1)
                brake.set_volume(self.gain*.3)
            else:brake.stop()

    def close(self):
        if self.available:pygame.mixer.stop()
