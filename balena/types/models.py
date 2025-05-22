from typing import Any, List, Literal, Optional, TypedDict, Union, TypeVar, Dict

__T = TypeVar("__T")


class PineDeferred(TypedDict):
    __id: int


NavigationResource = Union[List[__T], PineDeferred]
ReverseNavigationResource = Union[List[__T], None]
ConceptTypeNavigationResource = NavigationResource[__T]
OptionalNavigationResource = Union[List[__T], PineDeferred, None]


class WebResource(TypedDict):
    filename: str
    href: str
    content_type: str
    content_disposition: str
    size: int


class UserType(TypedDict):
    id: int
    actor: ConceptTypeNavigationResource["ActorType"]
    created_at: str
    username: str

    organization_membership: ReverseNavigationResource["OrganizationMembershipType"]
    user_application_membership: ReverseNavigationResource["ApplicationMembershipType"]
    team_membership: ReverseNavigationResource["TeamMembershipType"]
    has_direct_access_to__application: ReverseNavigationResource["TypeApplication"]


ApplicationMembershipRoles = Literal["developer", "operator", "observer"]
OrganizationMembershipRoles = Literal["administrator", "member"]


class ApplicationMembershipRoleType(TypedDict):
    id: int
    name: ApplicationMembershipRoles


class OrganizationMembershipRoleType(TypedDict):
    id: int
    name: OrganizationMembershipRoles


class TeamApplicationAccessType(TypedDict):
    id: int
    team: NavigationResource["TeamType"]
    # application
    grants_access_to__application: NavigationResource["TypeApplication"]
    application_membership_role: NavigationResource["ApplicationMembershipRoleType"]


class TeamType(TypedDict):
    id: int
    created_at: str
    name: str

    belongs_to__organization: NavigationResource["OrganizationType"]

    # includes__user
    team_membership: ReverseNavigationResource["TeamMembershipType"]
    # grants_access_to__application
    team_application_access: ReverseNavigationResource["TeamApplicationAccessType"]


class TeamMembershipType(TypedDict):
    id: int
    created_at: str

    user: NavigationResource[UserType]
    # team
    is_member_of__team: NavigationResource["TeamType"]


class PublicDeviceType(TypedDict):
    latitude: str
    longitude: str
    belongs_to__application: NavigationResource["TypeApplication"]
    is_of__device_type: NavigationResource["TypeDevice"]
    was_recently_online: bool


class PublicOrganizationType(TypedDict):
    id: int
    name: str
    handle: str


class ActorType(TypedDict):
    id: int

    is_of__user: OptionalNavigationResource[UserType]
    is_of__application: OptionalNavigationResource["TypeApplication"]
    is_of__device: OptionalNavigationResource["TypeDevice"]
    is_of__public_device: OptionalNavigationResource[PublicDeviceType]
    api_key: OptionalNavigationResource["APIKeyType"]


class ApplicationType:
    id: int
    name: str
    slug: str
    description: Optional[str]
    supports_multicontainer: bool
    supports_web_url: bool
    is_legacy: bool
    requires_payment: bool
    needs__os_version_range: Optional[str]
    maximum_device_count: Optional[int]


class APIKeyType(TypedDict):
    id: int
    created_at: str
    name: str
    description: Optional[str]
    expiry_date: Optional[str]
    is_of__actor: NavigationResource[ActorType]


class ApplicationHostedOnApplication:
    application: NavigationResource["TypeApplication"]
    can_use__application_as_host: NavigationResource["TypeApplication"]


class TypeApplication(TypedDict):
    id: int
    created_at: str
    app_name: str
    actor: ConceptTypeNavigationResource[ActorType]
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
    public_organization: OptionalNavigationResource[PublicOrganizationType]
    application_type: NavigationResource[ApplicationType]
    is_for__device_type: NavigationResource["DeviceTypeType"]
    depends_on__application: OptionalNavigationResource[ApplicationType]
    organization: NavigationResource["OrganizationType"]
    should_be_running__release: OptionalNavigationResource["ReleaseType"]

    application_config_variable: ReverseNavigationResource["EnvironmentVariableBase"]
    application_environment_variable: ReverseNavigationResource["EnvironmentVariableBase"]
    build_environment_variable: ReverseNavigationResource["EnvironmentVariableBase"]
    application_tag: ReverseNavigationResource["BaseTagType"]
    owns__device: ReverseNavigationResource["TypeDevice"]
    owns__public_device: ReverseNavigationResource[PublicDeviceType]
    owns__release: ReverseNavigationResource["ReleaseType"]
    service: ReverseNavigationResource["ServiceType"]
    is_depended_on_by__application: ReverseNavigationResource[ApplicationType]
    is_directly_accessible_by__user: ReverseNavigationResource[UserType]
    user_application_membership: ReverseNavigationResource["ApplicationMembershipType"]
    team_application_access: ReverseNavigationResource[TeamApplicationAccessType]
    can_use__application_as_host: ReverseNavigationResource[ApplicationHostedOnApplication]


class TypeApplicationWithDeviceServiceDetails(TypeApplication):
    owns__device: List["TypeDeviceWithServices"]  # type: ignore


class APIKeyInfoType(TypedDict, total=False):
    name: str
    description: Optional[str]
    expiry_date: Optional[str]


class InviteeType(TypedDict):
    id: int
    created_at: str
    email: str


class ApplicationInviteType(TypedDict):
    id: int
    message: str
    created_at: str
    invitationToken: str
    application_membership_role: NavigationResource[ApplicationMembershipRoleType]
    invitee: NavigationResource[InviteeType]
    is_invited_to__application: NavigationResource[ApplicationType]


class ApplicationMembershipType(TypedDict):
    id: int
    user: NavigationResource[UserType]
    is_member_of__application: NavigationResource[TypeApplication]
    application_membership_role: NavigationResource[ApplicationMembershipRoleType]


class DeviceManufacturerType(TypedDict):
    created_at: str
    modified_at: str
    id: int
    slug: str
    name: str


class DeviceFamilyType(TypedDict):
    created_at: str
    modified_at: str
    id: int
    slug: str
    name: str
    is_manufactured_by__device_manufacturer: OptionalNavigationResource[DeviceManufacturerType]


class CpuArchitectureType(TypedDict):
    id: int
    slug: str
    is_supported_by__device_type: ReverseNavigationResource["CpuArchitectureType"]


class DeviceTypeAliasType(TypedDict):
    id: int
    is_referenced_by__alias: str
    references__device_type: NavigationResource["DeviceTypeType"]


class DeviceTypeType(TypedDict):
    id: int
    slug: str
    name: str
    is_private: bool
    logo: str
    contract: Any
    belongs_to__device_family: OptionalNavigationResource[DeviceFamilyType]
    is_default_for__application: ReverseNavigationResource[TypeApplication]
    is_of__cpu_architecture: NavigationResource[CpuArchitectureType]
    is_accessible_privately_by__organization: ReverseNavigationResource["OrganizationType"]
    describes_device: ReverseNavigationResource["TypeDevice"]
    device_type_alias: ReverseNavigationResource["DeviceTypeAliasType"]


class ServiceInstanceType(TypedDict):
    id: int
    created_at: str
    service_type: str
    ip_address: str
    last_heartbeat: str


class ImageInstallType(TypedDict):
    id: int
    download_progress: Optional[float]
    status: str
    install_date: str

    installs__image: NavigationResource["ImageType"]
    device: NavigationResource["TypeDevice"]
    is_provided_by__release: NavigationResource["ReleaseType"]


class TypeDevice(TypedDict):
    id: int
    actor: ConceptTypeNavigationResource[ActorType]
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
    update_status: Literal[ "rejected", "downloading", "downloaded", "applying changes", "aborted", "done"]
    last_update_status_event: str
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
    status: str
    supervisor_version: str
    uuid: str
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
    overall_status: Literal[
        "configuring",
        "inactive",
        "post-provisioning",
        "updating",
        "operational",
        "disconnected",
        "reduced-functionality",
    ]

    # This is a computed term
    overall_progress: int

    is_of__device_type: NavigationResource[DeviceTypeType]
    belongs_to__application: NavigationResource[TypeApplication]
    belongs_to__user: OptionalNavigationResource[UserType]
    is_running__release: OptionalNavigationResource["ReleaseType"]
    is_pinned_on__release: OptionalNavigationResource["ReleaseType"]
    is_managed_by__service_instance: OptionalNavigationResource[ServiceInstanceType]
    should_be_operated_by__release: OptionalNavigationResource["ReleaseType"]
    should_be_managed_by__release: OptionalNavigationResource["ReleaseType"]
    device_config_variable: ReverseNavigationResource["EnvironmentVariableBase"]
    device_environment_variable: ReverseNavigationResource["EnvironmentVariableBase"]
    device_tag: ReverseNavigationResource["BaseTagType"]
    service_install: ReverseNavigationResource[ServiceInstanceType]
    image_install: ReverseNavigationResource[ImageInstallType]


class TypeCurrentService(TypedDict):
    id: int
    image_id: int
    service_id: int
    download_progress: int
    status: str
    install_date: str


class TypeDeviceWithServices(TypeDevice):
    current_services: Dict[str, List[TypeCurrentService]]


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


class OrganizationPrivateDeviceTypeAccess(TypedDict):
    id: int
    organization: NavigationResource["OrganizationType"]
    has_private_access_to__device_type: NavigationResource[TypeDevice]


class OrganizationType(TypedDict):
    id: int
    created_at: str
    name: str
    handle: str
    logo_image: WebResource
    has_past_due_invoice_since__date: str
    application: ReverseNavigationResource[TypeApplication]
    organization_membership: ReverseNavigationResource["OrganizationMembershipType"]
    owns__team: ReverseNavigationResource[TeamType]
    organization__has_private_access_to__device_type: ReverseNavigationResource[OrganizationPrivateDeviceTypeAccess]


class OrganizationInviteType(TypedDict):
    id: int
    message: str
    created_at: str
    invitationToken: str
    organization_membership_role: NavigationResource[OrganizationMembershipRoleType]
    invitee: NavigationResource[InviteeType]
    is_invited_to__organization: NavigationResource[OrganizationType]


class OrganizationMembershipType(TypedDict):
    id: int
    created_at: str
    user: NavigationResource[UserType]
    is_member_of__organization: NavigationResource[OrganizationType]
    organization_membership_role: NavigationResource[OrganizationMembershipRoleType]
    effective_seat_role: str
    organization_membership_tag: ReverseNavigationResource["OrganizationMembershipTagType"]


class OrganizationMembershipTagType(TypedDict):
    organization_membership: NavigationResource[OrganizationMembershipType]


class BaseTagType(TypedDict):
    id: int
    tag_key: str
    value: str


class EnvironmentVariableBase(TypedDict):
    id: int
    name: str
    value: str


class ReleaseImageType(TypedDict):
    id: int
    created_at: str
    image: NavigationResource["ImageType"]
    is_part_of__release: NavigationResource["ReleaseType"]


class ImageType(TypedDict):
    id: int
    created_at: str
    build_log: str
    contract: Any
    content_hash: str
    project_type: str
    status: str
    is_stored_at__image_location: str
    start_timestamp: str
    end_timestamp: str
    push_timestamp: str
    image_size: str
    dockerfile: str
    error_message: str
    is_a_build_of__service: NavigationResource["ServiceType"]
    release_image: ReverseNavigationResource[ReleaseImageType]


class ServiceType(TypedDict):
    id: int
    created_at: str
    service_name: str
    application: NavigationResource[TypeApplication]
    is_built_by__image: ReverseNavigationResource[ImageType]
    service_environment_variable: ReverseNavigationResource[EnvironmentVariableBase]
    device_service_environment_variable: ReverseNavigationResource[EnvironmentVariableBase]


ReleaseStatus = Literal["cancelled", "error", "failed", "interrupted", "local", "running", "success", "timeout"]


class ReleaseVersion(TypedDict):
    raw: str
    major: int
    minor: int
    patch: int
    version: str
    build: List[str]
    prerelease: List[Union[str, int]]


class ReleaseType(TypedDict):
    id: int
    created_at: str
    commit: str
    composition: Any
    contract: Any
    status: ReleaseStatus
    source: str
    build_log: str
    is_invalidated: bool
    start_timestamp: str
    update_timestamp: str
    end_timestamp: str
    phase: Literal["next", "current", "sunset", "end-of-life"]
    semver: str
    semver_major: int
    semver_minor: int
    semver_patch: int
    semver_prerelease: str
    semver_build: str
    variant: str
    revision: int
    known_issue_list: str
    # This is a computed term
    raw_version: str
    # This is a computed term
    version: ReleaseVersion
    is_final: bool
    is_finalized_at__date: str
    note: str
    invalidation_reason: str
    is_created_by__user: OptionalNavigationResource[UserType]
    belongs_to__application: NavigationResource[TypeApplication]
    release_image: ReverseNavigationResource[ReleaseImageType]
    should_be_running_on__application: ReverseNavigationResource[TypeApplication]
    is_running_on__device: ReverseNavigationResource[TypeDevice]
    is_pinned_to__device: ReverseNavigationResource[TypeDevice]
    should_operate__device: ReverseNavigationResource[TypeDevice]
    should_manage__device: ReverseNavigationResource[TypeDevice]
    release_tag: ReverseNavigationResource[BaseTagType]


class ImageBasicInfoType(TypedDict):
    id: int
    service_name: str


class BasicUserInfoType(TypedDict):
    id: int
    username: str


class ReleaseWithImageDetailsType(ReleaseType):
    images: List[ImageBasicInfoType]
    user: BasicUserInfoType


class DeviceHistoryType(TypedDict):
    created_at: str
    id: int
    end_timestamp: str
    is_created_by__actor: OptionalNavigationResource[ActorType]
    is_ended_by__actor: OptionalNavigationResource[ActorType]
    tracks__device: NavigationResource[TypeDevice]
    tracks__actor: OptionalNavigationResource[ActorType]
    uuid: Optional[str]
    belongs_to__application: NavigationResource[TypeApplication]
    is_active: bool
    is_running__release: OptionalNavigationResource[ReleaseType]
    should_be_running__release: OptionalNavigationResource[ReleaseType]
    os_version: Optional[str]
    os_variant: Optional[str]
    supervisor_version: Optional[str]
    is_of__device_type: OptionalNavigationResource[DeviceTypeType]
    should_be_managed_by__release: OptionalNavigationResource[ReleaseType]


class SSHKeyType(TypedDict):
    title: str
    public_key: str
    id: int
    created_at: str
    user: NavigationResource[UserType]


class CreditBundleType(TypedDict):
    id: int
    created_at: str
    is_created_by__user: OptionalNavigationResource[UserType]
    original_quantity: float
    total_balance: float
    total_cost: float
    payment_status: Literal["processing", "paid", "failed", "complimentary", "cancelled", "refunded"]
    belongs_to__organization: NavigationResource[OrganizationType]
    is_for__feature: Any
    is_associated_with__invoice_id: Optional[str]
    error_message: Optional[str]
