from src.data.birtdays import BirthdayProvider
from src.data.providers.birthday_factory import BirthdayFactory
from src.sql.database import DatabaseClient



class DataManager:
    """
    Central place for all dynamic data that the codebase uses.
    """
    def __init__(self):
        self._db_client = DatabaseClient()
        self._birthday_factory: BirthdayFactory = BirthdayFactory(self._db_client)

    @property
    async def birthday_provider(self) -> BirthdayProvider:
        return await self._birthday_factory.create_birthday_provider
