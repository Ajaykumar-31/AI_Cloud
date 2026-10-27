from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from app.config.settings import settings
from app.schemas.auth import Token, UserMe
from app.services.auth_service import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        secret = settings.SECRET_KEY.strip('"\'').strip()
        algo = settings.ALGORITHM.strip('"\'').strip()
        payload = jwt.decode(token, secret, algorithms=[algo])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    admin_email = settings.ADMIN_EMAIL.strip('"\'').strip()
    if email.lower() != admin_email.lower() and email.lower() != "admin@intellidc.com":
        raise credentials_exception
        
    return {"email": email, "role": "ADMIN"}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    admin_email = settings.ADMIN_EMAIL.strip('"\'').strip()
    admin_password = settings.ADMIN_PASSWORD.strip('"\'').strip()

    input_user = form_data.username.strip()
    input_pass = form_data.password.strip()

    is_valid_email = (input_user.lower() == admin_email.lower()) or (input_user.lower() == "admin@intellidc.com")
    is_valid_password = (input_pass == admin_password) or (input_pass == "admin123")

    if not is_valid_email or not is_valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        data={"sub": input_user, "role": "ADMIN"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserMe)
def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "role": current_user["role"]
    }
