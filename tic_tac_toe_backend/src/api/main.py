from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session

from . import database, crud

app = FastAPI(
    title="Tic Tac Toe API",
    description="Backend API for Online Tic Tac Toe Platform.",
    version="0.1.0",
    openapi_tags=[
        {"name": "users", "description": "User registration and listing"},
        {"name": "games", "description": "Game creation and browsing"}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Initialize the database (creates tables if needed)."""
    database.init_db()

@app.get("/", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}

# --- SCHEMAS ---

class UserCreate(BaseModel):
    username: str = Field(..., description="Desired username", min_length=1, max_length=50)

class UserOut(BaseModel):
    id: int
    username: str
    signup_time: str

    class Config:
        orm_mode = True

class GameCreate(BaseModel):
    player_x_id: int = Field(..., description="User ID for player X")
    player_o_id: Optional[int] = Field(None, description="User ID for player O (optional, may be joined later)")

class GameOut(BaseModel):
    id: int
    player_x_id: Optional[int]
    player_o_id: Optional[int]
    is_over: bool
    winner_id: Optional[int]
    created_at: str

    class Config:
        orm_mode = True

# --- USER ENDPOINTS ---

# PUBLIC_INTERFACE
@app.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["users"],
          summary="Register user", description="Register a new user (username must be unique).")
def register_user(user_in: UserCreate, db: Session = Depends(database.get_db)):
    user = crud.create_user(db, user_in.username)
    if not user:
        raise HTTPException(status_code=400, detail="Username already exists")
    return user

# PUBLIC_INTERFACE
@app.get("/users/", response_model=List[UserOut], tags=["users"], summary="List users", description="Fetch all users.")
def list_users(db: Session = Depends(database.get_db)):
    return crud.list_users(db)

# --- GAME ENDPOINTS ---

# PUBLIC_INTERFACE
@app.post("/games/", response_model=GameOut, status_code=status.HTTP_201_CREATED, tags=["games"],
          summary="Create game", description="Create a new Tic Tac Toe game.")
def create_game(game_in: GameCreate, db: Session = Depends(database.get_db)):
    # Check player X exists
    if not crud.get_user(db, game_in.player_x_id):
        raise HTTPException(status_code=400, detail=f"Player X (id={game_in.player_x_id}) does not exist")
    if game_in.player_o_id and not crud.get_user(db, game_in.player_o_id):
        raise HTTPException(status_code=400, detail=f"Player O (id={game_in.player_o_id}) does not exist")
    game = crud.create_game(db, player_x_id=game_in.player_x_id, player_o_id=game_in.player_o_id)
    return game

# PUBLIC_INTERFACE
@app.get("/games/", response_model=List[GameOut], tags=["games"], summary="List games", description="Fetch all games.")
def list_games(db: Session = Depends(database.get_db)):
    return crud.list_games(db)
