from abc import ABC, abstractmethod


class BaseService(ABC):
    @abstractmethod
    def create_object(self, *args, **kwargs): ...

    @abstractmethod
    def update_object(self, *args, **kwargs): ...

    @abstractmethod
    def delete_object(self, *args, **kwargs): ...
