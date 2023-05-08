from typing import Any, Literal, Optional, TypedDict

from ..types import Any


class APIKeyType(TypedDict):
    id: int
    created_at: str
    name: str
    description: Optional[str]
    expiry_date: Optional[str]
    is_of__actor: Any


class ApplicationType(TypedDict, total=False):
    id: int
    created_at: str
    app_name: str
    actor: Any
    slug: str
    uuid: str
    is_accessible_by_support_until__date: str
    is_host: bool
    should_track_latest_release: bool
    is_public: bool
    is_of__class: Literal["fleet", "block", "app"]
    is_archived: bool
    is_discoverable: bool
    is_stored_at__repository_url: str
    public_organization: Any
    application_type: Any
    is_for__device_type: Any
    depends_on__application: Any
    organization: Any
    should_be_running__release: Any

    application_config_variable: Any
    application_environment_variable: Any
    build_environment_variable: Any
    application_tag: Any
    owns__device: Any
    owns__public_device: Any
    owns__release: Any
    service: Any
    is_depended_on_by__application: Any
    is_directly_accessible_by__user: Any
    user_application_membership: Any
    team_application_access: Any
    can_use__application_as_host: Any


class APIKeyInfoType(TypedDict, total=False):
    name: str
    description: str
    expiry_date: str


class ApplicationInviteType(TypedDict, total=False):
    id: int
    message: str
    created_at: str
    invitationToken: str
    application_membership_role: Any
    invitee: Any
    is_invited_to__application: Any


class ApplicationMembershipType(TypedDict, total=False):
    id: int
    user: Any
    is_member_of__application: Any
    application_membership_role: Any


class DeviceTypeType(TypedDict, total=False):
    id: int
    slug: str
    name: str
    is_private: bool
    logo: str
    contract: Any
    belongs_to__device_family: Any
    is_default_for__application: Any
    is_of__cpu_architecture: Any
    is_accessible_privately_by__organization: Any
    describes_device: Any
    device_type_alias: Any
