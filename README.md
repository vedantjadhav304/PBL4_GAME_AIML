# 🕹️ Cyber Hunt: Infinite

**Cyber Hunt: Infinite** is a 2D grid-based tactical survival roguelike built entirely in Python using Pygame. Navigate through procedurally generated, infinite floors, manage your health, and outsmart dynamic AI enemies hunting you through the Fog of War.

## ✨ Features

* **Infinite Procedural Levels:** Every floor generates a unique maze of walls, enemies, and items. The difficulty scales up as you progress deeper.
* **Fog of War system:** You can only see a limited radius around your character. Explored areas stay dimly lit, but enemies hiding in the shadows remain invisible.
* **Dynamic AI & Pathfinding:** Enemies utilize the **A* (A-Star)** algorithm to calculate the shortest path to hunt you down once you enter their line of sight.
* **Visual "Juice":** Features smooth entity movement (Linear Interpolation/Lerping), combat particle explosions, and screen-shake when taking heavy damage.
* **Real-time AI Debug Visualizer:** A built-in developer tool that allows you to see exactly how the enemy AI calculates its pathfinding in real-time.

---

## 👾 Enemy Classes

The game features three distinct enemy types, each requiring different strategies to defeat:

* 🔵 **Hunter:** The standard patrol unit. Medium speed, medium damage, medium health.
* 🟡 **Scout:** Fast and aggressive. Moves very quickly and has a wide vision radius, but possesses low health and deals low damage.
* 🟠 **Tank:** Slow but deadly. Moves sluggishly and has poor vision, but boasts massive health and deals catastrophic damage if it catches you.

---

## 🎮 Controls

| Key | Action |
| :--- | :--- |
| **Arrow Keys** | Move your character (Hold for continuous movement) |
| **Arrow Keys (Into Enemy)** | Melee attack the enemy |
| **V** | Toggle **AI Debug Mode** |
| **R** | Restart game (from the Game Over screen) |

**Objective:** Survive the enemies, pick up Health Packs (white boxes with red crosses) to heal, and reach the **Green Exit Tile** to advance to the next floor.

---

## 🛠️ The AI Debug Tool (V Key)

If you want to see how the game works under the hood, press **V** during gameplay to toggle the Developer Debug Mode. 

* **Blue Outlines:** Shows the "Explored" tiles—every tile the enemy's AI looked at to calculate its next move.
* **Thick Red Outline:** Shows the final path or target the AI decided on.
* **Text Labels:** Displays the enemy's current state machine status (`PATROL`, `HUNT`, or `ATTACK`).

---

## 🚀 Installation & Running

### Prerequisites
You will need Python 3.x and the `pygame` library installed on your machine.

1. **Install Pygame:**
   Open your terminal or command prompt and run:
   ```bash
   pip install pygame

   

This game is driven by several classic computer science algorithms and game development techniques to create a smooth, intelligent, and challenging experience.

## 🧠  Alogrithms Used

### 1. A* (A-Star) Pathfinding

When an enemy spots you and enters the **HUNT** state, it uses the A* search algorithm to find the absolute shortest path to your location while navigating around walls. 
* **How it works:** It uses a priority queue (`heapq`) to evaluate tiles based on two costs: the distance already traveled from the enemy, and a "heuristic" (guess) of the remaining distance to the player. 
* **Why it's used:** It guarantees the shortest path on a 2D grid much faster than checking every single tile (like Dijkstra's algorithm would).

### 2. Manhattan Distance Metric
Throughout the code, you will see a `dist(p1, p2)` function calculating `abs(p1[x] - p2[x]) + abs(p1[y] - p2[y])`. 
* **How it works:** Because characters can only move strictly up, down, left, or right (no diagonals), standard Euclidean distance (the Pythagorean theorem) would be inaccurate. Manhattan distance measures the exact number of grid steps required to reach a target.
* **Where it's used:** It dictates the Fog of War radius, triggers enemy line-of-sight, calculates melee attack range, and serves as the heuristic for the A* algorithm.

### 3. Finite State Machine (FSM) for AI
Instead of complex, resource-heavy decision trees (like Minimax), the enemies use a lightweight Finite State Machine to transition between behaviors instantly:
* **PATROL:** The enemy wanders by shuffling adjacent tiles and moving to a random valid, unoccupied space.
* **HUNT:** Triggered when the player's Manhattan distance is `<=` the enemy's `vision` stat. Hands control over to the A* algorithm.
* **ATTACK:** Triggered when the distance is exactly `1`. Halts movement and deals damage directly to the player.

### 4. Linear Interpolation (Lerping)
Grid-based games often suffer from "teleporting" graphics, where a character instantly snaps from one tile to the next. 
* **How it works:** The game separates *Logical Position* (e.g., Grid `[2, 3]`) from *Drawing Position* (e.g., Pixel `[80, 120]`). The `lerp(a, b, t)` function smoothly glides the drawing coordinates toward the logical coordinates every frame.
* **Why it's used:** It creates buttery-smooth, modern-feeling movement animations without overcomplicating the grid math.

### 5. Procedural Generation with Rejection Sampling
Every floor is randomly generated, but it must be playable.
* **How it works:** When placing the 100+ walls, the game uses a `while` loop with Rejection Sampling. It generates a random coordinate, but *rejects* it if it lands within a 2-tile radius of the Player's spawn point or the Exit block. This guarantees you are never trapped the moment a level starts.
