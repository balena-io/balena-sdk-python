from typing import Any, Literal, Optional, TypedDict


class APIKeyType(TypedDict):
    id: int
    created_at: str
    name: str
    description: Optional[str]
    expiry_date: Optional[str]
    is_of__actor: Any


class ApplicationType(TypedDict):
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


class APIKeyInfoType(TypedDict):
    name: str
    description: str
    expiry_date: str


class ApplicationInviteType(TypedDict):
    id: int
    message: str
    created_at: str
    invitationToken: str
    application_membership_role: Any
    invitee: Any
    is_invited_to__application: Any


class ApplicationMembershipType(TypedDict):
    id: int
    user: Any
    is_member_of__application: Any
    application_membership_role: Any


class DeviceTypeType(TypedDict):
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


class TypeDeviceState(TypedDict):
    key: str
    name: str


class TypeDevice(TypedDict):
    id: int
    actor: Any
    created_at: str
    modified_at: str
    custom_latitude: str
    custom_longitude: str
    device_name: str
    download_progress: int
    ip_address: str
    public_address: str
    mac_address: str
    is_accessible_by_support_until__date: str
    is_connected_to_vpn: bool
    is_locked_until__date: str
    is_web_accessible: bool
    is_active: bool
    # This is a computed term
    is_frozen: bool
    is_online: bool
    last_connectivity_event: str
    last_vpn_event: str
    latitude: str
    local_id: str
    location: str
    longitude: str
    note: str
    os_variant: str
    os_version: str
    provisioning_progress: int
    provisioning_state: str
    state: TypeDeviceState
    status: str
    status_sort_index: int
    supervisor_version: str
    uuid: str
    vpn_address: str
    api_heartbeat_state: Literal["online", "offline", "timeout", "unknown"]
    memory_usage: int
    memory_total: int
    storage_block_device: str
    storage_usage: int
    storage_total: int
    cpu_usage: int
    cpu_temp: int
    cpu_id: str
    is_undervolted: bool
    # This is a computed term
    overall_status: Any
    # This is a computed term
    overall_progress: int

    is_of__device_type: Any
    belongs_to__application: Any
    belongs_to__user: Any
    is_running__release: Any
    should_be_running__release: Any
    is_managed_by__service_instance: Any
    should_be_managed_by__supervisor_release: Any
    device_config_variable: Any
    device_environment_variable: Any
    device_tag: Any
    service_install: Any
    image_install: Any


class DeviceMetricsType(TypedDict):
    memory_usage: int
    memory_total: int
    storage_block_device: str
    storage_usage: int
    storage_total: int
    cpu_usage: int
    cpu_temp: int
    cpu_id: str
    is_undervolted: bool


class OrganizationType(TypedDict):
    id: int
    created_at: str
    name: str
    handle: str
    has_past_due_invoice_since__date: str
    application: Any
    organization_membership: Any
    owns__team: Any
    organization__has_private_access_to__device_type: Any


class OrganizationInviteType(TypedDict):
    id: int
    message: str
    created_at: str
    invitationToken: str
    organization_membership_role: Any
    invitee: Any
    is_invited_to__organization: Any


class OrganizationMembershipType(TypedDict):
    id: int
    created_at: str
    user: Any
    is_member_of__organization: Any
    organization_membership_role: Any
    effective_seat_role: str
    organization_membership_tag: Any


class OrganizationMembershipTagType(TypedDict):
    organization_membership: Any


class BaseTagType(TypedDict):
    id: int
    tag_key: str
    value: str
