import sys
import pygame
import math
import tkinter as tk
from tkinter import simpledialog

pygame.init()

class Game:
    def __init__(self):
        self.fpsclock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((1500, 800))
        pygame.display.set_caption("Update")
        self.track = pygame.image.load("data/track1.png")
        self.arrow = pygame.image.load("data/arrow.png")
        self.start_imgs = {
            'start': pygame.image.load("data/start.png"),
            'start2': pygame.image.load("data/start2.png"),
            'start3': pygame.image.load("data/start3.png"),
        }
        self.car_imgs = {
            'car1': pygame.image.load("data/car1.png"),
            'car11': pygame.image.load("data/car1.1.png"),
            'car12': pygame.image.load("data/car1.2.png"),
            'car2': pygame.image.load("data/car2.png"),
            'car22': pygame.image.load("data/car2.2.png"),
        }
        self.rounds = self.get_rounds()
        self.show_menu = True

    def get_rounds(self):
        root = tk.Tk()
        root.withdraw()
        rounds = simpledialog.askinteger("Input", "Enter number of rounds:")
        root.destroy()
        return rounds if rounds else 1

    def ask_quit(self):
        root = tk.Tk()
        root.withdraw()
        answer = simpledialog.askstring("Quit", "Do you want to quit? (Y/N):")
        root.destroy()
        return answer.upper()

    def end(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def display_menu(self):
        while self.show_menu:
            mx, my = pygame.mouse.get_pos()
            ev = pygame.event.get()
            self.screen.blit(self.start_imgs['start'], (0, 0))
            if 950 > mx > 555 and 645 > my > 515:
                self.screen.blit(self.start_imgs['start3'], (0, 0))
                for event in ev:
                    if event.type == pygame.MOUSEBUTTONUP:
                        for _ in range(100):
                            self.screen.blit(self.start_imgs['start2'], (0, 0))
                            pygame.display.update()
                        for _ in range(100):
                            self.screen.blit(self.start_imgs['start'], (0, 0))
                            pygame.display.update()
                        self.show_menu = False
            pygame.display.update()
            self.fpsclock.tick(100)

class Car:
    def __init__(self, x, y, w, h, img1, img2, img3, screen, keys):
        self.x = x
        self.y = y
        self.h = h
        self.w = w
        self.n = 0
        self.speed = 0
        self.cond = False
        self.check = False
        self.check1 = False
        self.freeze = False
        self.point = 0
        self.ang1 = 0
        self.ang2 = 180
        self.rotate1 = 0
        self.rotate_rect = 0
        self.lines = [0] * 8
        self.car_img1 = img1
        self.car_img2 = img2
        self.car_img3 = img3
        self.screen = screen
        self.keys = keys

    def direction(self):
        temp_ang = math.radians(self.ang2)
        self.x += self.speed * math.cos(temp_ang)
        self.y += self.speed * math.sin(temp_ang)

    def hitbox(self):
        angrad = [
            math.radians(self.ang2 - 20),
            math.radians(self.ang2 + 20),
            math.radians(self.ang2 - 160),
            math.radians(self.ang2 + 160),
        ]
        for i in range(4):
            self.lines[2 * i] = self.x + math.cos(angrad[i]) * 30
            self.lines[2 * i + 1] = self.y + math.sin(angrad[i]) * 30
        return self.lines

    def controls(self):
        self.rotate1 = pygame.transform.rotate(self.car_img1, self.ang1)
        self.rotate_rect = self.rotate1.get_rect(center=self.car_img1.get_rect(center=(self.x, self.y)).center)
        self.screen.blit(self.rotate1, self.rotate_rect)
        kinput = pygame.key.get_pressed()

        if not self.freeze:
            if kinput[self.keys['right']] and self.speed != 0:
                if self.speed > 0:
                    self.ang1 -= 1
                    self.ang2 += 1
                else:
                    self.ang1 += 1
                    self.ang2 -= 1
                self.ang1 %= 360
            elif kinput[self.keys['left']] and self.speed != 0:
                if self.speed > 0:
                    self.ang1 += 1
                    self.ang2 -= 1
                else:
                    self.ang1 -= 1
                    self.ang2 += 1
                self.ang1 %= 360

            if kinput[self.keys['up']]:
                self.speed += 0.02
            else:
                if self.speed > 0:
                    self.speed -= 0.01
            if kinput[self.keys['down']]:
                self.speed -= 0.02
            else:
                if self.speed < 0:
                    self.speed += 0.01

            self.direction()
            self.lines = self.hitbox()
            self.speed = float(format(self.speed, ".2f"))

        boundaries = [
            ((0, 1), [(3, -3), (3, 3), (-3, 3), (-3, -3)]),
            ((2, 3), [(3, 3), (-3, 3), (-3, -3), (3, -3)]),
            ((4, 5), [(-3, -3), (3, -3), (3, 3), (-3, 3)]),
            ((6, 7), [(-3, 3), (-3, -3), (3, -3), (3, 3)]),
        ]

        for i, (indices, shifts) in enumerate(boundaries):
            if self.screen.get_at((int(self.lines[indices[0]]), int(self.lines[indices[1]]))) == (255, 255, 255, 255) and not self.freeze:
                if 360 >= self.ang1 > 315 or 45 >= self.ang1 > 0:
                    dx, dy = shifts[0]
                elif 315 >= self.ang1 > 225:
                    dx, dy = shifts[1]
                elif 225 >= self.ang1 > 135:
                    dx, dy = shifts[2]
                else:
                    dx, dy = shifts[3]
                self.x += dx
                self.y += dy
                self.cond = True

        if self.cond:
            self.n = 100
            self.speed = 0
            self.cond = False
            self.freeze = True

        if self.n > 0:
            rotate_img = pygame.transform.rotate(
                self.car_img3 if self.n > 75 or 50 > self.n > 25 else self.car_img2, self.ang1)
            rotate_rect = rotate_img.get_rect(center=self.car_img3.get_rect(center=(self.x, self.y)).center)
            self.screen.blit(rotate_img, rotate_rect)
            self.n -= 1
        elif self.n == 0:
            self.freeze = False

        if 140 > self.x > 54 and 515 > self.y > 500:
            self.check1 = True
        if self.x > 1000 and 100 > self.y > 30 and self.check1:
            self.check1 = False
            self.check = True
        if 1100 < self.x < 1125 and 772 > self.y > 702 and self.check:
            self.point += 1
            self.check = False

def main():
    game = Game()
    game.display_menu()

    keys1 = {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT}
    keys2 = {'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a, 'right': pygame.K_d}

    First_car = Car(1132, 720, 15, 15, game.car_imgs['car1'], game.car_imgs['car12'], game.car_imgs['car11'], game.screen, keys1)
    Second_car = Car(1130, 752, 15, 15, game.car_imgs['car2'], game.car_imgs['car22'], game.car_imgs['car11'], game.screen, keys2)

    run = True
    while run:
            game.screen.blit(game.track, (0, 0))
            game.screen.blit(game.arrow, (1020, 570))
            pygame.draw.rect(game.screen, (250, 250, 250), (1085, 702, 15, 70), 5)
            game.end()

            First_car.controls()
            Second_car.controls()

            font = pygame.font.SysFont("Arial", 36)
            points1 = str(First_car.point)
            points2 = str(Second_car.point)
            game.screen.blit(font.render("Player 1 Score: ", False, (255, 255, 255)), (200, 200))
            game.screen.blit(font.render(points1, False, (255, 255, 255)), (410, 200))
            game.screen.blit(font.render("Player 2 Score: ", False, (255, 255, 255)), (200, 250))
            game.screen.blit(font.render(points2, False, (255, 255, 255)), (410, 250))
            game.screen.blit(font.render("Finish", False, (255, 255, 255)), (1050, 660))

            font = pygame.font.SysFont("Arial", 100)
            if First_car.point == game.rounds:
                text = font.render("Player 1 Wins!", False, (0, 255, 0))
                game.screen.blit(text, (480, 350))
            elif Second_car.point == game.rounds:
                text = font.render("Player 2 Wins!", False, (255, 255, 0))
                game.screen.blit(text, (480, 350))

            pygame.display.update()
            game.fpsclock.tick(100)

            if First_car.point == game.rounds or Second_car.point == game.rounds:
                answer = game.ask_quit()
                if answer == "Y":
                    run = False
                    pygame.quit()
                    return
                elif answer == "N":
                    break

if __name__ == "__main__":
    main()