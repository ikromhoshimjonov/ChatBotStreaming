from os import getenv
import jwt
from dotenv import load_dotenv
from fastapi.security import HTTPAuthorizationCredentials
from openai import OpenAI
from pydantic import BaseModel,  PrivateAttr
from starlette import status
from starlette.responses import JSONResponse
from apps.models import User, History
from sqlalchemy import select
from sqlmodel import Session
from apps.database import engine
from typing import Annotated
from fastapi import Depends, HTTPException
from security import password_hash, ALGORITHM, security_scheme

def get_session():
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_session)]


load_dotenv()
SECRET_KEY = getenv("SECRET_KEY")
AI_SECRET_KEY = getenv("AI_SECRET_KEY")


class TextData(BaseModel):
    text: str


class UserData(BaseModel):
    username:str
    password:str

    def validate_user_data(self):
        with Session(engine) as session:
            statement = select(User).where(User.username == self.username)
            db_user = session.exec(statement).first()[0]

            if not db_user or not password_hash.verify(self.password, db_user.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Foydalanuvchi Username yoki parol xato"
                )

        return self


class TokenResponse(BaseModel):
    access: str
    refresh: str


class TokenRefreshRequest(BaseModel):
    refresh: str

    _verified_username: str = PrivateAttr(default=None)

    def validate_refresh_token(self):
        invalid_token_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token yaroqsiz yoki muddati o'tgan",
        )
        try:
            payload = jwt.decode(self.refresh, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            token_type: str = payload.get("token_type")

            if username is None or token_type != "refresh":
                raise invalid_token_exception

            self._verified_username = username

        except jwt.PyJWTError:
            raise invalid_token_exception
        return self


class TokenRefreshResponse(BaseModel):
    access: str


class PaginationQuery(BaseModel):
    size : int
    page : int


async def get_current_user(cred: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)]) -> str:
    if cred is None:
        raise HTTPException(status_code=401, detail="Token topilmadi!")

    token = cred.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type")

        if username is None or token_type != "access":
            raise HTTPException(status_code=401, detail="Yaroqsiz token turi!")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token xato yoki muddati o'tgan!")


def streaming_response(question : TextData,session:SessionDep,current_user: Annotated[str, Depends(get_current_user)]):
    client = OpenAI(
        api_key=AI_SECRET_KEY
    )
    db_user = get_user_from_db(u=current_user, session=session)[0]
    user_id = db_user.id
    question_collection = session.exec(
        select(History).where(History.user == user_id).order_by(History.id.desc()).limit(10)).all()
    messages = []
    for hist in question_collection:
        messages.append({
            "question": hist[0].user_question,
            "response": hist[0].ai_response
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f""" Siz foydalanuvchiga aniq va qisqa javob beruvchi aqlli yordamchisiz.
            Sizga kontekst sifatida foydalanuvchining oxirgi 10 ta savol-javoblar tarixi (Chat History) taqdim etiladi. Quyidagi qat'iy qoidalarga amal qiling:
            1. KONTEKSTNI TEKSHIRING: Foydalanuvchi bergan hozirgi yangi savolni diqqat bilan tahlil qiling. Agar bu savol taqdim etilgan 10 ta savol-javob ichidagi mavzularga, oldingi gaplarga yoki olmoshlarga  {messages}
            2. JAVOB FORMATI: Har qanday holatda ham foydalanuvchining hozirgi savoliga to'g'ridan-to'g'ri, juda aniq, ortiqcha gaplarsiz va lof-olqishlarsiz javob qaytaring.
            3. Agar Oxirgi 10 savolga bogliq bulmasa uzing ni bazanga asoslanib javob ber
            4. Javob chiqaryotgonda savolini qushib junatma """},
            {"role": "user", "content": question.text}
        ],
        stream=True
    )
    collected_chunks = []

    for chunk in response:
        if chunk.choices[0].delta.content:
            chunk_text = chunk.choices[0].delta.content
            collected_chunks.append(chunk_text)
            yield chunk_text

    full_response = "".join(collected_chunks)

    try:
        new_history = History(
            user=user_id,
            user_question=question.text,
            ai_response=full_response
        )
        session.add(new_history)
        session.commit()
    except:
        return JSONResponse({"error": "Bazada xatolik"})


def get_user_from_db(u: str, session: Session):
    statement = select(User).where(User.username == u)
    db_user = session.exec(statement).first()
    return db_user
