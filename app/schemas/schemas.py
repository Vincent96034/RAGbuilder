from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# remember to add new schemas to __all__ in app/schemas/__init__.py