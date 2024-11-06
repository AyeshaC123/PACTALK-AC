import pygame
import speech_recognition as sr
import threading
import time
from queue import Queue
import math
import re

# Initialize Pygame
pygame.init()

# Constants
CELL_SIZE = 30
GRID_WIDTH = 19
GRID_HEIGHT = 21
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Voice-Controlled Pac-Man")

# Command queue for voice inputs
command_queue = Queue()

# Maze layout
MAZE = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1],
    [1,3,1,1,0,1,1,1,0,1,0,1,1,1,0,1,1,3,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,0,1,0,1,1,1,1,1,0,1,0,1,1,0,1],
    [1,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1],
    [1,1,1,1,0,1,1,1,0,1,0,1,1,1,0,1,1,1,1],
    [1,1,1,1,0,1,0,0,0,0,0,0,0,1,0,1,1,1,1],
    [1,1,1,1,0,1,0,1,1,2,1,1,0,1,0,1,1,1,1],
    [0,0,0,0,0,0,0,1,2,2,2,1,0,0,0,0,0,0,0],
    [1,1,1,1,0,1,0,1,1,1,1,1,0,1,0,1,1,1,1],
    [1,1,1,1,0,1,0,0,0,0,0,0,0,1,0,1,1,1,1],
    [1,1,1,1,0,1,0,1,1,1,1,1,0,1,0,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,0,1,1,1,0,1,0,1,1,1,0,1,1,0,1],
    [1,3,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,3,1],
    [1,1,0,1,0,1,0,1,1,1,1,1,0,1,0,1,0,1,1],
    [1,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1],
    [1,0,1,1,1,1,1,1,0,1,0,1,1,1,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]

class PacMan:
    def __init__(self):
        self.x = 9
        self.y = 15
        self.direction = [0, 0]
        self.radius = CELL_SIZE // 2 - 2
        self.mouth_angle = 0
        self.mouth_change = 5
        self.score = 0
        self.blocks_to_move = 0
        self.target_position = None
        
    def set_movement(self, direction, blocks):
        self.direction = direction
        self.blocks_to_move = blocks
        self.target_position = [
            self.x + (direction[0] * blocks),
            self.y + (direction[1] * blocks)
        ]
        
    def move(self):
        if self.blocks_to_move > 0:
            new_x = self.x + self.direction[0]
            new_y = self.y + self.direction[1]
            
            if (0 <= new_x < GRID_WIDTH and 
                0 <= new_y < GRID_HEIGHT and 
                MAZE[new_y][new_x] != 1):
                
                if MAZE[new_y][new_x] == 0:
                    MAZE[new_y][new_x] = 2
                    self.score += 10
                elif MAZE[new_y][new_x] == 3:
                    MAZE[new_y][new_x] = 2
                    self.score += 50
                
                self.x = new_x
                self.y = new_y
                self.blocks_to_move -= 1
            else:
                self.blocks_to_move = 0
                
            if self.blocks_to_move == 0:
                self.direction = [0, 0]
    
    def draw(self):
        # Update mouth animation
        self.mouth_angle += self.mouth_change
        if self.mouth_angle >= 45 or self.mouth_angle <= 0:
            self.mouth_change = -self.mouth_change
            
        # Calculate center position
        center_x = self.x * CELL_SIZE + CELL_SIZE // 2
        center_y = self.y * CELL_SIZE + CELL_SIZE // 2
        
        # Draw Pac-Man body
        pygame.draw.circle(screen, YELLOW, (center_x, center_y), self.radius)
        
        # Draw mouth
        if any(self.direction):  # Only draw mouth if moving
            # Calculate mouth angles based on direction
            if self.direction == [1, 0]:  # Right
                start_angle = -self.mouth_angle
                end_angle = self.mouth_angle
            elif self.direction == [-1, 0]:  # Left
                start_angle = 180 - self.mouth_angle
                end_angle = 180 + self.mouth_angle
            elif self.direction == [0, -1]:  # Up
                start_angle = 90 - self.mouth_angle
                end_angle = 90 + self.mouth_angle
            else:  # Down
                start_angle = 270 - self.mouth_angle
                end_angle = 270 + self.mouth_angle
            
            # Convert angles to radians and calculate mouth points
            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)
            
            # Draw mouth (black triangle)
            pygame.draw.polygon(screen, BLACK, [
                (center_x, center_y),
                (center_x + self.radius * math.cos(start_rad),
                 center_y - self.radius * math.sin(start_rad)),
                (center_x + self.radius * math.cos(end_rad),
                 center_y - self.radius * math.sin(end_rad))
            ])

def draw_maze():
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = MAZE[y][x]
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            
            if cell == 1:  # Wall
                pygame.draw.rect(screen, BLUE, rect)
            elif cell == 0:  # Dot
                pygame.draw.circle(screen, WHITE,
                                 (x * CELL_SIZE + CELL_SIZE // 2,
                                  y * CELL_SIZE + CELL_SIZE // 2),
                                 2)
            elif cell == 3:  # Power pellet
                pygame.draw.circle(screen, WHITE,
                                 (x * CELL_SIZE + CELL_SIZE // 2,
                                  y * CELL_SIZE + CELL_SIZE // 2),
                                 6)

def voice_command_listener():
    recognizer = sr.Recognizer()
    
    # Optimize recognition settings
    recognizer.energy_threshold = 1000
    recognizer.dynamic_energy_threshold = False
    
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Ready for voice commands!")
    
    while True:
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=0.5)
                command = recognizer.recognize_google(audio).lower()
                print(f"Recognized: {command}")
                
                # Simplified command processing
                if "up" in command:
                    command_queue.put(([0, -1], 1))
                elif "down" in command:
                    command_queue.put(([0, 1], 1))
                elif "left" in command:
                    command_queue.put(([-1, 0], 1))
                elif "right" in command:
                    command_queue.put(([1, 0], 1))
                elif "stop" in command or "quit" in command:
                    command_queue.put("QUIT")
                    break
            except sr.UnknownValueError:
                pass  # Silently continue if command not understood
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print(f"Error: {e}")

def main():
    voice_thread = threading.Thread(target=voice_command_listener, daemon=True)
    voice_thread.start()
    
    pacman = PacMan()
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    pacman.set_movement([0, -1], 1)
                elif event.key == pygame.K_DOWN:
                    pacman.set_movement([0, 1], 1)
                elif event.key == pygame.K_LEFT:
                    pacman.set_movement([-1, 0], 1)
                elif event.key == pygame.K_RIGHT:
                    pacman.set_movement([1, 0], 1)
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        if not command_queue.empty():
            command = command_queue.get()
            if command == "QUIT":
                running = False
            else:
                direction, blocks = command
                pacman.set_movement(direction, blocks)
        
        pacman.move()
        
        screen.fill(BLACK)
        draw_maze()
        pacman.draw()
        
        font = pygame.font.Font(None, 36)
        score_text = f"Score: {pacman.score}"
        text_surface = font.render(score_text, True, WHITE)
        screen.blit(text_surface, (10, 10))
        
        pygame.display.flip()
        clock.tick(60)  # 60 FPS for smooth movement
    
    pygame.quit()

if __name__ == "__main__":
    main()