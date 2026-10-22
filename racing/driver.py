"""Shared arcade handling and fixed-step two-car contact physics."""
import math
import pygame

V = pygame.Vector2
FIXED_DT = 1 / 120
MAX_SPEED = 360.0
REVERSE_SPEED = 130.0
ACCELERATION = 180.0
BRAKING = 300.0
COAST_DRAG = 85.0
STEER_RATE = 120.0
BOOST_SPEED = 490.0
BOOST_ACCELERATION = 380.0
BOOST_DURATION = 2.0
BOOST_RECHARGE = .16
RECOVERY_PENALTY = 2.0


def approach(value, target, amount):
    return max(target, value-amount) if value > target else min(target, value+amount)


class Driver:
    def __init__(self, track, player, image, keys):
        self.track = track
        self.position, self.heading = track.spawn(player)
        self.car_img1 = self.car_img2 = self.car_img3 = image
        self.keys = keys
        self.speed = 0.0
        self.bump = V()
        self.point = 0
        self.cooldown = 0.0  # Brief visual feedback; controls always remain active.
        self.next_gate = 1
        self.n = 0
        self.gates_crossed = 0
        self.lap_times = []
        self.lap_start_time = 0.0
        self.finish_time = None
        self.impact = 0.0
        self.boost = 1.0
        self.boosting = False
        self.boost_locked = False
        self.recovery_time = 0.0
        self.recovery_cooldown = 0.0
        self.recoveries = 0

    @property
    def x(self): return self.position.x

    @property
    def y(self): return self.position.y

    @property
    def ang1(self): return 180 - self.heading

    @property
    def forward(self):
        angle = math.radians(self.heading)
        return V(math.cos(angle), math.sin(angle))

    @property
    def velocity(self):
        return self.forward*self.speed + self.bump

    def set_velocity(self, value):
        self.speed = max(-REVERSE_SPEED, min(BOOST_SPEED, value.dot(self.forward)))
        self.bump = value - self.forward*self.speed
        if self.bump.length() > 180: self.bump.scale_to_length(180)

    def sprite(self):
        return pygame.transform.rotate(self.car_img1, self.ang1)

    def progress(self, previous, current):
        center, tangent = self.track.gates[self.next_gate]
        a = (previous-center).dot(tangent)
        b = (current-center).dot(tangent)
        if a < 0 <= b:
            crossing = previous.lerp(current, -a/(b-a))
            normal = V(-tangent.y, tangent.x)
            if abs((crossing-center).dot(normal)) <= self.track.width/2 + 2:
                self.gates_crossed += 1
                completed = self.next_gate == 0
                if completed: self.point += 1
                self.next_gate = (self.next_gate + 1) % len(self.track.gates)
                if completed: return -a/(b-a)
        return None

    def integrate(self, dt, keys):
        self.impact = 0.0
        self.recovery_cooldown = max(0,self.recovery_cooldown-dt)
        if self.recovery_time > 0:
            self.recovery_time = max(0,self.recovery_time-dt)
            self.speed = 0
            self.bump = V()
            self.boosting = False
            return
        old = self.position.copy()
        old_heading = self.heading
        self.cooldown = max(0, self.cooldown-dt)
        up, down = bool(keys[self.keys['up']]), bool(keys[self.keys['down']])
        if up == down:
            self.speed = approach(self.speed, 0, COAST_DRAG*dt)
        elif up:
            self.speed += (BRAKING if self.speed < 0 else ACCELERATION)*dt
        else:
            self.speed -= (BRAKING if self.speed > 0 else ACCELERATION)*dt
        boost_key=self.keys.get('boost')
        held=bool(keys[boost_key]) if boost_key is not None else False
        if self.boost_locked and self.boost >= .3 and not held:self.boost_locked=False
        self.boosting=held and up and not down and self.speed>15 and self.boost>0 and not self.boost_locked
        if self.boosting:
            self.speed += BOOST_ACCELERATION*dt
            self.boost=max(0,self.boost-dt/BOOST_DURATION)
            if self.boost <= 1e-9:
                self.boost=0
                self.boost_locked=True
        else:
            if not held:self.boost=min(1,self.boost+BOOST_RECHARGE*dt)
            if self.speed > MAX_SPEED:self.speed=approach(self.speed,MAX_SPEED,400*dt)
        limit=BOOST_SPEED if self.boosting else max(MAX_SPEED,self.speed)
        self.speed = max(-REVERSE_SPEED, min(limit, self.speed))
        steering = int(keys[self.keys['right']])-int(keys[self.keys['left']])
        if abs(self.speed) > 2:
            self.heading += steering*STEER_RATE*dt*(1 if self.speed > 0 else -1)
        self.heading %= 360
        self.bump *= math.exp(-6*dt)
        displacement = self.velocity*dt
        self.position += displacement
        if not self.track.valid(self.sprite(), self.position):
            # Restore the last valid orientation and slide along a wall if possible.
            self.position = old
            self.heading = old_heading
            for axis in (V(displacement.x,0), V(0,displacement.y)):
                candidate = self.position+axis
                if self.track.valid(self.sprite(),candidate): self.position = candidate
            self.impact = self.velocity.length()
            self.speed *= .25
            self.bump *= .2
            self.cooldown = .16

    def update(self, dt, pressed=None):
        """Single-car helper; the game advances all cars together through RacePhysics."""
        keys = pygame.key.get_pressed() if pressed is None else pressed
        steps = max(1, math.ceil(dt/FIXED_DT))
        for _ in range(steps):
            previous = self.position.copy()
            self.integrate(dt/steps, keys)
            self.progress(previous, self.position)


def contact(a, b):
    """Separating-axis test for two oriented car bodies (slightly inset sprites)."""
    forward_a, forward_b = a.forward, b.forward
    side_a, side_b = V(-forward_a.y,forward_a.x), V(-forward_b.y,forward_b.x)
    delta = b.position-a.position
    best_depth, best_axis = float('inf'), None
    for axis in (forward_a,side_a,forward_b,side_b):
        radius_a = 26*abs(axis.dot(forward_a))+12*abs(axis.dot(side_a))
        radius_b = 26*abs(axis.dot(forward_b))+12*abs(axis.dot(side_b))
        depth = radius_a+radius_b-abs(delta.dot(axis))
        if depth <= 0: return None
        if depth < best_depth:
            best_depth = depth
            best_axis = axis if delta.dot(axis) >= 0 else -axis
    return best_axis, best_depth


def resolve_contact(a, b, previous):
    """Equal-mass bumper impulse; separation may never push a car off the road."""
    hit = contact(a,b)
    if hit is None: return False
    normal, depth = hit
    correction = normal*(depth+.25)
    candidates = [(a.position-correction*.5,b.position+correction*.5),
                  (a.position-correction,b.position.copy()),
                  (a.position.copy(),b.position+correction)]
    accepted = False
    for pa,pb in candidates:
        if a.track.valid(a.sprite(),pa) and b.track.valid(b.sprite(),pb):
            a.position,b.position = pa,pb
            accepted = True
            break
    va,vb = a.velocity,b.velocity
    closing = (vb-va).dot(normal)
    if closing < 0:
        impulse = -(1+.2)*closing/2
        va -= normal*impulse
        vb += normal*impulse
    if not accepted:
        # Tight wall contact: roll the whole pair back to its safe step, not into grass.
        for car,(position,heading) in zip((a,b),previous):
            car.position,car.heading = position.copy(),heading
        # Remove the closing component so a pinned pair does not repeatedly shove.
        va -= normal*max(0,va.dot(normal))
        vb -= normal*min(0,vb.dot(normal))
    a.set_velocity(va)
    b.set_velocity(vb)
    a.cooldown = b.cooldown = .12
    return True


class RacePhysics:
    """Both players share 120 Hz steps and contact resolution, independent of rendering."""
    def __init__(self, cars):
        self.cars = cars
        self.accumulator = 0.0
        self.elapsed = 0.0
        self.finished = []
        self.contacts = 0
        self.events = []

    def recover(self, index):
        """Return behind the last passed sector; never advance lap/checkpoint progress."""
        if self.finished:return False
        car=self.cars[index]
        if car.recovery_cooldown>0 or car.recovery_time>0:return False
        track=car.track
        last=track.gates[(car.next_gate-1)%len(track.gates)][0]
        nearest=min(range(len(track.path)),key=lambda i:track.path[i].distance_squared_to(last))
        old_position,old_heading=car.position.copy(),car.heading
        for back in (12,20,30,40):
            i=(nearest-back)%len(track.path)
            direction=(track.path[(i+2)%len(track.path)]-track.path[i-2]).normalize()
            normal=V(-direction.y,direction.x)
            for side in (0,-12,12):
                car.position=track.path[i]+normal*side
                car.heading=math.degrees(math.atan2(direction.y,direction.x))
                if not track.valid(car.sprite(),car.position):continue
                if any(contact(car,other) is not None for j,other in enumerate(self.cars) if j!=index):continue
                car.speed=0
                car.bump=V()
                car.boosting=False
                car.recovery_time=RECOVERY_PENALTY
                car.recovery_cooldown=5.0
                car.recoveries+=1
                return True
        car.position,car.heading=old_position,old_heading
        return False

    def advance(self, dt, pressed=None, target_laps=None):
        self.events = []
        keys = pygame.key.get_pressed() if pressed is None else pressed
        self.accumulator += max(0,min(.25,dt))
        while self.accumulator+1e-10 >= FIXED_DT and not self.finished:
            previous = [(car.position.copy(),car.heading) for car in self.cars]
            for car in self.cars: car.integrate(FIXED_DT,keys)
            for i,car in enumerate(self.cars):
                if car.impact > 70:
                    self.events.append({'kind':'hit','position':car.position.copy(),'strength':car.impact})
            if len(self.cars) == 2:
                relative=(self.cars[0].velocity-self.cars[1].velocity).length()
                if resolve_contact(*self.cars,previous):
                    self.contacts += 1
                    if relative > 70:
                        self.events.append({'kind':'hit','position':(self.cars[0].position+self.cars[1].position)/2,'strength':relative})
            for i,(car,(position,_)) in enumerate(zip(self.cars,previous)):
                fraction=car.progress(position,car.position) if car.recovery_time<=0 else None
                if fraction is not None:
                    timestamp=self.elapsed+fraction*FIXED_DT
                    duration=timestamp-car.lap_start_time
                    car.lap_times.append(duration)
                    car.lap_start_time=timestamp
                    self.events.append({'kind':'lap','player':i+1,'time':timestamp,'duration':duration})
                    if target_laps is not None and car.point>=target_laps:
                        car.finish_time=timestamp
            self.elapsed += FIXED_DT
            self.accumulator = max(0,self.accumulator-FIXED_DT)
            if target_laps is not None:
                self.finished = [i+1 for i,car in enumerate(self.cars) if car.point >= target_laps]
                for i in self.finished:
                    if self.cars[i-1].finish_time is None:self.cars[i-1].finish_time=self.elapsed
        return self.finished
