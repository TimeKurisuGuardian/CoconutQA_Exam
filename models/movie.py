from pydantic import BaseModel, Field
from typing import List, Optional

class GenreModel(BaseModel):
    name: str

class MovieModel(BaseModel):
    id: int
    name: str = Field(..., description="Название фильма")
    price: int
    description: str
    imageUrl: str
    location: str
    published: bool
    genreId: int
    genre: GenreModel
    createdAt: str
    rating: int

class MoviesListResponseModel(BaseModel):
    movies: List[MovieModel]
    count: int
    page: int
    pageSize: int
    pageCount: int