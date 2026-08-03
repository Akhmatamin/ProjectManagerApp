from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.shared.db.database import get_db
from app.auth.models import RefreshToken
from app.users.models import User
from .schemas import (UserRegisterSchema, UserLoginSchema,
                      ChangePasswordSchema, RefreshTokenSchema,
                      ResetPasswordSchema)
from app.shared.config import REFRESH_TOKEN_LIFETIME
from sqlalchemy.orm import Session
from .service import (get_password_hash, verify_password, create_access_token,
                      create_refresh_token,get_current_user, generate_code)


auth_router = APIRouter(prefix="/auth", tags=["Auth"])




@auth_router.post('/register', response_model=dict, status_code=status.HTTP_201_CREATED)
def register(user: UserRegisterSchema, db: Session = Depends(get_db)):
    hash_password = get_password_hash(user.password)
    user_email = db.query(User).filter(User.email == user.email).first()
    if user_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user_data = User(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hash_password,)

    db.add(user_data)
    db.commit()
    db.refresh(user_data)
    return {"message": "User registered successfully!"}


@auth_router.post('/login', response_model=dict, status_code=status.HTTP_200_OK)
def login(user_data: UserLoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password!")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    token = RefreshToken(user_id=user.id, token=refresh_token)
    db.add(token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@auth_router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
def logout(token: RefreshTokenSchema, db: Session = Depends(get_db)):
    stored_token = db.query(RefreshToken).filter(RefreshToken.token == token.refresh_token).first()
    if not stored_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect refresh token")

    db.delete(stored_token)
    db.commit()



@auth_router.post('/refresh', response_model=dict, status_code=status.HTTP_200_OK)
def refresh(token: RefreshTokenSchema, db: Session = Depends(get_db)):
    stored_token = db.query(RefreshToken).filter(RefreshToken.token == token.refresh_token).first()
    if not stored_token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect refresh token")

    valid_refresh_lifetime = datetime.now(timezone.utc) - timedelta(days=REFRESH_TOKEN_LIFETIME)
    if stored_token.created_at < valid_refresh_lifetime:
        db.delete(stored_token)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired, please login again")

    access_token = create_access_token(data={"sub": str(stored_token.user_id)})

    return {
        "access_token": access_token,
    }


@auth_router.put('/change_password', response_model=dict, status_code=status.HTTP_200_OK)
def change_password(password_data: ChangePasswordSchema,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):

    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")

    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).delete()
    db.commit()

    return {"message": "Password changed successfully!"}


# @auth_router.put('/reset_password', response_model=dict, status_code=status.HTTP_200_OK)
# def reset_password(user_data: ResetPasswordSchema, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == user_data.email).first()
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")
#     verification_code = generate_code()
#
#
#     if user_data.verifier_code != verification_code:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect verification code")
#
#     user.hashed_password = get_password_hash(user_data.new_password)
#     db.commit()
#     return {"message": "Password reset successfully!"}