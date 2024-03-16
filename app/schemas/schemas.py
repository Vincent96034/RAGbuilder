from pydantic import BaseModel


class CreateUserRequestSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class CurrentUserSchema(BaseModel):
    email: str
    user_id: int

# remember to add new schemas to __all__ in app/schemas/__init__.py