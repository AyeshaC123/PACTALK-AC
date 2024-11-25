import pygame
import speech_recognition as sr
import threading
import time
from queue import Queue
import math
from enum import Enum
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import threading
from queue import Queue
from collections import deque

import os
print("Current working directory:", os.getcwd())

from vosk import Model
model = Model(lang="en-us")  # Loads a pre-downloaded compact model

custom_vocabulary = [
    "up", "down", "left", "right", 
    "pause", "resume", "quit", "stop", "start",
    "one", "two", "three", "four", "five", 
    "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen",
    "fifteen", "sixteen", "seventeen", "eighteen",
    "nineteen", "twenty"
]
import json
grammar = json.dumps(custom_vocabulary)

# Initialize Pygame
pygame.init()

# Constants 
HISTORY_WIDTH = 200  # Width of command history panel
CELL_SIZE = 30
GRID_WIDTH = 19
GRID_HEIGHT = 20
GAME_SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
GAME_SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE
SCREEN_WIDTH = GAME_SCREEN_WIDTH + HISTORY_WIDTH  # Total width including history panel
SCREEN_HEIGHT = GAME_SCREEN_HEIGHT

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (50, 50, 50)

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Voice-Controlled Pac-Man")

# Command queue for voice inputs
command_queue = Queue()
mic_status_queue = Queue()

# Game States
class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"

# Command History
class CommandHistory:
    def __init__(self, max_commands=15):
        self.commands = deque(maxlen=max_commands)
        self.font = pygame.font.Font(None, 24)
    
    def add_command(self, command):
        timestamp = time.strftime("%H:%M:%S")
        self.commands.append(f"[{timestamp}] {command}")
    
    def draw(self):
        # Draw background for history panel
        history_rect = pygame.Rect(0, 0, HISTORY_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(screen, GRAY, history_rect)
        pygame.draw.line(screen, WHITE, (HISTORY_WIDTH-1, 0), (HISTORY_WIDTH-1, SCREEN_HEIGHT), 2)
        
        # Draw title
        title = self.font.render("Command History", True, WHITE)
        title_rect = title.get_rect(centerx=HISTORY_WIDTH//2, top=10)
        screen.blit(title, title_rect)
        pygame.draw.line(screen, WHITE, (10, 40), (HISTORY_WIDTH-10, 40), 1)
        
        # Draw commands
        y_offset = 50
        for command in reversed(self.commands):
            text = self.font.render(command, True, WHITE)
            # Wrap text if too long
            if text.get_width() > HISTORY_WIDTH - 20:
                words = command.split()
                current_line = words[0]
                lines = []
                for word in words[1:]:
                    test_line = current_line + " " + word
                    test_surface = self.font.render(test_line, True, WHITE)
                    if test_surface.get_width() <= HISTORY_WIDTH - 20:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                lines.append(current_line)
                for line in lines:
                    text = self.font.render(line, True, WHITE)
                    screen.blit(text, (10, y_offset))
                    y_offset += 25
            else:
                screen.blit(text, (10, y_offset))
                y_offset += 25
                

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

class Ghost:
    def __init__(self, x, y, image_path, target=None):
        self.x_pos = x * CELL_SIZE
        self.y_pos = y * CELL_SIZE
        self.image = pygame.transform.scale(pygame.image.load(image_path), (CELL_SIZE, CELL_SIZE))
        self.direction = 0
        self.speed = 2
        self.turns = [False, False, False, False]
        self.target = target

    def calculate_turns(self):
        grid_x = self.x_pos // CELL_SIZE
        grid_y = self.y_pos // CELL_SIZE
        self.turns = [False, False, False, False]

        if MAZE[grid_y][grid_x + 1] != 1:
            self.turns[0] = True
        if MAZE[grid_y][grid_x - 1] != 1:
            self.turns[1] = True
        if MAZE[grid_y - 1][grid_x] != 1:
            self.turns[2] = True
        if MAZE[grid_y + 1][grid_x] != 1:
            self.turns[3] = True

    def move_blinky(self):
        if self.x_pos % CELL_SIZE == 0 and self.y_pos % CELL_SIZE == 0:
            grid_x = self.x_pos // CELL_SIZE
            grid_y = self.y_pos // CELL_SIZE
            target_x = self.target[0]
            target_y = self.target[1]

            self.calculate_turns()

            moves = []
            if self.turns[0]:
                moves.append(((grid_x + 1, grid_y), (target_x - (grid_x + 1))**2 + (target_y - grid_y)**2, 0))
            if self.turns[1]:
                moves.append(((grid_x - 1, grid_y), (target_x - (grid_x - 1))**2 + (target_y - grid_y)**2, 1))
            if self.turns[2]:
                moves.append(((grid_x, grid_y - 1), (target_x - grid_x)**2 + (target_y - (grid_y - 1))**2, 2))
            if self.turns[3]:
                moves.append(((grid_x, grid_y + 1), (target_x - grid_x)**2 + (target_y - (grid_y + 1))**2, 3))

            if moves:
                best_move = min(moves, key=lambda x: x[1])
                self.direction = best_move[2]

        if self.direction == 0:
            self.x_pos += self.speed
        elif self.direction == 1:
            self.x_pos -= self.speed
        elif self.direction == 2:
            self.y_pos -= self.speed
        elif self.direction == 3:
            self.y_pos += self.speed

        if self.x_pos < 0:
            self.x_pos = GAME_SCREEN_WIDTH - CELL_SIZE
        elif self.x_pos >= GAME_SCREEN_WIDTH:
            self.x_pos = 0

    def draw(self):
        screen.blit(self.image, (self.x_pos + HISTORY_WIDTH, self.y_pos))

class PacMan:
    def __init__(self):
        self.x = 9
        self.y = 15
        self.direction = [0, 0]
        self.radius = CELL_SIZE // 2 - 2
        self.mouth_angle = 0
        self.mouth_change = 5
        self.score = 0
        self.speed = 2
        self.step_accumulator = 0

    def move(self):
        self.step_accumulator += self.speed
        if self.step_accumulator >= 1:
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
            self.step_accumulator -= 1

    def move_multiple(self, direction, steps):
        remaining_steps = steps
        while remaining_steps > 0:
            new_x = self.x + direction[0]
            new_y = self.y + direction[1]
            if (not 0 <= new_x < GRID_WIDTH or 
                not 0 <= new_y < GRID_HEIGHT or 
                MAZE[new_y][new_x] == 1):
                break
            if MAZE[new_y][new_x] == 0:
                MAZE[new_y][new_x] = 2
                self.score += 10
            elif MAZE[new_y][new_x] == 3:
                MAZE[new_y][new_x] = 2
                self.score += 50
            self.x = new_x
            self.y = new_y
            remaining_steps -= 1
        self.direction = [0, 0]

    def draw(self):
        self.mouth_angle += self.mouth_change
        if self.mouth_angle >= 45 or self.mouth_angle <= 0:
            self.mouth_change = -self.mouth_change

        center = (self.x * CELL_SIZE + CELL_SIZE // 2 + HISTORY_WIDTH,
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
            rect = pygame.Rect(x * CELL_SIZE + HISTORY_WIDTH, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if cell == 1:
                pygame.draw.rect(screen, BLUE, rect)
            elif cell == 0:
                pygame.draw.circle(screen, WHITE,
                                 (x * CELL_SIZE + CELL_SIZE // 2 + HISTORY_WIDTH,
                                  y * CELL_SIZE + CELL_SIZE // 2), 3)
            elif cell == 3:
                pygame.draw.circle(screen, WHITE,
                                 (x * CELL_SIZE + CELL_SIZE // 2 + HISTORY_WIDTH,
                                  y * CELL_SIZE + CELL_SIZE // 2), 8)

def draw_pause_screen():
    overlay = pygame.Surface((GAME_SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(128)
    screen.blit(overlay, (HISTORY_WIDTH, 0))
    
    font = pygame.font.Font(None, 74)
    text = font.render("PAUSED", True, WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)) # calculates the spot on screen
    screen.blit(text, text_rect) # draws it there
    #  renders the instruction text
    font_small = pygame.font.Font(None, 36)
    instruction = font_small.render("Say 'Resume' to continue", True, WHITE)
    instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(instruction, instruction_rect)

def draw_microphone_indicator(is_listening):
    mic_size = 30
    mic_x = 20
    mic_y = SCREEN_HEIGHT - 35
    
    # Draw background circle
    color = GREEN if is_listening else RED # if listening then green otherwise red
    pygame.draw.circle(screen, color, (mic_x, mic_y), 15)
    
    # Draw microphone icon in white
    # pygame.draw.rect(screen, WHITE, (mic_x - 3, mic_y - 8, 6, 12), border_radius=3)
    # pygame.draw.rect(screen, WHITE, (mic_x - 6, mic_y - 8, 12, 3), border_radius=1)
    
    # Base stand
    if is_listening:
        # Draw "sound waves" when active
        for i in range(1, 4):
            pygame.draw.arc(screen, WHITE,
                          (mic_x - 8 - i*4, mic_y - 8 - i*4, 
                           16 + i*8, 16 + i*8),
                          math.radians(-45), math.radians(225), 1)
    
    # Status text indicating whether it's listening or idle
    font = pygame.font.Font(None, 24)
    status_text = "Listening..." if is_listening else "Idle"
    text_surface = font.render(status_text, True, WHITE)
    screen.blit(text_surface, (mic_x + 20, mic_y - 10))

def draw_start_screen():
    screen.fill(BLACK)
    title_font = pygame.font.Font(None, 53)
    instruction_font = pygame.font.Font(None, 36)
    
    # Calculate the center of the game area (excluding command history panel)
    game_center_x = HISTORY_WIDTH + (GAME_SCREEN_WIDTH // 2)
    
    # Draw title
    title_text = "Voice-Controlled Pac-Man"
    title_surface = title_font.render(title_text, True, YELLOW)
    title_rect = title_surface.get_rect(center=(game_center_x, SCREEN_HEIGHT // 4))
    screen.blit(title_surface, title_rect)
    
    # Instructions
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
    
    # Calculate y-offset starting point
    start_y = title_rect.bottom + 30  # Leave space below the title
    line_spacing = 40  # Spacing between lines of text
    
    for i, line in enumerate(instructions):
        text_surface = instruction_font.render(line, True, WHITE)
        text_rect = text_surface.get_rect(center=(game_center_x, start_y + i * line_spacing))
        screen.blit(text_surface, text_rect)



def word_to_number(word):
    """Convert word numbers to integers"""
    number_dict = {
        'zero': 0, 'one': 1, 'two': 2, 'to': 2, 'three': 3, 'four': 4, 'for': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
        'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
        'fourteen': 14, 'fifteen': 15, 'sixteen': 16,
        'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
    }
    return number_dict.get(word.lower(), None)

def calibrate_microphone(p, rate=16000, channels=1, duration=2):
    """Calibrates the microphone by capturing background noise."""
    print("Calibrating microphone... Please stay quiet.")
    stream = p.open(format=pyaudio.paInt16, channels=channels, rate=rate, input=True, frames_per_buffer=8000)
    stream.start_stream()

    # Collect audio for calibration
    frames = []
    for _ in range(int(rate / 8000 * duration)):
        data = stream.read(8000, exception_on_overflow=False)
        frames.append(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    print("Calibration complete.")

    # Return background noise as raw data
    return b"".join(frames)

def voice_command_listener():
    recognizer = KaldiRecognizer(model, 16000, grammar) # processes 16kHz audio using the pre-loaded language model
    p = pyaudio.PyAudio() 
    background_noise = calibrate_microphone(p)
    print("Background noise calibration complete.")
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream() # continuous listening

    print("Vosk Voice Command Listener is active...")
    mic_status_queue.put(True)  # Indicate that the microphone is active

    try:
        while True:
            data = stream.read(4000, exception_on_overflow=False) # read and process chunk of audio
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                if "text" in result:
                    command = result["text"]
                    print(f"Recognized: {command}")
                    # Split command into words
                    words = command.split()
                    
                    # Parse commands
                    if "start" in command:
                        command_queue.put(("STATE", GameState.PLAYING))
                    elif "pause" in command: # changes game state to paused and stops movement
                        command_queue.put(("STATE", GameState.PAUSED))
                    elif "resume" in command:
                        command_queue.put(("STATE", GameState.PLAYING))
                    elif "stop" in command or "quit" in command:
                        command_queue.put(("QUIT", None))
                        running = False
                    # Handle movement commands with steps
                    elif any(direction in words for direction in ["up", "down", "left", "right", "write"]):
                        # Get direction
                        if "up" in words:
                            direction = [0, -1]
                        elif "down" in words:
                            direction = [0, 1]
                        elif "left" in words:
                            direction = [-1, 0]
                        else:  # right
                            direction = [1, 0]
                        
                        # Look for number in words (either digit or word form)
                        steps = 1  # default to 1 if no number given
                        for word in words:
                            # Check if it's a digit
                            if word.isdigit():
                                steps = int(word)
                                break
                            # Check if it's a word number
                            number = word_to_number(word)
                            if number is not None:
                                steps = number
                                break
                        
                        print(f"Moving {steps} steps in direction {direction}")  # Debug print
                        
                        if steps == 1:
                            command_queue.put(("MOVE", direction))  # Use old movement for single steps
                        else:
                            command_queue.put(("MOVE_MULTIPLE", (direction, steps)))               
    finally:
        mic_status_queue.put(False)  # Indicate that the microphone is no longer active
        stream.stop_stream()
        stream.close()
        p.terminate()

def main():
    voice_thread = threading.Thread(target=voice_command_listener, daemon=True)
    voice_thread.start()
    
    pacman = PacMan()
    clock = pygame.time.Clock()
    running = True
    game_state = GameState.MENU
    is_listening = False
    last_error_check = time.time()
    
    # Initialize command history
    command_history = CommandHistory()

    blinky = Ghost(9, 7, "assets/ghost_images/red.png", target=[pacman.x, pacman.y])

    while running:
        current_time = time.time()
        
        # Check if voice thread is still alive
        if current_time - last_error_check > 5:
            if not voice_thread.is_alive():
                print("Voice recognition thread died, restarting...")
                voice_thread = threading.Thread(target=voice_command_listener, daemon=True)
                voice_thread.start()
            last_error_check = current_time
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game_state == GameState.MENU and event.key == pygame.K_RETURN:
                    game_state = GameState.PLAYING
                    command_history.add_command("Game Started")
                elif game_state == GameState.PLAYING:
                    if event.key == pygame.K_UP:
                        pacman.direction = [0, -1]
                        command_history.add_command("Move Up")
                    elif event.key == pygame.K_DOWN:
                        pacman.direction = [0, 1]
                        command_history.add_command("Move Down")
                    elif event.key == pygame.K_LEFT:
                        pacman.direction = [-1, 0]
                        command_history.add_command("Move Left")
                    elif event.key == pygame.K_RIGHT:
                        pacman.direction = [1, 0]
                        command_history.add_command("Move Right")
                    elif event.key == pygame.K_p:
                        game_state = GameState.PAUSED
                        command_history.add_command("Game Paused")
                elif game_state == GameState.PAUSED and event.key == pygame.K_p:
                    game_state = GameState.PLAYING
                    command_history.add_command("Game Resumed")
        
        # Handle voice commands
        if not command_queue.empty():
            command_type, command_data = command_queue.get()
            if command_type == "QUIT":
                command_history.add_command("Game Quit")
                running = False
            elif command_type == "STATE":
                if command_data == GameState.PLAYING:
                    command_history.add_command("Game Started" if game_state == GameState.MENU else "Game Resumed")
                elif command_data == GameState.PAUSED:
                    command_history.add_command("Game Paused")
                game_state = command_data
            elif command_type == "MOVE" and game_state == GameState.PLAYING:
                direction_text = ""
                if command_data == [0, -1]:
                    direction_text = "Move Up"
                elif command_data == [0, 1]:
                    direction_text = "Move Down"
                elif command_data == [-1, 0]:
                    direction_text = "Move Left"
                elif command_data == [1, 0]:
                    direction_text = "Move Right"
                command_history.add_command(direction_text)
                pacman.direction = command_data
            elif command_type == "MOVE_MULTIPLE" and game_state == GameState.PLAYING:
                direction, steps = command_data
                direction_text = ""
                if direction == [0, -1]:
                    direction_text = f"Move Up {steps} steps"
                elif direction == [0, 1]:
                    direction_text = f"Move Down {steps} steps"
                elif direction == [-1, 0]:
                    direction_text = f"Move Left {steps} steps"
                elif direction == [1, 0]:
                    direction_text = f"Move Right {steps} steps"
                command_history.add_command(direction_text)
                pacman.move_multiple(direction, steps)
        
        # Update game state
        if game_state == GameState.PLAYING:
            pacman.move()

        # Check for microphone status updates
        while not mic_status_queue.empty():
            is_listening = mic_status_queue.get()
        
        # Draw screen
        screen.fill(BLACK)
        
        if game_state == GameState.MENU:
            draw_start_screen()
        elif game_state == GameState.PLAYING:
            draw_maze()
            blinky.target = [pacman.x, pacman.y]
            blinky.move_blinky()
            blinky.draw()
            
            if blinky.x_pos // CELL_SIZE == pacman.x and blinky.y_pos // CELL_SIZE == pacman.y:
                command_history.add_command("Game Over - Caught by Blinky!")
                font = pygame.font.Font(None, 74)
                text = font.render("GAME OVER", True, RED)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                screen.blit(text, text_rect)
                pygame.display.flip()
                pygame.time.wait(3000)
                running = False

            pacman.draw()
            
            # Draw score
            font = pygame.font.Font(None, 36)
            score_text = f"Score: {pacman.score}"
            text_surface = font.render(score_text, True, WHITE)
            screen.blit(text_surface, (10, 10))
        elif game_state == GameState.PAUSED: #dont call pacman.move
            # Draw the game state in background
            draw_maze()
            pacman.draw()
            draw_pause_screen()
        
        # Draw command history and microphone indicator
        command_history.draw()
        draw_microphone_indicator(is_listening)

        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()

if __name__ == "__main__":
    main()