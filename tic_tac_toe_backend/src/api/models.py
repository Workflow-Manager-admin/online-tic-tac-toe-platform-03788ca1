from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class MarkEnum(str, enum.Enum):
    X = "X"
    O = "O"
    empty = ""


# PUBLIC_INTERFACE
class User(Base):
    """User table for storing player info."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    signup_time = Column(DateTime, default=datetime.utcnow)

    games = relationship("Game", back_populates="player_x", foreign_keys="Game.player_x_id")
    games_as_o = relationship("Game", back_populates="player_o", foreign_keys="Game.player_o_id")


# PUBLIC_INTERFACE
class Game(Base):
    """Game table for Tic Tac Toe matches."""
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    player_x_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    player_o_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_over = Column(Boolean, default=False)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    player_x = relationship("User", foreign_keys=[player_x_id], back_populates="games")
    player_o = relationship("User", foreign_keys=[player_o_id], back_populates="games_as_o")
    winner = relationship("User", foreign_keys=[winner_id])
    state = relationship("GameState", back_populates="game", uselist=False, cascade="all, delete-orphan")


# PUBLIC_INTERFACE
class GameState(Base):
    """Store board state and whose turn it is for a given Game."""
    __tablename__ = "game_states"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), unique=True, nullable=False)
    board = Column(String(20), nullable=False, default=" " * 9)  # Board stored as a 9-char string
    turn = Column(Enum(MarkEnum), nullable=False, default=MarkEnum.X)

    game = relationship("Game", back_populates="state")
