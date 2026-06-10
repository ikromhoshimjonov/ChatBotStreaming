from datetime import timedelta
from typing import Annotated
from sqlalchemy import select
from sqlmodel import Session
from fastapi.responses import StreamingResponse
from starlette.responses import JSONResponse
from apps.models import User, History
from fastapi import Depends, FastAPI
from security import password_hash, create_access_token, create_refresh_token , create_token, ACCESS_TOKEN_EXPIRE_MINUTES
from validation import TokenResponse, UserData, TokenRefreshResponse, TokenRefreshRequest, TextData, PaginationQuery, \
    get_current_user, streaming_response, SessionDep, get_session

app = FastAPI()


@app.post("/api/v1/token/", response_model=TokenResponse)
async def get_token_pair(data:UserData):
    access_val = create_access_token(data.username)
    refresh_val = create_refresh_token(data.username)

    return {
        "access": access_val,
        "refresh": refresh_val
    }


@app.post("/api/v1/api/token/refresh/", response_model=TokenRefreshResponse)
async def refresh_access_token(body: TokenRefreshRequest):
    username = body._verified_username
    new_access_token = create_token({"sub": username, "token_type": "access"},
                                    timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return TokenRefreshResponse(access=new_access_token)


@app.get("/api/v1/users/me")
async def get_profile(current_user: Annotated[str, Depends(get_current_user)]):
    return {
        "username": current_user,
        "status": "Avtorizatsiya muvaffaqiyatli!"
    }


@app.post("/register/")
async def register_user(data:UserData,session:SessionDep):
    try:
        hashed = password_hash.hash(data.password)
        new_user = User(username=data.username, password=hashed)

        session.add(new_user)
        session.commit()

        return JSONResponse({"result":"Muvafaqiyatli ruyxatdan o'tdingiz"})
    except:
        return JSONResponse({"error":f"Bu foydalanuvchi oldin ruyxatdan o'tgan"})


@app.post("/question/")
async def chat_bot_question(question: TextData,session: Session = Depends(get_session),current_user: str = Depends(get_current_user)):
    return StreamingResponse(
        streaming_response(
            question=question,
            session=session,
            current_user=current_user
        ),
        media_type="text/plain"
    )


@app.get("/get/history/")
async def chat_bot_history(session:SessionDep , pagination:PaginationQuery=Depends() , current_user: str = Depends(get_current_user)):
    statement = select(User).where(User.username == current_user)
    db_user = session.exec(statement).first()
    user_id = db_user[0].id
    if pagination.size > 0 and  pagination.page > 0:
        question_collection = session.exec(select(History).where(History.user == user_id).offset((pagination.page-1)*pagination.size).limit(pagination.size)).all()
        messages_collection = []
        for history in question_collection:
            messages_collection.append([{
                "role":"user",
                "question": history[0].user_question,
                "created_at":history[0].created_at
            },
            {
                "role": "system",
                "response": history[0].ai_response,
                "created_at": history[0].created_at
            }
            ])

        return JSONResponse(messages_collection)
    return JSONResponse({"error":"Size va Page ni to'gri tartibda kiriting"})


