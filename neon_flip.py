#!/usr/bin/env python3
"""Neon Flip — full-colour Python 3 neon pinball arcade for ElbowOS.
Autoplay 9:16 MP4 reel. https://x.com/ElbowOS
"""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "NEON_FLIP_ElbowOS.mp4")
TITLE, HANDLE = "NEON FLIP", "x.com/ElbowOS"

# Palette
BG = (8, 12, 28)
INK = (18, 24, 48)
CYAN = (0, 255, 255)
MAG = (255, 40, 180)
GOLD = (255, 220, 60)
LIME = (80, 255, 120)
WHITE = (245, 250, 255)
ORANGE = (255, 140, 40)
PURPLE = (180, 60, 255)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 72, bold=True)
        self.small = pygame.font.SysFont("arial", 42, bold=True)
        self.reset()

    def reset(self):
        self.score = 0
        self.ball = [W // 2, 400]
        self.vx = random.uniform(-4, 4)
        self.vy = 2
        self.flip_l = False
        self.flip_r = False
        self.bumpers = [
            (280, 700, 70, CYAN),
            (800, 700, 70, MAG),
            (540, 1000, 90, GOLD),
            (320, 1300, 60, LIME),
            (760, 1300, 60, ORANGE),
        ]
        self.targets = [
            pygame.Rect(100, 500, 80, 30),
            pygame.Rect(900, 500, 80, 30),
            pygame.Rect(450, 800, 180, 25),
        ]
        self.frame = 0
        self.lives = 3

    def update(self, keys=None, auto=False):
        # Gravity
        self.vy += 0.18
        self.ball[0] += self.vx
        self.ball[1] += self.vy

        # Walls
        if self.ball[0] < 40 or self.ball[0] > W - 40:
            self.vx *= -0.92
            self.ball[0] = max(40, min(W - 40, self.ball[0]))
            self.score += 5
        if self.ball[1] < 60:
            self.vy *= -0.85
            self.ball[1] = 60
            self.score += 10

        # Flippers (simple angled bounce)
        flip_y = H - 220
        if auto:
            # AI: flip if ball is above and heading toward side
            if self.ball[1] > flip_y - 200 and self.vy > 0:
                if self.ball[0] < W // 2:
                    self.flip_l = True
                else:
                    self.flip_r = True
            else:
                self.flip_l = self.flip_r = False
        else:
            self.flip_l = keys and (keys[pygame.K_LEFT] or keys[pygame.K_a])
            self.flip_r = keys and (keys[pygame.K_RIGHT] or keys[pygame.K_d])

        # Left flipper
        if self.flip_l and flip_y - 40 < self.ball[1] < flip_y + 40 and 80 < self.ball[0] < 420:
            if self.vy > 0:
                self.vy = -abs(self.vy) * 1.15 - 3
                self.vx += 2
                self.score += 20
        # Right flipper
        if self.flip_r and flip_y - 40 < self.ball[1] < flip_y + 40 and 660 < self.ball[0] < 1000:
            if self.vy > 0:
                self.vy = -abs(self.vy) * 1.15 - 3
                self.vx -= 2
                self.score += 20

        # Bumpers
        for bx, by, r, _ in self.bumpers:
            dx, dy = self.ball[0] - bx, self.ball[1] - by
            dist = math.hypot(dx, dy)
            if dist < r + 18 and dist > 0:
                # Bounce
                nx, ny = dx / dist, dy / dist
                dot = self.vx * nx + self.vy * ny
                self.vx -= 2 * dot * nx
                self.vy -= 2 * dot * ny
                self.vx *= 1.05
                self.vy *= 1.05
                self.score += 50
                # Push out
                self.ball[0] = bx + nx * (r + 20)
                self.ball[1] = by + ny * (r + 20)

        # Targets
        for t in self.targets:
            if t.collidepoint(self.ball[0], self.ball[1]) and self.vy != 0:
                self.vy *= -0.9
                self.score += 100
                t.y -= 5  # visual feedback

        # Drain
        if self.ball[1] > H - 40:
            self.lives -= 1
            if self.lives <= 0:
                self.score = max(0, self.score - 200)
                self.lives = 3
            self.ball = [W // 2 + random.randint(-80, 80), 300]
            self.vx = random.uniform(-3, 3)
            self.vy = 1

        self.frame += 1

    def draw(self, surf):
        surf.fill(BG)
        # Table border
        pygame.draw.rect(surf, INK, (20, 40, W - 40, H - 80), 8)
        pygame.draw.rect(surf, CYAN, (20, 40, W - 40, H - 80), 3)

        # Flippers
        flip_y = H - 220
        col_l = GOLD if self.flip_l else (80, 80, 120)
        col_r = GOLD if self.flip_r else (80, 80, 120)
        # Left
        pts_l = [(100, flip_y + 20), (380, flip_y - 10 if self.flip_l else flip_y + 10), (380, flip_y + 30)]
        pygame.draw.polygon(surf, col_l, pts_l)
        pygame.draw.polygon(surf, WHITE, pts_l, 2)
        # Right
        pts_r = [(980, flip_y + 20), (700, flip_y - 10 if self.flip_r else flip_y + 10), (700, flip_y + 30)]
        pygame.draw.polygon(surf, col_r, pts_r)
        pygame.draw.polygon(surf, WHITE, pts_r, 2)

        # Bumpers
        for bx, by, r, c in self.bumpers:
            pygame.draw.circle(surf, c, (int(bx), int(by)), r)
            pygame.draw.circle(surf, WHITE, (int(bx), int(by)), r, 3)
            pygame.draw.circle(surf, (c[0]//2, c[1]//2, c[2]//2), (int(bx), int(by)), r // 2)

        # Targets
        for t in self.targets:
            pygame.draw.rect(surf, MAG, t)
            pygame.draw.rect(surf, WHITE, t, 2)

        # Ball
        pygame.draw.circle(surf, WHITE, (int(self.ball[0]), int(self.ball[1])), 22)
        pygame.draw.circle(surf, CYAN, (int(self.ball[0]), int(self.ball[1])), 22, 3)
        pygame.draw.circle(surf, GOLD, (int(self.ball[0]) - 6, int(self.ball[1]) - 6), 6)

        # UI
        title_s = self.font.render(TITLE, True, CYAN)
        surf.blit(title_s, (W // 2 - title_s.get_width() // 2, 60))
        score_s = self.small.render(f"SCORE {self.score}", True, GOLD)
        surf.blit(score_s, (40, 160))
        lives_s = self.small.render(f"LIVES {self.lives}", True, LIME)
        surf.blit(lives_s, (W - 280, 160))
        handle_s = self.small.render(HANDLE, True, MAG)
        surf.blit(handle_s, (W // 2 - handle_s.get_width() // 2, H - 120))

    def record(self):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-movflags", "+faststart", "-an", OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        total = FPS * SECS
        for i in range(total):
            self.update(auto=True)
            self.draw(self.screen)
            raw = pygame.image.tostring(self.screen, "RGB")
            try:
                proc.stdin.write(raw)
            except BrokenPipeError:
                break
            if i % 30 == 0:
                print(f"frame {i}/{total} score={self.score}")
        proc.stdin.close()
        proc.wait()
        print(f"Wrote {OUT}")

    def play(self):
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    running = False
            keys = pygame.key.get_pressed()
            self.update(keys=keys, auto=False)
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    g = Game()
    if RECORD or (not PLAY and not sys.stdin.isatty()):
        g.record()
    else:
        g.play()
