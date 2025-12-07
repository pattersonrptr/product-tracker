from abc import ABC, abstractmethod
from typing import List, Optional

from src.app.entities.user import User as UserEntity


class UserRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, user: UserEntity) -> UserEntity:
        raise NotImplementedError

    # @abstractmethod
    # async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
    #     raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[UserEntity]:
        raise NotImplementedError

    # @abstractmethod
    # async def update(self, user_id: int, user: UserEntity) -> Optional[UserEntity]:
    #     raise NotImplementedError
    #
    # @abstractmethod
    # async def delete(self, user_id: int) -> bool:
    #     raise NotImplementedError
