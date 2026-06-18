import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import get_current_user
from app.api.tasks import (
    TaskSortBy,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)
from app.database.database import Base
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

    def create_task_list_session(
        self,
        owner_task_count: int,
        titles: list[str] | None = None,
    ) -> Session:
        engine = create_engine("sqlite:///:memory:")
        testing_session_local = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )
        Base.metadata.create_all(bind=engine)

        db = testing_session_local()
        db.add_all(
            [
                User(
                    id=self.user.id,
                    username=self.user.username,
                    email=self.user.email,
                    password_hash=self.user.password_hash,
                ),
                User(
                    id=self.other_user_task.user_id,
                    username="other_user",
                    email="other_user@example.com",
                    password_hash="$argon2id$other-hash",
                ),
            ]
        )
        base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
        db.add_all(
            [
                Task(
                    id=index,
                    title=(
                        titles[index - 1]
                        if titles is not None
                        else f"Task {index:02d}"
                    ),
                    description=f"Task {index} description",
                    is_completed=index % 2 == 0,
                    created_at=base_time + timedelta(minutes=index),
                    updated_at=base_time + timedelta(hours=index),
                    user_id=self.user.id,
                )
                for index in range(1, owner_task_count + 1)
            ]
        )
        db.add(
            Task(
                id=100,
                title=self.other_user_task.title,
                description=self.other_user_task.description,
                is_completed=self.other_user_task.is_completed,
                created_at=base_time + timedelta(days=1),
                updated_at=base_time + timedelta(days=1),
                user_id=self.other_user_task.user_id,
            )
        )
        db.commit()
        return db

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

    def test_list_tasks_uses_default_limit(self) -> None:
        db = self.create_task_list_session(owner_task_count=25)

        try:
            tasks = list_tasks(db=db, current_user=self.user)
            task_ids = [task.id for task in tasks]
        finally:
            db.close()

        self.assertEqual(len(tasks), 20)
        self.assertEqual(task_ids, list(range(25, 5, -1)))

    def test_list_tasks_sorts_by_created_at_desc_by_default(self) -> None:
        db = self.create_task_list_session(owner_task_count=3)

        try:
            tasks = list_tasks(db=db, current_user=self.user)
            task_ids = [task.id for task in tasks]
        finally:
            db.close()

        self.assertEqual(task_ids, [3, 2, 1])

    def test_list_tasks_sorts_by_created_at_ascending(self) -> None:
        db = self.create_task_list_session(owner_task_count=3)

        try:
            tasks = list_tasks(
                db=db,
                current_user=self.user,
                sort_order="asc",
            )
            task_ids = [task.id for task in tasks]
        finally:
            db.close()

        self.assertEqual(task_ids, [1, 2, 3])

    def test_list_tasks_sorts_by_title(self) -> None:
        db = self.create_task_list_session(
            owner_task_count=3,
            titles=["Charlie", "Alpha", "Bravo"],
        )

        try:
            tasks = list_tasks(
                db=db,
                current_user=self.user,
                sort_by="title",
                sort_order="asc",
            )
            task_titles = [task.title for task in tasks]
        finally:
            db.close()

        self.assertEqual(task_titles, ["Alpha", "Bravo", "Charlie"])

    def test_list_tasks_applies_limit_and_offset(self) -> None:
        db = self.create_task_list_session(owner_task_count=5)

        try:
            tasks = list_tasks(
                db=db,
                current_user=self.user,
                limit=2,
                offset=1,
            )
            task_ids = [task.id for task in tasks]
        finally:
            db.close()

        self.assertEqual(task_ids, [4, 3])

    def test_list_tasks_filters_by_completion_status(self) -> None:
        db = self.create_task_list_session(owner_task_count=5)

        try:
            tasks = list_tasks(
                db=db,
                current_user=self.user,
                is_completed=True,
            )
            task_ids = [task.id for task in tasks]
        finally:
            db.close()

        self.assertEqual(task_ids, [4, 2])
        self.assertTrue(all(task.is_completed for task in tasks))

    def test_list_tasks_excludes_another_users_tasks(self) -> None:
        db = self.create_task_list_session(owner_task_count=3)

        try:
            tasks = list_tasks(
                db=db,
                current_user=self.user,
                limit=100,
                sort_by="created_at",
                sort_order="desc",
            )
            task_user_ids = [task.user_id for task in tasks]
        finally:
            db.close()

        self.assertEqual(task_user_ids, [self.user.id, self.user.id, self.user.id])
        self.assertNotIn(self.other_user_task.user_id, task_user_ids)

    def test_list_tasks_rejects_invalid_sort_by(self) -> None:
        adapter = TypeAdapter(TaskSortBy)

        with self.assertRaises(ValidationError):
            adapter.validate_python("id")

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
