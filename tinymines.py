import sys
import random

CHECKED = 0b10000000
IS_MINE = 0b00010000
FLAGGED = 0b01000000
UNSURE =  0b00100000
SURROUNDING_MASK = 0b00001111

# TODO: make Board class only for getting and setting board spaces
# TODO: GameState class should take space coordinates in x y and convert to i for Board
# TODO: maybe use letter-digit coordinates (A1, B2, etc)
# TODO: Print win and lose states


class Board:
    __slots__ = (
        "n_mines",
        "size_x",
        "size_y",
        "board",
        "mines"
    )

    def __init__(self, size_x: int, size_y: int, n_mines: int):
        n_spaces: int = size_x * size_y
        if n_mines not in range(0, n_spaces):
            raise ValueError("too many mines")
        
        # init board
        self.size_x = size_x
        self.size_y = size_y
        self.n_mines = n_mines
        self.board = [0 for _ in range(n_spaces)]
        self.mines = set()

        # populate mines
        while len(self.mines) < n_mines:
            self.mines.add(random.randrange(n_spaces))
        
        for m in self.mines:
            self._set_mine(m)

    def get_index(self, x, y):
        return x * self.size_y + y
    
    def get_num_spaces(self):
        return self.size_x * self.size_y
    
    # def _get_space(self, i):
    #     return self.board[i]
    
    # def _set_space(self, i, new_value):
    #     self.board[i] = new_value

    def _get_space(self, x, y):
        i = self.get_index(x,y)
        return self.board[i]
    
    def _set_space(self, x, y, new_value):
        i = self.get_index(x,y)
        self.board[i] = new_value

    def _set_mine(self, i):
        self.board[i] |= IS_MINE
        # increment counts around mine
        surr = self.get_surrounding(i)
        for s in surr:
            if s not in self.mines:
                self._increment(s)

    def is_mine(self, x, y):
        return self._get_space(x,y) & IS_MINE

    def toggle_flagged(self, x, y):
        old = self._get_space(x,y)
        self._set_space(x, y, old ^ FLAGGED)

    def is_flagged(self, i):
        return self.board[i] & FLAGGED

    def toggle_unsure(self, x, y):
        old = self._get_space(x,y)
        self._set_space(x, y, old ^ UNSURE)

    def is_unsure(self, i):
        return self.board[i] & UNSURE

    def set_checked(self, x, y):
        old = self._get_space(x,y)
        self._set_space(x, y, old | CHECKED)

    def is_checked(self, i):
        return self.board[i] & CHECKED

    def _increment(self, i):
        self.board[i] += 1

    def get_dims(self):
        return (self.size_x, self.size_y)
    
    def get_unchecked(self):
        unchkd = set()
        for i in range(self.get_num_spaces()):
            if not self.is_checked(i):
                unchkd.add(i)
        return unchkd

    def adjacent_mines(self, i):
        return self.board[i] & SURROUNDING_MASK

    def get_surrounding(self, i):
        s = []
        for j in [-1, 0, 1]:
            over_left_border = j == -1 and i % self.size_x == 0
            over_right_border = j == 1 and i % self.size_x == self.size_x - 1
            if over_left_border or over_right_border:
                continue
            for k in [-1, 0, 1]:
                new_i = i + k * self.size_x + j
                if new_i == i or new_i not in range(0, self.get_num_spaces()):
                    continue
                s.append(new_i)
        return s

    def bfs(self, root_i):
        q = [root_i]
        while len(q) > 0:
            i = q.pop(0)
            # self.set_checked(i)
            self.board[i] |= CHECKED
            if self.adjacent_mines(i):
                continue
            surr_spaces = self.get_surrounding(i)
            q.extend(filter(lambda x: not self.is_checked(x), surr_spaces))

    def __str__(self):
        y = 0
        out = ""
        line = ""
        for i in range(len(self.board)):
            if self.is_checked(i):
                sur_ct = self.adjacent_mines(i)
                line += f"[{sur_ct:1}]" if sur_ct > 0 else "[ ]"
            elif self.is_flagged(i):
                line += "[F]"
            elif self.is_unsure(i):
                line += "[?]"
            else:
                line += "[■]"

            if i > 0 and i % self.size_x == self.size_x - 1:
                out += f"{y:2} {line} {y:2}\n"
                line = ""
                y += 1

        header = "   "
        for x in range(self.size_x):
            header += f"{x:2} "
        out = f"{header}\n{out}{header}"
        return out

    

class GameState:
    def __init__(self, board: Board):
        self.board = board
        self.win = False
        self.lose = False
        self.get_index = board.get_index

    def click_space(self, x, y):
        if self.board.is_mine(x, y):
            self.lose = True
        else:
            self.board.bfs(self.get_index(x, y))
            self._check_win_state()

    def click_flag(self, x, y):
        self.click_clear(x, y)
        self.board.toggle_flagged(x, y)

    def click_unsure(self, x, y):
        self.click_clear(x, y)
        self.board.toggle_unsure(x, y)

    def click_clear(self, x, y):
        i = self.get_index(x, y)
        if(self.board.is_unsure(i)):
            self.board.toggle_unsure(x,y)
        if(self.board.is_flagged(i)):
            self.board.toggle_flagged(x, y)

    def _check_win_state(self):
        self.win = self.board.mines == self.board.get_unchecked()

    def is_win_state(self):
        return self.win 
    
    def is_lose_state(self):
        return self.lose


def game_loop(state: GameState):    
    b = state.board
    print(b)
    while True:
        choice = input("enter a command or ? for help: ")
        cmd = choice.split()
        if cmd[0] in ['q', 'Q']:
            sys.exit(0) 

        if len(cmd) < 3:
            print("missing coordinates")
            continue
        x = int(cmd[1])
        y = int(cmd[2])
        
        if cmd[0] in ['check', 'c','C']:
            state.click_space(x, y)
        elif cmd[0] in ['flag', 'f', 'F']:
            state.click_flag(x, y)
        elif cmd[0] in ['unsure', 'u', 'U']:
            state.click_unsure(x, y)
        elif cmd[0] in ['clear', 'x', 'X']:
            state.click_clear(x, y)
        print(b)

        if state.is_lose_state():
            print("Lose! :(")
            break
        if state.is_win_state():
            print("Win! :)")
            break
        





def main(argv):
    b = Board(10,10,10)
    state = GameState(b)
    # print(b)
    game_loop(state)
    pass

if __name__ == "__main__":
    main(sys.argv)