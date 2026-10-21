"""Infrastructure adapter that fulfills IdGenerator."""
from uuid import uuid4


class UUID4Ids:
    def new_id(self) -> str:
        return str(uuid4())
