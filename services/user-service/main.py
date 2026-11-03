from contextlib import asynccontextmanager

import grpc
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, select

from auth import create_access_token, hash_password, verify_password
from db import engine, get_session
from models import User, UserPublic
import product_pb2
import product_pb2_grpc
from shared.jwt_utils import verify_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: list your frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "user-service"}


@app.post("/users/", response_model=UserPublic)
def create_user(user: User, session: Session = Depends(get_session)):
    user.password = hash_password(user.password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/users/", response_model=list[UserPublic])
def read_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()


@app.get("/users/{user_id}/purchases/{product_id}")
def get_user_purchase(
    user_id: int,
    product_id: int,
    token_data: dict = Depends(verify_token),
):
    if str(user_id) != token_data.get("sub"):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this resource"
        )

    # Connect to the Product service via gRPC
    with grpc.insecure_channel("product-service:50051") as channel:
        stub = product_pb2_grpc.ProductServiceStub(channel)
        response = stub.GetProduct(product_pb2.ProductRequest(id=product_id))

    return {
        "user_id": user_id,
        "product_details": {
            "id": response.id,
            "name": response.name,
            "price": response.price,
        },
        "source": "gRPC",
    }


@app.post("/login")
def login(user_data: User, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == user_data.email)
    db_user = session.exec(statement).first()

    if not db_user or not verify_password(user_data.password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token = create_access_token(data={"sub": str(db_user.id), "email": db_user.email})
    return {"access_token": token, "token_type": "bearer"}
