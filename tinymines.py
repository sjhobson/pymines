import sys
import random

CHECKED = 0b10000000
IS_MINE = 0b00010000
FLAGGED = 0b01000000
UNSURE =  0b00100000
SURROUNDING_MASK = 0b00001111

# TODO: Merge Board and GameState classes
# TODO: maybe use letter-digit coordinates (A1, B2, etc)

class Board:
    """Representation of a Minesweeper board. Board is a byte array of length x*y
    where x and y are the board dimensions. Array elements are bytes which
    represent the contents of the space (mine, flagged, etc)"""

    __slots__ = (
        "n_mines", # total number of mines on the board
        "size_x",  # x dimension
        "size_y",  # y dimension
        "board"   # Array<int> of board spaces
    )

    def __init__(self, size_x: int, size_y: int, n_mines: int):
        """ create a game board of size size_x x size_y and n_mines mines
        """
        n_spaces: int = size_x * size_y
        if n_mines not in range(0, n_spaces):
            raise ValueError("too many mines")
        
        # init board
        self.size_x = size_x
        self.size_y = size_y
        self.n_mines = n_mines
        self.board = [0 for _ in range(n_spaces)]
    
    def get_num_spaces(self):
        """Return the total number of spaces on the board"""
        return self.size_x * self.size_y

    def get_dims(self):
        """Return the dimensions of the board in a 2tuple in form (x,y)"""
        return (self.size_x, self.size_y)
    
    def get_space(self, i):
        """Return the value of the space at i"""
        return self.board[i]
    
    def set_space(self, i, new_value):
        """Set the value of the space at i to new_value"""
        self.board[i] = new_value

    def get_surrounding(self, i):
        """Return a set of indices of spaces surrounding the space at the given
        index i
        """
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
    

    

class GameState:
    __slots__ = (
        "_b",       # The board itself
        "_n_mines", # total number of mines on the board # TODO not necessary?
        "_mines",   # Set of indices where mines are located
        "_win",     # True if this is a winning state
        "_lose"     # True if this is a losing state
    )

    def __init__(self, size_x: int, size_y: int, n_mines: int):
        self._b = Board(size_x, size_y, n_mines)
        self._n_mines = n_mines
        self._win = False
        self._lose = False
        self._mines = set()

        # populate mines
        n_spaces = self._b.get_num_spaces()
        l = random.sample(range(n_spaces), n_mines)
        self._mines = self._mines.union(l)

        # DEBUG
        # self._mines = {50}
        
        for m in self._mines:
            self._set_mine(m)


    def click_space(self, x, y):
        i = self._get_index(x, y)
        if self._is_mine(i):
            self._lose = True
        else:
            self.bfs(i)
            self._check_win_state()

    def click_flag(self, x, y):
        i = self._get_index(x, y)
        self.click_clear(x, y)
        self._toggle_flagged(i)

    def click_unsure(self, x, y):
        i = self._get_index(x, y)
        self.click_clear(x, y)
        self._toggle_unsure(i)

    def click_clear(self, x, y):
        i = self._get_index(x, y)
        if(self._is_unsure(i)):
            self._toggle_unsure(i)
        if(self._is_flagged(i)):
            self._toggle_flagged(i)

    def is_win_state(self):
        return self._win 
    
    def is_lose_state(self):
        return self._lose

    def _get_index(self, x, y):
        """Calculate the index of the array corresponding to the given 
        coordinates on the board
        """
        _, size_y = self._b.get_dims()
        return x * size_y + y

    def _check_win_state(self):
        self._win = self._mines == self._get_unchecked()

    def get_space(self, i):
        """Return the value of the space at (x, y)"""
        return self._b.get_space(i)
    
    def set_space(self, i, new_value):
        """Set the value of the space at (x,y) to new_value"""
        self._b.set_space(i, new_value)

    def _set_mine(self, i):
        self._b.set_space(i, IS_MINE)
        # self.board[i] |= IS_MINE
        # increment counts around mine
        surr = self._b.get_surrounding(i)
        for s in surr:
            if s not in self._mines:
                # self._increment(s)
                val = self.get_space(s)
                self._b.set_space(s, val + 1)

    def _is_mine(self, i):
        return self.get_space(i) & IS_MINE

    # TODO make into a set function that takes a boolean instead
    def _toggle_flagged(self, i):
        old = self.get_space(i)
        self.set_space(i, old ^ FLAGGED)

    def _is_flagged(self, i):
        return self.get_space(i) & FLAGGED

    # TODO make into a set function that takes a boolean instead
    def _toggle_unsure(self, i):
        old = self.get_space(i)
        self.set_space(i, old ^ UNSURE)

    def _is_unsure(self, i):
        return self.get_space(i) & UNSURE

    def _set_checked(self, i):
        # i = self._get_index(x, y)
        old = self.get_space(i)
        self.set_space(i, old | CHECKED)

    def _is_checked(self, i):
        # i = self._get_index(x, y)
        return self.get_space(i) & CHECKED
    
    def _get_unchecked(self):
        unchkd = set()
        for i in range(self._b.get_num_spaces()):
            if not self._is_checked(i):
                unchkd.add(i)
        return unchkd

    def _adjacent_mines(self, i):
        # i = self._get_index(x, y)
        return self.get_space(i) & SURROUNDING_MASK

    def bfs(self, root_i):
        q = [root_i]
        while len(q) > 0:
            i = q.pop(0)
            self._set_checked(i)
            # self.board[i] |= CHECKED
            if self._adjacent_mines(i):
                continue
            surr_spaces = self._b.get_surrounding(i)
            q.extend(filter(lambda x: not self._is_checked(x), surr_spaces))

    def __str__(self):
        # TODO print losing move and correct flags
        size_x, _ = self._b.get_dims()
        y = 0
        out = ""
        line = ""
        for i in range(self._b.get_num_spaces()):
            game_over = self.is_lose_state() or self.is_win_state()
            if game_over and self._is_mine(i):
                line += "[*]"
            elif self._is_checked(i):
                sur_ct = self._adjacent_mines(i)
                line += f"[{sur_ct:1}]" if sur_ct > 0 else '[ ]'
            elif self._is_flagged(i):
                line += "[⚑]"
            elif self._is_unsure(i):
                line += "[?]"
            else:
                line += "[⏹]"

            if i > 0 and i % size_x == size_x - 1:
                out += f"{y:2} {line} {y:2}\n"
                line = ""
                y += 1

        header = "   "
        for x in range(size_x):
            header += f"{x:2} "
        out = f"{header}\n{out}{header}"
        return out


def game_loop(state: GameState):    
    print(state)
    while True:
        choice = input("enter a command or ? for help: ")
        cmd = choice.split()
        if cmd[0] in ['q', 'Q']:
            print("Bye bye!")
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
        print(state)

        if state.is_lose_state():
            print("Lose! :(")
            break
        if state.is_win_state():
            print("Win! :)")
            break

def main(argv):
    while(True):
        state = GameState(10, 10, 10)
        game_loop(state)
        new_game = input("Play again? (y/n)")
        if new_game[0] in ['y', 'Y']:
            continue
        else:
            print("Bye bye!")
            sys.exit(0) 

if __name__ == "__main__":
    main(sys.argv)