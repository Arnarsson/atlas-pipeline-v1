"""
Tests for RBAC System (Phase 6)
===============================

Tests Role-Based Access Control functionality.
"""

import pytest

from app.auth.rbac import (
    Permission,
    RBACManager,
    Role,
    User,
    mask_sensitive_columns,
)


class TestRBACManager:
    """Test cases for RBACManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rbac = RBACManager()

    def test_default_users_created(self):
        """Test that default users are created."""
        users = self.rbac.list_users()
        assert len(users) >= 4  # admin, engineer, analyst, viewer

        # Check admin exists
        admin = self.rbac.get_user_by_api_key("atlas-admin-key")
        assert admin is not None
        assert admin.username == "admin"
        assert Role.ADMIN in admin.roles

    def test_create_user(self):
        """Test creating a new user."""
        user = self.rbac.create_user(
            username="testuser",
            email="test@example.com",
            roles=[Role.DATA_ANALYST],
        )

        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert Role.DATA_ANALYST in user.roles
        assert user.is_active is True

    def test_create_user_with_dataset_restrictions(self):
        """Test creating user with dataset restrictions."""
        user = self.rbac.create_user(
            username="restricted_user",
            email="restricted@example.com",
            roles=[Role.VIEWER],
            allowed_datasets=["dataset_a", "dataset_b"],
            denied_datasets=["dataset_secret"],
        )

        assert user.allowed_datasets == ["dataset_a", "dataset_b"]
        assert "dataset_secret" in user.denied_datasets

    def test_update_user_roles(self):
        """Test updating user roles."""
        user = self.rbac.create_user(
            username="rolechange",
            email="rolechange@example.com",
            roles=[Role.VIEWER],
        )

        # Update roles
        success = self.rbac.update_user_roles(user.user_id, [Role.DATA_ENGINEER])
        assert success is True

        # Verify
        updated = self.rbac.get_user(user.user_id)
        assert Role.DATA_ENGINEER in updated.roles
        assert Role.VIEWER not in updated.roles

    def test_delete_user(self):
        """Test deleting a user."""
        user = self.rbac.create_user(
            username="deleteuser",
            email="delete@example.com",
            roles=[Role.VIEWER],
        )

        # Delete
        success = self.rbac.delete_user(user.user_id)
        assert success is True

        # Verify deleted
        assert self.rbac.get_user(user.user_id) is None

        # Delete non-existent
        success = self.rbac.delete_user("non-existent")
        assert success is False


class TestUserPermissions:
    """Test permission checking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rbac = RBACManager()

    def test_admin_has_all_permissions(self):
        """Test that admin has all permissions."""
        admin = self.rbac.get_user_by_api_key("atlas-admin-key")

        for perm in Permission:
            assert admin.has_permission(perm), f"Admin missing permission: {perm}"

    def test_viewer_has_limited_permissions(self):
        """Test that viewer has limited permissions."""
        viewer = self.rbac.get_user_by_api_key("atlas-viewer-key")

        # Should have read permissions
        assert viewer.has_permission(Permission.PIPELINE_READ)
        assert viewer.has_permission(Permission.DATA_READ)
        assert viewer.has_permission(Permission.CATALOG_READ)

        # Should NOT have write permissions
        assert not viewer.has_permission(Permission.PIPELINE_CREATE)
        assert not viewer.has_permission(Permission.DATA_WRITE)
        assert not viewer.has_permission(Permission.ADMIN_USERS)

    def test_data_analyst_permissions(self):
        """Test data analyst permissions."""
        analyst = self.rbac.get_user_by_api_key("atlas-analyst-key")

        # Should have read and export
        assert analyst.has_permission(Permission.DATA_READ)
        assert analyst.has_permission(Permission.DATA_EXPORT)
        assert analyst.has_permission(Permission.DATA_PROFILE)

        # Should NOT have admin
        assert not analyst.has_permission(Permission.ADMIN_USERS)
        assert not analyst.has_permission(Permission.DATA_DELETE)

    def test_data_engineer_permissions(self):
        """Test data engineer permissions."""
        engineer = self.rbac.get_user_by_api_key("atlas-engineer-key")

        # Should have pipeline and connector management
        assert engineer.has_permission(Permission.PIPELINE_CREATE)
        assert engineer.has_permission(Permission.CONNECTOR_CREATE)
        assert engineer.has_permission(Permission.DATA_DELETE)

        # Should NOT have admin
        assert not engineer.has_permission(Permission.ADMIN_USERS)
        assert not engineer.has_permission(Permission.ADMIN_SETTINGS)

    def test_has_any_permission(self):
        """Test checking any of multiple permissions."""
        viewer = self.rbac.get_user_by_api_key("atlas-viewer-key")

        # Has at least one
        assert viewer.has_any_permission([
            Permission.DATA_READ,
            Permission.DATA_WRITE,
        ])

        # Has none
        assert not viewer.has_any_permission([
            Permission.ADMIN_USERS,
            Permission.ADMIN_ROLES,
        ])

    def test_has_all_permissions(self):
        """Test checking all permissions."""
        admin = self.rbac.get_user_by_api_key("atlas-admin-key")
        viewer = self.rbac.get_user_by_api_key("atlas-viewer-key")

        perms = [Permission.DATA_READ, Permission.PIPELINE_READ]

        # Admin has all
        assert admin.has_all_permissions(perms)

        # Viewer has both read permissions
        assert viewer.has_all_permissions(perms)

        # Viewer doesn't have all write permissions
        write_perms = [Permission.DATA_WRITE, Permission.DATA_DELETE]
        assert not viewer.has_all_permissions(write_perms)


class TestDatasetAccess:
    """Test dataset-level access control."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rbac = RBACManager()

    def test_user_can_access_dataset(self):
        """Test dataset access checking."""
        # Create user with allowed datasets
        user = self.rbac.create_user(
            username="dataset_user",
            email="ds@example.com",
            roles=[Role.DATA_ANALYST],
            allowed_datasets=["dataset_a", "dataset_b"],
        )

        assert user.can_access_dataset("dataset_a")
        assert user.can_access_dataset("dataset_b")
        assert not user.can_access_dataset("dataset_c")

    def test_denied_takes_precedence(self):
        """Test that denied datasets take precedence."""
        user = self.rbac.create_user(
            username="denied_user",
            email="denied@example.com",
            roles=[Role.DATA_ANALYST],
            allowed_datasets=["dataset_a", "dataset_secret"],
            denied_datasets=["dataset_secret"],
        )

        assert user.can_access_dataset("dataset_a")
        assert not user.can_access_dataset("dataset_secret")

    def test_none_allowed_means_all(self):
        """Test that None for allowed_datasets means all allowed."""
        user = self.rbac.create_user(
            username="all_access",
            email="all@example.com",
            roles=[Role.DATA_ANALYST],
            allowed_datasets=None,  # All allowed
        )

        assert user.can_access_dataset("any_dataset")
        assert user.can_access_dataset("another_dataset")

    def test_check_dataset_access_with_permission(self):
        """Test combined permission and dataset access check."""
        user = self.rbac.create_user(
            username="combined",
            email="combined@example.com",
            roles=[Role.DATA_ANALYST],
            allowed_datasets=["allowed_dataset"],
        )

        # Has permission AND dataset access
        assert self.rbac.check_dataset_access(
            user, "allowed_dataset", Permission.DATA_READ
        )

        # Has permission but NOT dataset access
        assert not self.rbac.check_dataset_access(
            user, "forbidden_dataset", Permission.DATA_READ
        )


class TestColumnMasking:
    """Test column-level masking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rbac = RBACManager()

    def test_user_column_masking(self):
        """Test getting masked columns for user."""
        user = self.rbac.create_user(
            username="masked_user",
            email="masked@example.com",
            roles=[Role.DATA_ANALYST],
            masked_columns={
                "customer_data": ["ssn", "credit_card"],
                "employee_data": ["salary"],
            },
        )

        # Get masked columns
        assert user.get_masked_columns("customer_data") == ["ssn", "credit_card"]
        assert user.get_masked_columns("employee_data") == ["salary"]
        assert user.get_masked_columns("other_data") == []

    def test_mask_sensitive_columns(self):
        """Test masking sensitive data."""
        user = User(
            user_id="test",
            username="test",
            email="test@example.com",
            roles=[Role.VIEWER],
            masked_columns={
                "dataset_1": ["password", "ssn"],
            },
        )

        data = {
            "id": 1,
            "name": "John",
            "password": "secret123",
            "ssn": "123-45-6789",
        }

        masked = mask_sensitive_columns(data, user, "dataset_1")

        # Non-masked columns unchanged
        assert masked["id"] == 1
        assert masked["name"] == "John"

        # Masked columns hidden
        assert masked["password"] == "***MASKED***"
        assert masked["ssn"] == "***MASKED***"

    def test_no_masking_for_unspecified_dataset(self):
        """Test that masking doesn't apply to unspecified datasets."""
        user = User(
            user_id="test",
            username="test",
            email="test@example.com",
            roles=[Role.VIEWER],
            masked_columns={
                "dataset_1": ["password"],
            },
        )

        data = {
            "id": 1,
            "password": "secret123",
        }

        # Different dataset - no masking
        masked = mask_sensitive_columns(data, user, "dataset_2")
        assert masked["password"] == "secret123"


class TestAccessLogging:
    """Test access logging functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rbac = RBACManager()

    def test_access_is_logged(self):
        """Test that access checks are logged."""
        user = self.rbac.get_user_by_api_key("atlas-admin-key")

        # Make some access checks
        self.rbac.check_permission(user, Permission.DATA_READ, "test_resource")
        self.rbac.check_permission(user, Permission.ADMIN_USERS, "admin_panel")

        # Get logs
        logs = self.rbac.get_access_logs(limit=10)
        assert len(logs) >= 2

    def test_filter_logs_by_user(self):
        """Test filtering logs by user."""
        admin = self.rbac.get_user_by_api_key("atlas-admin-key")
        viewer = self.rbac.get_user_by_api_key("atlas-viewer-key")

        self.rbac.check_permission(admin, Permission.DATA_READ)
        self.rbac.check_permission(viewer, Permission.DATA_READ)

        # Filter by admin
        admin_logs = self.rbac.get_access_logs(user_id=admin.user_id)
        assert all(log.user_id == admin.user_id for log in admin_logs)

    def test_filter_denied_access(self):
        """Test filtering denied access logs."""
        viewer = self.rbac.get_user_by_api_key("atlas-viewer-key")

        # Try to access admin permission (will be denied)
        self.rbac.check_permission(viewer, Permission.ADMIN_USERS)

        # Get denied logs
        denied_logs = self.rbac.get_access_logs(granted=False)
        assert len(denied_logs) >= 1
