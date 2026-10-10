from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .utils import merge

NUMERIC_ID_CHUNK_SIZE = 200
STRING_ID_CHUNK_SIZE = 50


def _chunk(lst: list, size: int) -> list:
    return [lst[i : i + size] for i in range(0, len(lst), size)]  # noqa: E203


def _group_by_map(items: list, key_fn: Callable) -> Dict:
    result: Dict[Any, list] = defaultdict(list)
    for item in items:
        result[key_fn(item)].append(item)
    return dict(result)


def batch_resource_operation_factory(
    get_all: Callable,
    not_found_error: Type[Exception],
    ambiguous_error: Type[Exception],
    chunk_size: Optional[Union[int, Dict]] = None,
) -> Callable:
    """
    Factory that creates a batch resource operation function.

    Args:
        get_all (Callable): function to retrieve all resources matching given options.
        not_found_error (Type[Exception]): exception raised when a resource is not found.
        ambiguous_error (Type[Exception]): exception raised when a UUID matches multiple resources.
        chunk_size (Optional[Union[int, Dict]]): optional overrides for numeric_id and string_id chunk sizes.

    Returns:
        Callable: batch operation function.
    """

    if isinstance(chunk_size, int):
        numeric_chunk = chunk_size
        string_chunk = chunk_size
    else:
        numeric_chunk = (chunk_size or {}).get("numeric_id", NUMERIC_ID_CHUNK_SIZE)
        string_chunk = (chunk_size or {}).get("string_id", STRING_ID_CHUNK_SIZE)

    def batch_resource_operation(
        uuid_or_id_or_array: Union[str, int, List[int], List[str]],
        fn: Callable,
        parameter_name: str = "uuid_or_id_or_array",
        options: Optional[Any] = None,
        group_by_navigation_property: Optional[str] = None,
    ) -> None:
        """
        Perform a batch operation on resources identified by uuid(s) or id(s).

        Args:
            uuid_or_id_or_array (Union[str, int, List[int], List[str]]): resource identifier(s).
            fn (Callable): function called with resolved items, and owner id when group_by_navigation_property is set.
            parameter_name (str): parameter name used in error messages.
            options (Optional[AnyObject]): extra pine options to merge.
            group_by_navigation_property (Optional[str]): navigation property to group items by before calling fn.
        """
        from .exceptions import InvalidParameter

        if uuid_or_id_or_array == "":
            raise InvalidParameter(parameter_name, uuid_or_id_or_array)

        if isinstance(uuid_or_id_or_array, list):
            if not uuid_or_id_or_array:
                raise InvalidParameter(parameter_name, uuid_or_id_or_array)
            first_type = type(uuid_or_id_or_array[0])
            for param in uuid_or_id_or_array:
                if not isinstance(param, (int, str)):
                    raise InvalidParameter("uuid_or_id_or_array", uuid_or_id_or_array)
                if type(param) is not first_type:
                    raise InvalidParameter("uuid_or_id_or_array", uuid_or_id_or_array)
                if isinstance(param, str) and len(param) not in (32, 62):
                    raise InvalidParameter("uuid_or_id_or_array", uuid_or_id_or_array)

        if isinstance(uuid_or_id_or_array, list):
            chunks = (
                _chunk(uuid_or_id_or_array, string_chunk)
                if isinstance(uuid_or_id_or_array[0], str)
                else _chunk(uuid_or_id_or_array, numeric_chunk)
            )
        else:
            chunks = [uuid_or_id_or_array]

        items = []
        for chunk in chunks:
            if isinstance(chunk, list):
                resource_filter = {"uuid": {"$in": chunk}} if isinstance(chunk[0], str) else {"id": {"$in": chunk}}
            else:
                resource_filter = {"uuid": chunk} if isinstance(chunk, str) else {"id": chunk}

            select: List[str] = ["id"]
            if isinstance(chunk, list) and isinstance(chunk[0], str):
                select.append("uuid")
            if group_by_navigation_property:
                select.append(group_by_navigation_property)

            options_without_select = options
            if options and "$select" in options:
                opt_select = options["$select"]
                if opt_select != "*":
                    extra = opt_select if isinstance(opt_select, list) else [opt_select]
                    select = list(set(select + extra))
                options_without_select = {k: v for k, v in options.items() if k != "$select"}

            items.extend(get_all(merge({"$select": select, "$filter": resource_filter}, options_without_select)))

        if not items:
            raise not_found_error(str(uuid_or_id_or_array))

        if isinstance(uuid_or_id_or_array, str) and len(items) > 1:
            raise ambiguous_error(uuid_or_id_or_array)

        if isinstance(uuid_or_id_or_array, list):
            identifier_key = "uuid" if isinstance(uuid_or_id_or_array[0], str) else "id"
            found = {item[identifier_key] for item in items}
            for identifier in uuid_or_id_or_array:
                if identifier not in found:
                    raise not_found_error(identifier)

        if group_by_navigation_property:
            groups = _group_by_map(items, lambda item: item[group_by_navigation_property]["__id"])
        else:
            groups = {None: items}

        for owner_id, group_items in groups.items():
            for chunked_items in _chunk(group_items, numeric_chunk):
                if group_by_navigation_property:
                    fn(chunked_items, owner_id)
                else:
                    fn(chunked_items)

    return batch_resource_operation
