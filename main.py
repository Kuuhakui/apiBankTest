from fastapi import FastAPI, HTTPException, Depends
import asyncpg
from pydantic import BaseModel, ValidationError
app = FastAPI()

class AuthRequest(BaseModel):
    login: str
    password: str

class UserRequest(BaseModel):
    lastname: str
    name: str
    patronymic: str

# Функция для подключения к базе данных
async def get_db_connection():
    conn = await asyncpg.connect(user='prb01', password='prb01', 
                                 database='user1', host='176.56.14.200')
    return conn

# /all - вывод всех транзакций пользователя
@app.get("/all")
async def get_all_transactions(user_id: int, db=Depends(get_db_connection)):
    query = """
    SELECT t.*, p.lastname, p.name, p.patronymic
    FROM "Bank_team_1"."transaction" t
    JOIN "Bank_team_1".personal_account pa ON t.personal_account_id = pa.id_personal_account
    JOIN "Bank_team_1".person p ON pa.person_id = p.id_person
    WHERE p.id_person = $1
    """
    transactions = await db.fetch(query, user_id)
    if not transactions:
        raise HTTPException(status_code=404, detail="Transactions not found")
    return transactions

# /transactions - вывод транзакций по типу
@app.get("/transactions")
async def get_transactions_by_type(category_id: int, db=Depends(get_db_connection)):
    query = """
    SELECT t.*, p.lastname, p.name, p.patronymic
    FROM "Bank_team_1"."transaction" t
    JOIN "Bank_team_1".categoru_place cp ON t.categoru_place = cp.id_categoru_place
    JOIN "Bank_team_1".personal_account pa ON t.personal_account_id = pa.id_personal_account
    JOIN "Bank_team_1".person p ON pa.person_id = p.id_person
    WHERE cp.categoru_id = $1
    """
    transactions = await db.fetch(query, category_id)
    if not transactions:
        raise HTTPException(status_code=404, detail="Transactions not found")
    return transactions

# /authorisation - авторизация по логину и паролю
@app.post("/authorisation")
async def authorise_user(auth: AuthRequest, db=Depends(get_db_connection)):
    try:
        auth_data = AuthRequest(**auth.dict())
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    query = """
    SELECT person_id
    FROM "Bank_team_1"."authorization"
    WHERE login = $1 AND password = $2
    """
    user = await db.fetchrow(query, auth_data.login, auth_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "User authorized", "user_id": user['person_id']}

# /add_user - добавление пользователя
@app.post("/add_user")
async def add_user(user: UserRequest, db=Depends(get_db_connection)):
    query = """
    INSERT INTO "Bank_team_1".person (lastname, name, patronymic)
    VALUES ($1, $2, $3)
    RETURNING id_person
    """
    result = await db.fetchrow(query, user.lastname, user.name, user.patronymic)
    return {"message": "User added", "user_id": result['id_person']}

# /delete_user - удаление пользователя
@app.delete("/delete_user")
async def delete_user(user_id: int, db=Depends(get_db_connection)):
    query = """
    DELETE FROM "Bank_team_1".person
    WHERE id_person = $1
    RETURNING id_person
    """
    result = await db.fetchrow(query, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted", "user_id": result['id_person']}

if __name__ == "__main__":

    import uvicorn
    uvicorn.run(app, host="192.168.31.94", port=4044)
