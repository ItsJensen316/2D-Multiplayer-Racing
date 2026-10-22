"""Hand-authored centerlines; deterministic vector scenery, no generated imagery."""
import json
import math
import random
from pathlib import Path
import pygame

V = pygame.Vector2
SIZE = (1500, 800)
DATA = Path(__file__).resolve().parent.parent / 'data'
PALETTES = {
    'park': ((67, 89, 68), (77, 101, 75), (203, 192, 156)),
    'club': ((71, 86, 73), (82, 96, 80), (195, 188, 165)),
    'quarry': ((130, 113, 88), (143, 125, 97), (191, 173, 139)),
    'dock': ((70, 85, 91), (78, 94, 99), (164, 174, 174)),
    'ridge': ((82, 91, 78), (94, 102, 87), (179, 178, 157)),
}


def centerline(points):
    """Closed Catmull-Rom curve, then resample by distance for even gates/kerbs."""
    points = [V(p) for p in points]
    raw = []
    for i, b in enumerate(points):
        a, c, d = points[i-1], points[(i+1) % len(points)], points[(i+2) % len(points)]
        for k in range(80):
            t = k / 80
            raw.append((2*b + (-a+c)*t + (2*a-5*b+4*c-d)*t*t + (-a+3*b-3*c+d)*t*t*t) * .5)
    raw.append(raw[0])
    result = [raw[0]]
    remaining = 4.0
    for a, b in zip(raw, raw[1:]):
        delta = b-a
        length = delta.length()
        if not length: continue
        direction = delta/length
        while length >= remaining:
            a = a + direction*remaining
            result.append(a)
            length -= remaining
            remaining = 4.0
        remaining -= length
    return result


def ribbon(surface, points, width, color, closed=True):
    pygame.draw.lines(surface, color, closed, points, width)
    for point in points:
        pygame.draw.circle(surface, color, (round(point.x), round(point.y)), width//2)


class Track:
    def __init__(self, config):
        self.config = config
        self.id = config['id']
        self.name = config['name']
        self.difficulty = config['difficulty']
        self.label = config['label']
        self.description = config['description']
        self.width = config['width']
        self.legacy = False
        self.path = centerline(config['points'])
        # Finish is on the initial straight, away from the first bend.
        self.path = self.path[25:] + self.path[:25]
        self.length = len(self.path)*4
        self.gates = []
        for i in range(0, len(self.path), max(1, len(self.path)//20)):
            tangent = (self.path[(i+2) % len(self.path)] - self.path[i-2]).normalize()
            self.gates.append((self.path[i], tangent))
        self.finish, self.tangent = self.gates[0]
        self.road = pygame.Surface(SIZE, pygame.SRCALPHA)
        ribbon(self.road, self.path, self.width, (255, 255, 255, 255))
        self.mask = pygame.mask.from_surface(self.road)
        self.blocked = self.mask.copy()
        self.blocked.invert()
        self.image = self.render()
        self.preview = pygame.transform.smoothscale(self.image, (620, 331))

    def spawn(self, player):
        normal = V(-self.tangent.y, self.tangent.x)
        position = self.finish - self.tangent*70 + normal*(-22 if player == 0 else 22)
        return position, math.degrees(math.atan2(self.tangent.y, self.tangent.x))

    def valid(self, image, position):
        rect = image.get_rect(center=(round(position.x), round(position.y)))
        if not pygame.Rect((0, 0), SIZE).contains(rect): return False
        return self.blocked.overlap(pygame.mask.from_surface(image), rect.topleft) is None

    def render(self):
        bg, patch, gravel = PALETTES[self.config['theme']]
        surface = pygame.Surface(SIZE)
        surface.fill(bg)
        rng = random.Random(self.id)
        for _ in range(100):
            pos = (rng.randrange(1500), rng.randrange(100, 800))
            pygame.draw.circle(surface, patch, pos, rng.randrange(8, 28))
        ribbon(surface, self.path, self.width+30, gravel)
        ribbon(surface, self.path, self.width+12, (207, 209, 197))
        ribbon(surface, self.path, self.width, (53, 57, 60))
        # Fine asphalt speckle is clipped to the physical road.
        grain = pygame.Surface(SIZE, pygame.SRCALPHA)
        for _ in range(19000):
            p = (rng.randrange(1500), rng.randrange(800))
            if self.mask.get_at(p):
                grain.set_at(p, (170, 173, 173, rng.randrange(5, 17)))
        surface.blit(grain, (0, 0))
        for i in range(len(self.path)):
            p, q = self.path[i], self.path[(i+1) % len(self.path)]
            direction = q-p
            if not direction.length_squared(): continue
            normal = V(-direction.y, direction.x).normalize()
            color = (183, 74, 65) if (i//5) % 2 else (224, 221, 205)
            for side in (-1, 1):
                a, b = p+normal*(self.width/2+2)*side, q+normal*(self.width/2+2)*side
                pygame.draw.line(surface, color, a, b, 6)
            if (i//8) % 3 == 0:
                pygame.draw.line(surface, (128, 130, 122), p, q, 2)
        # Trees, rocks or stacked containers, placed safely away from the road.
        clearance = self.road.copy()
        clearance.fill((0, 0, 0, 0))
        ribbon(clearance, self.path, self.width+95, (255, 255, 255))
        scenery_mask = pygame.mask.from_surface(clearance)
        for _ in range(160):
            x, y = rng.randrange(55, 1445), rng.randrange(130, 755)
            if scenery_mask.get_at((x, y)): continue
            if self.config['theme'] == 'dock':
                rect = pygame.Rect(x-25, y-10, 50, 20)
                pygame.draw.rect(surface, (43, 54, 59), rect.move(4, 5), border_radius=2)
                pygame.draw.rect(surface, rng.choice([(122, 104, 77), (89, 116, 116), (142, 91, 75)]), rect, border_radius=2)
                for off in range(5, 50, 7):
                    pygame.draw.line(surface, (60, 69, 69), (x-25+off,y-7), (x-25+off,y+7), 1)
            elif self.config['theme'] in ('quarry', 'ridge'):
                pygame.draw.ellipse(surface, (67, 69, 61), (x-13, y-4, 29, 18))
                pygame.draw.polygon(surface, (151, 148, 127), [(x-13,y),(x-5,y-12),(x+12,y-8),(x+15,y+4),(x,y+9)])
                pygame.draw.line(surface, (180, 174, 152), (x-5,y-10), (x+10,y-6), 2)
            else:
                pygame.draw.circle(surface, (44, 61, 47), (x+5,y+5), 18)
                pygame.draw.circle(surface, (43, 69, 47), (x,y), 17)
                pygame.draw.circle(surface, (62, 88, 57), (x-4,y-5), 11)
        self.draw_grid(surface)
        # Direction chevrons on the asphalt.
        for i in range(90, len(self.path), 125):
            p = self.path[i]
            direction = (self.path[(i+2)%len(self.path)]-self.path[i-2]).normalize()
            normal = V(-direction.y, direction.x)
            pygame.draw.lines(surface, (167, 165, 141), False, [p-direction*7+normal*7,p+direction*6,p-direction*7-normal*7], 3)
        return surface

    def draw_grid(self, surface):
        normal = V(-self.tangent.y, self.tangent.x)
        for across in range(-int(self.width/2)+4, int(self.width/2)-4, 10):
            for row in range(2):
                a = self.finish + normal*across + self.tangent*(row*10-10)
                b = a+normal*10
                color = (228, 227, 211) if (across//10+row)%2 else (33, 37, 40)
                pygame.draw.polygon(surface, color, [a,b,b+self.tangent*10,a+self.tangent*10])
        for player in range(2):
            position, _ = self.spawn(player)
            corners = [position + self.tangent*a + normal*b for a,b in [(-30,-17),(30,-17),(30,17),(-30,17)]]
            pygame.draw.lines(surface, (194, 191, 170), True, corners, 2)


class OriginalTrack(Track):
    """Classic artwork with a physical road mask and ordered route gates."""
    def __init__(self, image):
        self.id = 'original'
        self.name = 'Classic Circuit'
        self.difficulty = 3
        self.label = 'Intermediate'
        self.description = 'A winding circuit with a long straight and a tight infield bend.'
        self.legacy = True  # Artwork/HUD placement only, never a different engine.
        self.width = 76
        points = [[1100,735],[930,720],[810,680],[750,610],[730,530],
                  [745,440],[800,375],[900,350],[1050,330],[1120,290],
                  [1135,255],[1090,210],[990,185],[800,182],[670,190],
                  [600,230],[565,300],[550,410],[550,540],[520,620],
                  [460,680],[380,715],[275,715],[190,690],[130,630],
                  [100,550],[92,420],[92,280],[120,185],[180,125],
                  [270,82],[390,67],[700,67],[1050,67],[1300,67],
                  [1380,100],[1415,165],[1420,310],[1420,500],
                  [1400,620],[1350,690],[1250,725]]
        self.path = centerline(points)
        self.length = len(self.path)*4
        self.gates = []
        for i in range(0, len(self.path), max(1, len(self.path)//24)):
            tangent = (self.path[(i+2)%len(self.path)]-self.path[i-2]).normalize()
            self.gates.append((self.path[i], tangent))
        self.finish, self.tangent = self.gates[0]
        # Flood the enclosed asphalt once. No collision queries read the display.
        barriers = pygame.mask.from_threshold(image, (255,255,255,255), (45,45,45,255))
        barriers.invert()
        self.mask = barriers.connected_component((1132,720))
        if not 200000 < self.mask.count() < 500000:
            raise ValueError('Classic Circuit road boundary is not enclosed.')
        self.blocked = self.mask.copy()
        self.blocked.invert()
        self.road = self.mask.to_surface(setcolor=(255,255,255,255), unsetcolor=(0,0,0,0))
        self.image = image.copy()
        normal = V(-self.tangent.y, self.tangent.x)
        for across in range(-32,33,8):
            for row in range(2):
                a = self.finish+normal*across+self.tangent*(row*8-8)
                b = a+normal*8
                color = (228,227,211) if (across//8+row)%2 else (33,37,40)
                pygame.draw.polygon(self.image,color,[a,b,b+self.tangent*8,a+self.tangent*8])
        for i in range(100,len(self.path),130):
            point = self.path[i]
            direction = (self.path[(i+2)%len(self.path)]-self.path[i-2]).normalize()
            normal = V(-direction.y,direction.x)
            pygame.draw.lines(self.image,(178,177,152),False,
                              [point-direction*7+normal*6,point+direction*6,point-direction*7-normal*6],2)
        self.preview = pygame.transform.smoothscale(self.image,(620,331))

    def spawn(self, player):
        # The painted straight narrows here: use its measured asphalt center.
        return V(1170, 733 + (-13.5 if player == 0 else 13.5)), 180.0


def load_tracks(original):
    configs = json.loads((DATA / 'tracks' / 'circuits.json').read_text())
    tracks = [Track(config) for config in configs]
    tracks.append(OriginalTrack(original))
    return sorted(tracks, key=lambda track: (track.difficulty, track.legacy))
