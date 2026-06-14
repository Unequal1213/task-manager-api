import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies import get_current_user
from app.api.tasks import create_task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse


class TaskCreationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.user = User(
            id=42,
            username="task_owner",
            email="task_owner@example.com",
            password_hash="$argon2id$stored-hash",
        )
        self.task_data = TaskCreate(
            title="Finish portfolio API",
            description="Add authenticated task endpoints.",
        )

    def test_authenticated_user_can_create_task(self) -> None:
        db = MagicMock()
        timestamp = datetime.now(timezone.utc)

        def refresh_task(task: object) -> None:
            task.id = 1
            task.created_at = timestamp
            task.updated_at = timestamp

        db.refresh.side_effect = refresh_task

        task = create_task(self.task_data, db, self.user)
        response = TaskResponse.model_validate(task)

        self.assertEqual(response.title, self.task_data.title)
        self.assertEqual(response.description, self.task_data.description)
        self.assertFalse(response.is_completed)
        self.assertEqual(response.user_id, self.user.id)
        db.add.assert_called_once_with(task)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(task)

    def test_missing_token_prevents_task_creation(self) -> None:
        db = MagicMock()

        with self.assertRaises(HTTPException) as context:
            get_current_user(None, db)

        self.assertEqual(
            context.exception.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_invalid_token_prevents_task_creation(self) -> None:
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-token",
        )
        db = MagicMock()

        with self.assertRaises(HTTPException) as context:
            get_current_user(credentials, db)

        self.assertEqual(
            context.exception.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        db.add.assert_not_called()
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
