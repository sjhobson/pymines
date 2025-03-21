import sys
import random

CHECKED = 0b10000000
IS_MINE = 0b00010000
FLAGGED = 0b01000000
UNSURE =  0b00100000
SURROUNDING_MASK = 0b00001111

# TODO: maybe use letter-digit coordinates (A1, B2, etc)

class GameState:
    __slots__ = (
        "_b",       # List of ints representing board spaces
        "_n_mines", # total number of mines on the board 
        "_size_x",  # x dimension
        "_size_y",  # y dimension
        "_mines",   # Set of indices where mines are located
        "_win",     # True if this is a winning state
        "_lose"     # True if this is a losing state
    )

    def __init__(self, size_x: int, size_y: int, n_mines: int):
        n_spaces = size_x * size_y
        if n_mines not in range(1, n_spaces):
            raise ValueError("too many/few mines")
        
        self._b = [0 for _ in range(n_spaces)]
        self._n_mines = n_mines
        self._size_x = size_x
        self._size_y = size_y
        self._win = False
        self._lose = False
        self._mines = set()

        # populate mines
        l = random.sample(range(n_spaces), n_mines)
        self._mines = self._mines.union(l)

        # DEBUG
        # self._mines = {50}
        
        for m in self._mines:
            self._set_mine(m)
    
    def get_num_spaces(self):
        """Return the total number of spaces on the board"""
        return self._size_x * self._size_y

    def get_dims(self):
        """Return the dimensions of the board in a 2tuple in form (x,y)"""
        return (self._size_x, self._size_y)

    def get_space(self, i: int | tuple[int]) -> int:
        """Return the value of the space at `i`, which can be either a 2tuple of 
        coordinates (x,y) or the index of the space in the board array.
        """
        if type(i) is tuple:
            i = self._get_index(*i)
        return self._b[i]
    
    def set_space(self, i: int | tuple[int], new_value: int):
        """Set the value of the space at `i` to `new_value`. `i` can be either a 
        2tuple of coordinates (x,y) or the index of the space in the board 
        array.
        """
        if type(i) is tuple:
            i = self._get_index(*i)
        self._b[i] = new_value

    def click_space(self, x: int, y: int):
        """Register an input action on the space at the given coordinates"""
        i = self._get_index(x, y)
        if self._is_mine(i):
            self._lose = True
        else:
            self._bfs(i)
            self._check_win_state()

    def click_flag(self, x: int, y: int):
        """Add a flag at the space at the given coordinates"""
        i = self._get_index(x, y)
        self.click_clear(x, y)
        self._set_flagged(i, True)

    def click_unsure(self, x: int, y: int):
        """Add a question mark to the space at the given coordinates"""
        i = self._get_index(x, y)
        self.click_clear(x, y)
        self._set_unsure(i, True)

    def click_clear(self, x: int, y: int):
        """Clear flag and/or question mark at the given coordinates"""
        i = self._get_index(x, y)
        self._set_flagged(i, False)
        self._set_unsure(i, False)
        # if(self._is_unsure(i)):
        #     self._toggle_unsure(i)
        # if(self._is_flagged(i)):
        #     self._toggle_flagged(i)

    def is_win_state(self) -> bool:
        """Return True if the current state is a winning state"""
        return self._win 
    
    def is_lose_state(self) -> bool:
        """Return True if the current state is a losing state"""
        return self._lose

    def _get_index(self, x: int, y: int) -> int:
        """Calculate the index of the array corresponding to the given 
        coordinates on the board
        """
        return x * self._size_y + y

    def _check_win_state(self):
        """Set `self._win` to True if all unchecked spaces are mines"""
        self._win = self._mines == self._get_unchecked()

    def _get_surrounding(self, i: int):
        """Return a set of indices of spaces surrounding the space at the given
        index `i`
        """
        s = []
        for j in [-1, 0, 1]:
            over_left_border = j == -1 and i % self._size_x == 0
            over_right_border = j == 1 and i % self._size_x == self._size_x - 1
            if over_left_border or over_right_border:
                continue
            for k in [-1, 0, 1]:
                new_i = i + k * self._size_x + j
                if new_i == i or new_i not in range(0, self.get_num_spaces()):
                    continue
                s.append(new_i)
        return s


    def _set_mine(self, i: int):
        """Set a mine at the given space, updating the surrounding spaces
        adjacent mine count in the process.
        """
        self.set_space(i, IS_MINE)

        # increment counts around mine
        surr = self._get_surrounding(i)
        for s in surr:
            if s not in self._mines:
                # self._increment(s)
                val = self.get_space(s)
                self.set_space(s, val + 1)

    def _is_mine(self, i: int) -> int:
        """Return `True` if the space at `i` contains a mine"""
        return self.get_space(i) & IS_MINE

    def _set_flagged(self, i: int, flagged: bool):
        """Set whether or not the space at `i` is flagged or not according
        to `flagged`
        """
        old = self.get_space(i)
        if flagged:
            new = old | FLAGGED
        else:
            new = old & ~FLAGGED
        self.set_space(i, new)

    def _is_flagged(self, i: int) -> int:
        """Return a nonzero integer if the space at `i` is flagged."""
        return self.get_space(i) & FLAGGED

    def _set_unsure(self, i: int, unsure: bool):
        """Set whether or not the space at `i` has a question mark or not 
        according to `unsure`
        """
        old = self.get_space(i)
        if unsure:
            new = old | UNSURE
        else:
            new = old & ~UNSURE
        self.set_space(i, new)

    def _is_unsure(self, i: int) -> int:
        """Returns a nonzero integer if the space at `i` has a question mark"""
        return self.get_space(i) & UNSURE

    def _set_checked(self, i: int):
        """Set the space at `i` as having been checked"""
        # i = self._get_index(x, y)
        old = self.get_space(i)
        self.set_space(i, old | CHECKED)

    def _is_checked(self, i: int):
        """Returns a nonzero integer if the space at `i` has been checked"""
        # i = self._get_index(x, y)
        return self.get_space(i) & CHECKED
    
    def _get_unchecked(self) -> set[int]:
        """Return a set of all spaces that haven't been checked"""
        unchkd = set()
        for i in range(self.get_num_spaces()):
            if not self._is_checked(i):
                unchkd.add(i)
        return unchkd

    def _adjacent_mines(self, i: int) -> int:
        """Return the number of mines adjacent to the space at `i`"""
        # i = self._get_index(x, y)
        return self.get_space(i) & SURROUNDING_MASK

    def _bfs(self, root_i: int):
        """Broadly traverse the board starting at `root_i`, marking all spaces
        visited as checked and stopping at spaces that have an adjacent mine
        count. The board is modified in place."""
        q = [root_i]
        while len(q) > 0:
            i = q.pop(0)
            self._set_checked(i)
            # self.board[i] |= CHECKED
            if self._adjacent_mines(i):
                continue
            surr_spaces = self._get_surrounding(i)
            q.extend(filter(lambda x: not self._is_checked(x), surr_spaces))

    def __str__(self):
        # TODO print losing move and correct flags
        # TODO move this implementation out of GameState into an external function
        #      and implement a simpler representation here.
        y = 0
        out = ""
        line = ""
        for i in range(self.get_num_spaces()):
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

            if i > 0 and i % self.size_x == self.size_x - 1:
                out += f"{y:2} {line} {y:2}\n"
                line = ""
                y += 1

        header = "   "
        for x in range(self.size_x):
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
        new_game = input("Play again? (y/n) (default: y) ")
        if new_game[0] in ['n', 'N']:
            break

    print("Bye bye!")
    sys.exit(0) 

if __name__ == "__main__":
    main(sys.argv)