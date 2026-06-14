import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies import get_current_user
from app.api.tasks import (
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate


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
        self.timestamp = datetime.now(timezone.utc)
        self.own_task = Task(
            id=1,
            title="Own task",
            description="Current user's task",
            is_completed=False,
            created_at=self.timestamp,
            updated_at=self.timestamp,
            user_id=self.user.id,
        )
        self.other_user_task = Task(
            id=2,
            title="Private task",
            description="Another user's task",
            is_completed=False,
            created_at=self.timestamp,
            updated_at=self.timestamp,
            user_id=99,
        )

    def test_authenticated_user_can_create_task(self) -> None:
        db = MagicMock()
        def refresh_task(task: object) -> None:
            task.id = 1
            task.created_at = self.timestamp
            task.updated_at = self.timestamp

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

    def test_list_tasks_returns_only_current_users_tasks(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            self.own_task
        ]

        tasks = list_tasks(db, self.user)

        self.assertEqual(tasks, [self.own_task])
        self.assertTrue(all(task.user_id == self.user.id for task in tasks))
        db.query.return_value.filter.assert_called_once()

    def test_get_own_task(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = (
            self.own_task
        )

        task = get_task(self.own_task.id, db, self.user)

        self.assertEqual(task, self.own_task)

    def test_get_another_users_task_returns_not_found(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            get_task(self.other_user_task.id, db, self.user)

        self.assertEqual(
            context.exception.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(context.exception.detail, "Task not found")

    def test_update_own_task(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = (
            self.own_task
        )
        task_data = TaskUpdate(
            title="Updated task",
            is_completed=True,
        )

        task = update_task(self.own_task.id, task_data, db, self.user)

        self.assertEqual(task.title, "Updated task")
        self.assertTrue(task.is_completed)
        self.assertEqual(task.description, "Current user's task")
        self.assertEqual(task.user_id, self.user.id)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(task)

    def test_delete_own_task(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = (
            self.own_task
        )

        response = delete_task(self.own_task.id, db, self.user)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        db.delete.assert_called_once_with(self.own_task)
        db.commit.assert_called_once()

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
