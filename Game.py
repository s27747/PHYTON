import pygame
import sqlite3
import os

pygame.init()

WIDTH, HEIGHT = 600, 600
CELL_SIZE = 50
BOARD_OFFSET = 50
SMALL_BOARD_SIZE = CELL_SIZE * 3
BIG_BOARD_SIZE = SMALL_BOARD_SIZE * 3 + 20
FONT = pygame.font.SysFont('arial', 24)
SMALL_FONT = pygame.font.SysFont('arial', 18)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
FPS = 60

MENU = 0
GAME_TYPE = 1
NICKNAME = 2
PLAYING = 3
GAME_OVER = 4

DB_FILE = 'bestScores.db'


def init_database():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    game_type TEXT PRIMARY KEY,
                    player TEXT NOT NULL,
                    score INTEGER NOT NULL
                )
            ''')
            cursor.execute('INSERT OR IGNORE INTO scores (game_type, player, score) VALUES (?, ?, ?)', ('1', 'N/A', float('inf')))
            cursor.execute('INSERT OR IGNORE INTO scores (game_type, player, score) VALUES (?, ?, ?)', ('3', 'N/A', float('inf')))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")

def save_score(game_type, player, score):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scores (game_type, player, score)
                VALUES (?, ?, ?)
            ''', (str(game_type), player, score))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving score: {e}")

def load_scores():
    default_scores = {
        '1': {'player': 'N/A', 'score': float('inf')},
        '3': {'player': 'N/A', 'score': float('inf')}
    }
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT game_type, player, score FROM scores')
            rows = cursor.fetchall()
            scores = default_scores.copy()
            for row in rows:
                scores[row[0]] = {'player': row[1], 'score': row[2]}
            return scores
    except sqlite3.Error as e:
        print(f"Error loading scores: {e}")
        return default_scores


class UltimateTicTacToe:
    def __init__(self):
        self.cursor_visible = True
        self.cursor_timer = 0
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Ultimate Tic-Tac-Toe")
        self.state = MENU
        self.current_player = 2
        self.boards = [[[0 for _ in range(3)] for _ in range(3)] for _ in range(9)]
        self.big_board = [[0 for _ in range(3)] for _ in range(3)]
        self.active_board = None
        self.move_count = 0
        self.game_type = None
        self.wins = [0, 0]
        self.player_names = ["", ""]
        self.current_name = ""
        self.name_index = 0
        init_database()
        self.best_scores = load_scores()
        self.games_played = 0
        self.winner = None

    def reset_game(self):
        self.boards = [[[0 for _ in range(3)] for _ in range(3)] for _ in range(9)]
        self.big_board = [[0 for _ in range(3)] for _ in range(3)]
        self.active_board = None
        self.current_player = 2
        self.move_count = 0
        self.winner = None

    def draw_menu(self):
        self.screen.fill(BLACK)

        title = FONT.render("Ultimate Tic Tac Toe", True, (200, 0, 200))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 150))

        start_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50)
        pygame.draw.rect(self.screen, (128, 0, 128), start_button, border_radius=10)
        text = FONT.render("Start", True, WHITE)
        text_rect = text.get_rect(center=start_button.center)
        self.screen.blit(text, text_rect)

        single_score = self.best_scores['1']
        score_text = SMALL_FONT.render(
            f"Best Single Game: {single_score['score'] if single_score['score'] != float('inf') else 'N/A'} moves by {single_score['player']}",
            True, WHITE)
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 + 60))

        best3_score = self.best_scores['3']
        score_text = SMALL_FONT.render(
            f"Best of 3: {best3_score['score'] if best3_score['score'] != float('inf') else 'N/A'} moves by {best3_score['player']}",
            True, WHITE)
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 + 90))

    def draw_game_type(self):
        self.screen.fill(BLACK)

        title = FONT.render("Choose Game Mode", True, (200, 0, 200))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 130))

        single_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 60, 200, 50)
        pygame.draw.rect(self.screen, (128, 0, 128), single_button, border_radius=10)
        text_single = FONT.render("Single Game", True, WHITE)
        text_rect = text_single.get_rect(center=single_button.center)
        self.screen.blit(text_single, text_rect)

        best3_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 10, 200, 50)
        pygame.draw.rect(self.screen, (128, 0, 128), best3_button, border_radius=10)
        text_best3 = FONT.render("Best of 3", True, WHITE)
        text_rect = text_best3.get_rect(center=best3_button.center)
        self.screen.blit(text_best3, text_rect)

    def draw_nickname(self):
        self.screen.fill(BLACK)

        title = FONT.render("Enter Player Nickname", True, (200, 0, 200))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 130))

        prompt = f"Player {self.name_index + 1} ({'O' if self.name_index == 0 else 'X'}) Nickname (max 10 chars):"
        prompt_text = SMALL_FONT.render(prompt, True, WHITE)
        self.screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2 - 60))

        input_box = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 40)
        pygame.draw.rect(self.screen, (128, 0, 128), input_box, border_radius=10)

        name_text = FONT.render(self.current_name, True, WHITE)
        self.screen.blit(name_text, (WIDTH // 2 - name_text.get_width() // 2, HEIGHT // 2 + 5))

    def draw_board(self):
        self.screen.fill(BLACK)
        for big_row in range(3):
            for big_col in range(3):
                board_idx = big_row * 3 + big_col
                x_offset = BOARD_OFFSET + big_col * (SMALL_BOARD_SIZE + 10)
                y_offset = BOARD_OFFSET + big_row * (SMALL_BOARD_SIZE + 10)

                if self.active_board == (big_row, big_col):
                    pygame.draw.rect(self.screen, (200, 200, 255),
                                     (x_offset - 5, y_offset - 5, SMALL_BOARD_SIZE + 10, SMALL_BOARD_SIZE + 10))

                for row in range(3):
                    for col in range(3):
                        x = x_offset + col * CELL_SIZE
                        y = y_offset + row * CELL_SIZE
                        pygame.draw.rect(self.screen, WHITE, (x, y, CELL_SIZE, CELL_SIZE), 1)
                        if self.boards[board_idx][row][col] == 1:
                            pygame.draw.circle(self.screen, BLUE,
                                               (x + CELL_SIZE // 2, y + CELL_SIZE // 2), CELL_SIZE // 3)
                        elif self.boards[board_idx][row][col] == 2:
                            pygame.draw.line(self.screen, RED,
                                             (x + 10, y + 10), (x + CELL_SIZE - 10, y + CELL_SIZE - 10), 3)
                            pygame.draw.line(self.screen, RED,
                                             (x + 10, y + CELL_SIZE - 10), (x + CELL_SIZE - 10, y + 10), 3)

                if self.big_board[big_row][big_col] == 1:
                    pygame.draw.circle(self.screen, BLUE,
                                       (x_offset + SMALL_BOARD_SIZE // 2, y_offset + SMALL_BOARD_SIZE // 2),
                                       SMALL_BOARD_SIZE // 3)
                elif self.big_board[big_row][big_col] == 2:
                    pygame.draw.line(self.screen, RED,
                                     (x_offset + 20, y_offset + 20),
                                     (x_offset + SMALL_BOARD_SIZE - 20, y_offset + SMALL_BOARD_SIZE - 20), 5)
                    pygame.draw.line(self.screen, RED,
                                     (x_offset + 20, y_offset + SMALL_BOARD_SIZE - 20),
                                     (x_offset + SMALL_BOARD_SIZE - 20, y_offset + 20), 5)

        status = f"{self.player_names[self.current_player - 1]}'s turn ({'X' if self.current_player == 2 else 'O'})"
        text = FONT.render(status, True, WHITE )
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 10))

    def draw_game_over(self):
        self.screen.fill(BLACK)
        if self.winner:
            text = FONT.render(f"{self.player_names[self.winner - 1]} wins in {self.move_count} moves!", True, WHITE)
        else:
            text = FONT.render("It's a draw!", True, WHITE)
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 20))

        restart_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 50)
        pygame.draw.rect(self.screen, (128, 0, 128), restart_button, border_radius=10)
        text = FONT.render("Back to Menu", True, WHITE)
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 + 35))

    def check_small_board_win(self, board_idx):
        board = self.boards[board_idx]
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] != 0:
                return board[i][0]
            if board[0][i] == board[1][i] == board[2][i] != 0:
                return board[0][i]
        if board[0][0] == board[1][1] == board[2][2] != 0:
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] != 0:
            return board[0][2]
        if all(board[row][col] != 0 for row in range(3) for col in range(3)):
            return -1
        return 0

    def check_big_board_win(self):
        for i in range(3):
            if self.big_board[i][0] == self.big_board[i][1] == self.big_board[i][2] != 0:
                return self.big_board[i][0]
            if self.big_board[0][i] == self.big_board[1][i] == self.big_board[2][i] != 0:
                return self.big_board[0][i]
        if self.big_board[0][0] == self.big_board[1][1] == self.big_board[2][2] != 0:
            return self.big_board[0][0]
        if self.big_board[0][2] == self.big_board[1][1] == self.big_board[2][0] != 0:
            return self.big_board[0][2]
        if all(self.big_board[row][col] != 0 or
               all(self.boards[row * 3 + col][r][c] != 0 for r in range(3) for c in range(3))
               for row in range(3) for col in range(3)):
            return -1
        return 0

    def update_best_score(self):
        if self.winner:
            game_type_str = str(self.game_type)
            if self.move_count < self.best_scores[game_type_str]['score']:
                self.best_scores[game_type_str] = {
                    'player': self.player_names[self.winner - 1],
                    'score': self.move_count
                }
                save_score(self.game_type, self.player_names[self.winner - 1], self.move_count)

    def handle_click(self, pos):
        if self.state == MENU:
            if WIDTH // 2 - 100 <= pos[0] <= WIDTH // 2 + 100 and HEIGHT // 2 - 25 <= pos[1] <= HEIGHT // 2 + 25:
                self.state = GAME_TYPE
        elif self.state == GAME_TYPE:
            if WIDTH // 2 - 100 <= pos[0] <= WIDTH // 2 + 100:
                if HEIGHT // 2 - 60 <= pos[1] <= HEIGHT // 2 - 10:
                    self.game_type = 1
                    self.state = NICKNAME
                    self.name_index = 0
                    self.current_name = ""
                elif HEIGHT // 2 <= pos[1] <= HEIGHT // 2 + 50:
                    self.game_type = 3
                    self.state = NICKNAME
                    self.name_index = 0
                    self.current_name = ""
        elif self.state == PLAYING:
            x, y = pos
            for big_row in range(3):
                for big_col in range(3):
                    board_idx = big_row * 3 + big_col
                    x_offset = BOARD_OFFSET + big_col * (SMALL_BOARD_SIZE + 10)
                    y_offset = BOARD_OFFSET + big_row * (SMALL_BOARD_SIZE + 10)
                    if x_offset <= x < x_offset + SMALL_BOARD_SIZE and y_offset <= y < y_offset + SMALL_BOARD_SIZE:
                        if self.active_board is None or self.active_board == (big_row, big_col):
                            if self.big_board[big_row][big_col] == 0:
                                col = (x - x_offset) // CELL_SIZE
                                row = (y - y_offset) // CELL_SIZE
                                if 0 <= row < 3 and 0 <= col < 3 and self.boards[board_idx][row][col] == 0:
                                    self.boards[board_idx][row][col] = self.current_player
                                    self.move_count += 1
                                    result = self.check_small_board_win(board_idx)
                                    if result != 0:
                                        if result != -1:
                                            self.big_board[big_row][big_col] = result
                                    next_board_idx = row * 3 + col
                                    next_big_row, next_big_col = next_board_idx // 3, next_board_idx % 3
                                    if self.big_board[next_big_row][next_big_col] != 0 or \
                                            all(self.boards[next_board_idx][r][c] != 0 for r in range(3) for c in
                                                range(3)):
                                        self.active_board = None
                                    else:
                                        self.active_board = (next_big_row, next_big_col)
                                    big_result = self.check_big_board_win()
                                    if big_result != 0:
                                        if big_result != -1:
                                            self.winner = big_result
                                            self.update_best_score()
                                        self.games_played += 1
                                        if self.game_type == 3 and self.games_played < 3 and big_result != -1:
                                            self.wins[big_result - 1] += 1
                                            if self.wins[big_result - 1] >= 2:
                                                self.state = GAME_OVER
                                            else:
                                                self.reset_game()
                                        else:
                                            self.state = GAME_OVER
                                    else:
                                        self.current_player = 1 if self.current_player == 2 else 2
        elif self.state == GAME_OVER:
            if WIDTH // 2 - 100 <= pos[0] <= WIDTH // 2 + 100 and HEIGHT // 2 + 20 <= pos[1] <= HEIGHT // 2 + 70:
                self.state = MENU
                self.reset_game()
                self.games_played = 0
                self.wins = [0, 0]

    def handle_key(self, event):
        if self.state == NICKNAME:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.current_name:
                    self.player_names[self.name_index] = self.current_name
                    self.name_index += 1
                    self.current_name = ""
                    if self.name_index == 2:
                        self.state = PLAYING
                elif event.key == pygame.K_BACKSPACE:
                    self.current_name = self.current_name[:-1]
                elif len(self.current_name) < 10 and event.unicode.isalnum():
                    self.current_name += event.unicode


def main():
    game = UltimateTicTacToe()
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                game.handle_key(event)

        if game.state == MENU:
            game.draw_menu()
        elif game.state == GAME_TYPE:
            game.draw_game_type()
        elif game.state == NICKNAME:
            game.draw_nickname()
        elif game.state == PLAYING:
            game.draw_board()
        elif game.state == GAME_OVER:
            game.draw_game_over()

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()