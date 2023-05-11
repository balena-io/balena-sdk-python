from typing import Any, Dict, Literal, TypedDict, Union

AnyObject = Dict[str, Any]
ApplicationMembershipRoles = Literal["developer", "operator", "observer"]


class ShutdownOptions(TypedDict, total=False):
    force: bool


class ApplicationInviteOptions(TypedDict, total=False):
    invitee: str
    roleName: ApplicationMembershipRoles
    message: str


class ResourceKeyDict(TypedDict, total=False):
    user: int
    is_member_of__application: int
    is_member_of__organization: int


ResourceKey = Union[int, ResourceKeyDict]
