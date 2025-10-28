from teams.models import Team
from utils.interfaces import BaseService


class TeamService(BaseService):
    def create_object(self, name: str, description: str = None, **kwargs: dict) -> Team:
        team = Team(name=name, description=description, **kwargs)
        team.save()
        return team

    def update_object(self, instance: Team, **kwargs: dict) -> Team:
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        instance.save(update_fields=kwargs.keys())
        return instance

    def delete_object(self, instance: Team) -> None:
        instance.is_active = False
        instance.save(update_fields=["is_active"])
