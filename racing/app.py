"""Pygame menus and race lifecycle. All interface coordinates use a logical canvas."""
from pathlib import Path
from math import ceil
import pygame
from .tracks import load_tracks
from .driver import Driver, RacePhysics
from .records import Records, format_time
from .audio import Audio
from .effects import Effects

ASSETS = Path(__file__).resolve().parent.parent / 'data'
BG = (13, 18, 30)
PANEL = (24, 33, 49)
TEXT = (235, 241, 248)
MUTED = (148, 164, 184)
ACCENT = (82, 225, 190)


class App:
    def __init__(self, record_directory=None):
        pygame.mixer.pre_init(22050, -16, 2, 512)
        pygame.init()
        self.records = Records(record_directory)
        self.audio = Audio(**self.records.data['audio'])
        self.effects = Effects()
        self.go_time = 0.0
        self.new_records = set()
        info = pygame.display.Info()
        scale = min(1, max(640, info.current_w - 80) / 1500,
                    max(360, info.current_h - 100) / 800)
        self.window = pygame.display.set_mode((int(1500 * scale), int(800 * scale)), pygame.RESIZABLE)
        pygame.display.set_caption('APEX / Local Racing')
        self.canvas = pygame.Surface((1500, 800))
        self.clock = pygame.time.Clock()
        self.fonts = {n: pygame.font.SysFont('arial', n, bold=n >= 40) for n in (20, 24, 30, 40, 64, 96)}
        self.images = {n: pygame.image.load(str(ASSETS / n)).convert_alpha() for n in
                       ('track1.png', 'car1.png', 'car1.1.png', 'car1.2.png', 'car2.png', 'car2.2.png')}
        self.tracks = load_tracks(self.images['track1.png'])
        self.track_index = 0
        self.active_track = self.tracks[0]
        self.preview = self.tracks[0].preview
        self.state = 'menu'
        self.running = True
        self.laps = 3
        self.buttons = []
        self.focus = 0
        self.mouse = (-1, -1)
        self.viewport = pygame.Rect(0, 0, *self.window.get_size())
        self.cars = []
        self.elapsed = 0
        self.winner = ''
        self.notice = ''
        self.notice_time = 0.0

    def change(self, state):
        self.state = state
        self.focus = 0
        if state != 'race': self.audio.silence()

    def text(self, text, x, y, size=30, color=TEXT):
        self.canvas.blit(self.fonts[size].render(text, True, color), (x, y))

    def button(self, label, rect, action):
        rect = pygame.Rect(rect)
        i = len(self.buttons)
        self.buttons.append((rect, action))
        selected = rect.collidepoint(self.mouse) or self.focus == i
        pygame.draw.rect(self.canvas, ACCENT if selected else PANEL, rect, border_radius=12)
        surface = self.fonts[24].render(label, True, BG if selected else TEXT)
        self.canvas.blit(surface, surface.get_rect(center=rect.center))

    @property
    def selected_track(self):
        return self.tracks[self.track_index]

    def select_track(self, amount):
        self.track_index = (self.track_index + amount) % len(self.tracks)
        self.preview = self.selected_track.preview

    def race(self):
        keys = [dict(up=pygame.K_UP, down=pygame.K_DOWN, left=pygame.K_LEFT, right=pygame.K_RIGHT, boost=pygame.K_RSHIFT),
                dict(up=pygame.K_w, down=pygame.K_s, left=pygame.K_a, right=pygame.K_d, boost=pygame.K_LSHIFT)]
        self.active_track = self.selected_track
        self.cars = [Driver(self.active_track, i, self.images[f'car{i+1}.png'], keys[i]) for i in range(2)]
        self.physics = RacePhysics(self.cars)
        self.effects = Effects()
        self.new_records = set()
        self.go_time = 0.0
        self.elapsed = 0
        self.winner = ''
        self.notice = ''
        self.notice_time = 0.0
        self.countdown = 3.0
        self.change('countdown')
        self.audio.play('tick')

    def adjust(self, amount):
        self.laps = max(1, min(99, self.laps + amount))

    def stop(self):
        self.running = False
        self.audio.close()

    def set_volume(self, amount):
        self.audio.volume = round(max(0,min(1,self.audio.volume+amount)),2)
        if self.audio.volume == 0 and self.audio.available: pygame.mixer.stop()
        self.records.audio(self.audio.volume,self.audio.muted)

    def toggle_mute(self):
        self.audio.muted = not self.audio.muted
        if self.audio.muted and self.audio.available: pygame.mixer.stop()
        self.records.audio(self.audio.volume,self.audio.muted)

    def lap_text(self, car):
        now = car.finish_time if car.finish_time is not None else self.elapsed
        return format_time(max(0,now-car.lap_start_time))

    def draw_timing(self):
        classic = self.active_track.legacy
        if classic:
            pygame.draw.rect(self.canvas,BG,(175,175,310,300),border_radius=12)
        else:
            pygame.draw.rect(self.canvas,BG,(15,10,1470,87),border_radius=12)
            self.text(self.active_track.name.upper(),35,22,20,ACCENT)
        for i,car in enumerate(self.cars):
            last = car.lap_times[-1] if car.lap_times else None
            best = min(car.lap_times) if car.lap_times else None
            x,y = (190,190+i*110) if classic else (460+i*350,17)
            self.text(f'P{i+1}  {car.point}/{self.laps}   {self.lap_text(car)}',x,y,20,ACCENT)
            self.text('LAST '+format_time(last),x,y+27,20)
            self.text('BEST '+format_time(best),x,y+50,20,MUTED)
            bar_y=y+76
            width=260 if classic else 270
            pygame.draw.rect(self.canvas,PANEL,(x,bar_y,width,5),border_radius=2)
            if car.boost>0:pygame.draw.rect(self.canvas,(246,190,91) if car.boosting else ACCENT,(x,bar_y,int(width*car.boost),5),border_radius=2)
        if classic:
            self.text('RACE  '+format_time(self.elapsed),190,415,20)
            self.text('Esc pause / M mute',190,445,20,MUTED)
        else:
            self.text(format_time(self.elapsed),1180,20,24)
            self.text('Esc: pause',1180,55,20,MUTED)
            self.text('M mute | [ quieter | ] louder',35,59,20,MUTED)

    def overlay(self, title, subtitle):
        shade = pygame.Surface((1500, 800), pygame.SRCALPHA)
        shade.fill((5, 10, 20, 210))
        self.canvas.blit(shade, (0, 0))
        self.text(title, 450, 180, 64)
        self.text(subtitle, 450, 270, 24, MUTED)

    def draw(self):
        self.buttons = []
        self.canvas.fill(BG)
        if self.state in ('menu', 'setup', 'controls', 'settings', 'records'):
            self.text('APEX / LOCAL RACING', 80, 45, 24, ACCENT)
            self.text('02 PLAYERS  /  ONE KEYBOARD', 1030, 48, 20, MUTED)
            pygame.draw.line(self.canvas, PANEL, (80, 100), (1420, 100), 2)
        if self.state == 'menu':
            self.text('Race together.', 80, 190, 64)
            self.text('Win the next corner.', 85, 305, 40, MUTED)
            self.text('Six circuits. Two drivers. One chequered flag.', 85, 380, 24, MUTED)
            self.button('PLAY', (85, 455, 390, 60), lambda: self.change('setup'))
            self.button('HOW TO PLAY', (85, 530, 390, 60), lambda: self.change('controls'))
            self.button('SETTINGS', (85, 605, 390, 60), lambda: self.change('settings'))
            self.button('EXIT', (85, 680, 390, 60), self.stop)
            self.canvas.blit(self.preview, (790, 260))
            self.text(self.selected_track.name.upper(), 790, 615, 24, ACCENT)
            self.text('6 circuits / Beginner to Expert', 790, 655, 24, MUTED)
        elif self.state == 'setup':
            self.text('Set your race.', 80, 145, 64)
            self.button('<', (80, 230, 65, 45), lambda: self.select_track(-1))
            self.text(f'TRACK {self.track_index+1:02} / {len(self.tracks):02}    Q / E TO SWITCH', 170, 240, 20, MUTED)
            self.button('>', (635, 230, 65, 45), lambda: self.select_track(1))
            self.canvas.blit(self.preview, (80, 290))
            track = self.selected_track
            self.text(track.name.upper(), 80, 640, 30, ACCENT)
            self.text(track.description, 80, 690, 20, MUTED)
            self.text(f'{track.label.upper()}   {track.difficulty}/5', 850, 180, 24, ACCENT)
            for i in range(5):
                pygame.draw.rect(self.canvas, ACCENT if i < track.difficulty else PANEL, (850+i*75, 225, 60, 8), border_radius=3)
            self.text('LAPS', 850, 260, 24, MUTED)
            self.button('-', (850, 310, 80, 70), lambda: self.adjust(-1))
            self.text(f'{self.laps:02}', 975, 300, 64)
            self.button('+', (1135, 310, 80, 70), lambda: self.adjust(1))
            self.text('Choose 1–99 laps. Left / Right also adjusts.', 850, 410, 20, MUTED)
            self.text('P1: Arrows / RShift / Enter',850,455,24)
            self.text('P2: WASD / LShift / R',850,492,24)
            self.button('START RACE', (850, 545, 430, 75), self.race)
            self.button('BACK', (850, 645, 430, 60), lambda: self.change('menu'))
            self.button('TRACK RECORDS', (850, 720, 430, 50), lambda: self.change('records'))
            best=self.records.best(track.id+'-boost-v1')
            self.text('TRACK BEST  '+format_time(best),80,738,20,ACCENT)
        elif self.state == 'settings':
            self.text('Sound & settings.',80,155,64)
            self.text('MASTER VOLUME',450,275,24,MUTED)
            self.text(f'{round(self.audio.volume*100)}%',1030,270,30,ACCENT)
            pygame.draw.rect(self.canvas,PANEL,(450,350,600,20),border_radius=8)
            if self.audio.volume>0:
                pygame.draw.rect(self.canvas,ACCENT,(450,350,int(600*self.audio.volume),20),border_radius=8)
            self.button('- 10%',(450,420,180,65),lambda:self.set_volume(-.1))
            self.button('UNMUTE' if self.audio.muted else 'MUTE',(660,420,180,65),self.toggle_mute)
            self.button('+ 10%',(870,420,180,65),lambda:self.set_volume(.1))
            self.text('M: mute    [: quieter    ]: louder',450,535,24,MUTED)
            status='Audio ready' if self.audio.available else 'Audio device unavailable / silent mode'
            self.text(status,450,585,24,ACCENT)
            if self.records.error:self.text(self.records.error,450,630,20,MUTED)
            self.button('BACK',(450,690,600,60),lambda:self.change('menu'))
        elif self.state == 'records':
            self.text('Track records.',80,150,64)
            self.text('BOOST CLASS',80,225,20,ACCENT)
            self.text('TRACK',80,265,20,MUTED)
            self.text('BEST LAP',500,265,20,MUTED)
            self.text('P1 BEST',760,265,20,MUTED)
            self.text('P2 BEST',1000,265,20,MUTED)
            self.text(f'{self.laps}-LAP RACE',1240,265,20,MUTED)
            for i,track in enumerate(self.tracks):
                y=320+i*57
                self.text(track.name,80,y,24)
                for x,key in [(500,'lap'),(760,'p1_lap'),(1000,'p2_lap'),(1240,f'race_{self.laps}')]:
                    self.text(format_time(self.records.best(track.id+'-boost-v1',key)),x,y,24,ACCENT)
            if self.records.error:self.text(self.records.error,80,680,20,MUTED)
            self.button('BACK TO SETUP',(80,720,400,55),lambda:self.change('setup'))
        elif self.state == 'controls':
            self.text('Own the racing line.', 80, 160, 64)
            self.text('PLAYER 1', 85, 300, 30, ACCENT)
            self.text('Arrows: drive    Right Shift: boost    Enter: recover', 85, 355)
            self.text('PLAYER 2', 85, 430, 30, ACCENT)
            self.text('WASD: drive    Left Shift: boost    R: recover', 85, 485)
            self.text('Recovery: 2-second stop. Boost recharges when released.', 85, 565, 24, MUTED)
            self.text('Esc: pause    M: mute    [: quieter    ]: louder', 85, 615, 24, MUTED)
            self.button('BACK', (85, 690, 320, 60), lambda: self.change('menu'))
        else:
            self.canvas.blit(self.active_track.image, (0, 0))
            self.effects.draw_marks(self.canvas)
            for car in self.cars:
                image = car.car_img1
                if car.n > 0:
                    image = car.car_img3 if car.n > 75 or 50 > car.n > 25 else car.car_img2
                sprite = pygame.transform.rotate(image, car.ang1)
                shadow = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
                shadow.blit(sprite, (0, 0))
                shadow.fill((0, 0, 0, 85), special_flags=pygame.BLEND_RGBA_MULT)
                self.canvas.blit(shadow, shadow.get_rect(center=(car.x+3, car.y+4)))
                self.canvas.blit(sprite, sprite.get_rect(center=(car.x, car.y)))
            self.effects.draw_sparks(self.canvas)
            self.draw_timing()
            for i,car in enumerate(self.cars):
                if car.recovery_time>0:
                    label=self.fonts[20].render(f'P{i+1} RECOVER {car.recovery_time:.1f}s',True,(255,208,130))
                    self.canvas.blit(label,label.get_rect(center=(car.x,car.y-40)))
                elif car.boosting:
                    tail=car.position-car.forward*29
                    pygame.draw.line(self.canvas,(255,183,78),tail,tail-car.forward*15,5)
            if self.notice_time>0:
                self.text(self.notice,500,740,24,(255,208,130))
            if self.state=='race' and self.go_time>0:
                text=self.fonts[96].render('GO!',True,ACCENT)
                self.canvas.blit(text,text.get_rect(center=(750,180)))
            if self.state == 'countdown':
                self.overlay(str(max(1, ceil(self.countdown))), 'Get ready. Arrow keys / WASD')
            elif self.state == 'paused':
                self.overlay('Race paused', 'Take a breath. The clock is stopped.')
                self.button('RESUME', (450, 350, 600, 65), lambda: self.change('race'))
                self.button('RESTART RACE', (450, 435, 600, 65), self.race)
                self.button('MAIN MENU', (450, 520, 600, 65), lambda: self.change('menu'))
                self.button('MUTE / UNMUTE', (450, 605, 600, 60), self.toggle_mute)
                self.text('[: quieter    ]: louder',450,690,20,MUTED)
            elif self.state == 'results':
                self.overlay(self.winner,f'{self.laps}-lap race / '+format_time(self.elapsed))
                for i,car in enumerate(self.cars):
                    x=260+i*510
                    pygame.draw.rect(self.canvas,PANEL,(x,330,470,235),border_radius=12)
                    status='FINISHED' if car.finish_time is not None else 'DNF'
                    self.text(f'PLAYER {i+1} / {status}',x+25,350,30,ACCENT)
                    total=format_time(car.finish_time) if car.finish_time is not None else 'DNF at '+format_time(self.elapsed)
                    self.text('Race: '+total,x+25,405,24)
                    self.text('Last: '+format_time(car.lap_times[-1] if car.lap_times else None),x+25,445,24)
                    self.text('Best: '+format_time(min(car.lap_times) if car.lap_times else None),x+25,485,24)
                    if i+1 in self.new_records:self.text('NEW TRACK LAP RECORD',x+25,530,20,ACCENT)
                self.button('RACE AGAIN',(260,625,300,65),self.race)
                self.button('RACE SETUP',(600,625,300,65),lambda:self.change('setup'))
                self.button('MAIN MENU',(940,625,300,65),lambda:self.change('menu'))
                if self.records.error:self.text(self.records.error,450,725,20,MUTED)

    def handle(self, event):
        if event.type == pygame.QUIT:
            self.stop()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                self.toggle_mute()
            elif event.key in (pygame.K_LEFTBRACKET,pygame.K_RIGHTBRACKET):
                self.set_volume(.1 if event.key==pygame.K_RIGHTBRACKET else -.1)
            elif self.state=='race' and event.key in (pygame.K_RETURN,pygame.K_r):
                player=0 if event.key==pygame.K_RETURN else 1
                if self.physics.recover(player):
                    self.effects.previous.pop(player,None)
                    self.notice=f'P{player+1}: recovered / 2-second stop'
                else:self.notice=f'P{player+1}: recovery unavailable; clear the area or wait'
                self.notice_time=2.0
            elif event.key == pygame.K_ESCAPE:
                if self.state == 'race': self.change('paused')
                elif self.state == 'paused': self.change('race')
                elif self.state == 'countdown': self.change('setup')
                elif self.state != 'menu': self.change('menu')
            elif self.state == 'setup' and event.key in (pygame.K_q, pygame.K_e):
                self.select_track(1 if event.key == pygame.K_e else -1)
            elif self.state == 'setup' and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.adjust(1 if event.key == pygame.K_RIGHT else -1)
            elif self.buttons:
                if event.key in (pygame.K_TAB, pygame.K_DOWN, pygame.K_UP):
                    self.focus = (self.focus + (-1 if event.key == pygame.K_UP or (event.key == pygame.K_TAB and event.mod & pygame.KMOD_SHIFT) else 1)) % len(self.buttons)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.buttons[self.focus][1]()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            x = (event.pos[0] - self.viewport.x) * 1500 / self.viewport.w
            y = (event.pos[1] - self.viewport.y) * 800 / self.viewport.h
            for rect, action in self.buttons:
                if rect.collidepoint(x, y):
                    action()
                    break

    def update(self, dt):
        pressed=pygame.key.get_pressed()
        if self.state == 'countdown':
            before=ceil(self.countdown)
            self.countdown -= dt
            if self.countdown <= 0:
                self.change('race')
                self.go_time=1.0
                self.audio.play('go')
            elif ceil(self.countdown)!=before:self.audio.play('tick')
        elif self.state == 'race':
            self.go_time=max(0,self.go_time-dt)
            self.notice_time=max(0,self.notice_time-dt)
            finished = self.physics.advance(dt, target_laps=self.laps)
            self.elapsed = self.physics.elapsed
            self.effects.update(dt,self.cars,pressed)
            for event in self.physics.events:
                if event['kind']=='hit':
                    self.effects.impact(event['position'],event['strength'])
                    self.audio.play('hit')
                elif event['kind']=='lap':
                    player=event['player']
                    if self.records.lap(self.active_track.id+'-boost-v1',player,event['duration']):self.new_records.add(player)
                    self.audio.play('lap')
            if finished:
                for player in finished:
                    car=self.cars[player-1]
                    self.records.race(self.active_track.id+'-boost-v1',player,self.laps,car.finish_time)
                self.winner = 'Dead heat!' if len(finished) > 1 else f'Player {finished[0]} wins!'
                self.change('results')
                self.audio.play('finish')
        self.audio.update(dt,self.state,self.cars,pressed)

    def present(self):
        w, h = self.window.get_size()
        ratio = min(w / 1500, h / 800)
        size = (max(1, int(1500 * ratio)), max(1, int(800 * ratio)))
        self.viewport = pygame.Rect((w-size[0])//2, (h-size[1])//2, *size)
        self.window.fill(BG)
        self.window.blit(pygame.transform.smoothscale(self.canvas, size), self.viewport)
        pygame.display.flip()
        mx, my = pygame.mouse.get_pos()
        self.mouse = ((mx-self.viewport.x)*1500/size[0], (my-self.viewport.y)*800/size[1])

    def run(self):
        while self.running:
            dt = min(self.clock.tick(100) / 1000, 0.1)
            self.draw()
            for event in pygame.event.get():
                before = self.state
                self.handle(event)
                if self.state != before:
                    self.draw()
            if not self.running: break
            self.update(dt)
            self.draw()
            self.present()


def main():
    try:
        App().run()
    finally:
        pygame.quit()
