from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.UUIDField(pk=True)
    username = fields.CharField(max_length=64, unique=True)
    email = fields.CharField(max_length=128, unique=True)
    display_name = fields.CharField(max_length=128)
    hashed_password = fields.CharField(max_length=256)
    is_active = fields.BooleanField(default=True)
    is_superuser = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    groups = fields.ManyToManyField("models.UserGroup", related_name="users")

    class Meta:
        table = "users"

    def __str__(self):
        return self.username


class Role(Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=32)
    is_system = fields.BooleanField(default=False)

    class Meta:
        table = "roles"

    def __str__(self):
        return self.name


class Permission(Model):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField("models.User", null=True)
    group = fields.ForeignKeyField("models.UserGroup", null=True)
    role = fields.ForeignKeyField("models.Role")
    path_pattern = fields.CharField(max_length=256)

    class Meta:
        table = "permissions"

    def __str__(self):
        return f"{self.role_id}: {self.path_pattern}"


class UserGroup(Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=64)

    class Meta:
        table = "user_groups"

    def __str__(self):
        return self.name


class RepoConfig(Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=128)
    git_url = fields.CharField(max_length=512, null=True)
    local_path = fields.CharField(max_length=1024, null=True)
    docs_dir = fields.CharField(max_length=256, default="docs")
    ssg_type = fields.CharField(max_length=32, default="vitepress")
    default_branch = fields.CharField(max_length=64, default="main")
    access_token = fields.TextField(null=True)
    commit_template = fields.CharField(max_length=256, default="docs: update {path}")
    review_mode = fields.BooleanField(default=False)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    @property
    def is_local(self) -> bool:
        return bool(self.local_path)

    class Meta:
        table = "repo_configs"

    def __str__(self):
        return self.name
