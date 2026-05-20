"""Tests for permissions loader and default policy."""

import json

import pytest

from bonsai.state.permissions import PermissionsManager, load_permissions, save_permissions


class TestLoadPermissions:
    def test_defaults_when_no_file(self, tmp_path):
        perms = load_permissions(tmp_path, plan_name="test")
        assert perms.allow_git_push is False
        assert perms.allow_external_api is True
        assert perms.hitl_pr_merge is True
        assert perms.max_restarts == 5
        assert perms.skills_dir is None

    def test_load_existing_file(self, tmp_path):
        data = {
            "plan_name": "test",
            "allow_git_push": True,
            "allow_external_api": False,
            "hitl_pr_merge": True,
            "max_restarts": 3,
            "skills_dir": "/some/path",
        }
        (tmp_path / "permissions.json").write_text(json.dumps(data))

        perms = load_permissions(tmp_path, plan_name="test")
        assert perms.allow_git_push is True
        assert perms.allow_external_api is False
        assert perms.max_restarts == 3
        assert perms.skills_dir == "/some/path"

    def test_extra_fields_ignored_on_load(self, tmp_path):
        data = {
            "plan_name": "test",
            "allow_git_push": False,
            "allow_external_api": True,
            "hitl_pr_merge": True,
            "max_restarts": 5,
            "future_field": "some_value",
        }
        (tmp_path / "permissions.json").write_text(json.dumps(data))

        # Should not raise even with extra fields (read model uses extra="ignore")
        perms = load_permissions(tmp_path, plan_name="test")
        assert perms.plan_name == "test"


class TestSavePermissions:
    def test_save_creates_file(self, tmp_path):
        from bonsai.state.schemas import PermissionsConfig

        config = PermissionsConfig(plan_name="test", allow_git_push=True)
        save_permissions(tmp_path, config)

        perms_file = tmp_path / "permissions.json"
        assert perms_file.exists()
        data = json.loads(perms_file.read_text())
        assert data["allow_git_push"] is True

    def test_save_and_reload_roundtrip(self, tmp_path):
        from bonsai.state.schemas import PermissionsConfig

        config = PermissionsConfig(
            plan_name="test",
            allow_git_push=False,
            allow_external_api=False,
            max_restarts=2,
            skills_dir="/opt/skills",
        )
        save_permissions(tmp_path, config)

        loaded = load_permissions(tmp_path, plan_name="test")
        assert loaded.allow_external_api is False
        assert loaded.max_restarts == 2
        assert loaded.skills_dir == "/opt/skills"


class TestPermissionsManager:
    def test_allows_action_by_default(self, tmp_path):
        mgr = PermissionsManager(run_dir=tmp_path, plan_name="p")
        assert mgr.can("allow_external_api") is True
        assert mgr.can("hitl_pr_merge") is True

    def test_denies_git_push_by_default(self, tmp_path):
        mgr = PermissionsManager(run_dir=tmp_path, plan_name="p")
        assert mgr.can("allow_git_push") is False

    def test_unknown_action_raises(self, tmp_path):
        mgr = PermissionsManager(run_dir=tmp_path, plan_name="p")
        with pytest.raises(AttributeError):
            mgr.can("nonexistent_permission")

    def test_max_restarts_property(self, tmp_path):
        mgr = PermissionsManager(run_dir=tmp_path, plan_name="p")
        assert mgr.max_restarts == 5

    def test_custom_max_restarts(self, tmp_path):
        from bonsai.state.schemas import PermissionsConfig

        config = PermissionsConfig(plan_name="p", max_restarts=2)
        save_permissions(tmp_path, config)

        mgr = PermissionsManager(run_dir=tmp_path, plan_name="p")
        assert mgr.max_restarts == 2
