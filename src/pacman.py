import pygame
import speech_recognition as sr
import threading
import time
from queue import Queue
import math

# Initialize Pygame
pygame.init()

# Constants 
CELL_SIZE = 30 # pixels
GRID_WIDTH = 19 # number of cells horizontally
GRID_HEIGHT = 21 # number of cells vertically
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Voice-Controlled Pac-Man")

# Command queue for voice inputs
command_queue = Queue()
mic_status_queue = Queue()

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
                                  y * CELL_SIZE + CELL_SIZE // 2), 8)

def draw_pause_screen():
    # Create semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(128)
    screen.blit(overlay, (0, 0))
    
    # Draw "PAUSED" text
    font = pygame.font.Font(None, 74)
    text = font.render("PAUSED", True, WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(text, text_rect)
    
    # Draw instruction text
    font_small = pygame.font.Font(None, 36)
    instruction = font_small.render("Say 'Resume game' to continue", True, WHITE)
    instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(instruction, instruction_rect)
def draw_microphone_indicator(is_listening):
    # Define microphone icon dimensions and position
    mic_size = 30
    mic_x = 20
    mic_y = SCREEN_HEIGHT - 35
    
    # Draw microphone base (circle)
    color = GREEN if is_listening else RED
    pygame.draw.circle(screen, color, (mic_x, mic_y), 10)
    
    # Draw microphone stem
    pygame.draw.rect(screen, color, 
                    (mic_x - 3, mic_y - 12, 6, 15))
    
    # Draw microphone top
    pygame.draw.rect(screen, color,
                    (mic_x - 8, mic_y - 12, 16, 4))
    
    # Add status text
    font = pygame.font.Font(None, 24)
    status_text = "Listening..." if is_listening else "Idle"
    text_surface = font.render(status_text, True, WHITE)
    screen.blit(text_surface, (mic_x + 20, mic_y - 10))

def voice_command_listener():
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Ready for voice commands!")
    
    while True:
        with sr.Microphone() as source:
            print("Listening for command...")
            mic_status_queue.put(True)  # Signal that microphone is listening
            try:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=2)
                command = recognizer.recognize_google(audio).lower()
                print(f"Recognized: {command}")
                
                if "move up" in command:
                    command_queue.put(("MOVE", [0, -1]))
                elif "move down" in command:
                    command_queue.put(("MOVE", [0, 1]))
                elif "move left" in command:
                    command_queue.put(("MOVE", [-1, 0]))
                elif "move right" in command:
                    command_queue.put(("MOVE", [1, 0]))
                elif "pause" in command:
                    command_queue.put(("PAUSE", None))
                elif "resume game" in command:
                    command_queue.put(("RESUME", None))
                elif "stop" in command or "quit" in command:
                    command_queue.put(("QUIT", None))
                    break
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                print(f"Error: {e}")
            finally:
                mic_status_queue.put(False)  # Signal that microphone is not listening

def main():
    voice_thread = threading.Thread(target=voice_command_listener, daemon=True)
    voice_thread.start()
    
    pacman = PacMan()
    clock = pygame.time.Clock()
    running = True
    paused = False
    is_listening = False
    
    while running:
        # Handle events and update game state
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p:
                    paused = not paused
                elif not paused:
                    if event.key == pygame.K_UP:
                        pacman.direction = [0, -1]
                    elif event.key == pygame.K_DOWN:
                        pacman.direction = [0, 1]
                    elif event.key == pygame.K_LEFT:
                        pacman.direction = [-1, 0]
                    elif event.key == pygame.K_RIGHT:
                        pacman.direction = [1, 0]
        
        # Check for voice commands
        if not command_queue.empty():
            command_type, command_data = command_queue.get()
            if command_type == "QUIT":
                running = False
            elif command_type == "PAUSE":
                paused = True
            elif command_type == "RESUME":
                paused = False
            elif command_type == "MOVE" and not paused:
                pacman.direction = command_data
        
        # Check for microphone status updates
        while not mic_status_queue.empty():
            is_listening = mic_status_queue.get()
        
        # Update game state only if not paused
        if not paused:
            pacman.move()
        
        # Draw screen
        screen.fill(BLACK)
        draw_maze()
        pacman.draw()
        
        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = f"Score: {pacman.score}"
        text_surface = font.render(score_text, True, WHITE)
        screen.blit(text_surface, (10, 10))
        
        # Draw microphone indicator
        draw_microphone_indicator(is_listening)
        
        # Draw pause screen if game is paused
        if paused:
            draw_pause_screen()
        
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()

if __name__ == "__main__":
    main()