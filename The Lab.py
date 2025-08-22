import pygame
import random
import json
import sys
import os

from decimal import Decimal, getcontext

is_resized = False

getcontext().prec = 50  # Set precision for Decimal operations
pygame.init()

screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
title_font = pygame.font.SysFont("Monospace", 150, bold=True, italic=True)
clock = pygame.time.Clock()

# Ensure the 'saves' directory exists
if not os.path.exists("saves"):
    os.makedirs("saves")

class DocumentObject:
    def __init__(self, type, content, font="Monospace", font_size=24):
        self.type = type
        self.content = content
        fs = font_size
        if type == "h1":
            fs *= 2
        elif type == "h2":
            fs *= 1.7
        elif type == "h3":
            fs *= 1.4
        self.font_size = int(fs)
        self.font = pygame.font.SysFont(font, int(fs))
        self.bold_font = pygame.font.SysFont(font, int(fs), bold=True)

    def draw(self, surface, y, last_object_rect):
        if self.type == "text":
            text_surface = self.font.render(self.content, True, (50, 50, 50))
            text_rect = text_surface.get_rect(topleft=(10, y))
            surface.blit(text_surface, text_rect.topleft)
            return text_rect
        elif self.type == "bold":
            text_surface = self.bold_font.render(self.content, True, (50, 50, 50))
            if last_object_rect:
                text_rect = text_surface.get_rect(topleft=(last_object_rect.right + 10, last_object_rect.top))
            else:
                text_rect = text_surface.get_rect(topleft=(10, y))
            surface.blit(text_surface, text_rect.topleft)
            return text_rect
        elif self.type == "listobj":
            text_surface = self.font.render(self.content, True, (50, 50, 50))
            surf = pygame.Surface((text_surface.get_width() + 20, text_surface.get_height()), pygame.SRCALPHA)
            pygame.draw.circle(surf, (50, 50, 50), (10, text_surface.get_height() // 2), 5)
            surf.blit(text_surface, (20, 0))
            text_rect = surf.get_rect(topleft=(10, y))
            surface.blit(surf, text_rect.topleft)
            return text_rect
        elif self.type == "split":
            text_surface = self.font.render(self.content, True, (50, 50, 50))
            text_rect = text_surface.get_rect(center=(surface.get_width() // 2, y + text_surface.get_height() // 2))
            line_width = (surface.get_width() - text_rect.width) // 2 - 20
            line = pygame.Surface((line_width, 2))
            surf = pygame.Surface((surface.get_width(), text_rect.height), pygame.SRCALPHA)
            surf.blit(line, (10, text_rect.centery - 1 - y))
            surf.blit(text_surface, (text_rect.x, 0))
            surf.blit(line, (text_rect.x + text_rect.width + 10, text_rect.centery - 1 - y))
            surface.blit(surf, (0, y))
            return pygame.Rect(0, y, surface.get_width(), text_surface.get_height())
        elif self.type in ["h1", "h2", "h3"]:
            text_surface = self.font.render(self.content, True, (50, 50, 50))
            text_rect = text_surface.get_rect(topleft=(10, y))
            surface.blit(text_surface, text_rect.topleft)
            return text_rect
        elif self.type == "newline":
            return pygame.Rect(0, y, surface.get_width(), self.font.get_height() + 5)
        else:
            raise ValueError(f"Unknown DocumentObject type: {self.type}")

class Document:
    def __init__(self):
        self.objects = []
        self.font = "Monospace"

    def add(self, obj):
        if isinstance(obj, DocumentObject):
            self.objects.append(obj)
        else:
            raise TypeError("Object must be an instance of DocumentObject")
        
    def init(self):
        pass

    def draw(self, surface, offset_y=0):
        if not self.objects:
            return

        y = offset_y
        last_object_rect = None
        for obj in self.objects:
            rect = obj.draw(surface, y, last_object_rect)
            if rect:
                y = rect.bottom + 5  # 5 pixels spacing
                last_object_rect = rect
        return last_object_rect

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
    


def about():
    global screen, is_resized

    offset_y = 0
    WIDTH, HEIGHT = screen.get_size()
    font = pygame.font.SysFont("Monospace", 24, bold=True)

    eve = None

    # Document
    doc = Document()
    doc.add(DocumentObject("h1", "About The Lab"))
    doc.add(DocumentObject("text", "Space Exploration game where you build rockets,"))
    doc.add(DocumentObject("text", "experiment with chemical reactions, explore the"))
    doc.add(DocumentObject("text", "universe, bioengineer organisms, and land on"))
    doc.add(DocumentObject("text", "real life exoplanets."))
    doc.add(DocumentObject("newline", ""))
    doc.add(DocumentObject("h2", "Labcopedia"))
    doc.add(DocumentObject("text", "A collection of documents that explain the"))
    doc.add(DocumentObject("text", "Universe, Chemistry, Biology, and Rocket"))
    doc.add(DocumentObject("text", "Science. Features in Labcopedia include:"))
    doc.add(DocumentObject("listobj", "Implemented chemical reactions in the game"))
    doc.add(DocumentObject("text", "  and their applications."))
    doc.add(DocumentObject("listobj", "A list of real life exoplanets and their"))
    doc.add(DocumentObject("text", "  properties."))
    doc.add(DocumentObject("listobj", "Biological systems implemented in the game"))
    doc.add(DocumentObject("text", "  and their applications."))
    doc.add(DocumentObject("listobj", "Rocket science and engineering principles."))
    doc.add(DocumentObject("listobj", "A few examples of experiments you can try"))
    doc.add(DocumentObject("text", "  in the game."))
    doc.add(DocumentObject("newline", ""))
    doc.init()

    # Buttons
    exit_button = Button("Back", (10, 10), (60, 60))
    buttons = [exit_button]

    # Surfaces
    about_text = font.render("About The Lab", True, (50, 50, 50))

    # Rects
    about_rect = about_text.get_rect(center=(WIDTH // 2, 24))
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                is_resized = True
                eve = event
            elif event.type == pygame.MOUSEWHEEL:
                offset_y += event.y * 5
                offset_y = min(offset_y, 0)

        screen.fill((200, 200, 200))

        doc.draw(screen, offset_y+100)

        screen.blit(about_text, about_rect.topleft)

        for button in buttons:
            button.draw(screen)
            if button.is_clicked_once():
                if button.text == "Back":
                    return
                
        pygame.display.flip()
        clock.tick(60)

        if is_resized:
            screen = pygame.display.set_mode((eve.w, eve.h), pygame.RESIZABLE)
            WIDTH, HEIGHT = screen.get_size()
            exit_button = Button("Back", (10, 10), (60, 60))
            buttons = [exit_button]
            about_rect = about_text.get_rect(center=(WIDTH // 2, 24))
            is_resized = False

def create_new_menu():
    global screen, is_resized

    eve = None

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
                is_resized = True
                eve = event

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

        if is_resized:
            screen = pygame.display.set_mode((eve.w, eve.h), pygame.RESIZABLE)
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
            is_resized = False

def load_menu() -> tuple[dict, str]:
    global screen, is_resized

    eve = None
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
                is_resized = True
                eve = event

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

        if is_resized:
            screen = pygame.display.set_mode((eve.w, eve.h), pygame.RESIZABLE)
            WIDTH, HEIGHT = screen.get_size()
            subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            title_rect = title_text.get_rect(center=(WIDTH // 2, 150))
            is_resized = False

def play_game(save_data, save_file):
    global screen, is_resized

    eve = None
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
                is_resized = True
                eve = event

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
                        about()
                    elif button.text == "Quit":
                        return 

        screen.blit(font.render(f"FPS: {clock.get_fps():.2f}", True, (0, 0, 0)), fps_pos)

        pygame.display.flip()
        clock.tick(60)

        if is_resized:
            screen = pygame.display.set_mode((eve.w, eve.h), pygame.RESIZABLE)
            WIDTH, HEIGHT = screen.get_size()
            resume_button = Button("Resume", (WIDTH // 2 - 100, HEIGHT // 2 - 50), (200, 50))
            save_button = Button("Save", (WIDTH // 2 - 100, HEIGHT // 2 + 10), (200, 50))
            about_button = Button("About", (WIDTH // 2 - 100, HEIGHT // 2 + 70), (200, 50))
            quit_button = Button("Quit", (WIDTH // 2 - 100, HEIGHT // 2 + 130), (200, 50))
            pause_buttons = [resume_button, save_button, about_button, quit_button]
            is_resized = False

def main_menu():
    global screen, is_resized

    eve = None
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
                is_resized = True
                eve = event

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
                    about()
                elif button.text == "Quit":
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()
        clock.tick(60)

        if is_resized:
            screen = pygame.display.set_mode((eve.w, eve.h), pygame.RESIZABLE)
            WIDTH, HEIGHT = screen.get_size()
            load_button = Button("Load", (WIDTH // 2 - 100, HEIGHT // 2 - 50), (200, 50))
            new_button = Button("New", (WIDTH // 2 - 100, HEIGHT // 2 + 10), (200, 50))
            about_button = Button("About", (WIDTH // 2 - 100, HEIGHT // 2 + 70), (200, 50))
            quit_button = Button("Quit", (WIDTH // 2 - 100, HEIGHT // 2 + 130), (200, 50))
            buttons = [load_button, new_button, about_button, quit_button]
            title_rect = title_text.get_rect(center=(WIDTH // 2, 150))
            is_resized = False

def main():
    while True:
        save_data, save_file = main_menu()
        play_game(save_data, save_file)

if __name__ == "__main__":
    main()