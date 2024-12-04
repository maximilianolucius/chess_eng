import subprocess


class ChessEngine:
    def __init__(self, engine_path):
        # Start the engine process
        self.engine = subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self._initialize_engine()

    def _initialize_engine(self):
        # Initialize the engine with UCI protocol
        self._send_command("uci")
        while True:
            output = self._read_output()
            if output == "uciok":
                break

        # Set engine options to minimize memory usage
        self._send_command("isready")
        self._send_command("setoption name Hash value 1")

    def _send_command(self, command):
        """Send a command to the engine."""

        self.engine.stdin.write(command + "\n")
        self.engine.stdin.flush()

    def _read_output(self):
        """Read a single line of output from the engine."""
        output = self.engine.stdout.readline().strip()
        return output

    def get_best_move(self, fen, movetime=200):
        """Get the best move for a given position."""
        # Set the position
        self._send_command(f"position fen {fen}")

        # Start the search
        self._send_command(f"go movetime {movetime}")

        # Wait for the best move
        best_move = None
        while True:
            output = self._read_output()
            if output.startswith("bestmove"):
                best_move = output.split()[1]
                break

        # Clear the engine's internal cache to minimize memory usage
        self._send_command("setoption name Clear Hash")

        return best_move

    def stop(self):
        """Stop the engine process."""
        self._send_command("quit")
        self.engine.terminate()
        self.engine.wait()


# How to load database, and prepare it.
filename = '/kaggle_simulations/agent/chess_data.bin'
try:
    with open(filename, 'rb') as file:
        pass
except:
    filename = './chess_data.bin'

item_size = 34  # Each item is 34 bytes

def board_to_fen(board) -> str:
    number_to_piece = {
        0: '',  # Empty squares will be handled by counting
        1: 'P', 2: 'N', 3: 'B', 4: 'R', 5: 'Q', 6: 'K',
        7: 'p', 8: 'n', 9: 'b', 10: 'r', 11: 'q', 12: 'k'
    }

    fen_rows = []
    # FEN notation starts from rank 8 (top of the board)
    for rank in range(7, -1, -1):  # From rank 7 down to 0
        row = ''
        empty_count = 0
        for file in range(8):
            index = rank * 8 + file
            piece = number_to_piece.get(board[index], '')
            if piece == '':
                empty_count += 1
            else:
                if empty_count > 0:
                    row += str(empty_count)
                    empty_count = 0
                row += piece
        if empty_count > 0:
            row += str(empty_count)
        fen_rows.append(row)
    return '/'.join(reversed(fen_rows))

def unpack_data(data_bytes):
    data_bits = ''
    for byte in data_bytes:
        data_bits += format(byte, '08b')

    index = 0
    board = []
    # Unpack board (64 squares * 4 bits)
    for _ in range(64):
        bits = data_bits[index:index + 4]
        if len(bits) < 4:
            raise ValueError("Insufficient bits for board data.")
        value = int(bits, 2)
        board.append(value)
        index += 4

    # Unpack from-square index (6 bits)
    bits = data_bits[index:index + 6]
    if len(bits) < 6:
        raise ValueError("Insufficient bits for from-square index.")
    from_index = int(bits, 2)
    index += 6

    # Unpack to-square index (6 bits)
    bits = data_bits[index:index + 6]
    if len(bits) < 6:
        raise ValueError("Insufficient bits for to-square index.")
    to_index = int(bits, 2)
    index += 6

    # Unpack promotion piece (3 bits)
    bits = data_bits[index:index + 3]
    if len(bits) < 3:
        raise ValueError("Insufficient bits for promotion piece.")
    promotion_piece = int(bits, 2)
    index += 3

    return board, (from_index, to_index, promotion_piece)

def index_to_square_name(index: int) -> str:
    if index < 0 or index > 63:
        raise ValueError(f"Invalid index: {index}")

    file = index % 8
    rank = 8 - (index // 8)
    file_char = chr(ord('a') + file)
    return f"{file_char}{rank}"


moves_dict = {}
with open(filename, 'rb') as file:
    while True:
        data_bytes = file.read(item_size)
        if not data_bytes:
            break  # End of file
        if len(data_bytes) != item_size:
            raise ValueError("Incomplete item read from file.")
        # Unpack data
        board, move = unpack_data(data_bytes)

        key = board_to_fen(board)

        # Decode the move
        from_square = index_to_square_name(move[0])
        to_square = index_to_square_name(move[1])
        promotion_pieces = {0: '', 1: 'n', 2: 'b', 3: 'r', 4: 'q'}
        promotion_char = promotion_pieces.get(move[2], '')
        move_str = f"{from_square}{to_square}{promotion_char}"
        moves_dict[key] = move_str


use_db_flag = True


# Define a global variable to store the ChessEngine instance
ultima = None

def chess_bot(obs):
    global ultima, moves_dict, use_db_flag # Declare ultima as global to modify it

    fen = obs['board']

    if use_db_flag:
        best_move = moves_dict.get(fen.split(' ')[0], None)
        if best_move is not None:
            return best_move
        else:
            del moves_dict
            moves_dict = None
            use_db_flag = False

    remainingOverageTime = obs.remainingOverageTime

    movetime = 175
    if remainingOverageTime < 3.675:
        movetime = 175
    if remainingOverageTime < 1.875:
        movetime = 90
    if remainingOverageTime < 1:
        movetime = 75

    # (10-3.675)/0.175+(3.675-1.875)/0.12+1.75/0.085

    engine_path = '/kaggle_simulations/agent/AltairChess'
    if ultima is None:
        try:
            ultima = ChessEngine(engine_path)
        except:
            ultima = ChessEngine('./submissions/altairchess_with_esteriod_v2.1.4/AltairChess')


    # Get the best move from the engine
    best_move = ultima.get_best_move(fen, movetime=movetime)


    return best_move

