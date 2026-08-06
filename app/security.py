from fastapi import Header, HTTPException
from dotenv import load_dotenv
from os import getenv
load_dotenv()



auth_token = getenv("API_SECRET_KEY")



def get_user_auth_token(
    token: str = Header(alias="X-API-Key") # alias типо проверяет название для заголовка там регистр и другое
) -> str:
    if token != auth_token:
        raise HTTPException(status_code=401,detail="invalid_token")
    return token

















