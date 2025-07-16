from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models
from typing import Optional, List, Tuple
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import os

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev_secret_jwt_key_change_this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h

# --- USER CRUD ---

# PUBLIC_INTERFACE
def create_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Create a new user with a hashed password. Returns user if successful, None if username exists."""
    hash_ = pwd_context.hash(password)
    user = models.User(username=username, password_hash=hash_)
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        return None

# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

# PUBLIC_INTERFACE
def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Check username/password and return user if valid, else None."""
    user = get_user_by_username(db, username)
    if user and verify_password(password, user.password_hash):
        return user
    return None

# PUBLIC_INTERFACE
def create_access_token(*, data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token encoding the specified data."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# PUBLIC_INTERFACE
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Retrieve a user by ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

# PUBLIC_INTERFACE
def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Retrieve a user by username."""
    return db.query(models.User).filter(models.User.username == username).first()

# PUBLIC_INTERFACE
def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """List users with pagination."""
    return db.query(models.User).offset(skip).limit(limit).all()

# --- GAME CRUD ---

# PUBLIC_INTERFACE
def create_game(db: Session, player_x_id: Optional[int], player_o_id: Optional[int] = None) -> models.Game:
    """Create a new game. Player X required, Player O optional."""
    game = models.Game(player_x_id=player_x_id, player_o_id=player_o_id)
    db.add(game)
    db.commit()
    db.refresh(game)
    # Create initial state for game
    state = models.GameState(game_id=game.id, board=" " * 9, turn=models.MarkEnum.X)
    db.add(state)
    db.commit()
    db.refresh(game)
    return game

# PUBLIC_INTERFACE
def get_game(db: Session, game_id: int) -> Optional[models.Game]:
    """Retrieve game by id, including its state."""
    return db.query(models.Game).filter(models.Game.id == game_id).first()

# PUBLIC_INTERFACE
def list_games(db: Session, skip: int = 0, limit: int = 100) -> List[models.Game]:
    """List games, paginated."""
    return db.query(models.Game).offset(skip).limit(limit).all()

# PUBLIC_INTERFACE
def join_game(db: Session, game_id: int, user_id: int) -> Optional[models.Game]:
    """Let a user join a game as O if slot is free."""
    game = get_game(db, game_id)
    if not game or game.player_o_id is not None or game.player_x_id == user_id:
        return None
    game.player_o_id = user_id
    db.commit()
    db.refresh(game)
    return game

# PUBLIC_INTERFACE
def get_game_state(db: Session, game_id: int) -> Optional[models.GameState]:
    """Get the state (board/turn) for a game."""
    return db.query(models.GameState).filter(models.GameState.game_id == game_id).first()

def _set_game_over(db: Session, game: models.Game, winner_id=None):
    game.is_over = True
    if winner_id:
        game.winner_id = winner_id
    db.commit()
    db.refresh(game)

def _check_winner(board: str) -> Optional[str]:
    WIN_COMBOS = [
        [0,1,2],[3,4,5],[6,7,8],
        [0,3,6],[1,4,7],[2,5,8],
        [0,4,8],[2,4,6]
    ]
    for c in WIN_COMBOS:
        if board[c[0]] == board[c[1]] == board[c[2]] and board[c[0]] in "XO":
            return board[c[0]]
    return None

def _is_draw(board: str) -> bool:
    return " " not in board and _check_winner(board) is None

# PUBLIC_INTERFACE
def make_move(db: Session, game_id: int, user_id: int, position: int) -> Tuple[Optional[models.Game], Optional[models.GameState], str]:
    """Attempt to make a move. Returns updated game, gamestate, and a status string message."""
    game = get_game(db, game_id)
    if not game or game.is_over:
        return (None, None, "Game does not exist or already finished")
    state = get_game_state(db, game_id)
    # Determine symbol for this user
    if user_id == game.player_x_id:
        symbol = "X"
    elif user_id == game.player_o_id:
        symbol = "O"
    else:
        return (game, state, "User is not a player in this game")
    if (symbol == "X" and state.turn != models.MarkEnum.X) or (symbol == "O" and state.turn != models.MarkEnum.O):
        return (game, state, "Not your turn")
    # Validate position
    if not (0 <= position <= 8):
        return (game, state, "Position must be 0-8")
    if state.board[position] != " ":
        return (game, state, "Position already taken")
    # Make move
    board_list = list(state.board)
    board_list[position] = symbol
    state.board = "".join(board_list)
    # Switch turn
    state.turn = models.MarkEnum.O if state.turn == models.MarkEnum.X else models.MarkEnum.X
    db.commit()
    db.refresh(state)
    # Check for win
    winner = _check_winner(state.board)
    if winner:
        _set_game_over(db, game, winner_id=game.player_x_id if winner == "X" else game.player_o_id)
        msg = f"Player {winner} wins!"
        db.refresh(game)  # To update is_over
        return (game, state, msg)
    if _is_draw(state.board):
        _set_game_over(db, game)
        db.refresh(game)
        return (game, state, "Draw! No more valid moves")
    return (game, state, "Move accepted")

# PUBLIC_INTERFACE
def get_user_games(db: Session, user_id: int) -> List[models.Game]:
    """Fetch history of games where user was X, O (or winner), sorted by creation."""
    return db.query(models.Game).filter(
        ((models.Game.player_x_id == user_id) | (models.Game.player_o_id == user_id))
    ).order_by(models.Game.created_at.desc()).all()
