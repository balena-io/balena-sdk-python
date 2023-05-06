from typing import Any, Literal, Optional, TypedDict

from ..types import AnyObject


class APIKeyType(TypedDict):
    id: int
    created_at: str
    name: str
    description: Optional[str]
    expiry_date: Optional[str]
    is_of__actor: AnyObject


class ApplicationType(TypedDict, total=False):
    id: int
    created_at: str
    app_name: str
    actor: AnyObject
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
    application_membership_role: AnyObject
    invitee: AnyObject
    is_invited_to__application: AnyObject


class ApplicationMembershipType(TypedDict, total=False):
    id: int
    user: AnyObject
    is_member_of__application: AnyObject
    application_membership_role: AnyObject
