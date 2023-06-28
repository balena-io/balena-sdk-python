from datetime import datetime, timedelta
from typing import List, Optional, Union

from .. import exceptions
from ..pine import PineClient
from ..types import AnyObject
from ..types.models import DeviceHistoryType
from ..utils import is_full_uuid, is_id, merge
from ..settings import Settings
from .application import Application


def history_timerange_filter_with_guard(from_date=None, to_date=None):
    from_date_filter = {}
    to_date_filter = {}

    if from_date is not None:
        if not isinstance(from_date, datetime):
            raise exceptions.InvalidParameter("from_date", from_date)
        else:
            from_date_filter = {"$ge": from_date}

    if to_date is not None:
        if not isinstance(to_date, datetime):
            raise exceptions.InvalidParameter("to_date", to_date)
        else:
            to_date_filter = {"$le": to_date}

    filter = {**from_date_filter, **to_date_filter}

    if filter == {}:
        return {}

    return {"created_at": filter}


class DeviceHistory:
    """
    This class implements device history model for balena python SDK.

    """

    def __init__(self, pine: PineClient, settings: Settings):
        self.__pine = pine
        self.__application = Application(pine, settings)

    def get_all_by_device(
        self,
        uuid_or_id: Union[str, int],
        from_date: datetime = datetime.utcnow() + timedelta(days=-7),
        to_date: Optional[datetime] = None,
        options: AnyObject = {},
    ) -> List[DeviceHistoryType]:
        """
        Get all device history entries for a device.

        Args:
            uuid_or_id (str): device uuid (32 / 62 digits string) or id (number) __note__: No short IDs supported
            from_date (datetime): history entries newer than or equal to this timestamp. Defaults to 7 days ago
            to_date (datetime): history entries younger or equal to this date.
            options (AnyObject): extra pine options to use

        Returns:
            List[DeviceHistoryType]: device history entries.

        Examples:
            >>> balena.models.device.history.get_all_by_device('6046335305c8142883a4466d30abe211')
            >>> balena.models.device.history.get_all_by_device(11196426)
            >>> balena.models.device.history.get_all_by_device(
            ...     11196426, from_date=datetime.utcnow() + timedelta(days=-5)
            ... )
            >>> balena.models.device.history.get_all_by_device(
            ...     11196426,
            ...     from_date=datetime.utcnow() + timedelta(days=-10),
            ...     to_date=from_date = datetime.utcnow() + timedelta(days=-5))
            ... )

        """
        dollar_filter = history_timerange_filter_with_guard(from_date, to_date)
        if is_id(uuid_or_id):
            dollar_filter = {**dollar_filter, "tracks__device": uuid_or_id}
        elif is_full_uuid(uuid_or_id):
            dollar_filter = {**dollar_filter, "uuid": uuid_or_id}
        else:
            raise exceptions.InvalidParameter("uuid_or_id", uuid_or_id)

        return self.__pine.get({"resource": "device_history", "options": merge({"$filter": dollar_filter}, options)})

    def get_all_by_application(
        self,
        slug_or_uuid_or_id: Union[str, int],
        from_date: datetime = datetime.utcnow() + timedelta(days=-7),
        to_date: Optional[datetime] = None,
        options: AnyObject = {},
    ) -> List[DeviceHistoryType]:
        """
        Get all device history entries for an application.

        Args:
            slug_or_uuid_or_id (Union[str, int]): application slug (string), uuid (string) or id (number)
            from_date (datetime): history entries newer than or equal to this timestamp. Defaults to 7 days ago
            to_date (datetime): history entries younger or equal to this date.
            options (AnyObject): extra pine options to use

        Returns:
            List[DeviceHistoryType]: device history entries.

        Examples:
            >>> balena.models.device.history.get_all_by_application('myorg/myapp')
            >>> balena.models.device.history.get_all_by_application(11196426)
            >>> balena.models.device.history.get_all_by_application(
            ...     11196426, from_date=datetime.utcnow() + timedelta(days=-5)
            ... )
            >>> balena.models.device.history.get_all_by_application(
            ...     11196426,
            ...     from_date=datetime.utcnow() + timedelta(days=-10),
            ...     to_date=from_date = datetime.utcnow() + timedelta(days=-5))
            ... )
        """
        app_id = self.__application.get(slug_or_uuid_or_id, {"$select": "id"})["id"]

        return self.__pine.get(
            {
                "resource": "device_history",
                "options": merge(
                    {
                        "$filter": {
                            **history_timerange_filter_with_guard(from_date, to_date),
                            "belongs_to__application": app_id,
                        }
                    },
                    options,
                ),
            }
        )
