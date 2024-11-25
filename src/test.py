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
import os
from collections import deque

# Constants 
HISTORY_WIDTH = 200  # Width of command history panel
CELL_SIZE = 30
GRID_WIDTH = 19
GRID_HEIGHT = 21
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

# Initialize screen with new dimensions
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Voice-Controlled Pac-Man")

# Command history
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

# Modify the draw functions to account for the history panel offset
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

class Ghost:
    def __init__(self, x, y, image_path, target=None):
        self.x_pos = x * CELL_SIZE
        self.y_pos = y * CELL_SIZE
        self.image = pygame.transform.scale(pygame.image.load(image_path), (CELL_SIZE, CELL_SIZE))
        self.direction = 0
        self.speed = 2
        self.turns = [False, False, False, False]
        self.target = target

    def draw(self):
        screen.blit(self.image, (self.x_pos + HISTORY_WIDTH, self.y_pos))

def draw_pause_screen():
    overlay = pygame.Surface((GAME_SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(128)
    screen.blit(overlay, (HISTORY_WIDTH, 0))
    
    font = pygame.font.Font(None, 74)
    text = font.render("PAUSED", True, WHITE)
    text_rect = text.get_rect(center=(GAME_SCREEN_WIDTH // 2 + HISTORY_WIDTH, SCREEN_HEIGHT // 2))
    screen.blit(text, text_rect)
    
    font_small = pygame.font.Font(None, 36)
    instruction = font_small.render("Say 'Resume' to continue", True, WHITE)
    instruction_rect = instruction.get_rect(center=(GAME_SCREEN_WIDTH // 2 + HISTORY_WIDTH, SCREEN_HEIGHT // 2 + 50))
    screen.blit(instruction, instruction_rect)

def main():
    command_history = CommandHistory()
    voice_thread = threading.Thread(target=voice_command_listener, daemon=True)
    voice_thread.start()
    
    pacman = PacMan()
    blinky = Ghost(9, 7, "assets/ghost_images/red.png", target=[pacman.x, pacman.y])
    clock = pygame.time.Clock()
    running = True
    game_state = GameState.MENU
    is_listening = False
    last_error_check = time.time()

    while running:
        current_time = time.time()
        
        # Check voice thread
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
                game_state = command_data
                command_history.add_command(f"Game State: {command_data.value}")
            elif command_type == "MOVE" and game_state == GameState.PLAYING:
                direction_map = {
                    (0, -1): "Move Up",
                    (0, 1): "Move Down",
                    (-1, 0): "Move Left",
                    (1, 0): "Move Right"
                }
                pacman.direction = command_data
                command_history.add_command(direction_map[tuple(command_data)])
            elif command_type == "MOVE_MULTIPLE" and game_state == GameState.PLAYING:
                direction, steps = command_data
                direction_map = {
                    (0, -1): "Up",
                    (0, 1): "Down",
                    (-1, 0): "Left",
                    (1, 0): "Right"
                }
                command_history.add_command(f"Move {direction_map[tuple(direction)]} {steps} steps")
                pacman.move_multiple(direction, steps)
        
        # Draw screen
        screen.fill(BLACK)
        
        # Always draw command history
        command_history.draw()
        
        if game_state == GameState.MENU:
            draw_start_screen()
        elif game_state == GameState.PLAYING:
            pacman.move()
            draw_maze()
            blinky.target = [pacman.x, pacman.y]
            blinky.move_blinky()
            blinky.draw()
            pacman.draw()
            
            # Draw score
            font = pygame.font.Font(None, 36)
            score_text = f"Score: {pacman.score}"
            text_surface = font.render(score_text, True, WHITE)
            screen.blit(text_surface, (HISTORY_WIDTH + 10, 10))
            
            # Check for collision with Blinky
            if (blinky.x_pos // CELL_SIZE == pacman.x and 
                blinky.y_pos // CELL_SIZE == pacman.y):
                command_history.add_command("Game Over - Caught by Blinky!")
                font = pygame.font.Font(None, 74)
                text = font.render("GAME OVER", True, RED)
                text_rect = text.get_rect(center=(GAME_SCREEN_WIDTH // 2 + HISTORY_WIDTH, SCREEN_HEIGHT // 2))
                screen.blit(text, text_rect)
                pygame.display.flip()
                pygame.time.wait(3000)
                running = False
                
        elif game_state == GameState.PAUSED:
            draw_maze()
            pacman.draw()
            draw_pause_screen()
            
        draw_microphone_indicator(is_listening)
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()

if __name__ == "__main__":
    main()