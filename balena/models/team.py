from typing import List, Union

from .. import exceptions
from ..exceptions import InvalidParameter
from ..pine import PineClient
from ..settings import Settings
from ..types import AnyObject
from ..types.models import ApplicationMembershipRoles, TeamApplicationAccessType, TeamMembershipType, TeamType
from ..utils import is_id, merge
from .organization import Organization


class TeamApplicationAccess:
    """
    This class implements team application access model for balena python SDK.

    """

    def __init__(self, pine: PineClient, team: "Team", settings: Settings):
        self.__pine = pine
        self.__team = team
        self.__settings = settings
        self.RESOURCE = "team_application_access"

    def __get_role_id(self, role_name: str) -> int:
        role = self.__pine.get(
            {
                "resource": "application_membership_role",
                "id": {"name": role_name},
                "options": {"$select": "id"},
            }
        )
        if role is None:
            raise exceptions.BalenaApplicationMembershipRoleNotFound(role_name)
        return role["id"]

    def get_all_by_team(self, team_id: int, options: AnyObject = {}) -> List[TeamApplicationAccessType]:
        """
        Get all team applications access.

        Args:
            team_id (int): team id.
            options (AnyObject): extra pine options to use.

        Returns:
            List[TeamApplicationAccessType]: team application access.

        Examples:
            >>> balena.models.team.application_access.get_all_by_team(1239948)
        """

        team = self.__team.get(team_id, {"$select": "id"})

        return self.__pine.get(
            {
                "resource": self.RESOURCE,
                "options": merge(
                    {"$filter": {"team": team["id"]}},
                    options,
                ),
            }
        )

    def get(self, team_application_access_id: int, options: AnyObject = {}) -> TeamApplicationAccessType:
        """
        Get team applications access.

        Args:
            team_application_access_id (int): team application access id.
            options (AnyObject): extra pine options to use.

        Returns:
            TeamApplicationAccessType: team application access.

        Raises:
            TeamApplicationAccessNotFound: if team application access couldn't be found.

        Examples:
            >>> balena.models.team.application_access.get(1239948)
        """

        result = self.__pine.get(
            {
                "resource": self.RESOURCE,
                "id": team_application_access_id,
                "options": options,
            }
        )
        if result is None:
            raise exceptions.TeamApplicationAccessNotFound(team_application_access_id)
        return result

    def add(
        self,
        team_id: int,
        application_id_or_slug: Union[int, str],
        role_name: ApplicationMembershipRoles,
    ) -> TeamApplicationAccessType:
        """
        Add applications access to team.

        Args:
            team_id (int): team id the application access will be granted for.
            application_id_or_slug (Union[int, str]): application id or slug.
            role_name (ApplicationMembershipRoles): application membership role name.

        Returns:
            TeamApplicationAccessType: team application access.

        Examples:
            >>> balena.models.team.application_access.add(1239948, 'MyAppSlug', 'developer')
            >>> balena.models.team.application_access.add(1239948, 456789, 'observer')
        """

        from .application import Application

        app_id = Application(self.__pine, self.__settings).get(application_id_or_slug, {"$select": "id"})["id"]

        role_id = self.__get_role_id(role_name)

        return self.__pine.post(
            {
                "resource": self.RESOURCE,
                "body": {
                    "team": team_id,
                    "grants_access_to__application": app_id,
                    "application_membership_role": role_id,
                },
            }
        )

    def update(self, team_application_access_id: int, role_name: ApplicationMembershipRoles) -> None:
        """
        Update team application access.

        Args:
            team_application_access_id (int): team application access id.
            role_name (ApplicationMembershipRoles): the new role to assign.

        Examples:
            >>> balena.models.team.application_access.update(123, 'developer')
        """

        role_id = self.__get_role_id(role_name)

        self.__pine.patch(
            {
                "resource": self.RESOURCE,
                "id": team_application_access_id,
                "body": {"application_membership_role": role_id},
            }
        )

    def remove(self, team_application_access_id: int) -> None:
        """
        Remove team application access.

        Args:
            team_application_access_id (int): team application access id.

        Examples:
            >>> balena.models.team.application_access.remove(123)
        """

        self.__pine.delete(
            {
                "resource": self.RESOURCE,
                "id": team_application_access_id,
            }
        )


class TeamMembership:
    """
    This class implements team membership model for balena python SDK.

    """

    def __init__(self, pine: PineClient, team: "Team"):
        self.__pine = pine
        self.__team = team
        self.RESOURCE = "team_membership"

    def get(self, membership_id: int, options: AnyObject = {}) -> TeamMembershipType:
        """
        Get a single team membership.

        Args:
            membership_id (int): team membership id.
            options (AnyObject): extra pine options to use.

        Returns:
            TeamMembershipType: team membership.

        Raises:
            TeamMembershipNotFound: if team membership couldn't be found.

        Examples:
            >>> balena.models.team.membership.get(5)
        """

        if not isinstance(membership_id, int):
            raise InvalidParameter("membership_id", membership_id)

        result = self.__pine.get(
            {
                "resource": self.RESOURCE,
                "id": membership_id,
                "options": options,
            }
        )
        if result is None:
            raise exceptions.TeamMembershipNotFound(membership_id)

        return result

    def get_all_by_team(self, team_id: int, options: AnyObject = {}) -> List[TeamMembershipType]:
        """
        Get all memberships by team.

        Args:
            team_id (int): team id.
            options (AnyObject): extra pine options to use.

        Returns:
            List[TeamMembershipType]: team memberships.

        Examples:
            >>> balena.models.team.membership.get_all_by_team(123)
        """

        return self.__pine.get(
            {
                "resource": self.RESOURCE,
                "options": merge(
                    {"$filter": {"is_member_of__team": team_id}},
                    options,
                ),
            }
        )

    def get_all_by_user(self, username_or_id: Union[str, int], options: AnyObject = {}) -> List[TeamMembershipType]:
        """
        Get all memberships by user.

        Args:
            username_or_id (Union[str, int]): the user's username (string) or id (number).
            options (AnyObject): extra pine options to use.

        Returns:
            List[TeamMembershipType]: team memberships.

        Examples:
            >>> balena.models.team.membership.get_all_by_user('balena_os')
            >>> balena.models.team.membership.get_all_by_user(123)
        """

        if not isinstance(username_or_id, (int, str)):
            raise InvalidParameter("username_or_id", username_or_id)

        return self.__pine.get(
            {
                "resource": self.RESOURCE,
                "options": merge(
                    {
                        "$filter": {
                            "user": (
                                username_or_id
                                if isinstance(username_or_id, int)
                                else {
                                    "$any": {
                                        "$alias": "u",
                                        "$expr": {"u": {"username": username_or_id}},
                                    }
                                }
                            ),
                        },
                    },
                    options,
                ),
            }
        )

    def create(self, team: int, username: str) -> TeamMembershipType:
        """
        Creates a new membership for a team.

        Args:
            team (int): team id.
            username (str): the username of the balena user that will become a member.

        Returns:
            TeamMembershipType: team membership.

        Examples:
            >>> balena.models.team.membership.create(team=123, username="user123")
        """

        return self.__pine.post(
            {
                "resource": self.RESOURCE,
                "body": {
                    "username": username,
                    "is_member_of__team": team,
                },
            }
        )

    def remove(self, id_or_ids: Union[int, List[int]]) -> None:
        """
        Remove a team membership.

        Args:
            id_or_ids (Union[int, List[int]]): team membership id or array of team membership ids.

        Examples:
            >>> balena.models.team.membership.remove(123)
            >>> balena.models.team.membership.remove([123, 456])
        """

        ids = id_or_ids if isinstance(id_or_ids, list) else [id_or_ids]
        self.__pine.delete(
            {
                "resource": self.RESOURCE,
                "options": {"$filter": {"id": {"$in": ids}}},
            }
        )


class Team:
    """
    This class implements team model for balena python SDK.

    """

    def __init__(self, pine: PineClient, settings: Settings):
        self.__pine = pine
        self.__settings = settings
        self.__organization = Organization(pine, settings)
        self.application_access = TeamApplicationAccess(pine, self, settings)
        self.membership = TeamMembership(pine, self)

    def create(self, organization_slug_or_id: Union[str, int], name: str) -> TeamType:
        """
        Creates a new team.

        Args:
            organization_slug_or_id (Union[str, int]): organization handle (string) or id (number).
            name (str): the name of the team that will be created.

        Returns:
            TeamType: team info.

        Examples:
            >>> balena.models.team.create(1239948, 'MyTeam')
            >>> balena.models.team.create('myOrgHandle', 'MyTeam')
        """

        org_id = self.__organization.get(organization_slug_or_id, {"$select": "id"})["id"]

        return self.__pine.post({"resource": "team", "body": {"name": name, "belongs_to__organization": org_id}})

    def get_all_by_organization(
        self, organization_slug_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[TeamType]:
        """
        Get all Teams of a specific Organization.

        Args:
            organization_slug_or_id (Union[str, int]): organization handle (string), or id (number).
            options (AnyObject): extra pine options to use.

        Returns:
            List[TeamType]: list contains information of teams.

        Examples:
            >>> balena.models.team.get_all_by_organization(123)
            >>> balena.models.team.get_all_by_organization('MyOrganizationHandle')
        """

        organization = self.__organization.get(organization_slug_or_id, {"$select": "id"})

        return self.__pine.get(
            {
                "resource": "team",
                "options": merge(
                    {
                        "$filter": {
                            "belongs_to__organization": (
                                organization["id"]
                                if is_id(organization_slug_or_id)
                                else {
                                    "$any": {
                                        "$alias": "bto",
                                        "$expr": {"bto": {"handle": organization_slug_or_id}},
                                    }
                                }
                            ),
                        }
                    },
                    options,
                ),
            }
        )

    def get(self, team_id: int, options: AnyObject = {}) -> TeamType:
        """
        Get a single Team.

        Args:
            team_id (int): team id (number).
            options (AnyObject): extra pine options to use.

        Returns:
            TeamType: team info.

        Raises:
            TeamNotFound: if team couldn't be found.

        Examples:
            >>> balena.models.team.get(123)
        """

        if team_id is None:
            raise InvalidParameter("team_id", team_id)

        team = self.__pine.get({"resource": "team", "id": team_id, "options": options})
        if team is None:
            raise exceptions.TeamNotFound(team_id)

        return team

    def rename(self, team_id: int, new_team_name: str) -> None:
        """
        Rename Team.

        Args:
            team_id (int): team id (number).
            new_team_name (str): new team name (string).

        Examples:
            >>> balena.models.team.rename(123, 'MyNewTeamName')
        """

        team_options = {
            "$select": "id",
            "$expand": {
                "belongs_to__organization": {
                    "$select": "id",
                    "$expand": {
                        "owns__team": {
                            "$top": 1,
                            "$select": "name",
                            "$filter": {
                                "name": new_team_name,
                            },
                        },
                    },
                },
            },
        }
        team = self.get(team_id, team_options)
        org = team["belongs_to__organization"][0]

        if org["id"] is None:
            raise Exception(f"Team does not belong to any organization: {team_id}")

        if len(org["owns__team"]) > 0:
            raise Exception(
                f"A team with this name already exists in the organization. "
                f"Organization: {org['id']}, Name: {new_team_name}"
            )

        self.__pine.patch({"resource": "team", "id": team_id, "body": {"name": new_team_name}})

    def remove(self, team_id: int) -> None:
        """
        Remove a Team.

        Args:
            team_id (int): team id (number).

        Examples:
            >>> balena.models.team.remove(123)
        """
        self.__pine.delete({"resource": "team", "id": team_id})
