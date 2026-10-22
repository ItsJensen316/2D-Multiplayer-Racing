"""Lightweight tyre marks and short-lived impact sparks."""
from collections import deque
import random
import pygame

V=pygame.Vector2


class Effects:
    def __init__(self):
        self.marks=deque(maxlen=1400)
        self.sparks=[]
        self.previous={}
        self.rng=random.Random(21)

    def impact(self,position,strength):
        for _ in range(min(16,max(5,int(strength/20)))):
            velocity=V(self.rng.uniform(-130,130),self.rng.uniform(-130,130))
            self.sparks.append([V(position),velocity,self.rng.uniform(.15,.35)])
        self.sparks=self.sparks[-160:]

    def update(self,dt,cars,pressed):
        for i,car in enumerate(cars):
            old=self.previous.get(i,car.position.copy())
            turning=pressed[car.keys['left']] or pressed[car.keys['right']]
            braking=pressed[car.keys['down']] and car.speed>70
            if (braking or (turning and abs(car.speed)>190)) and old.distance_to(car.position)>1:
                normal=V(-car.forward.y,car.forward.x)
                for side in (-1,1):
                    offset=normal*side*9-car.forward*17
                    self.marks.append((old+offset,car.position+offset,7.0))
            self.previous[i]=car.position.copy()
        self.marks=deque(((a,b,life-dt) for a,b,life in self.marks if life>dt),maxlen=1400)
        for spark in self.sparks:
            spark[0]+=spark[1]*dt
            spark[1]*=max(0,1-4*dt)
            spark[2]-=dt
        self.sparks=[s for s in self.sparks if s[2]>0]

    def draw_marks(self,surface):
        for a,b,life in self.marks:
            shade=round(53-22*min(1,life/2))
            pygame.draw.line(surface,(shade,shade+3,shade+5),a,b,3)

    def draw_sparks(self,surface):
        for position,velocity,life in self.sparks:
            pygame.draw.line(surface,(255,202,104),position,position-velocity*.025,2)
