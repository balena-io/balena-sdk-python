from typing import List, Union

from .. import exceptions
from ..exceptions import InvalidParameter
from ..pine import PineClient
from ..settings import Settings
from ..types import AnyObject
from ..types.models import TeamType
from ..utils import is_id, merge
from .organization import Organization


class Team:
    """
    This class implements team model for balena python SDK.

    """

    def __init__(self, pine: PineClient, settings: Settings):
        self.__pine = pine
        self.__settings = settings
        self.__organization = Organization(pine, settings)

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
