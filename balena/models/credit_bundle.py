from typing import Union, List
from .organization import Organization
from ..utils import merge
from ..pine import PineClient
from ..types import AnyObject
from ..types.models import CreditBundleType
from ..settings import Settings


class CreditBundle:
    """
    This class implements credit bundle model for balena python SDK.
    """

    def __init__(self, pine: PineClient, settings: Settings):
        self.__organization = Organization(pine, settings)
        self.__pine = pine

    def __get_org_id(self, organization: Union[str, int]) -> int:
        return self.__organization.get(organization, {"$select": "id"})["id"]

    def get_all_by_org(self, organization: Union[str, int], options: AnyObject = {}) -> List[CreditBundleType]:
        """
        Get all of the credit bundles purchased by the given org

        Args:
            organization (Union[str, int]): handle (string) or id (number) of the target organization.
            options (AnyObject): extra pine options to use

        Returns:
            List[CreditBundleType]: credit bundles.

        Examples:
            >>> balena.models.credit_bundle.get_all_by_org('myorghandle')
        """
        org_id = self.__get_org_id(organization)
        return self.__pine.get(
            {
                "resource": "credit_bundle",
                "options": merge(
                    options, {"$filter": {"belongs_to__organization": org_id}, "$orderby": {"created_at": "desc"}}
                ),
            }
        )

    def create(self, organization: Union[str, int], feature_id: int, credits_to_purchase: float) -> CreditBundleType:
        """
        Purchase a credit bundle for the given feature and org of the given quantity

        Args:
            organization (Union[str, int]): handle (string) or id (number) of the target organization.
            feature_id (int): id (number) of the feature for which credits are being purchased.
            credits_to_purchase (float): number of credits being purchased.

        Returns:
            CreditBundleType: credit bundle.

        Examples:
            >>> balena.models.credit_bundle.create('myorghandle', 1234, 200)
        """
        org_id = self.__get_org_id(organization)
        return self.__pine.post(
            {
                "resource": "credit_bundle",
                "body": {
                    "belongs_to__organization": org_id,
                    "is_for__feature": feature_id,
                    "original_quantity": credits_to_purchase,
                },
            }
        )
