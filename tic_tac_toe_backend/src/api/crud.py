from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models
from typing import Optional, List

# --- USER CRUD ---

# PUBLIC_INTERFACE
def create_user(db: Session, username: str) -> Optional[models.User]:
    """Create a new user. Returns user if successful, None if username exists."""
    user = models.User(username=username)
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        return None

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
