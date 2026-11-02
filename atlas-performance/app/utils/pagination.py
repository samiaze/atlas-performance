from typing import TypeVar, Generic, List
from math import ceil
from pydantic import BaseModel
from sqlalchemy.orm import Query

# Type générique (peut être un Player, un Match, une Team...)
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Modèle de réponse standard pour la pagination."""
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int

def paginate(query: Query, page: int = 1, per_page: int = 20) -> PaginatedResponse[T]:
    """
    Applique la pagination à une requête SQLAlchemy et retourne une structure standardisée.
    
    Args:
        query: La requête SQLAlchemy de base (sans offset/limit).
        page: Le numéro de page demandé (commence à 1).
        per_page: Le nombre d'éléments par page.
        
    Returns:
        PaginatedResponse: Objet contenant les items et les métadonnées.
    """
    if page < 1:
        page = 1
        
    total = query.count()
    pages = ceil(total / per_page) if per_page > 0 else 0
    
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )