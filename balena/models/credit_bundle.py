from typing import Union, List
from .organization import organization as org_model
from ..utils import merge
from ..pine import pine
from ..types import AnyObject
from ..types.models import CreditBundleType


class CreditBundle:
    """
    This class implements credit bundle model for balena python SDK.
    """

    def __get_org_id(self, organization: Union[str, int]) -> int:
        return org_model.get(organization, {"$select": "id"})["id"]

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
        return pine.get(
            {
                "resource": "credit_bundle",
                "options": merge(
                    options, {"$filter": {"belongs_to__organization": org_id}, "$orderby": {"created_at": "desc"}}
                ),
            }
        )

    def create(self, organization: Union[str, int], feature_id: int, credits_to_purchase: float) -> CreditBundleType:
        """
        Get all of the credit bundles purchased by the given org

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
        return pine.post(
            {
                "resource": "credit_bundle",
                "body": {
                    "belongs_to__organization": org_id,
                    "is_for__feature": feature_id,
                    "original_quantity": credits_to_purchase,
                },
            }
        )
