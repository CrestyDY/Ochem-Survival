import pygame
import time
import background
import sqlite3 as sql
import random as rd
import os
from PIL import Image
from io import BytesIO
import math

class Time_Trial:
    def __init__(self, width, height, playground_rect, base_path, current_background, dark_mode, music_play):
        # Playground rect from App
        self.playground_rect = playground_rect
        self.scale_factor = min(width / 1600, height / 1000)
        self.width = width
        self.height = height
        self.size = (width, height)

        # Background and mode
        self.base_path = base_path

        # Background setup
        self.background_light = background.Background(os.path.join(base_path, 'images', 'background.jpg'), [0, 0])
        self.background_dark = background.Background(os.path.join(base_path, 'images', 'background-dark-mode.jpg'), [0, 0])

        # Clock and timer
        self.clock = pygame.time.Clock()
        self.start_time = None
        self.time_limit = 60
        self.time_left = self.time_limit
        pygame.font.init()
        self.font = pygame.font.SysFont('comicsansms', 36)

        # Game state
        self.selected_answer = None
        self.current_compounds = None
        self.correct_answer = None
        self.score = 0
        self.current_question_start = None
        self.question_duration = 60  # Time per question in seconds
        self.feedback_displayed = False
        self.feedback_start = None
        self.feedback_duration = 0.5

        # Minigames
        self.Minigame_dictionary = {1: "Most Acidic", 2: "Name To Structure", 3: "Structure To Name"}
        self.current_minigame = None
        self.question_answered = False

        # Button dimensions for answers
        self.button_width = 300
        self.button_height = 300
        self.button_margin = 50
        self.button_rects = []
        self.button_color = (200, 200, 200)

        self.cached_images = []

        # Hover effect
        self.button_hover_states = [False, False, False, False]
        self.game_over_button_hover = False

        # Game over button
        self.game_over_button_rect = pygame.Rect(
            self.playground_rect.centerx - 150,
            self.playground_rect.centery + 100,
            300,
            50
        )
        self.return_to_menu = False
        self.menu_hover_state = False

        # Initialize UI elements with initial scaling

        # Button rects based on App's width
        self.button_rect = pygame.Rect(width - 100, 0, 100, 50)
        self.music_rect = pygame.Rect(width - 100, 50, 100, 50)

        # Return to menu button
        self.return_to_menu_rect = pygame.Rect(
            (self.playground_rect.topleft[0] + 20, self.playground_rect.topleft[1] + 20),
            (100, 50)
        )
        self.initialize_ui_elements()
        self.setup_button_rects()


        # Remove duplicate initialization of these attributes
        self._running = True
        self.current_screen = "time_trial"


        self.high_score = self.load_high_score()

        # Use passed background and dark mode
        self.current_background = current_background
        self.dark_mode = dark_mode
        self.music_play = music_play

    def get_image_path(self, filename):
        return os.path.join(self.base_path, 'images', filename)

    def initialize_ui_elements(self):
        """
        Reinitialize all UI elements with proper scaling
        """
        # Calculate scaled dimensions
        scale_factor = self.scale_factor

        # Button rects based on scaled width
        button_width = int(100 * scale_factor)
        button_height = int(50 * scale_factor)
        self.button_rect = pygame.Rect(self.width - button_width, 0, button_width, button_height)
        self.music_rect = pygame.Rect(self.width - button_width, button_height, button_width, button_height)

        # Return to menu button with scaling
        self.return_to_menu_rect = pygame.Rect(
            (self.playground_rect.topleft[0] + int(20 * scale_factor),
             self.playground_rect.topleft[1] + int(20 * scale_factor)),
            (int(100 * scale_factor), int(50 * scale_factor))
        )

        # Game over button with scaling
        self.game_over_button_rect = pygame.Rect(
            self.playground_rect.centerx - int(150 * scale_factor),
            self.playground_rect.centery + int(100 * scale_factor),
            int(300 * scale_factor),
            int(50 * scale_factor)
        )

        # Scaled button dimensions for answer buttons
        self.button_width = int(300 * scale_factor)
        self.button_height = int(300 * scale_factor)
        self.button_margin = int(50 * scale_factor)

        # Scale font sizes
        title_font_size = max(int(36 * scale_factor), 12)
        small_font_size = max(int(16 * scale_factor), 10)

        # Reinitialize fonts with scaled sizes
        self.font = pygame.font.SysFont('comicsansms', title_font_size)
        self.small_font = pygame.font.SysFont('comicsansms', small_font_size)

    def load_high_score(self):
        """Load the high score from a file"""
        try:
            with open('High_Scores.txt', 'r') as file:
                return int(file.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def save_high_score(self):
        """Save the high score to a file if current score is higher"""
        if self.score > self.high_score:
            with open('High_Scores.txt', 'w') as file:
                file.write(str(self.score))
            self.high_score = self.score

    def select_random_minigame(self):
        """Randomly select a minigame type"""
        game_type = rd.randint(1, 3)
        self.current_minigame = self.Minigame_dictionary[game_type]
        print(f"Selected minigame: {self.current_minigame}")
    def start_timer(self):
        self.start_time = time.time()

    def update_timer(self):
        if self.start_time:
            elapsed_time = time.time() - self.start_time
            self.time_left = max(0, self.time_limit - int(elapsed_time))
        return self.time_left

    def pause_music(self):
        if self.music_play:
            self.music_play = False
            pygame.mixer_music.pause()
        elif not self.music_play:
            self.music_play = True
            pygame.mixer_music.unpause()

    def draw_timer(self, surface):
        time_text = f"Time Left: {self.time_left}s"
        text_surface = self.font.render(time_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        text_rect.centerx = self.playground_rect.centerx
        text_rect.y = self.playground_rect.y
        surface.blit(text_surface, text_rect)

    def draw_game_over(self, surface):
        game_over_text = "Time's Up! Game Over!"
        text_surface = self.font.render(game_over_text, True, (255, 0, 0))
        text_rect = text_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 50))
        surface.blit(text_surface, text_rect)

        # Display final score
        score_text = f"Final Score: {self.score}"
        score_surface = self.font.render(score_text, True, (0, 0, 0))
        score_rect = score_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
        surface.blit(score_surface, score_rect)

        # Draw Return to Menu button with hover effect
        button_color = (140, 140, 140) if self.game_over_button_hover else (200, 200, 200)
        pygame.draw.rect(surface, button_color, self.game_over_button_rect, border_radius=10)
        button_font = pygame.font.SysFont('comicsansms', 24)
        button_text = "Return to Menu"
        button_text_surface = button_font.render(button_text, True, (0, 0, 0))
        button_text_rect = button_text_surface.get_rect(center=self.game_over_button_rect.center)
        surface.blit(button_text_surface, button_text_rect)

        self.save_high_score()
        high_score_font = pygame.font.SysFont('comicsansms', 24)
        high_score_text = f"High Score: {self.high_score}"
        high_score_surface = high_score_font.render(high_score_text, True, (0, 0, 0))
        high_score_rect = high_score_surface.get_rect(
            center=(surface.get_width() // 2, surface.get_height() // 2 + 50)
        )
        surface.blit(high_score_surface, high_score_rect)

    def toggle_background(self):
        """Toggle between light and dark backgrounds."""
        if self.dark_mode:
            self.current_background = self.background_light
        else:
            self.current_background = self.background_dark
        self.dark_mode = not self.dark_mode


    def truncate_text(self, text, max_length=50):
        if len(text) <= max_length:
            return text
        return text[:max_length] + '...'

    def render_wrapped_text(self, text, font, max_width, color=(0, 0, 0)):
        """
        Render text that wraps or truncates to fit within max_width
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = font.render(test_line, True, color)

            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                # If first word is too long, truncate
                if not current_line:
                    test_surface = font.render(word[:int(max_width / font.get_height())] + '...', True, color)
                    lines.append(test_surface)
                    break

                # Finish current line and start a new one
                lines.append(font.render(' '.join(current_line), True, color))
                current_line = [word]

        if current_line:
            lines.append(font.render(' '.join(current_line), True, color))

        return lines

    def setup_button_rects(self):
        """
        Create button rectangles dynamically based on minigame type and scaling
        with positioning relative to the playground rect
        """
        if self.current_minigame is None:
            self.select_random_minigame()

        scale_factor = self.scale_factor
        playground_width = self.playground_rect.width
        playground_height = self.playground_rect.height

        # Dynamically calculate button sizes based on playground dimensions
        button_width = int(playground_width * 0.20)  # 22% of playground width
        button_height = int(playground_height * 0.31)  # 30% of playground height
        button_margin = int(playground_width * 0.03)  # 2% of playground width for margin

        # Calculate starting x and y to center the grid in the playground
        total_grid_width = 2 * button_width + button_margin
        total_grid_height = 2 * button_height + button_margin

        start_x = self.playground_rect.x + (self.playground_rect.width - total_grid_width) // 2
        start_y = self.playground_rect.y + (self.playground_rect.height - total_grid_height) // 1.60

        # Adjust for Structure To Name minigame
        if self.current_minigame == "Structure To Name":
            button_width = int(playground_width * 0.40)
            button_height = int(playground_height * 0.15)  # Shorter for text
            button_margin = int(playground_width * 0.02)

            start_x = self.playground_rect.x + (self.playground_rect.width - (2 * button_width) - button_margin) // 2
            start_y = self.playground_rect.y + self.playground_rect.height * 0.5

        # Create button rectangles
        self.button_rects = [
            pygame.Rect(start_x, start_y, button_width, button_height),
            pygame.Rect(start_x + button_width + button_margin, start_y, button_width, button_height),
            pygame.Rect(start_x, start_y + button_height + button_margin, button_width, button_height),
            pygame.Rect(start_x + button_width + button_margin, start_y + button_height + button_margin,
                        button_width, button_height)
        ]

    def resize(self, new_width, new_height):
        """
        Comprehensive window resizing method
        """
        # Update width, height, and size
        self.width = new_width
        self.height = new_height
        self.size = (new_width, new_height)

        # Recalculate scaling factor
        self.scale_factor = min(new_width / 1600, new_height / 1000)

        # Update playground rect
        playground_width = int(1200 * self.scale_factor)
        playground_height = int(800 * self.scale_factor)

        # Center the playground in the window
        playground_left = (new_width - playground_width) // 2
        playground_top = (new_height - playground_height) // 2

        self.playground_rect = pygame.Rect(
            playground_left,
            playground_top,
            playground_width,
            playground_height
        )

        # Reinitialize UI elements with new scaling
        self.initialize_ui_elements()
        self.setup_button_rects()

        # Rescale cached images to match new button sizes
        if self.current_compounds:
            self.rescale_cached_images()

    def check_hover(self, mouse_pos):
        # Check hover for game option buttons
        if self.time_left > 0:
            for i, rect in enumerate(self.button_rects):
                if rect.collidepoint(mouse_pos):
                    self.button_hover_states[i] = True
                else:
                    self.button_hover_states[i] = False
            if self.return_to_menu_rect.collidepoint(mouse_pos):
                self.menu_hover_state = True
            else:
                self.menu_hover_state = False

        # Check hover for game over button
        if self.time_left <= 0:
            self.game_over_button_hover = self.game_over_button_rect.collidepoint(mouse_pos)

    def rescale_cached_images(self):
        """
        Rescale cached images based on current button dimensions
        This method can be called during window resize events
        """
        if not self.current_compounds:
            return

        # Reset cached images
        self.cached_images = []
        for compound in self.current_compounds:
            image_data = compound[3] if self.current_minigame == "Most Acidic" else compound[0]
            if image_data:
                pil_image = Image.open(BytesIO(image_data))

                # Use the current button width and height for scaling
                # Reduce image size to 80% of button size to ensure some padding
                scale = min(
                    (self.button_width * 0.8) / pil_image.width,
                    (self.button_height * 0.8) / pil_image.height
                )

                new_size = (
                    int(pil_image.width * scale),
                    int(pil_image.height * scale)
                )

                pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)

                # Convert to pygame surface
                mode = pil_image.mode
                size = pil_image.size
                data = pil_image.tobytes()
                pygame_image = pygame.image.fromstring(data, size, mode)
                self.cached_images.append(pygame_image)
            else:
                self.cached_images.append(None)

    def load_new_question(self):
        try:
            ochem_database = sql.connect("ochem.db")
            cursor = ochem_database.cursor()

            cursor.execute("SELECT MIN(id), MAX(id) FROM ochem_table;")
            min_id, max_id = cursor.fetchone()

            if min_id is None or max_id is None or max_id - min_id + 1 < 4:
                raise ValueError("Not enough compounds in database")

            random_compounds = rd.sample(range(min_id, max_id + 1), 4)

            if self.current_minigame == "Most Acidic":
                extract_query = """
                    SELECT DISTINCT pH, chemical_formula, iupac, image_file 
                    FROM ochem_table WHERE id IN (?, ?, ?, ?);
                """
                cursor.execute(extract_query, random_compounds)
                compounds = cursor.fetchall()

                if not compounds:
                    print("No compounds found for Most Acidic")
                    return False

                # Sort by pH to know which is most acidic
                compounds = sorted(compounds, key=lambda x: x[0])
                self.correct_answer = 0  # Index of most acidic compound

                # Shuffle the compounds for display
                display_order = list(range(4))
                rd.shuffle(display_order)
                self.current_compounds = [compounds[i] for i in display_order]
                # Update correct_answer to track shuffled position
                self.correct_answer = display_order.index(0)

            elif self.current_minigame == "Name To Structure":
                extract_query = """
                SELECT image_file, iupac from ochem_table
                WHERE id in (?,?,?,?)"""

                cursor.execute(extract_query, random_compounds)
                compounds = cursor.fetchall()

                if not compounds:
                    print("No compounds found for Name To Structure")
                    return False

                self.correct_answer = 0

                display_order = list(range(4))
                rd.shuffle(display_order)
                self.current_compounds = [compounds[i] for i in display_order]
                self.correct_answer = display_order.index(0)

            elif self.current_minigame == "Structure To Name":
                extract_query = """
                SELECT image_file, iupac from ochem_table
                WHERE id in (?,?,?,?)"""

                cursor.execute(extract_query, random_compounds)
                compounds = cursor.fetchall()

                if not compounds:
                    print("No compounds found for Structure To Name")
                    return False
                self.corrent_answer = 0
                display_order = list(range(4))
                rd.shuffle(display_order)
                self.current_compounds = compounds
                self.correct_answer = display_order.index(0)

            # Cache images with dynamic scaling
            self.cached_images = []
            for compound in self.current_compounds:
                image_data = compound[3] if self.current_minigame == "Most Acidic" else compound[0]
                if image_data:
                    pil_image = Image.open(BytesIO(image_data))

                    # Use the current button width and height for scaling
                    # Reduce image size to 80% of button size to ensure some padding
                    scale = min(
                        (self.button_width * 0.8) / pil_image.width,
                        (self.button_height * 0.8) / pil_image.height
                    )

                    new_size = (
                        int(pil_image.width * scale),
                        int(pil_image.height * scale)
                    )

                    pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)

                    # Convert to pygame surface
                    mode = pil_image.mode
                    size = pil_image.size
                    data = pil_image.tobytes()
                    pygame_image = pygame.image.fromstring(data, size, mode)
                    self.cached_images.append(pygame_image)
                else:
                    self.cached_images.append(None)

            ochem_database.close()

            self.current_question_start = time.time()
            self.feedback_displayed = False
            self.selected_answer = None

            return True

        except Exception as e:
            print(f"Database error in load_new_question: {e}")
            return False

    def Most_Acidic(self, surface):
        if not self.current_compounds:
            if not self.load_new_question():
                print("No Compounds")
                return

        # Draw timer first
        self.draw_timer(surface)

        # Calculate the position for instructions below the timer
        timer_rect = self.font.render(f"Time Left: {self.time_left}s", True, (255, 255, 255)).get_rect()
        timer_bottom = self.playground_rect.y + timer_rect.height + 10  # Add some padding

        # Draw instructions
        instructions_font = self.font
        instructions_text = "Select The Most Acidic Compound:"
        instructions_surface = instructions_font.render(instructions_text, True, (0, 0, 0))
        instructions_rect = instructions_surface.get_rect(
            center=(self.playground_rect.centerx, timer_bottom + 20))  # Position below timer
        surface.blit(instructions_surface, instructions_rect)

        # Draw score
        score_text = f"Score: {self.score}"
        score_surface = self.font.render(score_text, True, (0, 0, 0))
        score_rect = score_surface.get_rect(topright=(self.playground_rect.right - 20, self.playground_rect.y + 20))
        surface.blit(score_surface, score_rect)

        if not self.button_rects or not self.current_compounds:
            print("Button rects or compounds are not initialized!")
            print("Button rects:", self.button_rects)
            return

        # Draw compound options
        for i, (compound, button_rect) in enumerate(zip(self.current_compounds, self.button_rects)):
            # Draw button background
            button_color = (140, 140, 140) if self.button_hover_states[i] else self.button_color
            if self.feedback_displayed and i == self.selected_answer:
                button_color = (0, 255, 0) if i == self.correct_answer else (255, 0, 0)
            pygame.draw.rect(surface, button_color, button_rect, border_radius=10)

            # Draw image
            if self.cached_images[i]:
                image_rect = self.cached_images[i].get_rect(center=button_rect.center)
                surface.blit(self.cached_images[i], image_rect)

            # Draw formula
            # formula_font = pygame.font.SysFont('comicsansms', 14)
            # formula_text = self.truncate_text(compound[2]) # iupac
            # formula_surface = formula_font.render(formula_text, True, (0, 0, 0))
            # formula_rect = formula_surface.get_rect(
            #     centerx=button_rect.centerx,
            #     top=button_rect.bottom + 10
            # )
            # surface.blit(formula_surface, formula_rect)

        # Check if it's time for a new question
        current_time = time.time()

        if self.feedback_displayed and current_time - self.feedback_start >= self.feedback_duration:
            print("Loading new question due to feedback duration")
            self.select_random_minigame()
            self.load_new_question()
        elif not self.feedback_displayed and current_time - self.current_question_start >= self.question_duration:
            # Time's up for this question
            self.selected_answer = -1  # Force incorrect
            self.handle_answer()

    def Name_To_Structure(self, surface):
        if not self.current_compounds:
            print("No compounds available for Name to Structure")
            return

        # Draw timer first
        self.draw_timer(surface)

        # Calculate the position for instructions below the timer
        timer_rect = self.font.render(f"Time Left: {self.time_left}s", True, (255, 255, 255)).get_rect()
        timer_bottom = self.playground_rect.y + timer_rect.height + 10  # Add some padding

        # Draw instructions
        instructions_font = self.font
        instructions_text = "Match the following IUPAC name to its structure:"
        instructions_surface = instructions_font.render(instructions_text, True, (0, 0, 0))
        instructions_rect = instructions_surface.get_rect(
            center=(self.playground_rect.centerx, timer_bottom + 20))
        surface.blit(instructions_surface, instructions_rect)

        # Safely access the IUPAC name
        compound_font = pygame.font.SysFont('comicsansms', 20)
        compound_text = str(self.current_compounds[self.correct_answer][1])
        compound_surface = compound_font.render(compound_text, True, (0, 0, 0))
        compound_rect = compound_surface.get_rect(
            center=(self.playground_rect.centerx, instructions_rect.bottom + 20)
        )
        surface.blit(compound_surface, compound_rect)

        # Draw score
        score_text = f"Score: {self.score}"
        score_surface = self.font.render(score_text, True, (0, 0, 0))
        score_rect = score_surface.get_rect(topright=(self.playground_rect.right - 20, self.playground_rect.y + 20))
        surface.blit(score_surface, score_rect)

        # Draw compound options
        for i, (compound, button_rect) in enumerate(zip(self.current_compounds, self.button_rects)):
            # Draw button background
            button_color = (140, 140, 140) if self.button_hover_states[i] else self.button_color
            if self.feedback_displayed and i == self.selected_answer:
                button_color = (0, 255, 0) if i == self.correct_answer else (255, 0, 0)
            pygame.draw.rect(surface, button_color, button_rect, border_radius=10)

            # Draw image
            if self.cached_images[i]:
                image_rect = self.cached_images[i].get_rect(center=button_rect.center)
                surface.blit(self.cached_images[i], image_rect)

        # Check if it's time for a new question
        current_time = time.time()
        if self.feedback_displayed and current_time - self.feedback_start >= self.feedback_duration:
            self.select_random_minigame()
            self.load_new_question()
        elif not self.feedback_displayed and current_time - self.current_question_start >= self.question_duration:
            # Time's up for this question
            self.selected_answer = -1  # Force incorrect
            self.handle_answer()

    def Structure_To_Name(self, surface):
        if not self.current_compounds:
            print("No compounds available for Structure to Name")
            return

        # Draw timer first
        self.draw_timer(surface)

        # Calculate the position for instructions below the timer
        timer_rect = self.font.render(f"Time Left: {self.time_left}s", True, (255, 255, 255)).get_rect()
        timer_bottom = self.playground_rect.y + timer_rect.height + 10  # Add some padding

        # Draw instructions
        instructions_font = self.font
        instructions_text = "Match the structure to its IUPAC name:"
        instructions_surface = instructions_font.render(instructions_text, True, (0, 0, 0))
        instructions_rect = instructions_surface.get_rect(
            center=(self.playground_rect.centerx, timer_bottom + 20))  # Position below timer
        surface.blit(instructions_surface, instructions_rect)

        # Draw score
        score_text = f"Score: {self.score}"
        score_surface = self.font.render(score_text, True, (0, 0, 0))
        score_rect = score_surface.get_rect(topright=(self.playground_rect.right - 20, self.playground_rect.y + 20))
        surface.blit(score_surface, score_rect)

        # Draw compound options
        for i, (compound, button_rect) in enumerate(zip(self.current_compounds, self.button_rects)):
            # Draw button background
            button_color = (140, 140, 140) if self.button_hover_states[i] else self.button_color
            if self.feedback_displayed and i == self.selected_answer:
                button_color = (0, 255, 0) if i == self.correct_answer else (255, 0, 0)
            pygame.draw.rect(surface, button_color, button_rect, border_radius=10)

            name_font = pygame.font.SysFont('comicsansms', 16)
            name_lines = self.render_wrapped_text(compound[1], name_font, button_rect.width - 10)
            total_text_height = len(name_lines) * name_font.get_linesize()

            # Calculate the starting y position to center the text block
            start_y = button_rect.centery - total_text_height // 2

            for i, line_surface in enumerate(name_lines):
                line_rect = line_surface.get_rect(
                    centerx=button_rect.centerx,
                    top=start_y + i * name_font.get_linesize()
                )
                surface.blit(line_surface, line_rect)

        # Draw the structure to identify
        if self.cached_images[self.correct_answer]:
            structure_image = self.cached_images[self.correct_answer]
            image_rect = structure_image.get_rect(
                center=(self.playground_rect.centerx, self.playground_rect.y + 225)
            )
            surface.blit(structure_image, image_rect)

        # Check if it's time for a new question
        current_time = time.time()
        if self.feedback_displayed and current_time - self.feedback_start >= self.feedback_duration:
            self.select_random_minigame()
            self.load_new_question()
        elif not self.feedback_displayed and current_time - self.current_question_start >= self.question_duration:
            # Time's up for this question
            self.selected_answer = -1  # Force incorrect
            self.handle_answer()

    def on_event(self, event, app_instance):
        # Handle button clicks for background toggle and return to menu
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Background toggle button
            if self.button_rect.collidepoint(event.pos):
                self.toggle_background(app_instance)

            # Return to menu button
            if self.return_to_menu_rect.collidepoint(event.pos):
                return "return_to_menu"

            # Game over button
            if self.time_left <= 0 and self.game_over_button_rect.collidepoint(event.pos):
                return "return_to_menu"
        if event.type == pygame.VIDEORESIZE:
            self.width, self.height = event.w, event.h
            self.size = (self.width, self.height)
            self._display_surf = pygame.display.set_mode(self.size,
                                                         pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
            self.update_layout()

        return None

    def update_playground_rect(self):
        scale_factor = min(self.width / 1600, self.height / 1000)
        playground_width = int(1200 * scale_factor)
        playground_height = int(800 * scale_factor)

        # Center the playground in the window
        playground_left = (self.width - playground_width) // 2
        playground_top = (self.height - playground_height) // 2

        self.playground_rect = pygame.Rect(
            playground_left,
            playground_top,
            playground_width,
            playground_height
        )

    def update_layout(self):
        # Recalculate scaling factor
        scale_factor = min(self.width / 1600, self.height / 1000)

        self.update_playground_rect()

        # Update other layout elements if needed
        button_width = int(100 * scale_factor)
        button_height = int(50 * scale_factor)
        button_x = self.width - button_width
        button_y = 0  # Keep at the top-right corner

        self.button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    def handle_answer(self):
        """Process the selected answer and update game state"""
        if self.selected_answer == self.correct_answer:
            self.score += 1


        self.feedback_displayed = True
        self.feedback_start = time.time()

    def handle_click(self, pos):
        """Handle mouse clicks for answer selection"""
        # Prevent multiple clicks during feedback or if compounds not loaded
        if not self.current_compounds or self.feedback_displayed:
            return
        for i, rect in enumerate(self.button_rects):
            if rect.collidepoint(pos):
                self.selected_answer = i
                self.handle_answer()
                break

    def run_once(self, surface):
        # Draw background and playground
        surface.blit(self.current_background.image, self.current_background.rect)

        playground_surface = pygame.Surface(
            (self.playground_rect.width, self.playground_rect.height), pygame.SRCALPHA)
        playground_color = (150, 150, 150, 180) if self.dark_mode else (169, 169, 169, 180)
        pygame.draw.rect(playground_surface, playground_color,
                         playground_surface.get_rect(), border_radius=50)
        surface.blit(playground_surface, self.playground_rect)

        # Draw the button with smooth corners (rounded rectangle)
        button_color = (169, 169, 169) if self.dark_mode else (230, 230, 230)
        pygame.draw.rect(surface, button_color, self.button_rect, border_radius=10)  # Rounded corners
        music_button_color = (169, 169, 169) if self.dark_mode else (230, 230, 230)
        pygame.draw.rect(surface, music_button_color, self.music_rect, border_radius=10)

        button_text = "Light" if self.dark_mode else "Lighter"
        text_color = (255, 255, 255) if self.dark_mode else (0, 0, 0)
        button_font = pygame.font.Font('freesansbold.ttf', 20)
        button_text_surface = button_font.render(button_text, True, text_color)
        button_text_rect = button_text_surface.get_rect(center=self.button_rect.center)
        surface.blit(button_text_surface, button_text_rect)

        music_button_text = "Playing" if self.music_play else "Paused"
        text_color = (255, 255, 255) if self.dark_mode else (0, 0, 0)
        music_button_font = pygame.font.Font('freesansbold.ttf', 20)
        music_button_text_surface = music_button_font.render(music_button_text, True, text_color)
        music_button_text_rect = music_button_text_surface.get_rect(center = self.music_rect.center)
        surface.blit(music_button_text_surface, music_button_text_rect)

        # Render the return to menu button
        menu_color = (140, 140, 140) if self.menu_hover_state else (169, 169, 169) if self.dark_mode else (
        230, 230, 230)
        pygame.draw.rect(surface, menu_color, self.return_to_menu_rect, border_radius=10)
        menu_font = pygame.font.SysFont('comicsansms', 20)
        menu_text = "Menu"
        menu_surface = menu_font.render(menu_text, True, text_color)
        menu_rect = menu_surface.get_rect(center=self.return_to_menu_rect.center)
        surface.blit(menu_surface, menu_rect)

        # Update and draw timer
        if self.start_time is None:
            self.start_timer()

        self.time_left = self.update_timer()

        if self.time_left > 0:
            self.draw_timer(surface)

            # If no current question or previous question was answered, load a new question
            if not self.current_compounds or self.question_answered:
                # Randomly select a new minigame type
                self.select_random_minigame()
                self.load_new_question()

                # Load new question
                if self.load_new_question():
                    self.question_answered = False
                else:
                    print("Failed to load new question")
                    return

            # Run the selected minigame
            if self.current_minigame == "Most Acidic":
                self.setup_button_rects()
                self.Most_Acidic(surface)
            elif self.current_minigame == "Name To Structure":
                self.setup_button_rects()
                self.Name_To_Structure(surface)
            elif self.current_minigame == "Structure To Name":
                self.setup_button_rects()
                self.Structure_To_Name(surface)

        else:
            self.draw_game_over(surface)

        pygame.display.flip()

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

        if event.type == pygame.VIDEORESIZE:
            new_width, new_height = event.w, event.h
            self.resize(new_width, new_height)

            # Optional: Recreate the display surface with new size
            self._display_surf = pygame.display.set_mode(
                (new_width, new_height),
                pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE
            )

        elif event.type == pygame.MOUSEMOTION:
            # Check hover states for buttons
            self.check_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Game over state button
            if self.time_left <= 0 and self.game_over_button_rect.collidepoint(event.pos):
                self.return_to_menu = True
                self._running = False
            # Toggle music
            if self.music_rect.collidepoint(event.pos):
                self.pause_music()
            # Dark mode toggle
            elif self.button_rect.collidepoint(event.pos):
                self.toggle_background()
            # Return to menu during game
            elif self.return_to_menu_rect.collidepoint(event.pos):
                print("Return to Menu button clicked!")
                print(f"Time left: {self.time_left}")
                self.return_to_menu = True
                self._running = False
            elif self.time_left > 0:  # Only handle clicks if the game is still running
                self.handle_click(event.pos)
