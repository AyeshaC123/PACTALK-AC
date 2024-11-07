# Pacman game

import pygame
import speech_recognition as sr
import threading
import time
from queue import Queue
import math

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
# 0 = empty path with dot
# 1 = wall
# 2 = empty path without dot
# 3 = power pellet
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
        
    def move(self):
        new_x = self.x + self.direction[0]
        new_y = self.y + self.direction[1]
        
        # Check if the new position is within bounds and not a wall
        if (0 <= new_x < GRID_WIDTH and 
            0 <= new_y < GRID_HEIGHT and 
            MAZE[new_y][new_x] != 1):
            
            # Collect dot
            if MAZE[new_y][new_x] == 0:
                MAZE[new_y][new_x] = 2  # Remove dot
                self.score += 10
            elif MAZE[new_y][new_x] == 3:  # Power pellet
                MAZE[new_y][new_x] = 2
                self.score += 50
            
            self.x = new_x
            self.y = new_y
    
    def draw(self):
        # Animate mouth
        self.mouth_angle += self.mouth_change
        if self.mouth_angle >= 45 or self.mouth_angle <= 0:
            self.mouth_change = -self.mouth_change
        
        # Calculate center position
        center = (self.x * CELL_SIZE + CELL_SIZE // 2, 
                 self.y * CELL_SIZE + CELL_SIZE // 2)
        
        # Draw Pac-Man body
        start_angle = self.mouth_angle
        end_angle = 360 - self.mouth_angle
        
        # Rotate based on direction
        if self.direction[0] == 1:  # Right
            rotation = 0
        elif self.direction[0] == -1:  # Left
            rotation = 180
        elif self.direction[1] == -1:  # Up
            rotation = 90
        elif self.direction[1] == 1:  # Down
            rotation = 270
        else:
            rotation = 0
        
        # Draw pac-man
        pygame.draw.arc(screen, YELLOW,
                       (center[0] - self.radius, 
                        center[1] - self.radius,
                        self.radius * 2, 
                        self.radius * 2),
                       math.radians(rotation + start_angle),
                       math.radians(rotation + end_angle),
                       self.radius)

# iterates over the maze array to draw walls, dots, and power pellets at corresponding positions
def draw_maze():
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = MAZE[y][x]
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE) # calculates the coordinate to place the square 
            
            if cell == 1:  # Wall
                pygame.draw.rect(screen, BLUE, rect)
            elif cell == 0:  # Dot
                pygame.draw.circle(screen, WHITE,
                                 (x * CELL_SIZE + CELL_SIZE // 2,
                                  y * CELL_SIZE + CELL_SIZE // 2), 3) # radius 3 for smaller dot
            elif cell == 3:  # Power pellet
                pygame.draw.circle(screen, WHITE,
                                 (x * CELL_SIZE + CELL_SIZE // 2,
                                  y * CELL_SIZE + CELL_SIZE // 2), 8) # radius 8 for bigger circle for pellet

def voice_command_listener():
    recognizer = sr.Recognizer()
    
    # Adjust for ambient noise
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Ready for voice commands!")
    
    while True:
        with sr.Microphone() as source:
            print("Listening for command...")
            try:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=2)
                command = recognizer.recognize_google(audio).lower()
                print(f"Recognized: {command}")
                
                if "up" in command:
                    command_queue.put([0, -1])
                elif "down" in command:
                    command_queue.put([0, 1])
                elif "left" in command:
                    command_queue.put([-1, 0])
                elif "right" in command:
                    command_queue.put([1, 0])
                elif "stop" in command or "quit" in command:
                    command_queue.put("QUIT")
                    break
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print(f"Error: {e}")

def main():
    # Start voice command thread
    voice_thread = threading.Thread(target=voice_command_listener, daemon=True)
    voice_thread.start()
    
    pacman = PacMan()
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # Handle events and update game state
        for event in pygame.event.get(): # game loop
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    pacman.direction = [0, -1]
                elif event.key == pygame.K_DOWN:
                    pacman.direction = [0, 1]
                elif event.key == pygame.K_LEFT:
                    pacman.direction = [-1, 0]
                elif event.key == pygame.K_RIGHT:
                    pacman.direction = [1, 0]
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        # Check for voice commands
        if not command_queue.empty():
            command = command_queue.get()
            if command == "QUIT":
                running = False
            else:
                pacman.direction = command
        
        # Update game state
        pacman.move()
        
        # Draw screen with maze and pacman
        screen.fill(BLACK)
        draw_maze()
        pacman.draw()
        
        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = f"Score: {pacman.score}"
        text_surface = font.render(score_text, True, WHITE)
        screen.blit(text_surface, (10, 10))

        pygame.display.flip() # Updates game state and redraw graphics 
        clock.tick(30) # Run at 30 frames per second (run at consistent speed)
    
    pygame.quit()

if __name__ == "__main__":
    main()