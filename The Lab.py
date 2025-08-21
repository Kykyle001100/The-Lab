import pygame
import random
import json
import sys
import os

from decimal import Decimal, getcontext

getcontext().prec = 50  # Set precision for Decimal operations
pygame.init()

screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
title_font = pygame.font.SysFont("Monospace", 150, bold=True, italic=True)
clock = pygame.time.Clock()

# Ensure the 'saves' directory exists
if not os.path.exists("saves"):
    os.makedirs("saves")

class InputBox:
    def __init__(self, pos, size, color=(100, 100, 100), hover_color=(150, 150, 150), text_color=(255, 255, 255), font_family="Monospace", font_size=24, characters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-, "):
        self.rect = pygame.Rect(pos, size)
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont(font_family, font_size)
        self.font_size = font_size
        self.characters = characters
        self.text = ""
        self.column = 0
        self.cursor_timer = 0
        self.show_cursor = True
        self.active = False
        self.clicked = False
        self.has_backspaced = False

    def draw(self, surface, dt=1/60000):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(surface, self.hover_color, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)  # Draw border

        # Update cursor timer for flicker (1 Hz, toggle every 0.5s)
        if self.active:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.25:
                self.show_cursor = not self.show_cursor
                self.cursor_timer = 0
        else:
            self.show_cursor = False
            self.cursor_timer = 0

        # Draw text with cursor if active and show_cursor is True
        if self.active and self.show_cursor:
            display_text = self.text[:self.column] + "|" + self.text[self.column:]
        else:
            display_text = self.text

        text_surface = self.font.render(display_text, True, self.text_color)
        text_rect = text_surface.get_rect(topleft=(self.rect.x + 5, self.rect.y + 5))
        surface.blit(text_surface, text_rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:    
                if self.rect.collidepoint(event.pos):
                    self.active = True
                    self.clicked = True
                    # Set cursor position based on mouse click (optional: always at end)
                    self.column = len(self.text)
                else:
                    self.active = False
                    self.clicked = False
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                if self.column > 0:
                    self.text = self.text[:self.column - 1] + self.text[self.column:]
                    self.column -= 1
                    self.has_backspaced = True
            elif event.key == pygame.K_DELETE:
                if self.column < len(self.text):
                    self.text = self.text[:self.column] + self.text[self.column + 1:]
            elif event.key == pygame.K_HOME or event.key == pygame.K_UP:
                self.column = 0
            elif event.key == pygame.K_END or event.key == pygame.K_DOWN:
                self.column = len(self.text)
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_LEFT:
                if self.column > 0:
                    self.column -= 1
            elif event.key == pygame.K_RIGHT:
                if self.column < len(self.text):
                    self.column += 1
            elif event.unicode in self.characters and len(self.text) * self.font_size < self.rect.width - self.font_size:
                self.text = self.text[:self.column] + event.unicode + self.text[self.column:]
                self.column += 1
            if event.key not in [pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_HOME, pygame.K_END, pygame.K_RETURN, pygame.K_LEFT, pygame.K_RIGHT]:
                self.has_backspaced = False

class Button:
    def __init__(self, text, pos, size, color=(100, 100, 100), hover_color=(150, 150, 150), text_color=(255, 255, 255), font_family="Monospace"):
        self.text = text
        self.pos = pos
        self.size = size
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.rect = pygame.Rect(pos, size)
        self.font = pygame.font.SysFont(font_family, 24)
        self.clicked = False

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(surface, self.hover_color, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)  # Draw border

        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect.topleft)

    def is_clicked_once(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        # If mouse is down on the button, set clicked to True
        if self.rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            self.clicked = True
        # If mouse is released and was previously clicked, return True once
        elif self.clicked and not mouse_pressed[0]:
            self.clicked = False
            return True
        return False
    
    def is_clicked(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        if self.rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            return True
        return False
    
def load_save(file_name):
    file_path = os.path.join("saves", file_name)
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
        print(f"Loaded save file: {file_name}")
        print(data)
        return data
    else:
        print(f"Save file {file_name} does not exist.")
        return None
    

def create_new_menu():
    global screen

    WIDTH, HEIGHT = screen.get_size()
    font = pygame.font.SysFont("Monospace", 24, bold=True)

    # Buttons
    x = WIDTH // 2
    exit_button = Button("Back", (10, 10), (60, 60))
    create_button = Button("Create", (x, HEIGHT // 2 - 30), (200, 50))
    rollseed_button = Button("Roll Seed", (x, HEIGHT // 2 + 30), (200, 50))
    buttons = [exit_button, create_button, rollseed_button]

    # Input boxes
    name_input = InputBox((x - 220, HEIGHT // 2 - 30), (200, 30), text_color=(0, 0, 0))
    seed_input = InputBox((x - 220, HEIGHT // 2 + 30), (200, 30), text_color=(0, 0, 0), characters="0123456789")
    inputs = [name_input, seed_input]

    # Surfaces
    subtitle_text = font.render("Create New Save", True, (50, 50, 50))
    title_text = title_font.render("The Lab", True, (50, 50, 50))

    # Rects
    subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    title_rect = title_text.get_rect(center=(WIDTH // 2, 150))

    running = True
    while running:
        dt = clock.tick(60) / 1000  # Convert milliseconds to seconds
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                WIDTH, HEIGHT = screen.get_size()
                exit_button = Button("Back", (10, 10), (60, 60))
                create_button = Button("Create", (WIDTH // 2, HEIGHT // 2 - 30), (200, 50))
                rollseed_button = Button("Roll Seed", (WIDTH // 2, HEIGHT // 2 + 30), (200, 50))
                buttons = [exit_button, create_button, rollseed_button]
                name_input = InputBox((WIDTH // 2 - 220, HEIGHT // 2 - 30), (200, 30), text_color=(0, 0, 0))
                seed_input = InputBox((WIDTH // 2 - 220, HEIGHT // 2 + 30), (200, 30), text_color=(0, 0, 0), characters="0123456789")
                inputs = [name_input, seed_input]
                subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
                title_rect = title_text.get_rect(center=(WIDTH // 2, 150))
            for input_box in inputs:
                input_box.handle_event(event)

        screen.fill((200, 200, 200))

        screen.blit(title_text, title_rect.topleft)
        screen.blit(subtitle_text, subtitle_rect.topleft)

        for button in buttons:
            button.draw(screen)
            if button.is_clicked_once():
                if button.text == "Back":
                    return "Main Menu"
                elif button.text == "Create":
                    name = name_input.text.strip()
                    seed = seed_input.text.strip()
                    with open(os.path.join("saves", f"{name}.tlab"), 'w') as file:
                        data = {
                            "seed": seed
                        }
                        json.dump(data, file)
                    print(f"Created new save file: {name}.tlab with seed {seed}")
                    return "Load Menu"
                elif button.text == "Roll Seed":
                    seed_input.text = str(random.randint(0, 9999999999))
                
        for input_box in inputs:
            input_box.draw(screen, dt)
                
        pygame.display.flip()
        clock.tick(60)

def load_menu() -> tuple[dict, str]:
    global screen

    WIDTH, HEIGHT = screen.get_size()
    font = pygame.font.SysFont("Monospace", 24, bold=True)

    # Save files
    save_files = [f for f in os.listdir("saves") if f.endswith(".tlab")]
    save_buttons = []

    # Buttons
    exit_button = Button("Back", (10, 10), (60, 60))
    buttons = [exit_button]

    # Surfaces
    subtitle_text = font.render("Select Save", True, (50, 50, 50))
    title_text = title_font.render("The Lab", True, (50, 50, 50))

    # Rects
    subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    title_rect = title_text.get_rect(center=(WIDTH // 2, 150))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                WIDTH, HEIGHT = screen.get_size()
                exit_button = Button("Back", (10, 10), (60, 60))
                buttons = [exit_button]
                subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
                title_rect = title_text.get_rect(center=(WIDTH // 2, 150))

        for i, save_file in enumerate(save_files):
            save_button = Button(save_file[:-5], (WIDTH // 2 - 100, HEIGHT // 2 + i * 40), (200, 30))
            save_buttons.append(save_button)

        screen.fill((200, 200, 200))

        screen.blit(title_text, title_rect.topleft)
        screen.blit(subtitle_text, subtitle_rect.topleft)

        for button in save_buttons:
            button.draw(screen)
            if button.is_clicked_once():
                return load_save(button.text + ".tlab"), button.text + ".tlab"

        for button in buttons:
            button.draw(screen)
            if button.is_clicked_once():
                if button.text == "Back":
                    return None
                
        pygame.display.flip()
        clock.tick(60)

def play_game(save_data, save_file):
    global screen

    WIDTH, HEIGHT = screen.get_size()
    font = pygame.font.SysFont("Monospace", 24, bold=True)

    # Flags
    paused = False

    # Buttons
    resume_button = Button("Resume", (WIDTH // 2 - 100, HEIGHT // 2 - 50), (200, 50))
    save_button = Button("Save", (WIDTH // 2 - 100, HEIGHT // 2 + 10), (200, 50))
    about_button = Button("About", (WIDTH // 2 - 100, HEIGHT // 2 + 70), (200, 50))
    quit_button = Button("Quit", (WIDTH // 2 - 100, HEIGHT // 2 + 130), (200, 50))
    pause_buttons = [resume_button, save_button, about_button, quit_button]

    # Surfaces
    paused_text = font.render("Paused", True, (50, 50, 50))

    # Rects
    fps_pos = (10, 10)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                WIDTH, HEIGHT = screen.get_size()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused

        screen.fill((200, 200, 200))

        if paused:
            surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); pygame.draw.rect(surf, (0, 0, 0, 127), (0, 0, WIDTH, HEIGHT)); screen.blit(surf, (0, 0))
            screen.blit(paused_text, (WIDTH // 2 - paused_text.get_width() // 2, HEIGHT // 3 - paused_text.get_height() // 2))
            for button in pause_buttons:
                button.draw(screen)
                if button.is_clicked_once():
                    if button.text == "Resume":
                        paused = False
                    elif button.text == "Save":
                        with open(os.path.join("saves", save_file), 'w') as file:
                            json.dump(save_data, file)
                    elif button.text == "About":
                        print("About button clicked")
                    elif button.text == "Quit":
                        pygame.quit()
                        sys.exit()

        screen.blit(font.render(f"FPS: {clock.get_fps():.2f}", True, (0, 0, 0)), fps_pos)

        pygame.display.flip()
        clock.tick(60)

def main_menu():
    global screen

    WIDTH, HEIGHT = screen.get_size()
    font = pygame.font.SysFont("Monospace", 24, bold=True)

    # Buttons
    load_button = Button("Load", (WIDTH // 2 - 100, HEIGHT // 2 - 50), (200, 50))
    new_button = Button("New", (WIDTH // 2 - 100, HEIGHT // 2 + 10), (200, 50))
    about_button = Button("About", (WIDTH // 2 - 100, HEIGHT // 2 + 70), (200, 50))
    quit_button = Button("Quit", (WIDTH // 2 - 100, HEIGHT // 2 + 130), (200, 50))
    buttons = [load_button, new_button, about_button, quit_button]

    # Surfaces
    title_text = title_font.render("The Lab", True, (50, 50, 50))

    # Rects
    title_rect = title_text.get_rect(center=(WIDTH // 2, 150))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                WIDTH, HEIGHT = screen.get_size()
                load_button = Button("Load", (WIDTH // 2 - 100, HEIGHT // 2 - 50), (200, 50))
                new_button = Button("New", (WIDTH // 2 - 100, HEIGHT // 2 + 10), (200, 50))
                about_button = Button("About", (WIDTH // 2 - 100, HEIGHT // 2 + 70), (200, 50))
                quit_button = Button("Quit", (WIDTH // 2 - 100, HEIGHT // 2 + 130), (200, 50))
                buttons = [load_button, new_button, about_button, quit_button]
                title_rect = title_text.get_rect(center=(WIDTH // 2, 150))

        screen.fill((200, 200, 200))

        screen.blit(title_text, title_rect.topleft)

        for button in buttons:
            button.draw(screen)
            if button.is_clicked_once():
                if button.text == "Load":
                    save_data = load_menu()
                    if save_data is not None:
                        return save_data
                elif button.text == "New":
                    scene = create_new_menu()
                    if scene == "Load Menu":
                        save_data = load_menu()
                        if save_data is not None:
                            return save_data
                    elif scene == "Main Menu":
                        continue
                elif button.text == "About":
                    print("About button clicked")
                elif button.text == "Quit":
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()
        clock.tick(60)

def main():
    while True:
        save_data, save_file = main_menu()
        play_game(save_data, save_file)

if __name__ == "__main__":
    main()