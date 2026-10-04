"""线程安全的内存用户仓库，仅用于本地接口 Demo。"""

from dataclasses import dataclass
from threading import RLock

from app.schemas import UserCreate, UserRole


@dataclass(frozen=True, slots=True)
class StoredUser:
    id: int
    username: str
    password: str
    display_name: str
    email: str
    role: UserRole


class DuplicateUserError(Exception):
    def __init__(self, field: str) -> None:
        self.field = field
        super().__init__(field)


class UserStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._users: dict[int, StoredUser] = {
            1: StoredUser(
                id=1,
                username="admin",
                password="admin123",
                display_name="系统管理员",
                email="admin@example.com",
                role=UserRole.ADMIN,
            ),
            2: StoredUser(
                id=2,
                username="tester",
                password="test123",
                display_name="测试用户",
                email="tester@example.com",
                role=UserRole.USER,
            ),
        }
        self._next_id = 3

    def authenticate(self, username: str, password: str) -> StoredUser | None:
        with self._lock:
            return next(
                (
                    user
                    for user in self._users.values()
                    if user.username == username and user.password == password
                ),
                None,
            )

    def list_users(
        self,
        role: UserRole | None = None,
        keyword: str | None = None,
    ) -> list[StoredUser]:
        with self._lock:
            users = list(self._users.values())
            if role is not None:
                users = [user for user in users if user.role == role]
            if keyword is not None:
                normalized_keyword = keyword.casefold()
                users = [
                    user
                    for user in users
                    if normalized_keyword in user.username.casefold()
                    or normalized_keyword in user.display_name.casefold()
                    or normalized_keyword in user.email.casefold()
                ]
            return sorted(users, key=lambda user: user.id)

    def get_user(self, user_id: int) -> StoredUser | None:
        with self._lock:
            return self._users.get(user_id)

    def create_user(self, payload: UserCreate) -> StoredUser:
        with self._lock:
            if any(user.username == payload.username for user in self._users.values()):
                raise DuplicateUserError("username")
            if any(user.email == payload.email for user in self._users.values()):
                raise DuplicateUserError("email")

            user = StoredUser(id=self._next_id, **payload.model_dump())
            self._users[user.id] = user
            self._next_id += 1
            return user

    def delete_user(self, user_id: int) -> bool:
        with self._lock:
            return self._users.pop(user_id, None) is not None

