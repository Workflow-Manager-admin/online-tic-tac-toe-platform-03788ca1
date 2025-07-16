from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models
from typing import Optional, List
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
