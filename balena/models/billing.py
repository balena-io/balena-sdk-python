from typing import Union, TypedDict, Literal, Optional, List
from .organization import Organization
from ..pine import PineClient
from ..settings import Settings
from ..balena_auth import request


class BillingAccountAddressInfo(TypedDict):
    address1: str
    address2: str
    city: str
    state: str
    zip: str
    country: str
    phone: str


class BillingAccountInfo(TypedDict):
    account_state: str
    first_name: str
    last_name: str
    company_name: str
    email: str
    cc_emails: str
    vat_number: str
    address: BillingAccountAddressInfo


BillingInfoType = Literal["bank_account", "credit_card", "paypal"]


class BillingInfo(TypedDict):
    full_name: str
    first_name: str
    last_name: str
    company: str
    vat_number: str
    address1: str
    address2: str
    city: str
    state: str
    zip: str
    country: str
    phone: str

    type: Optional[BillingInfoType]


class CardBillingInfo(BillingInfo):
    card_type: str
    year: str
    month: str
    first_one: str
    last_four: str


class BankAccountBillingInfo(BillingInfo):
    account_type: str
    last_four: str
    name_on_account: str
    routing_number: str


TokenBillingSubmitInfo = TypedDict("TokenBillingSubmitInfo", {"token_id": str, "g-recaptcha-response": Optional[str]})


class Charge(TypedDict):
    itemType: str
    name: str
    code: str
    unitCostCents: str
    quantity: str
    isQuantifiable: Optional[bool]


class BillingPlanBillingInfo(TypedDict):
    currency: str
    totalCostCents: str
    charges: List[Charge]


class Addon(TypedDict):
    code: str
    unitCostCents: Optional[str]
    quantity: Optional[str]


class BillingAddonPlanInfo(TypedDict):
    code: str
    currentPeriodEndDate: Optional[str]
    billing: BillingPlanBillingInfo
    addOns: List[Addon]


SupportInfo = TypedDict("Support", {"name": str, "title": str})


class BillingPlanInfo(TypedDict):
    name: str
    title: str
    code: str
    tier: str
    currentPeriodEndDate: Optional[str]
    intervalUnit: Optional[str]
    intervalLength: Optional[str]
    addonPlan: Optional[BillingAddonPlanInfo]
    billing: BillingPlanBillingInfo
    support: SupportInfo


class InvoiceInfo(TypedDict):
    closed_at: str
    created_at: str
    due_on: str
    currency: str
    invoice_number: str
    subtotal_in_cents: str
    total_in_cents: str
    uuid: str
    state: Literal["pending", "paid", "failed", "past_due"]


class PlanChangeOptions(TypedDict):
    tier: str
    cycle: Literal["monthly", "annual"]
    planChangeReason: Optional[str]


class UpdateAccountBody(TypedDict, total=False):
    email: str
    cc_emails: str


class Billing:
    """
    This class implements billing model for balena python SDK.
    """

    def __init__(self, pine: PineClient, settings: Settings):
        self.__settings = settings
        self.__organization = Organization(pine, settings)

    def __get_org_id(self, organization: Union[str, int]) -> int:
        return self.__organization.get(organization, {"$select": "id"})["id"]

    def get_account(self, organization: Union[str, int]) -> BillingAccountInfo:
        """
        Get the user's billing account

        Args:
            organization (Union[str, int]): handle (string) or id (number) of the target organization.

        Returns:
            BillingAccountInfo: billing account.

        Examples:
            >>> balena.models.billing.get_account('myorghandle')
        """
        org_id = self.__get_org_id(organization)
        return request(method="GET", settings=self.__settings, path=f"/billing/v1/account/{org_id}")

    def get_plan(self, organization: Union[str, int]) -> BillingPlanInfo:
        """
        Get the current billing plan

        Args:
            organization (Union[str, int]): handle (string) or id (number) of the target organization.

        Returns:
            BillingPlanInfo: billing account.

        Examples:
            >>> balena.models.billing.get_plan('myorghandle')
        """
        org_id = self.__get_org_id(organization)
        return request(method="GET", settings=self.__settings, path=f"/billing/v1/account/{org_id}/plan")

    def get_billing_info(self, organization: Union[str, int]) -> BillingInfo:
        """
        Get the current billing information

        Args:
            organization (Union[str, int]): handle (string) or id (number) of the target organization.

        Returns:
            BillingInfo: billing information.

        Examples:
            >>> balena.models.billing.get_billing_info('myorghandle')
        """
        org_id = self.__get_org_id(organization)
        return request(method="GET", settings=self.__settings, path=f"/billing/v1/account/{org_id}/info")

    def update_billing_info(self, organization: Union[str, int], billing_info: TokenBillingSubmitInfo) -> BillingInfo:
        """
        Updates the current billing information

        Args:
            organization (Union[str, int]): handle (string) or id (number) of the target organization.
            billing_info (TokenBillingSubmitInfo): a dict containing a billing info token_id

        Returns:
            BillingInfo: billing information.

        Examples:
            >>> balena.models.billing.update_billing_info('myorghandle', { token_id: 'xxxxxxx' })
        """
        org_id = self.__get_org_id(organization)
        return request(
            method="PATCH", settings=self.__settings, path=f"/billing/v1/account/{org_id}/info", body=billing_info
        )

    def update_account_info(self, organization: Union[str, int], account_info: UpdateAccountBody) -> None:
        """
        Update the current billing account information

        Args:
            organization (Union[str, int]): handle (string) or id (number) of the target organization.
            account_info (UpdateAccountBody): a dict containing billing account info

        Examples:
            >>> balena.models.billing.update_account_info('myorghandle', { email: 'hello@balena.io' })
        """
        org_id = self.__get_org_id(organization)
        return request(
            method="PATCH", settings=self.__settings, path=f"/billing/v1/account/{org_id}", body=account_info
        )

    def change_plan(self, organization: Union[str, int], plan_change_options: PlanChangeOptions) -> None:
        """
        Change the current billing plan

        Args:
            organization (Union[str, int]): handle (string) or id (number) of the target organization.
            plan_change_options (PlanChangeOptions): a dict containing billing account info

        Examples:
            >>> balena.models.billing.change_plan('myorghandle', { billingCode: 'prototype-v2', cycle: 'annual' })
        """
        org_id = self.__get_org_id(organization)
        body = {**plan_change_options, "annual": plan_change_options["cycle"] == "annual"}
        return request(method="PATCH", settings=self.__settings, path=f"/billing/v1/account/{org_id}", body=body)

    def get_invoices(self, organization: Union[str, int]) -> List[InvoiceInfo]:
        """
        Get the available invoices

        Args:
            organization (Union[str, int]): handle (string) or id (number) of the target organization.

        Examples:
            >>> balena.models.billing.get_invoices('myorghandle')
        """
        org_id = self.__get_org_id(organization)
        return request(method="GET", settings=self.__settings, path=f"/billing/v1/account/{org_id}/invoices")

    def download_invoice(self, organization: Union[str, int], invoice_number: Union[str, int]):
        """
        Download a specific invoice

        Args:
            organization (Union[str, int]): handle (string) or id (number) of the target organization.
            invoice_number (Union[str, int]): an invoice number (or the number inside a string)

        Examples:
            >>> with b.models.billing.download_invoice("myorg", "0000") as stream:
            ...    stream.raise_for_status()
            ...    with open("myinvoice.pdf", "wb") as f:
            ...        for chunk in stream.iter_content(chunk_size=8192):
            ...            f.write(chunk)
        """
        org_id = self.__get_org_id(organization)
        return request(
            method="GET",
            path=f"/billing/v1/account/{org_id}/invoices/{invoice_number}/download",
            settings=self.__settings,
            stream=True,
            return_raw=True,
        )
