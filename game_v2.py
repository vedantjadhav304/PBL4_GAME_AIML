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
COLOR_FOG_EXPLORED = (20, 20, 30, 150)
COLOR_FOG_UNSEEN = (0, 0, 0)           
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
        self.state = "PATROL"
        self.last_move_time = pygame.time.get_ticks()
        
        # Debug properties
        self.debug_path = []
        self.debug_explored = []
        self.patrol_target = None # Used for BFS
        
        # --- ENEMY CLASSES ---
        if e_type == "Scout":
            self.hp = 20
            self.max_hp = 20
            self.damage = 5
            self.move_cooldown = 150 
            self.color = (255, 200, 50)
            self.vision = 8
        elif e_type == "Tank":
            self.hp = 120
            self.max_hp = 120
            self.damage = 30
            self.move_cooldown = 500 
            self.color = (255, 100, 0)
            self.vision = 5
        elif e_type == "Boss": # Uses Minimax!
            self.hp = 150
            self.max_hp = 150
            self.damage = 25
            self.move_cooldown = 400
            self.color = (150, 50, 255) # Purple
            self.vision = 7
        else: # Hunter (Uses BFS for patrol)
            self.hp = 50
            self.max_hp = 50
            self.damage = 15
            self.move_cooldown = 300 
            self.color = (40, 200, 255)
            self.vision = 6

    def draw(self, surface, offset_x, offset_y):
        tx, ty = self.pos[0] * GRID_SIZE, self.pos[1] * GRID_SIZE
        self.draw_pos[0] = lerp(self.draw_pos[0], tx, 0.3)
        self.draw_pos[1] = lerp(self.draw_pos[1], ty, 0.3)
        
        bx, by = self.draw_pos[0] + offset_x, self.draw_pos[1] + offset_y
        center = (bx + GRID_SIZE//2, by + GRID_SIZE//2)

        if self.type == "Scout":
            pygame.draw.polygon(surface, self.color, [(center[0], by+5), (bx+GRID_SIZE-5, by+GRID_SIZE-5), (bx+5, by+GRID_SIZE-5)])
        elif self.type == "Tank":
            pygame.draw.rect(surface, self.color, (bx+4, by+4, GRID_SIZE-8, GRID_SIZE-8), border_radius=4)
            pygame.draw.rect(surface, (50,50,50), (bx+10, by+10, GRID_SIZE-20, GRID_SIZE-20))
        elif self.type == "Boss":
            pygame.draw.polygon(surface, self.color, [(center[0], by), (bx+GRID_SIZE, center[1]), (center[0], by+GRID_SIZE), (bx, center[1])])
            pygame.draw.circle(surface, (255,0,0), center, 6) # Red Eye
        else: # Hunter
            pygame.draw.circle(surface, self.color, center, GRID_SIZE//2 - 4)
            pygame.draw.circle(surface, (255,255,255), center, 6)
        
        # HP Bar
        pygame.draw.rect(surface, (100,0,0), (bx, by + GRID_SIZE - 4, GRID_SIZE, 4))
        pygame.draw.rect(surface, (0,255,0), (bx, by + GRID_SIZE - 4, (self.hp/self.max_hp) * GRID_SIZE, 4))

class Item:
    def __init__(self, x, y, i_type):
        self.pos = [x, y]
        self.type = i_type 

    def draw(self, surface, offset_x, offset_y):
        ix, iy = self.pos[0] * GRID_SIZE + offset_x, self.pos[1] * GRID_SIZE + offset_y
        if self.type == "HEALTH":
            pygame.draw.rect(surface, (255,255,255), (ix+8, iy+8, GRID_SIZE-16, GRID_SIZE-16), border_radius=3)
            pygame.draw.rect(surface, (255,50,50), (ix+16, iy+10, GRID_SIZE-32, GRID_SIZE-20)) 
            pygame.draw.rect(surface, (255,50,50), (ix+10, iy+16, GRID_SIZE-20, GRID_SIZE-32)) 

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Cyber Hunt: Infinite")
        self.clock = pygame.time.Clock()
        
        self.monster_hp = 100
        self.max_hp = 100
        self.level = 1
        self.show_debug = False
        
        self.generate_level()

    def generate_level(self):
        self.state = "PLAYING"
        self.exit_pos = [COLS - 2, ROWS - 2]
        self.vision_radius = 6
        self.visible_tiles = set()
        self.explored_tiles = set()
        self.fog_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

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

        self.enemies = []
        enemy_types = ["Hunter", "Hunter", "Scout", "Tank", "Boss"]
        while len(self.enemies) < num_enemies:
            x, y = random.randint(1, COLS-2), random.randint(1, ROWS-2)
            if (x, y) not in self.walls and dist((x, y), self.monster_pos) > 5:
                e_type = random.choice(enemy_types)
                self.enemies.append(Enemy(x, y, e_type))

        self.items = []
        while len(self.items) < num_items:
            x, y = random.randint(1, COLS-2), random.randint(1, ROWS-2)
            if (x, y) not in self.walls and (x, y) != tuple(self.exit_pos):
                self.items.append(Item(x, y, "HEALTH"))

        self.particles = []
        self.screen_shake = 0
        self.update_fov()

    def update_fov(self):
        self.visible_tiles.clear()
        mx, my = self.monster_pos
        for dx in range(-self.vision_radius, self.vision_radius + 1):
            for dy in range(-self.vision_radius, self.vision_radius + 1):
                if dx**2 + dy**2 <= self.vision_radius**2:
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

    # --- ALGORITHM 1: A* SEARCH (Used for standard hunting) ---
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
        path = []
        if curr in came_from:
            while curr != tuple(start):
                path.append(list(curr))
                curr = tuple(came_from[curr])
                
        next_step = path[-1] if path else start
        return next_step, path, list(cost_so_far.keys())

    # --- ALGORITHM 2: BFS (Used for structured patrolling) ---
    def bfs(self, start, goal):
        queue = [(start, [start])]
        explored = {tuple(start)}
        
        while queue:
            curr, path = queue.pop(0)
            if curr == goal:
                next_step = path[1] if len(path) > 1 else start
                return next_step, path, list(explored)
                
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nxt = [curr[0] + dx, curr[1] + dy]
                if self.is_valid(*nxt) and not self.is_occupied(nxt) and tuple(nxt) not in explored:
                    explored.add(tuple(nxt))
                    queue.append((nxt, path + [nxt]))
                    
        return start, [], list(explored)

    # --- ALGORITHM 3: MINIMAX (Used by Boss for tactical cornering) ---
    def evaluate_minimax(self, e_pos, p_pos, depth, is_maximizing):
        if depth == 0 or e_pos == p_pos:
            return -dist(e_pos, p_pos) # Minimax wants to minimize distance to player

        if is_maximizing: # Enemy's turn
            best_score = -float('inf')
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nxt = [e_pos[0]+dx, e_pos[1]+dy]
                if self.is_valid(*nxt):
                    score = self.evaluate_minimax(nxt, p_pos, depth-1, False)
                    best_score = max(best_score, score)
            return best_score
        else: # Player's turn (simulate player running away)
            best_score = float('inf')
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nxt = [p_pos[0]+dx, p_pos[1]+dy]
                if self.is_valid(*nxt):
                    score = self.evaluate_minimax(e_pos, nxt, depth-1, True)
                    best_score = min(best_score, score)
            return best_score

    def get_minimax_move(self, e_pos, p_pos):
        best_score = -float('inf')
        best_move = e_pos
        explored = []
        
        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
            nxt = [e_pos[0]+dx, e_pos[1]+dy]
            if self.is_valid(*nxt) and not self.is_occupied(nxt):
                explored.append(nxt) # Track for debug visuals
                score = self.evaluate_minimax(nxt, p_pos, 2, False) # Depth = 2
                if score > best_score:
                    best_score = score
                    best_move = nxt
                    
        return best_move, [best_move], explored

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
                    if event.key == pygame.K_v:
                        self.show_debug = not self.show_debug

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
                        
                        for e in self.enemies:
                            if e.pos == new_pos:
                                e.hp -= 25 
                                self.spawn_particles(new_pos, e.color, 15)
                                attacked = True
                                
                        if not attacked and self.is_valid(*new_pos):
                            self.monster_pos = new_pos
                            self.update_fov()
                            for item in self.items[:]:
                                if item.pos == self.monster_pos:
                                    if item.type == "HEALTH":
                                        self.monster_hp = min(self.max_hp, self.monster_hp + 40)
                                        self.spawn_particles(self.monster_pos, (50, 255, 50), 20)
                                    self.items.remove(item)
                        self.last_move_time = current_time

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
                        
                    if current_time - e.last_move_time > e.move_cooldown:
                        d = dist(e.pos, self.monster_pos)
                        next_pos = e.pos
                        
                        if d == 1:
                            # 1. ATTACK STATE
                            self.monster_hp -= e.damage
                            self.screen_shake = e.damage // 2
                            self.spawn_particles(self.monster_pos, (255, 40, 80), 15)
                            e.debug_path, e.debug_explored, e.state = [self.monster_pos], [], "ATTACK"
                            if self.monster_hp <= 0: self.state = "GAME_OVER"
                                
                        elif d <= e.vision: 
                            # 2. TACTICAL COMBAT STATE
                            if e.type == "Boss" and d <= 4:
                                next_pos, e.debug_path, e.debug_explored = self.get_minimax_move(e.pos, self.monster_pos)
                                e.state = "MINIMAX"
                            else:
                                next_pos, e.debug_path, e.debug_explored = self.a_star(e.pos, self.monster_pos)
                                e.state = "A* HUNT"
                        else:
                            # 3. PATROL STATE
                            if e.type == "Hunter":
                                # Hunter uses BFS to patrol to a specific valid tile
                                if not e.patrol_target or e.pos == e.patrol_target:
                                    while True:
                                        rx = e.pos[0] + random.randint(-4, 4)
                                        ry = e.pos[1] + random.randint(-4, 4)
                                        if self.is_valid(rx, ry):
                                            e.patrol_target = [rx, ry]
                                            break
                                next_pos, e.debug_path, e.debug_explored = self.bfs(e.pos, e.patrol_target)
                                e.state = "BFS PATROL"
                            else:
                                # Others wander randomly
                                e.state = "WANDER"
                                e.debug_explored = []
                                dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                                random.shuffle(dirs)
                                for mx, my in dirs:
                                    test_pos = [e.pos[0] + mx, e.pos[1] + my]
                                    if self.is_valid(*test_pos):
                                        e.debug_explored.append(test_pos)
                                        if not self.is_occupied(test_pos):
                                            next_pos = test_pos
                                            break
                                e.debug_path = [next_pos] if next_pos != e.pos else []
                        
                        e.pos = next_pos
                        e.last_move_time = current_time

            # --- RENDERING ---
            self.screen.fill(COLOR_BG)
            
            shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
            shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
            if self.screen_shake > 0: self.screen_shake -= 1

            if self.state in ["PLAYING", "GAME_OVER"]:
                for x in range(0, WIDTH, GRID_SIZE): pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, HEIGHT))
                for y in range(0, HEIGHT, GRID_SIZE): pygame.draw.line(self.screen, COLOR_GRID, (0, y), (WIDTH, y))

                if tuple(self.exit_pos) in self.explored_tiles:
                    ex_x, ex_y = self.exit_pos[0]*GRID_SIZE, self.exit_pos[1]*GRID_SIZE
                    pygame.draw.rect(self.screen, COLOR_EXIT, (ex_x + shake_x, ex_y + shake_y, GRID_SIZE, GRID_SIZE), border_radius=8)

                for item in self.items:
                    if tuple(item.pos) in self.explored_tiles: item.draw(self.screen, shake_x, shake_y)

                for x, y in self.walls:
                    if (x, y) in self.explored_tiles:
                        rect = (x*GRID_SIZE + shake_x, y*GRID_SIZE + shake_y, GRID_SIZE, GRID_SIZE)
                        pygame.draw.rect(self.screen, COLOR_WALL, rect, border_radius=5)
                        pygame.draw.line(self.screen, (80,90,110), (rect[0], rect[1]), (rect[0]+GRID_SIZE, rect[1]), 2)
                        pygame.draw.line(self.screen, (30,40,50), (rect[0], rect[1]+GRID_SIZE), (rect[0]+GRID_SIZE, rect[1]+GRID_SIZE), 2)
                
                for p in self.particles[:]:
                    p.update()
                    p.draw(self.screen, shake_x, shake_y)
                    if p.life <= 0: self.particles.remove(p)

                for e in self.enemies:
                    if tuple(e.pos) in self.visible_tiles: e.draw(self.screen, shake_x, shake_y)

                target_mx, target_my = self.monster_pos[0]*GRID_SIZE, self.monster_pos[1]*GRID_SIZE
                self.monster_draw_pos[0] = lerp(self.monster_draw_pos[0], target_mx, 0.4) 
                self.monster_draw_pos[1] = lerp(self.monster_draw_pos[1], target_my, 0.4)
                mx, my = self.monster_draw_pos[0] + shake_x, self.monster_draw_pos[1] + shake_y
                center = (mx + GRID_SIZE//2, my + GRID_SIZE//2)
                
                pygame.draw.circle(self.screen, (255, 40, 80), center, GRID_SIZE//2 - 2)
                pygame.draw.polygon(self.screen, (255, 255, 255), [(mx+10, my+15), (mx+30, my+15), (mx+20, my+25)])

                self.fog_surface.fill(COLOR_FOG_UNSEEN)
                for x in range(COLS):
                    for y in range(ROWS):
                        tile = (x, y)
                        rect = (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                        if tile in self.visible_tiles: pygame.draw.rect(self.fog_surface, (0,0,0,0), rect)
                        elif tile in self.explored_tiles: pygame.draw.rect(self.fog_surface, COLOR_FOG_EXPLORED, rect)
                self.screen.blit(self.fog_surface, (0,0))

                # --- DEBUG RENDERING ---
                if self.show_debug:
                    for e in self.enemies:
                        if hasattr(e, 'debug_explored') and hasattr(e, 'debug_path'):
                            # Change Blue Outline Color based on Algorithm!
                            outline_color = (0, 100, 255) # Blue for BFS/A*
                            if e.state == "MINIMAX": outline_color = (255, 0, 255) # Pink for Minimax
                            
                            for node in e.debug_explored:
                                pygame.draw.rect(self.screen, outline_color, (node[0] * GRID_SIZE + shake_x, node[1] * GRID_SIZE + shake_y, GRID_SIZE, GRID_SIZE), 1)
                            for node in e.debug_path:
                                pygame.draw.rect(self.screen, (255, 50, 50), (node[0] * GRID_SIZE + shake_x, node[1] * GRID_SIZE + shake_y, GRID_SIZE, GRID_SIZE), 3)
                            
                            state_text = font.render(e.state, True, (255, 255, 0))
                            self.screen.blit(state_text, (e.draw_pos[0] + shake_x - 5, e.draw_pos[1] + shake_y - 25))

                hp_color = (255, 40, 80) if self.monster_hp < 30 else (255,255,255)
                hp_text = font.render(f"HP: {self.monster_hp}/{self.max_hp}", True, hp_color)
                level_text = font.render(f"FLOOR: {self.level}", True, COLOR_TEXT)
                pygame.draw.rect(self.screen, (20,20,30), (10, 10, 150, 60), border_radius=5)
                self.screen.blit(hp_text, (20, 15))
                self.screen.blit(level_text, (20, 40))

            if self.state == "GAME_OVER":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((40, 0, 0, 200))
                self.screen.blit(overlay, (0, 0))
                title = large_font.render("YOU DIED", True, (255, 40, 80))
                self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 80))

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()