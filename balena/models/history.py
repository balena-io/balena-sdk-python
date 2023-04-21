from abc import ABC
from datetime import datetime, timedelta
from ..utils import is_id, is_full_uuid
from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions


class History:
    """
    This class is a wrapper for history models.

    """

    def __init__(self):
        self.device_history = DeviceHistory()


class HistoryBaseClass(ABC):
    """
    This class is a private abstract base class for history models.

    """

    def __init__(self):
        self.settings = Settings()
        self.base_request = BaseRequest()

    def _history_timerange_filter_with_guard(self, fromDate=None, toDate=None):
        rawTimeRangeFilters = []
        if fromDate is not None:
            if isinstance(fromDate, datetime):
                rawTimeRangeFilters.append(f"(created_at ge datetime'{fromDate.isoformat()}')")
            else:
                raise exceptions.InvalidParameter("fromDate", fromDate)

        if toDate is not None:
            if isinstance(toDate, datetime):
                rawTimeRangeFilters.append(f"(created_at le datetime'{toDate.isoformat()}')")
            else:
                raise exceptions.InvalidParameter("toDate", toDate)

        rawFilterString = "$filter=" + " and ".join(rawTimeRangeFilters)

        if len(rawTimeRangeFilters) > 0:
            return rawFilterString
        else:
            return None

    def _get_history_by_resource_and_filter(self, resource_name, fromDate=None, toDate=None, **options):
        rawTimeRangeFilter = self._history_timerange_filter_with_guard(fromDate=fromDate, toDate=toDate)

        params = {"filters": options}

        history_resource = resource_name + "_history"
        return self.base_request.request(
            history_resource,
            "GET",
            params=params,
            endpoint=self.settings.get("pine_endpoint"),
            raw_query=rawTimeRangeFilter,
        )["d"]


class DeviceHistory(HistoryBaseClass):
    """
    This class implements device history model for balena python SDK.

    """

    def get_all_by_device(self, uuid_or_id, fromDate=datetime.utcnow() + timedelta(days=-7), toDate=None):
        """
        Get all device history entries for a device.

        Args:
            uuid_or_id (str): device uuid or id.

        Returns:
            list: device history entries.

        Examples:
            >>> balena.models.history.device_history.get_all_by_device('6046335305c8142883a4466d30abe211c3a648251556c23520dcff503c9dab')
            >>> balena.models.history.device_history.get_all_by_device('6046335305c8142883a4466d30abe211')
            >>> balena.models.history.device_history.get_all_by_device('11196426')
            >>> balena.models.history.device_history.get_all_by_device('11196426', fromDate=datetime.utcnow() + timedelta(days=-5))
            >>> balena.models.history.device_history.get_all_by_device('11196426', fromDate=datetime.utcnow() + timedelta(days=-10), toDate=fromDate = datetime.utcnow() + timedelta(days=-5)))
            [
                {
                    "id": 48262901,
                    "tracks__device": {
                        "__id": 11196426,
                        "__deferred": {"uri": "/v6/device(@id)?@id=11196426"},
                    },
                    "tracks__actor": {
                        "__id": 14923839,
                        "__deferred": {"uri": "/v6/actor(@id)?@id=14923839"},
                    },
                    "uuid": "6046335305c8142883a4466d30abe211c3a648251556c23520dcff503c9dab",
                    "is_active": False,
                    "belongs_to__application": {
                        "__id": 2036095,
                        "__deferred": {"uri": "/v6/application(@id)?@id=2036095"},
                    },
                    "is_running__release": {
                        "__id": 2534745,
                        "__deferred": {"uri": "/v6/release(@id)?@id=2534745"},
                    },
                    "should_be_running__release": {
                        "__id": 2534744,
                        "__deferred": {"uri": "/v6/release(@id)?@id=2534744"},
                    },
                    "should_be_managed_by__release": None,
                    "os_version": None,
                    "os_variant": None,
                    "supervisor_version": None,
                    "is_of__device_type": {
                        "__id": 57,
                        "__deferred": {"uri": "/v6/device_type(@id)?@id=57"},
                    },
                    "end_timestamp": None,
                    "created_at": "2023-03-28T20:28:22.773Z",
                    "is_created_by__actor": {
                        "__id": 14845379,
                        "__deferred": {"uri": "/v6/actor(@id)?@id=14845379"},
                    },
                    "is_ended_by__actor": None,
                    "__metadata": {"uri": "/v6/device_history(@id)?@id=48262901"},
                }
            ]

        """  # noqa: E501

        if is_id(uuid_or_id):
            return self._get_history_by_resource_and_filter(
                "device", tracks__device=uuid_or_id, fromDate=fromDate, toDate=toDate
            )
        elif is_full_uuid(uuid_or_id):
            return self._get_history_by_resource_and_filter("device", uuid=uuid_or_id, fromDate=fromDate, toDate=toDate)
        else:
            raise exceptions.InvalidParameter("uuid_or_id", uuid_or_id)

    def get_all_by_application(self, app_id, fromDate=datetime.utcnow() + timedelta(days=-7), toDate=None):
        """
        Get all device history entries for an application.

        Args:
            app_id (str): application id.

        Returns:
            list: device history entries.

        Examples:
            >>> balena.models.history.device.get_all_by_application('2036095')
            >>> balena.models.history.device.get_all_by_application('2036095', fromDate=datetime.utcnow() + timedelta(days=-5))
            >>> balena.models.history.device.get_all_by_application('2036095', fromDate=datetime.utcnow() + timedelta(days=-10), toDate=fromDate = datetime.utcnow() + timedelta(days=-5)))
            [
                {
                    "id": 48262901,
                    "tracks__device": {
                        "__id": 11196426,
                        "__deferred": {"uri": "/v6/device(@id)?@id=11196426"},
                    },
                    "tracks__actor": {
                        "__id": 14923839,
                        "__deferred": {"uri": "/v6/actor(@id)?@id=14923839"},
                    },
                    "uuid": "6046335305c8142883a4466d30abe211c3a648251556c23520dcff503c9dab",
                    "is_active": False,
                    "belongs_to__application": {
                        "__id": 2036095,
                        "__deferred": {"uri": "/v6/application(@id)?@id=2036095"},
                    },
                    "is_running__release": {
                        "__id": 2534745,
                        "__deferred": {"uri": "/v6/release(@id)?@id=2534745"},
                    },
                    "should_be_running__release": {
                        "__id": 2534744,
                        "__deferred": {"uri": "/v6/release(@id)?@id=2534744"},
                    },
                    "should_be_managed_by__release": None,
                    "os_version": None,
                    "os_variant": None,
                    "supervisor_version": None,
                    "is_of__device_type": {
                        "__id": 57,
                        "__deferred": {"uri": "/v6/device_type(@id)?@id=57"},
                    },
                    "end_timestamp": None,
                    "created_at": "2023-03-28T20:28:22.773Z",
                    "is_created_by__actor": {
                        "__id": 14845379,
                        "__deferred": {"uri": "/v6/actor(@id)?@id=14845379"},
                    },
                    "is_ended_by__actor": None,
                    "__metadata": {"uri": "/v6/device_history(@id)?@id=48262901"},
                }
            ]

        """  # noqa: E501

        return self._get_history_by_resource_and_filter(
            "device", belongs_to__application=app_id, fromDate=fromDate, toDate=toDate
        )
