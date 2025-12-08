from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List, Type, TypeVar

T = TypeVar("T", bound=BaseModel)


class ResourceIdentifier(BaseModel):
    type: str
    id: Optional[str] = None


class ResourceObject(BaseModel):
    type: str = Field(..., example="users")
    id: Optional[str] = None
    attributes: Any = None
    relationships: Optional[Dict[str, Any]] = None

    @classmethod
    def from_model(
        cls,
        model: Any,
        type_name: str,
        attributes_field: Optional[Type[T]] = None,
        exclude: Optional[List[str]] = None,
    ) -> "ResourceObject":
        """
        Constrói um ResourceObject a partir de uma entidade/model.
        - model: pydantic model ou objeto com __dict__.
        - type_name: valor fixo para o campo 'type' (ex: "users").
        - attributes_field: se fornecido, instancia este BaseModel com os dados de atributos.
        - exclude: lista de campos a excluir dos attributes (ex: ['hashed_password']).
        """
        exclude = exclude or []

        # Extrair dados da entidade (suporte pydantic e objetos normais)
        if hasattr(model, "model_dump"):
            attrs = model.model_dump(exclude_unset=True)
        else:
            attrs = {
                k: v
                for k, v in getattr(model, "__dict__", {}).items()
                if not k.startswith("_")
            }

        entity_id = attrs.get("id", None)

        # Preparar os dados de attributes (removendo id e campos excluídos)
        attributes_data = {k: v for k, v in attrs.items() if k not in exclude and k != "id"}

        if attributes_field:
            attributes = attributes_field(**attributes_data)
        else:
            attributes = attributes_data

        return cls(
            type=type_name,
            id=str(entity_id) if entity_id is not None else None,
            attributes=attributes,
        )


class ResourceObjectForCreation(BaseModel):
    """ResourceObject para requests de criação (POST) - sem campo id"""
    type: str = Field(..., example="users")
    attributes: Any = None
    relationships: Optional[Dict[str, Any]] = None


class SingleResourceRequest(BaseModel):
    data: ResourceObjectForCreation


class SingleResourceResponse(BaseModel):
    data: ResourceObject


class CollectionResponse(BaseModel):
    data: List[ResourceObject]
    meta: Optional[Dict[str, Any]] = None
    links: Optional[Dict[str, str]] = None
