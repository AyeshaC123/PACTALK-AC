import pygame
import speech_recognition as sr
import threading
import time
from queue import Queue
import math
from enum import Enum

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

# Game States - properly defined enum
class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"

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
        
    def move(self):
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
    
    def draw(self):
        self.mouth_angle += self.mouth_change
        if self.mouth_angle >= 45 or self.mouth_angle <= 0:
            self.mouth_change = -self.mouth_change
        
        center = (self.x * CELL_SIZE + CELL_SIZE // 2, 
                 self.y * CELL_SIZE + CELL_SIZE // 2)
        
        start_angle = self.mouth_angle
        end_angle = 360 - self.mouth_angle
        
        if self.direction[0] == 1:
            rotation = 0
        elif self.direction[0] == -1:
            rotation = 180
        elif self.direction[1] == -1:
            rotation = 90
        elif self.direction[1] == 1:
            rotation = 270
        else:
            rotation = 0
        
        pygame.draw.arc(screen, YELLOW,
                       (center[0] - self.radius, 
                        center[1] - self.radius,
                        self.radius * 2, 
                        self.radius * 2),
                       math.radians(rotation + start_angle),
                       math.radians(rotation + end_angle),
                       self.radius)




def draw_maze():
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = MAZE[y][x]
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            
            if cell == 1:
                pygame.draw.rect(screen, BLUE, rect)
            elif cell == 0:
                pygame.draw.circle(screen, WHITE,
                                 (x * CELL_SIZE + CELL_SIZE // 2,
                                  y * CELL_SIZE + CELL_SIZE // 2), 3)
            elif cell == 3:
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
    instruction = font_small.render("Say 'Resume' to continue", True, WHITE)
    instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(instruction, instruction_rect)

def draw_start_screen():
    screen.fill(BLACK)
    title_font = pygame.font.Font(None, 53)
    instruction_font = pygame.font.Font(None, 36)
    
    # Draw title
    title_text = "Voice-Controlled Pac-Man"
    title_surface = title_font.render(title_text, True, YELLOW)
    title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    screen.blit(title_surface, title_rect)
    
    # Draw instructions
    instructions = [
        "Voice Commands:",
        '"Start" - Begin game',
        '"Move up/down/left/right" - Control Pacman',
        '"Pause" - Pause game',
        '"Resume" - Resume game',
        '"Stop" or "Quit" - Exit game',
        "",
        "Press Enter or say 'Start' to begin"
    ]
    
    for i, line in enumerate(instructions):
        text_surface = instruction_font.render(line, True, WHITE)
        text_rect = text_surface.get_rect(
            center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + i * 40)
        )
        screen.blit(text_surface, text_rect)


def voice_command_listener():
    recognizer = sr.Recognizer()
    running = True
    
    while running:
        try:
            with sr.Microphone() as source:
                if not hasattr(voice_command_listener, 'noise_adjusted'):
                    print("Adjusting for ambient noise...")
                    recognizer.adjust_for_ambient_noise(source, duration=2)
                    voice_command_listener.noise_adjusted = True
                    print("Ready for voice commands!")
                
                try:
                    print("Listening...")
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=2)
                    try:
                        command = recognizer.recognize_google(audio).lower()
                        print(f"Recognized: {command}")
                        
                        if "start" in command:
                            command_queue.put(("STATE", GameState.PLAYING))
                        elif "pause" in command:
                            command_queue.put(("STATE", GameState.PAUSED))
                        elif "resume" in command:
                            command_queue.put(("STATE", GameState.PLAYING))
                        elif "move up" in command:
                            command_queue.put(("MOVE", [0, -1]))
                        elif "move down" in command:
                            command_queue.put(("MOVE", [0, 1]))
                        elif "move left" in command:
                            command_queue.put(("MOVE", [-1, 0]))
                        elif "move right" in command:
                            command_queue.put(("MOVE", [1, 0]))
                        elif "stop" in command or "quit" in command:
                            command_queue.put(("QUIT", None))
                            running = False
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        print(f"Could not request results; {e}")
                        time.sleep(1)
                        continue
                except sr.WaitTimeoutError:
                    continue
                    
        except Exception as e:
            print(f"Error in voice recognition: {e}")
            time.sleep(1)
            continue

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
    instruction = font_small.render("Say 'Resume' to continue", True, WHITE)
    instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(instruction, instruction_rect)

def main():
    # Start voice command thread
    voice_thread = threading.Thread(target=voice_command_listener, daemon=True)
    voice_thread.start()
    
    pacman = PacMan()
    clock = pygame.time.Clock()
    running = True
    game_state = GameState.MENU
    last_error_check = time.time()
    
    while running:
        current_time = time.time()
        
        # Check if voice thread is still alive
        if current_time - last_error_check > 5:
            if not voice_thread.is_alive():
                print("Voice recognition thread died, restarting...")
                voice_thread = threading.Thread(target=voice_command_listener, daemon=True)
                voice_thread.start()
            last_error_check = current_time
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_state == GameState.PLAYING:
                    if event.key == pygame.K_UP:
                        pacman.direction = [0, -1]
                    elif event.key == pygame.K_DOWN:
                        pacman.direction = [0, 1]
                    elif event.key == pygame.K_LEFT:
                        pacman.direction = [-1, 0]
                    elif event.key == pygame.K_RIGHT:
                        pacman.direction = [1, 0]
                    elif event.key == pygame.K_p:
                        game_state = GameState.PAUSED
                elif game_state == GameState.MENU and event.key == pygame.K_RETURN:
                    game_state = GameState.PLAYING
                elif game_state == GameState.PAUSED and event.key == pygame.K_p:
                    game_state = GameState.PLAYING
                
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Handle voice commands
        if not command_queue.empty():
            command_type, command_data = command_queue.get()
            if command_type == "QUIT":
                running = False
            elif command_type == "STATE":
                game_state = command_data
            elif command_type == "MOVE" and game_state == GameState.PLAYING:
                pacman.direction = command_data
        
        # Update game state
        screen.fill(BLACK)
        
        if game_state == GameState.MENU:
            draw_start_screen()
        elif game_state == GameState.PLAYING:
            pacman.move()
            draw_maze()
            pacman.draw()
            
            # Draw score
            font = pygame.font.Font(None, 36)
            score_text = f"Score: {pacman.score}"
            text_surface = font.render(score_text, True, WHITE)
            screen.blit(text_surface, (10, 10))
        elif game_state == GameState.PAUSED:
            # Draw the game state in background
            draw_maze()
            pacman.draw()
            # Overlay pause screen
            draw_pause_screen()

        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()

if __name__ == "__main__":
    main()