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
