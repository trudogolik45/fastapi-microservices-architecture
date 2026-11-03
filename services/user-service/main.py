from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlmodel import Session, SQLModel, select

from db import engine, get_session
from models import User, UserPublic


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "user-service"}


@app.post("/users/", response_model=UserPublic)
def create_user(user: User, session: Session = Depends(get_session)):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/users/", response_model=list[UserPublic])
def read_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()
