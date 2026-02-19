import pygame
import heapq
import random
import math

# --- INITIALIZATION & CONSTANTS ---
pygame.init()
WIDTH, HEIGHT = 800, 800
GRID_SIZE = 40
COLS, ROWS = WIDTH // GRID_SIZE, HEIGHT // GRID_SIZE
FPS = 60

# Colors
COLOR_BG = (10, 10, 15)
COLOR_GRID = (25, 25, 35)
COLOR_FOG_EXPLORED = (20, 20, 30, 150) # Dark overlay for seen tiles
COLOR_FOG_UNSEEN = (0, 0, 0)           # Pitch black for unseen tiles
COLOR_WALL = (50, 60, 80)
COLOR_TEXT = (255, 255, 255)
COLOR_EXIT = (50, 255, 100)

font = pygame.font.SysFont("impact", 20)
large_font = pygame.font.SysFont("impact", 72)

# --- UTILITY ALGORITHMS ---
def dist(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def lerp(a, b, t):
    return a + (b - a) * t

# --- CLASSES ---
class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.vx, self.vy = random.uniform(-3, 3), random.uniform(-3, 3)
        self.life = 1.0
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 0.05

    def draw(self, surface, offset_x, offset_y):
        if self.life > 0:
            alpha = int(255 * self.life)
            size = max(2, int(6 * self.life))
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            s.fill((*self.color, alpha))
            surface.blit(s, (self.x + offset_x, self.y + offset_y))

class Enemy:
    def __init__(self, x, y, e_type):
        self.pos = [x, y]
        self.draw_pos = [x * GRID_SIZE, y * GRID_SIZE]
        self.type = e_type
        self.state = "Patrol"
        self.last_move_time = pygame.time.get_ticks()
        
        # --- ENEMY CLASSES ---
        if e_type == "Scout":
            self.hp = 20
            self.max_hp = 20
            self.damage = 5
            self.move_cooldown = 150 # Fast
            self.color = (255, 200, 50)
            self.vision = 8
        elif e_type == "Tank":
            self.hp = 120
            self.max_hp = 120
            self.damage = 30
            self.move_cooldown = 500 # Slow
            self.color = (255, 100, 0)
            self.vision = 5
        else: # Hunter
            self.hp = 50
            self.max_hp = 50
            self.damage = 15
            self.move_cooldown = 300 # Medium
            self.color = (40, 200, 255)
            self.vision = 6

    def draw(self, surface, offset_x, offset_y):
        # Update smooth rendering position
        tx, ty = self.pos[0] * GRID_SIZE, self.pos[1] * GRID_SIZE
        self.draw_pos[0] = lerp(self.draw_pos[0], tx, 0.3)
        self.draw_pos[1] = lerp(self.draw_pos[1], ty, 0.3)
        
        bx, by = self.draw_pos[0] + offset_x, self.draw_pos[1] + offset_y
        center = (bx + GRID_SIZE//2, by + GRID_SIZE//2)

        # PROCEDURAL SPRITES: Change shapes based on class
        # TO USE IMAGES INSTEAD: surface.blit(my_image, (bx, by))
        if self.type == "Scout":
            pygame.draw.polygon(surface, self.color, [(center[0], by+5), (bx+GRID_SIZE-5, by+GRID_SIZE-5), (bx+5, by+GRID_SIZE-5)])
        elif self.type == "Tank":
            pygame.draw.rect(surface, self.color, (bx+4, by+4, GRID_SIZE-8, GRID_SIZE-8), border_radius=4)
            pygame.draw.rect(surface, (50,50,50), (bx+10, by+10, GRID_SIZE-20, GRID_SIZE-20))
        else: # Hunter
            pygame.draw.circle(surface, self.color, center, GRID_SIZE//2 - 4)
            pygame.draw.circle(surface, (255,255,255), center, 6) # "Eye"
        
        # HP Bar
        pygame.draw.rect(surface, (100,0,0), (bx, by + GRID_SIZE - 4, GRID_SIZE, 4))
        pygame.draw.rect(surface, (0,255,0), (bx, by + GRID_SIZE - 4, (self.hp/self.max_hp) * GRID_SIZE, 4))

class Item:
    def __init__(self, x, y, i_type):
        self.pos = [x, y]
        self.type = i_type # "HEALTH"

    def draw(self, surface, offset_x, offset_y):
        ix, iy = self.pos[0] * GRID_SIZE + offset_x, self.pos[1] * GRID_SIZE + offset_y
        if self.type == "HEALTH":
            pygame.draw.rect(surface, (255,255,255), (ix+8, iy+8, GRID_SIZE-16, GRID_SIZE-16), border_radius=3)
            pygame.draw.rect(surface, (255,50,50), (ix+16, iy+10, GRID_SIZE-32, GRID_SIZE-20)) # Cross H
            pygame.draw.rect(surface, (255,50,50), (ix+10, iy+16, GRID_SIZE-20, GRID_SIZE-32)) # Cross V

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Cyber Hunt: Infinite")
        self.clock = pygame.time.Clock()
        
        # Player Stats (Carry over between levels)
        self.monster_hp = 100
        self.max_hp = 100
        self.level = 1
        
        self.generate_level()

    def generate_level(self):
        self.state = "PLAYING"
        self.exit_pos = [COLS - 2, ROWS - 2]
        
        # Fog of War Setup
        self.vision_radius = 6
        self.visible_tiles = set()
        self.explored_tiles = set()
        self.fog_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # Scale difficulty with level
        num_walls = min(150, 60 + (self.level * 15))
        num_enemies = min(15, 3 + self.level)
        num_items = random.randint(1, 3)

        self.walls = set()
        while len(self.walls) < num_walls:
            x, y = random.randint(1, COLS-2), random.randint(1, ROWS-2)
            if dist((x, y), (2, 2)) > 2 and dist((x, y), self.exit_pos) > 2:
                self.walls.add((x, y))
                
        self.monster_pos = [2, 2]
        self.monster_draw_pos = [2 * GRID_SIZE, 2 * GRID_SIZE]
        self.last_move_time = 0
        self.move_cooldown = 120 

        # Spawning Enemies
        self.enemies = []
        enemy_types = ["Hunter", "Hunter", "Scout", "Tank"]
        while len(self.enemies) < num_enemies:
            x, y = random.randint(1, COLS-2), random.randint(1, ROWS-2)
            if (x, y) not in self.walls and dist((x, y), self.monster_pos) > 5:
                e_type = random.choice(enemy_types)
                self.enemies.append(Enemy(x, y, e_type))

        # Spawning Items
        self.items = []
        while len(self.items) < num_items:
            x, y = random.randint(1, COLS-2), random.randint(1, ROWS-2)
            if (x, y) not in self.walls and (x, y) != tuple(self.exit_pos):
                self.items.append(Item(x, y, "HEALTH"))

        self.particles = []
        self.screen_shake = 0
        self.update_fov()

    def update_fov(self):
        """Calculates which tiles the player can currently see."""
        self.visible_tiles.clear()
        mx, my = self.monster_pos
        for dx in range(-self.vision_radius, self.vision_radius + 1):
            for dy in range(-self.vision_radius, self.vision_radius + 1):
                if dx**2 + dy**2 <= self.vision_radius**2: # Circle radius check
                    vx, vy = mx + dx, my + dy
                    if 0 <= vx < COLS and 0 <= vy < ROWS:
                        self.visible_tiles.add((vx, vy))
                        self.explored_tiles.add((vx, vy))

    def is_valid(self, x, y):
        return 0 <= x < COLS and 0 <= y < ROWS and (x, y) not in self.walls

    def is_occupied(self, pos, current_ent=None):
        for e in self.enemies:
            if e != current_ent and e.pos == list(pos): return True
        return False

    def spawn_particles(self, pos, color, amount=10):
        px, py = pos[0] * GRID_SIZE + GRID_SIZE//2, pos[1] * GRID_SIZE + GRID_SIZE//2
        for _ in range(amount):
            self.particles.append(Particle(px, py, color))

    def a_star(self, start, goal):
        pq = [(0, start)]
        came_from = {tuple(start): None}
        cost_so_far = {tuple(start): 0}
        
        while pq:
            _, curr = heapq.heappop(pq)
            if curr == goal: break
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nxt = [curr[0] + dx, curr[1] + dy]
                nxt_tuple = tuple(nxt)
                if self.is_valid(*nxt) and not self.is_occupied(nxt):
                    new_cost = cost_so_far[tuple(curr)] + 1
                    if nxt_tuple not in cost_so_far or new_cost < cost_so_far[nxt_tuple]:
                        cost_so_far[nxt_tuple] = new_cost
                        priority = new_cost + dist(nxt, goal)
                        heapq.heappush(pq, (priority, nxt))
                        came_from[nxt_tuple] = curr
                        
        curr = tuple(goal)
        if curr not in came_from: return start
        path = []
        while curr != tuple(start):
            path.append(list(curr))
            curr = tuple(came_from[curr])
        return path[-1] if path else start

    def run(self):
        running = True
        while running:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if self.state == "GAME_OVER" and event.key == pygame.K_r:
                        self.monster_hp = 100
                        self.level = 1
                        self.generate_level()

            # --- PLAYER LOGIC ---
            if self.state == "PLAYING":
                keys = pygame.key.get_pressed()
                if current_time - self.last_move_time > self.move_cooldown:
                    dx, dy = 0, 0
                    if keys[pygame.K_UP]: dy = -1
                    elif keys[pygame.K_DOWN]: dy = 1
                    elif keys[pygame.K_LEFT]: dx = -1
                    elif keys[pygame.K_RIGHT]: dx = 1

                    if dx != 0 or dy != 0:
                        new_pos = [self.monster_pos[0] + dx, self.monster_pos[1] + dy]
                        attacked = False
                        
                        # Attack logic
                        for e in self.enemies:
                            if e.pos == new_pos:
                                e.hp -= 25 # Player Damage
                                self.spawn_particles(new_pos, e.color, 15)
                                attacked = True
                                
                        # Movement
                        if not attacked and self.is_valid(*new_pos):
                            self.monster_pos = new_pos
                            self.update_fov() # Update fog when moving
                            
                            # Check item pickup
                            for item in self.items[:]:
                                if item.pos == self.monster_pos:
                                    if item.type == "HEALTH":
                                        self.monster_hp = min(self.max_hp, self.monster_hp + 40)
                                        self.spawn_particles(self.monster_pos, (50, 255, 50), 20)
                                    self.items.remove(item)

                        self.last_move_time = current_time

                # Progression
                if self.monster_pos == self.exit_pos:
                    self.level += 1
                    self.generate_level()

            # --- AI LOGIC ---
            if self.state == "PLAYING":
                for e in self.enemies[:]: 
                    if e.hp <= 0:
                        self.enemies.remove(e)
                        self.spawn_particles(e.pos, e.color, 30)
                        continue
                        
                    # Individual enemy cooldowns
                    if current_time - e.last_move_time > e.move_cooldown:
                        d = dist(e.pos, self.monster_pos)
                        next_pos = e.pos
                        
                        if d == 1:
                            # Attack Player
                            self.monster_hp -= e.damage
                            self.screen_shake = e.damage // 2 # Harder hits shake screen more
                            self.spawn_particles(self.monster_pos, (255, 40, 80), 15)
                            if self.monster_hp <= 0: 
                                self.state = "GAME_OVER"
                        elif d <= e.vision: 
                            # Hunt player if in vision
                            next_pos = self.a_star(e.pos, self.monster_pos)
                        else:
                            # Patrol randomly
                            dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                            random.shuffle(dirs)
                            for mx, my in dirs:
                                test_pos = [e.pos[0] + mx, e.pos[1] + my]
                                if self.is_valid(*test_pos) and not self.is_occupied(test_pos):
                                    next_pos = test_pos
                                    break
                        
                        e.pos = next_pos
                        e.last_move_time = current_time

            # --- RENDERING ---
            self.screen.fill(COLOR_BG)
            
            shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
            shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
            if self.screen_shake > 0: self.screen_shake -= 1

            if self.state in ["PLAYING", "GAME_OVER"]:
                # Draw Base Grid
                for x in range(0, WIDTH, GRID_SIZE):
                    pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, HEIGHT))
                for y in range(0, HEIGHT, GRID_SIZE):
                    pygame.draw.line(self.screen, COLOR_GRID, (0, y), (WIDTH, y))

                # Draw Exit
                if tuple(self.exit_pos) in self.explored_tiles:
                    ex_x, ex_y = self.exit_pos[0]*GRID_SIZE, self.exit_pos[1]*GRID_SIZE
                    pygame.draw.rect(self.screen, COLOR_EXIT, (ex_x + shake_x, ex_y + shake_y, GRID_SIZE, GRID_SIZE), border_radius=8)

                # Draw Items
                for item in self.items:
                    if tuple(item.pos) in self.explored_tiles:
                        item.draw(self.screen, shake_x, shake_y)

                # Draw Walls (Only if explored)
                for x, y in self.walls:
                    if (x, y) in self.explored_tiles:
                        rect = (x*GRID_SIZE + shake_x, y*GRID_SIZE + shake_y, GRID_SIZE, GRID_SIZE)
                        pygame.draw.rect(self.screen, COLOR_WALL, rect, border_radius=5)
                        
                        # Add a 3D bevel to the wall for better graphics
                        pygame.draw.line(self.screen, (80,90,110), (rect[0], rect[1]), (rect[0]+GRID_SIZE, rect[1]), 2)
                        pygame.draw.line(self.screen, (30,40,50), (rect[0], rect[1]+GRID_SIZE), (rect[0]+GRID_SIZE, rect[1]+GRID_SIZE), 2)
                
                # Draw Particles
                for p in self.particles[:]:
                    p.update()
                    p.draw(self.screen, shake_x, shake_y)
                    if p.life <= 0: self.particles.remove(p)

                # Draw Enemies (Only if in CURRENT vision)
                for e in self.enemies:
                    if tuple(e.pos) in self.visible_tiles:
                        e.draw(self.screen, shake_x, shake_y)

                # Draw Player (Procedural Sprite - Cyber Demon)
                # TO USE AN IMAGE: self.screen.blit(player_img, (self.monster_draw_pos[0], self.monster_draw_pos[1]))
                target_mx, target_my = self.monster_pos[0]*GRID_SIZE, self.monster_pos[1]*GRID_SIZE
                self.monster_draw_pos[0] = lerp(self.monster_draw_pos[0], target_mx, 0.4) 
                self.monster_draw_pos[1] = lerp(self.monster_draw_pos[1], target_my, 0.4)
                
                mx = self.monster_draw_pos[0] + shake_x
                my = self.monster_draw_pos[1] + shake_y
                center = (mx + GRID_SIZE//2, my + GRID_SIZE//2)
                
                pygame.draw.circle(self.screen, (255, 40, 80), center, GRID_SIZE//2 - 2) # Body
                pygame.draw.polygon(self.screen, (255, 255, 255), [(mx+10, my+15), (mx+30, my+15), (mx+20, my+25)]) # Visor

                # FOG OF WAR RENDERING
                self.fog_surface.fill(COLOR_FOG_UNSEEN)
                for x in range(COLS):
                    for y in range(ROWS):
                        tile = (x, y)
                        rect = (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                        if tile in self.visible_tiles:
                            # Completely transparent
                            pygame.draw.rect(self.fog_surface, (0,0,0,0), rect)
                        elif tile in self.explored_tiles:
                            # Dark overlay
                            pygame.draw.rect(self.fog_surface, COLOR_FOG_EXPLORED, rect)
                self.screen.blit(self.fog_surface, (0,0))

                # HUD
                hp_color = (255, 40, 80) if self.monster_hp < 30 else (255,255,255)
                hp_text = font.render(f"HP: {self.monster_hp}/{self.max_hp}", True, hp_color)
                level_text = font.render(f"FLOOR: {self.level}", True, COLOR_TEXT)
                
                # Draw HUD Background
                pygame.draw.rect(self.screen, (20,20,30), (10, 10, 150, 60), border_radius=5)
                self.screen.blit(hp_text, (20, 15))
                self.screen.blit(level_text, (20, 40))

            if self.state == "GAME_OVER":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((40, 0, 0, 200))
                self.screen.blit(overlay, (0, 0))
                
                title = large_font.render("YOU DIED", True, (255, 40, 80))
                floor_text = font.render(f"You reached Floor {self.level}", True, COLOR_TEXT)
                sub = font.render("Press 'R' to Restart Run", True, COLOR_TEXT)
                
                self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 80))
                self.screen.blit(floor_text, (WIDTH//2 - floor_text.get_width()//2, HEIGHT//2))
                self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 40))

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()