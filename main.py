import pygame
import random
import sys
from typing import Dict, List, Union

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
COLORS = {
    "background": ("lightblue"),  # Light blue
    "text": (0, 0, 0),              # Black
    "catcher": (255, 165, 0),       # Orange
    "lives": (255, 0, 0),           # Red
    "correct": (0, 255, 0),         # Green for correct catches
    "wrong": (255, 0, 0)            # Red for wrong catches
}
FONT_SIZE = 36
OBJECT_SPEED = 3
CATCHER_WIDTH = 100
CATCHER_HEIGHT = 20
CATCHER_SPEED = 8
FALLING_OBJECTS_COUNT = 10

# Constants for object spacing
HORIZONTAL_GAPS = FALLING_OBJECTS_COUNT
COLUMN_WIDTH = SCREEN_WIDTH // HORIZONTAL_GAPS
VERTICAL_GAP = 100

# New constant for number range
NUMBER_RANGE = list(range(1, 10))  # Numbers from 1 to 9

# Create game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Math Equation Catcher")
font = pygame.font.Font(None, FONT_SIZE)

class GameObject:
    def __init__(self, value: str, column: int, y: int):
        self.value = value
        self.column = column
        self.x = (COLUMN_WIDTH * column) + (COLUMN_WIDTH - FONT_SIZE) // 2
        self.y = y
        self.width = FONT_SIZE
        self.height = FONT_SIZE

    def move(self):
        self.y += OBJECT_SPEED

    def is_off_screen(self) -> bool:
        return self.y > SCREEN_HEIGHT

    def collides_with(self, catcher: Dict) -> bool:
        return (self.y + self.height >= catcher["y"] and
                self.x + self.width > catcher["x"] and
                self.x < catcher["x"] + catcher["width"])

class Game:
    def __init__(self):
        self.score = 0
        self.lives = 3
        self.falling_objects: List[GameObject] = []
        self.equation = ""
        self.missing_part = ""
        self.next_equation_ready = True
        self.feedback_message = ""
        self.feedback_timer = 0
        self.available_columns = list(range(HORIZONTAL_GAPS))
        self.last_spawn_time = 0  # Track when we last spawned objects
        self.spawn_delay = 800    # Minimum milliseconds between spawns
        self.catcher = {
            "x": SCREEN_WIDTH // 2 - CATCHER_WIDTH // 2,
            "y": SCREEN_HEIGHT - CATCHER_HEIGHT - 10,
            "width": CATCHER_WIDTH,
            "height": CATCHER_HEIGHT,
        }
        # Track which columns have active objects
        self.active_columns = {i: False for i in range(HORIZONTAL_GAPS)}

    def generate_equation(self):
        if not self.next_equation_ready:
            return

        self.available_columns = list(range(HORIZONTAL_GAPS))
        
        num1 = random.randint(1, 9)
        num2 = random.randint(1, 9)
        operator = random.choice(["+", "-", "*", "/"])
        
        # Ensure clean division results
        if operator == "/":
            num2 = random.randint(1, 9)
            num1 = num2 * random.randint(1, 9)
            while num1 > 9:  # Regenerate if result is > 9
                num2 = random.randint(1, 9)
                num1 = num2 * random.randint(1, 9)
        
        # For multiplication, ensure result is <= 9
        if operator == "*":
            while num1 * num2 > 9:
                num1 = random.randint(1, 9)
                num2 = random.randint(1, 9)
        
        # For addition, ensure result is <= 9
        if operator == "+":
            while num1 + num2 > 9:
                num1 = random.randint(1, 9)
                num2 = random.randint(1, 9)
        
        # For subtraction, ensure result is positive
        if operator == "-":
            while num1 < num2:
                num1 = random.randint(1, 9)
                num2 = random.randint(1, 9)
        
        result = eval(f"{num1} {operator} {num2}")
        if operator == "/":
            result = int(result)

        # Randomly choose which part to hide (only one part)
        missing_choice = random.choice(["first", "second", "operator", "result"])

        if missing_choice == "first":
            self.missing_part = str(num1)
            self.equation = f"? {operator} {num2} = {result}"
        elif missing_choice == "second":
            self.missing_part = str(num2)
            self.equation = f"{num1} {operator} ? = {result}"
        elif missing_choice == "operator":
            self.missing_part = operator
            self.equation = f"{num1} ? {num2} = {result}"
        else:  # result
            self.missing_part = str(result)
            self.equation = f"{num1} {operator} {num2} = ?"

        self._generate_falling_objects()
        self.next_equation_ready = False

    def _get_random_column(self) -> int:
        """Get a random available column that doesn't have an active object near the top."""
        available = [col for col in range(HORIZONTAL_GAPS) if not self.active_columns[col]]
        if not available:
            return random.randint(0, HORIZONTAL_GAPS - 1)
        column = random.choice(available)
        self.active_columns[column] = True
        return column


    def _can_spawn_in_column(self, column: int) -> bool:
        """Check if it's safe to spawn in this column."""
        min_vertical_gap = 100  # Minimum pixels between objects
        
        for obj in self.falling_objects:
            if obj.column == column and obj.y < min_vertical_gap:
                return False
        return True

    def _generate_falling_objects(self):
        """Generate new falling objects with better spacing."""
        current_time = pygame.time.get_ticks()
        
        # Check if enough time has passed since last spawn
        if current_time - self.last_spawn_time < self.spawn_delay:
            return

        # Reset active columns if all are marked as active
        if all(self.active_columns.values()):
            self.active_columns = {i: False for i in range(HORIZONTAL_GAPS)}

        # Add new objects only if we have less than the maximum
        if len(self.falling_objects) < FALLING_OBJECTS_COUNT:
            # Try to add correct answer if it's not already in play
            if not any(obj.value == self.missing_part for obj in self.falling_objects):
                column = self._get_random_column()
                if self._can_spawn_in_column(column):
                    self.falling_objects.append(GameObject(
                        self.missing_part,
                        column,
                        -FONT_SIZE
                    ))
                    self.last_spawn_time = current_time
                    return

            # Try to add a distractor
            column = self._get_random_column()
            if self._can_spawn_in_column(column):
                if random.random() < 0.7:  # 70% chance for numbers
                    value = str(random.randint(1, 9))
                else:
                    value = random.choice(["+", "-", "*", "/"])
                
                # Ensure distractor is different from missing part
                while value == self.missing_part:
                    if value.isdigit():
                        value = str(random.randint(1, 9))
                    else:
                        value = random.choice(["+", "-", "*", "/"])

                self.falling_objects.append(GameObject(
                    value,
                    column,
                    -FONT_SIZE
                ))
                self.last_spawn_time = current_time

    def update(self):
        """Main update method."""
        keys = pygame.key.get_pressed()
        self._move_catcher(keys)
        self._update_objects()
        self._check_collisions()
        
        # Generate new objects if needed
        self._generate_falling_objects()

        if self.feedback_timer > 0:
            self.feedback_timer -= 1


    def _move_catcher(self, keys):
        if keys[pygame.K_LEFT] and self.catcher["x"] > 0:
            self.catcher["x"] -= CATCHER_SPEED
        if keys[pygame.K_RIGHT] and self.catcher["x"] < SCREEN_WIDTH - self.catcher["width"]:
            self.catcher["x"] += CATCHER_SPEED

    def _check_collisions(self):
        """Check for collisions between catcher and falling objects."""
        objects_to_remove = []
        
        for obj in self.falling_objects:
            if obj.collides_with(self.catcher):
                if obj.value == self.missing_part:
                    self.score += 10
                    self.feedback_message = f"+10 Points!"
                    self.next_equation_ready = True
                    self.falling_objects.clear()
                    self.active_columns = {i: False for i in range(HORIZONTAL_GAPS)}
                    return
                else:
                    self.lives -= 1
                    self.feedback_message = f"Wrong! -{obj.value}"
                    self.feedback_timer = 60
                    objects_to_remove.append(obj)
        
        for obj in objects_to_remove:
            if obj in self.falling_objects:
                self.active_columns[obj.column] = False  # Free up the column
                self.falling_objects.remove(obj)

    def _update_objects(self):
        """Update positions and remove off-screen objects."""
        objects_to_remove = []
        
        for obj in self.falling_objects:
            obj.move()
            if obj.is_off_screen():
                self.active_columns[obj.column] = False  # Free up the column
                objects_to_remove.append(obj)
        
        for obj in objects_to_remove:
            if obj in self.falling_objects:
                self.falling_objects.remove(obj)

    def draw(self):
        screen.fill(COLORS["background"])
        
        # Draw equation
        equation_surface = font.render(f"Equation: {self.equation}", True, COLORS["text"])
        screen.blit(equation_surface, (SCREEN_WIDTH - 350, 10))

        # Draw score and lives
        score_text = font.render(f"Score: {self.score}", True, COLORS["text"])
        lives_text = font.render(f"Lives: {self.lives}", True, COLORS["lives"])
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (10, 50))

        # Draw feedback message
        if self.feedback_timer > 0:
            feedback_surface = font.render(self.feedback_message, True, 
                                        COLORS["correct"] if "Points" in self.feedback_message else COLORS["wrong"])
            screen.blit(feedback_surface, (SCREEN_WIDTH // 2 - 50, 50))

        # Draw falling objects
        for obj in self.falling_objects:
            text = font.render(obj.value, True, COLORS["text"])
            screen.blit(text, (obj.x, obj.y))

        # Draw catcher
        pygame.draw.rect(screen, COLORS["catcher"],
                        (self.catcher["x"], self.catcher["y"],
                         self.catcher["width"], self.catcher["height"]))

def main():
    clock = pygame.time.Clock()
    game = Game()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if game.lives <= 0:
            print(f"Game Over! Final score: {game.score}")
            running = False

        if game.next_equation_ready:
            game.generate_equation()

        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()