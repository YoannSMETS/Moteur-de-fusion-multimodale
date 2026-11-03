
import pygame
import sys
from IvyClass import IvyAgent
import threading
import queue
import itertools
from dataclasses import dataclass



# ============================================================
# CONFIGURATION
# ============================================================

WIDTH = 1100
HEIGHT = 720
FPS = 60


WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
LIGHT_GRAY = (240, 242, 245)
GRAY = (150, 155, 165)
BLUE = (65, 125, 230)
GREEN = (50, 180, 110)
RED = (225, 75, 75)

COLORS = {
    "red": (230, 65, 65),
    "green": (50, 180, 100),
    "blue": (65, 125, 230),
}

SHAPES = ["rectangle", "circle", "triangle", "diamond"]


# ============================================================
# IVY AGENT
# ============================================================


# ============================================================
# DRAWING OBJECT
# ============================================================

@dataclass
class Shape:
    id: int
    shape_type: str
    color: str
    x: int
    y: int
    size: int = 70

    def contains(self, pos):
        px, py = pos

        # Test simple de sélection par boîte englobante
        return (
            self.x - self.size // 2 <= px <= self.x + self.size // 2
            and
            self.y - self.size // 2 <= py <= self.y + self.size // 2
        )

    def draw(self, surface, selected=False):
        color = COLORS.get(self.color, BLUE)

        rect = pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size
        )

        if self.shape_type == "rectangle":
            pygame.draw.rect(surface, color, rect, border_radius=4)

        elif self.shape_type == "circle":
            pygame.draw.circle(
                surface, color, (self.x, self.y), self.size // 2
            )

        elif self.shape_type == "triangle":
            points = [
                (self.x, self.y - self.size // 2),
                (self.x - self.size // 2, self.y + self.size // 2),
                (self.x + self.size // 2, self.y + self.size // 2),
            ]
            pygame.draw.polygon(surface, color, points)

        elif self.shape_type == "diamond":
            points = [
                (self.x, self.y - self.size // 2),
                (self.x + self.size // 2, self.y),
                (self.x, self.y + self.size // 2),
                (self.x - self.size // 2, self.y),
            ]
            pygame.draw.polygon(surface, color, points)

        if selected:
            pygame.draw.rect(
                surface,
                BLACK,
                rect.inflate(10, 10),
                2,
                border_radius=5
            )


# ============================================================
# BUTTON
# ============================================================

class Button:

    def __init__(self, rect, text, callback, color=LIGHT_GRAY):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color

    def draw(self, surface, font):
        pygame.draw.rect(
            surface, self.color, self.rect, border_radius=7
        )
        pygame.draw.rect(
            surface, GRAY, self.rect, 1, border_radius=7
        )

        label = font.render(self.text, True, BLACK)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()
            return True
        return False


# ============================================================
# WHITEBOARD
# ============================================================

class Whiteboard:

    TOOLBAR_HEIGHT = 105
    SIDEBAR_WIDTH = 250

    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Multimodal Whiteboard - Ivy")

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("Arial", 18)
        self.small_font = pygame.font.SysFont("Arial", 14)
        self.title_font = pygame.font.SysFont("Arial", 23, bold=True)

        self.shapes = []
        self.id_counter = itertools.count(1)

        self.selected_shape = "rectangle"
        self.selected_color = "blue"

        self.dragging = None
        self.drag_offset = (0, 0)

        self.event_queue = queue.Queue()
        self.logs = []

        self.canvas = pygame.Rect(
            0,
            self.TOOLBAR_HEIGHT,
            WIDTH - self.SIDEBAR_WIDTH,
            HEIGHT - self.TOOLBAR_HEIGHT
        )

        # Agent Ivy indépendant du thread graphique
        self.ivy = IvyAgent(self.event_queue)

        self.create_buttons()

        self.log("Whiteboard ready")
        self.log(f"Ivy bus: {self.ivy.IVY_BUS}")

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def create_buttons(self):
        self.buttons = []

        shapes = [
            ("Rectangle", "rectangle"),
            ("Cercle", "circle"),
            ("Triangle", "triangle"),
            ("Losange", "diamond"),
        ]

        for i, (label, shape) in enumerate(shapes):
            self.buttons.append(
                Button(
                    (15 + i * 125, 48, 115, 38),
                    label,
                    lambda s=shape: self.set_shape(s)
                )
            )

        colors = [
            ("Rouge", "red"),
            ("Vert", "green"),
            ("Bleu", "blue"),
        ]

        for i, (label, color) in enumerate(colors):
            self.buttons.append(
                Button(
                    (540 + i * 105, 48, 95, 38),
                    label,
                    lambda c=color: self.set_color(c),
                    COLORS[color]
                )
            )

        self.buttons.append(
            Button(
                (15, 8, 120, 32),
                "Effacer",
                self.clear_board,
                (255, 220, 220)
            )
        )

    def set_shape(self, shape):
        self.selected_shape = shape
        self.log(f"Selected shape: {shape}")

    def set_color(self, color):
        self.selected_color = color
        self.log(f"Selected color: {color}")

    def clear_board(self):
        self.shapes.clear()
        self.log("Board cleared")

        self.ivy.send("PALETTE_CLEAR")

    # --------------------------------------------------------
    # SHAPE MANAGEMENT
    # --------------------------------------------------------

    def create_shape(self, shape_type, color, x, y, notify=True):
        if shape_type not in SHAPES:
            self.log(f"Unknown shape: {shape_type}")
            return

        if color not in COLORS:
            self.log(f"Unknown color: {color}")
            return

        object_id = next(self.id_counter)

        shape = Shape(
            id=object_id,
            shape_type=shape_type,
            color=color,
            x=x,
            y=y
        )

        self.shapes.append(shape)

        self.log(
            f"Created #{object_id}: {shape_type} / {color}"
        )

        if notify:
            self.ivy.send(
                f"PALETTE_CREATED id={object_id} "
                f"shape={shape_type} color={color} x={x} y={y}"
            )

    def move_shape(self, object_id, x, y, notify=True):
        shape = next(
            (s for s in self.shapes if s.id == object_id),
            None
        )

        if shape is None:
            self.log(f"Object #{object_id} not found")
            return

        shape.x = x
        shape.y = y

        if notify:
            self.ivy.send(
                f"PALETTE_MOVED id={object_id} x={x} y={y}"
            )

    def find_shape(self, pos):
        # Sélectionner la forme la plus récemment créée
        for shape in reversed(self.shapes):
            if shape.contains(pos):
                return shape
        return None

    # --------------------------------------------------------
    # IVY EVENTS
    # --------------------------------------------------------

    def process_ivy_events(self):
        while not self.event_queue.empty():
            event = self.event_queue.get()

            if event["type"] == "create":
                self.create_shape(
                    event["shape"],
                    event["color"],
                    event["x"],
                    event["y"],
                    notify=False
                )

            elif event["type"] == "move":
                self.move_shape(
                    event["id"],
                    event["x"],
                    event["y"],
                    notify=False
                )

            elif event["type"] == "clear":
                self.shapes.clear()
                self.log("Clear command received from Ivy")

    # --------------------------------------------------------
    # MOUSE
    # --------------------------------------------------------

    def handle_mouse_down(self, pos):
        # Toolbar
        for button in self.buttons:
            if button.handle_click(pos):
                return

        # Canvas
        if not self.canvas.collidepoint(pos):
            return

        x, y = pos

        self.ivy.send(f"PALETTE_CLICK x={x} y={y}")

        shape = self.find_shape(pos)

        if shape:
            self.dragging = shape
            self.drag_offset = (
                shape.x - x,
                shape.y - y
            )
        else:
            self.create_shape(
                self.selected_shape,
                self.selected_color,
                x,
                y
            )

    def handle_mouse_motion(self, pos):
        if self.dragging:
            x, y = pos

            self.dragging.x = x + self.drag_offset[0]
            self.dragging.y = y + self.drag_offset[1]

    def handle_mouse_up(self):
        if self.dragging:
            shape = self.dragging

            self.ivy.send(
                f"PALETTE_MOVED id={shape.id} "
                f"x={shape.x} y={shape.y}"
            )

            self.log(f"Moved object #{shape.id}")
            self.dragging = None

    # --------------------------------------------------------
    # DRAWING
    # --------------------------------------------------------

    def log(self, message):
        self.logs.append(message)
        self.logs = self.logs[-12:]

        print("[UI]", message)

    def draw_toolbar(self):
        pygame.draw.rect(
            self.screen,
            LIGHT_GRAY,
            (0, 0, WIDTH, self.TOOLBAR_HEIGHT)
        )

        title = self.title_font.render(
            "Multimodal Whiteboard",
            True,
            BLACK
        )
        self.screen.blit(title, (155, 12))

        for button in self.buttons:
            button.draw(self.screen, self.font)

    def draw_canvas(self):
        pygame.draw.rect(self.screen, WHITE, self.canvas)

        # Grille discrète
        for x in range(0, self.canvas.width, 25):
            pygame.draw.line(
                self.screen, (245, 245, 245),
                (x, self.canvas.top),
                (x, HEIGHT)
            )

        for y in range(self.canvas.top, HEIGHT, 25):
            pygame.draw.line(
                self.screen, (245, 245, 245),
                (0, y),
                (self.canvas.width, y)
            )

        for shape in self.shapes:
            shape.draw(
                self.screen,
                selected=(shape == self.dragging)
            )

    def draw_sidebar(self):
        x = WIDTH - self.SIDEBAR_WIDTH

        pygame.draw.rect(
            self.screen,
            LIGHT_GRAY,
            (x, 0, self.SIDEBAR_WIDTH, HEIGHT)
        )

        pygame.draw.line(
            self.screen,
            GRAY,
            (x, 0),
            (x, HEIGHT),
            2
        )

        title = self.title_font.render("Ivy Probe", True, BLACK)
        self.screen.blit(title, (x + 20, 20))

        status = self.small_font.render(
            "Connected | Port 2010",
            True,
            GREEN
        )
        self.screen.blit(status, (x + 20, 55))

        pygame.draw.line(
            self.screen, GRAY,
            (x + 15, 85), (WIDTH - 15, 85)
        )

        label = self.font.render("Event log", True, BLACK)
        self.screen.blit(label, (x + 20, 100))

        for i, message in enumerate(self.logs):
            text = self.small_font.render(
                message[:30],
                True,
                BLACK
            )
            self.screen.blit(text, (x + 20, 135 + i * 27))

        pygame.draw.line(
            self.screen, GRAY,
            (x + 15, 490), (WIDTH - 15, 490)
        )

        help_lines = [
            "Mouse:",
            "Click = create / select",
            "Drag = move",
            "",
            "Ivy RX:",
            "PALETTE_CREATE",
            "PALETTE_MOVE",
            "PALETTE_CLEAR",
        ]

        for i, line in enumerate(help_lines):
            text = self.small_font.render(line, True, BLACK)
            self.screen.blit(text, (x + 20, 510 + i * 22))

    def draw(self):
        self.screen.fill(WHITE)

        self.draw_canvas()
        self.draw_toolbar()
        self.draw_sidebar()

        pygame.display.flip()

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    def run(self):
        running = True

        while running:
            self.clock.tick(FPS)

            self.process_ivy_events()

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_mouse_down(event.pos)

                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.handle_mouse_up()

            self.draw()

        self.ivy.stop()
        pygame.quit()
        sys.exit()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    app = Whiteboard()
    app.run()