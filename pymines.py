import random

UNCHECKED = 0b01110000
CHECKED   = 0b10000000
FLAGGED   = 0b01000000
UNSURE    = 0b00100000
IS_MINE   = 0b00010000
SURROUNDING_MASK = 0b00001111

class PyMinesState:
    __slots__ = (
        "_b",       # List of bytes representing board spaces
        "_n_mines", # total number of mines on the board 
        "_n_rows",  # number of rows (also length of a column)
        "_n_cols",  # number of columns (also length of a row)
        "_mines",   # Set of indices where mines are located
        "_win",     # True if this is a winning state
        "_lose"     # True if this is a losing state
    )

    def __init__(self, n_rows: int, n_cols: int, n_mines: int):
        n_spaces = n_rows * n_cols
        if n_mines not in range(1, n_spaces):
            raise ValueError("too many/few mines")
        
        self._b = bytearray([0 for _ in range(n_spaces)])
        self._n_mines = n_mines
        self._n_rows = n_rows
        self._n_cols = n_cols
        self._win = False
        self._lose = False
        self._mines = set()

        # populate mines
        l = random.sample(range(n_spaces), n_mines)
        self._mines = self._mines.union(l)

        # DEBUG
        # self._mines = { }
        
        for m in self._mines:
            self._set_mine(m)
    
    def get_num_spaces(self):
        """Return the total number of spaces on the board."""
        return self._n_rows * self._n_cols

    def get_dims(self):
        """Return the dimensions of the board in a 2tuple in form (row,col)"""
        return (self._n_rows, self._n_cols)
    
    def get_board(self, formatted = True) -> list[int] | list[list[int]]:
        """Return a representation of the board of the current state 
        for frontend design purposes. If `formatted` is true, the board will be 
        returned as a 2D list. Otherwise, it is returned as a single list.

        It is important to note that the returned board will represent what the
        player will see on screen for the current state, and will not reveal the
        locations of mines unless the current state is a win or lose state. To 
        get the locations of mines, use `get_mines()`.
        
        The elements of the board will be populated as follows:
        - `IS_MINE` if the space is a mine. Shown only in win/lose states
        - `FLAGGED` if the space has a flag
        - `UNSURE` if the space has a question mark
        - `UNCHECKED` if the space hasn't been checked and doesn't have a flag
            or question mark.
        - If none of the above constants apply, then the element will be the 
            number of mines adjacent to the space. This number will always be in
            range [0, 8].
        """
        # TODO add losing move and correct flags for win/lose states
        n_spaces = self.get_num_spaces()
        row_len = self._n_cols
        out = []
        for i in range(n_spaces):
            game_over = self.is_win_state() or self.is_lose_state()
            if game_over and self._is_mine(i):
                out.append(IS_MINE)
            elif self._is_checked(i):
                out.append(self._adjacent_mines(i))
            elif self._is_flagged(i):
                out.append(FLAGGED)
            elif self._is_unsure(i):
                out.append(UNSURE)
            else:
                out.append(UNCHECKED)
            
        if formatted:
            return [out[i:i + row_len] for i in range(0, n_spaces, row_len)]
        else:
            return out
        
    def get_mines(self, formatted = True) -> set[int] | set[tuple[int]]:
        """Return a list of locations of mines for this game. If `formatted` is
        `True`, then the locations will be given as 2tuples in the format  
        (row, column). Otherwise, the locations will be given as single ints
        corresponding to the board as a flat list."""
        if formatted:
            i2rowcol = lambda i: (i // self._n_rows, i % self._n_rows)
            return set(map(i2rowcol, self._mines))
        else:
            return self._mines

    def click_space(self, row: int, col: int):
        """Register an input action on the space at the given coordinates."""
        i = self._get_index(row, col)
        if self._is_mine(i):
            self._lose = True
        else:
            self._bfs(i)
            self._check_win_state()

    def click_flag(self, row: int, col: int):
        """Add a flag at the space at the given coordinates."""
        i = self._get_index(row, col)
        self.click_clear(row, col)
        self._set_flagged(i, True)

    def click_unsure(self, row: int, col: int):
        """Add a question mark to the space at the given coordinates."""
        i = self._get_index(row, col)
        self.click_clear(row, col)
        self._set_unsure(i, True)

    def click_clear(self, row: int, col: int):
        """Clear flag and/or question mark at the given coordinates."""
        i = self._get_index(row, col)
        self._set_flagged(i, False)
        self._set_unsure(i, False)

    def is_win_state(self) -> bool:
        """Return True if the current state is a winning state."""
        return self._win 
    
    def is_lose_state(self) -> bool:
        """Return True if the current state is a losing state."""
        return self._lose

    def _get_index(self, row: int, col: int) -> int:
        """Calculate the index of the array corresponding to the given 
        coordinates on the board.
        """
        return row * self._n_cols + col

    def _check_win_state(self):
        """Set `self._win` to True if all unchecked spaces are mines."""
        self._win = self._mines == self._get_unchecked()

    def _get_space(self, i: int | tuple[int]) -> int:
        """Return the value of the space at `i`, which can be either a 2tuple of 
        coordinates (row,col) or the index of the space in the board array.
        """
        if type(i) is tuple:
            i = self._get_index(*i)
        return self._b[i]
    
    def _set_space(self, i: int | tuple[int], new_value: int):
        """Set the value of the space at `i` to `new_value`. `i` can be either a 
        2tuple of coordinates (row,col) or the index of the space in the board 
        array.
        """
        if type(i) is tuple:
            i = self._get_index(*i)
        self._b[i] = new_value

    def _get_surrounding(self, i: int):
        """Return a set of indices of spaces surrounding the space at the given
        index `i`.
        """
        s = []
        for j in [-1, 0, 1]:
            over_left_border = j == -1 and i % self._n_cols == 0
            over_right_border = j == 1 and i % self._n_cols == self._n_cols - 1
            if over_left_border or over_right_border:
                continue
            for k in [-1, 0, 1]:
                new_i = i + k * self._n_cols + j
                if new_i == i or new_i not in range(0, self.get_num_spaces()):
                    continue
                s.append(new_i)
        return s

    def _set_mine(self, i: int):
        """Set a mine at the given space, updating the surrounding spaces
        adjacent mine count in the process.
        """
        self._set_space(i, IS_MINE)

        # increment counts around mine
        surr = self._get_surrounding(i)
        for s in surr:
            if s not in self._mines:
                val = self._get_space(s)
                self._set_space(s, val + 1)

    def _is_mine(self, i: int) -> int:
        """Return `True` if the space at `i` contains a mine."""
        return self._get_space(i) & IS_MINE

    def _set_flagged(self, i: int, flagged: bool):
        """Set whether or not the space at `i` is flagged or not according
        to `flagged`.
        """
        old = self._get_space(i)
        if flagged:
            new = old | FLAGGED
        else:
            new = old & ~FLAGGED
        self._set_space(i, new)

    def _is_flagged(self, i: int) -> int:
        """Return a nonzero integer if the space at `i` is flagged."""
        return self._get_space(i) & FLAGGED

    def _set_unsure(self, i: int, unsure: bool):
        """Set whether or not the space at `i` has a question mark or not 
        according to `unsure`.
        """
        old = self._get_space(i)
        if unsure:
            new = old | UNSURE
        else:
            new = old & ~UNSURE
        self._set_space(i, new)

    def _is_unsure(self, i: int) -> int:
        """Returns a nonzero integer if the space at `i` has a question mark."""
        return self._get_space(i) & UNSURE

    def _set_checked(self, i: int):
        """Set the space at `i` as having been checked."""
        old = self._get_space(i)
        self._set_space(i, old | CHECKED)

    def _is_checked(self, i: int):
        """Returns a nonzero integer if the space at `i` has been checked."""
        return self._get_space(i) & CHECKED
    
    def _get_unchecked(self) -> set[int]:
        """Return a set of all spaces that haven't been checked."""
        unchkd = set()
        for i in range(self.get_num_spaces()):
            if not self._is_checked(i):
                unchkd.add(i)
        return unchkd

    def _adjacent_mines(self, i: int) -> int:
        """Return the number of mines adjacent to the space at `i`"""
        return self._get_space(i) & SURROUNDING_MASK

    def _bfs(self, root_i: int):
        """Broadly traverse the board starting at `root_i`, marking all spaces
        visited as checked and stopping at spaces that have an adjacent mine
        count. The board is modified in place."""
        q = {root_i}
        while len(q) > 0:
            i = q.pop()
            self._set_checked(i)
            if self._adjacent_mines(i):
                continue
            surr_spaces = self._get_surrounding(i)
            q.update(filter(lambda x: not self._is_checked(x), surr_spaces))

# basic text interface when run from command line
# TODO: maybe use letter-digit coordinates (A1, B2, etc)
HELP_MSG="""
How to play:
help           - display this help message (alias: ?)
quit           - exit the game (alias: x)
check row col  - check the space at row,col (alias: c)
flag row col   - place a flag at row,col (alias: f)
unsure row col - place a ? at row,col (alias: u)
clear row col  - remove flag or ? at row,col (alias: x)
"""

def print_board(state: PyMinesState):
    """Print the board"""
    b = state.get_board()
    _, row_length = state.get_dims()
    out = ""
    for i, row in enumerate(b):
        line = ""
        for col in row:
            if col == IS_MINE:
                line += "[*]"
            elif col == UNCHECKED:
                line += "[⏹]"
            elif col == FLAGGED:
                line += "[⚑]"
            elif col == UNSURE:
                line += "[?]"
            else:
                line += f"[{col:1}]" if col > 0 else '[ ]'
        out += f"{i:2} {line} {i:2}\n"
    header = "   "
    for i in range(row_length):
        header += f"{i:2} "
    out = f"{header}\n{out}{header}"
    print(out)


def game_loop(state: PyMinesState):    
    """Main game loop. Uses an REPL interface"""
    n_rows, n_cols = state.get_dims()
    while True:
        print_board(state)

        if state.is_lose_state():
            print("Lose! :(")
            break
        if state.is_win_state():
            print("Win! :)")
            break

        choice = input("Enter a command or ? for help: ")
        cmd = choice.split()
        if cmd[0] in ['q', 'Q']:
            print("Bye bye!")
            sys.exit(0) 
        elif cmd[0] in ['help', '?']:
            print(HELP_MSG)
            continue

        if len(cmd) < 3:
            print("Missing coordinates")
            continue
        row = int(cmd[1])
        col = int(cmd[2])

        if not (row in range(0, n_rows) or col in range(0, n_cols)):
            print("Coordinates out of board range.")
            continue
        
        if cmd[0] in ['check', 'c','C']:
            state.click_space(row, col)
        elif cmd[0] in ['flag', 'f', 'F']:
            state.click_flag(row, col)
        elif cmd[0] in ['unsure', 'u', 'U']:
            state.click_unsure(row, col)
        elif cmd[0] in ['clear', 'x', 'X']:
            state.click_clear(row, col)

def main(argv):
    """Basic CLI frontend for pyMines"""
    if len(argv) == 4:
        row = int(argv[1])
        col = int(argv[2])
        n_mines = int(argv[3])
    else:
        print("usage: pymines.py rows columns num_mines")
        sys.exit(0)
    while(True):
        state = PyMinesState(row, col, n_mines)
        game_loop(state)
        new_game = input("Play again? (y/n) (default: y) ") or 'y'
        if new_game[0] in ['n', 'N']:
            break

    print("Bye bye!")
    sys.exit(0) 

if __name__ == "__main__":
    import sys
    main(sys.argv)
