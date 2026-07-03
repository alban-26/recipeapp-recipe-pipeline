from pydantic import BaseModel


class Ingredient(BaseModel):
    quantity: float | None = None
    unit: str | None = None
    name: str


class Recipe(BaseModel):
    name: str
    portions: int | None = None
    duration: int | None = None  # Minuten
    ingredients: list[Ingredient]
    instructions: list[str]