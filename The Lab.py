import pygame
import sys

pygame.init()

screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
title_font = pygame.font.SysFont("Monospace", 150, bold=True, italic=True)
clock = pygame.time.Clock()

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
        if self.rect.collidepoint(mouse_pos) and mouse_pressed[0] and not self.clicked:
            self.clicked = True
            return True
        elif not mouse_pressed[0]:
            self.clicked = False
        return False
    
    def is_clicked(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        if self.rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            return True
        return False

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
                    print("Load button clicked")
                elif button.text == "New":
                    print("New button clicked")
                elif button.text == "About":
                    print("About button clicked")
                elif button.text == "Quit":
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main_menu()