from titles.models import Title
from utils.interfaces import BaseService


class TitleService(BaseService):
    def create_object(self, name: str, **kwargs: dict) -> Title:
        title = Title.objects.create(name=name, **kwargs)
        return title

    def update_object(self, instance: Title, **kwargs: dict) -> Title:
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        instance.save(update_fields=kwargs.keys())
        return instance

    def delete_object(self, instance: Title) -> None:
        instance.is_active = False
        instance.save(update_fields=["is_active"])
