from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import SessionLocal # Ajusta según tu setup de DB //REVISAR EN PRODUCCION
from app.models.user import User
from app.core import security
from app.core.security import get_current_user
from app.schemas.auth_schema import UserPublic

router = APIRouter()

# Función para obtener DB 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/token")
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 1. Buscar usuario
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 2. Validar
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Crear Token
    access_token = security.create_access_token(data={"sub": user.username})

    # 4. Setear Cookie HttpOnly (Seguridad)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=315360000,  # 10 años
        samesite="lax",
        secure=False  # Pon True en producción con HTTPS
    )

    return {"user": UserPublic.model_validate(user)}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Sesión cerrada"}


@router.get("/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Endpoint para verificar si la sesión (cookie) es válida.
    El frontend lo llama al cargar la app para saber si está autenticado.
    """
    return current_user