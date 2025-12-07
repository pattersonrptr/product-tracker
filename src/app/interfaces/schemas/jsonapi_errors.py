from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class JsonApiError(BaseModel):
    """Representa um erro individual no padrão JSON:API"""
    id: Optional[str] = None
    status: str  # HTTP status code como string (ex: "400", "422")
    code: Optional[str] = None  # Código de erro específico da aplicação
    title: Optional[str] = None  # Título resumido do erro
    detail: Optional[str] = None  # Descrição detalhada
    source: Optional[Dict[str, Any]] = None  # Campo problemático (ex: {"pointer": "/data/attributes/email"})
    meta: Optional[Dict[str, Any]] = None


class JsonApiErrorResponse(BaseModel):
    """Response padrão JSON:API para erros"""
    errors: List[JsonApiError]
