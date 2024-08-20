"""Functions for formatting filters for querying."""
import pandas as pd
import warnings

from collections.abc import Iterable
from datetime import datetime
from typing import List, Union
import logging

from teehr.models.dataset.filters import FilterBaseModel
from teehr.models.dataset.table_models import TableBaseModel

logger = logging.getLogger(__name__)

SQL_DATETIME_STR_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_datetime_list_string(values):
    """Get a datetime list as a list of strings."""
    return [f"'{v.strftime(SQL_DATETIME_STR_FORMAT)}'" for v in values]


def format_iterable_value(
    values: Iterable[Union[str, int, float, datetime]]
) -> str:
    """Return an SQL formatted string from list of values.

    Parameters
    ----------
    values : Iterable
        Contains values to be formatted as a string for SQL. Only one type of
        value (str, int, float, datetime) should be used. First value in list
        is used to determine value type. Values are not checked for type
        consistency.

    Returns
    -------
    str
        An SQL formatted string from list of values.
    """
    # string
    if isinstance(values[0], str):
        return f"""({",".join([f"'{v}'" for v in values])})"""
    # int or float
    elif isinstance(values[0], int) or isinstance(values[0], float):
        return f"""({",".join([f"{v}" for v in values])})"""
    # datetime
    elif isinstance(values[0], datetime):
        return f"""({",".join(get_datetime_list_string(values))})"""
    else:
        warnings.warn(
            "treating value as string because didn't know what else to do."
        )
        return f"""({",".join([f"'{str(v)}'" for v in values])})"""


def format_filter_to_str(
    filter: FilterBaseModel
) -> str:
    r"""Return an SQL formatted string for single filter object.

    Parameters
    ----------
    filter : FilterBaseModel
        A single FilterBaseModel object or a subclass
        of FilterBaseModel.

    Returns
    -------
    str
        An SQL formatted string for single filter object.
    """
    column = filter.column.value
    operator = filter.operator.value

    if isinstance(filter.value, str):
        return f"""{column} {operator} '{filter.value}'"""
    elif (
        isinstance(filter.value, int)
        or isinstance(filter.value, float)
    ):
        return f"""{column} {operator} {filter.value}"""
    elif isinstance(filter.value, datetime):
        dt_str = filter.value.strftime(SQL_DATETIME_STR_FORMAT)
        return f"""{column} {operator} '{dt_str}'"""
    elif (
        isinstance(filter.value, Iterable)
        and not isinstance(filter.value, str)
    ):
        value = format_iterable_value(filter.value)
        return f"""{column} {operator} {value}"""
    else:
        logger.warn(
            f"treating value {filter.value} as string because "
            "didn't know what else to do."
        )
        return f"""{column} {operator} '{str(filter.value)}'"""


def validate_filter_values(
    filters: Union[FilterBaseModel, List[FilterBaseModel]],
    model: TableBaseModel
):
    """Validate filter values."""
    filter_was_iterable = True
    if not isinstance(filters, List):
        filters = [filters]
        filter_was_iterable = False

    validated_filters = []
    for filter in filters:
        if filter.column not in model.model_fields:
            raise ValueError(f"Filter column not in model fields: {filter}")

        model_field_data_type = model.model_fields[filter.column].annotation
        logging.debug(
            f"Model field {filter.column} has type: {model_field_data_type}"
        )

        # if string or not iterable, make it iterable
        vals = filter.value
        value_was_iterable = True
        if isinstance(vals, str) or not isinstance(vals, Iterable):
            vals = [vals]
            value_was_iterable = False

        validate_vals = []
        for v in vals:
            logging.debug(f"Validating filter value: {v}")
            if model_field_data_type == str:
                validate_vals.append(str(v))
            elif model_field_data_type == int:
                validate_vals.append(int(v))
            elif model_field_data_type == float:
                validate_vals.append(float(v))
            elif model_field_data_type == datetime:
                validate_vals.append(pd.Timestamp(v))
            else:
                validate_vals.append(str(v))

        if value_was_iterable:
            filter.value = validate_vals
            validated_filters.append(filter)
        else:
            filter.value = validate_vals[0]
            validated_filters.append(filter)

    if filter_was_iterable:
        return validated_filters
    else:
        return validated_filters[0]


def apply_filters(df, filters):
    """Apply filters to a DataFrame."""
    if not isinstance(filters, List):
        filters = [filters]

    for filter in filters:
        filter_str = format_filter_to_str(filter)
        df = df.filter(filter_str)
    return df
