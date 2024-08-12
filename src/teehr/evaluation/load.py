"""Component class for loading data into the dataset."""
from typing import Union, List
import logging
from pathlib import Path

from teehr.pre.locations import (
    convert_locations,
    validate_and_insert_locations,
)
from teehr.pre.location_crosswalks import (
    convert_location_crosswalks,
    validate_and_insert_location_crosswalks,
)
from teehr.pre.location_attributes import (
    convert_location_attributes,
    validate_and_insert_location_attributes,
)
from teehr.pre.timeseries import (
    convert_timeseries,
    validate_and_insert_timeseries,
)
from teehr.models.domain_tables import (
    Configuration,
    Unit,
    Variable,
    Attribute,
)
from teehr.pre.add_domains import (
    add_configuration,
    add_unit,
    add_variable,
    add_attribute,
)
import teehr.const as const

logger = logging.getLogger(__name__)


class Load:
    """Component class for loading data into the dataset."""

    def __init__(self, eval) -> None:
        """Initialize the Load class."""
        self.cache_dir = eval.cache_dir
        self.dataset_dir = eval.dataset_dir
        self.locations_cache_dir = Path(
            self.cache_dir,
            const.LOADING_CACHE_DIR,
            const.LOCATIONS_DIR
        )
        self.crosswalk_cache_dir = Path(
            self.cache_dir,
            const.LOADING_CACHE_DIR,
            const.LOCATION_CROSSWALKS_DIR
        )
        self.attributes_cache_dir = Path(
            self.cache_dir,
            const.LOADING_CACHE_DIR,
            const.LOCATION_ATTRIBUTES_DIR
        )
        self.secondary_cache_dir = Path(
            self.cache_dir,
            const.LOADING_CACHE_DIR,
            const.SECONDARY_TIMESERIES_DIR
        )
        self.primary_cache_dir = Path(
            self.cache_dir,
            const.LOADING_CACHE_DIR,
            const.PRIMARY_TIMESERIES_DIR
        )

    def add_configuration(
        self,
        configuration: Union[Configuration, List[Configuration]]
    ):
        """Add a configuration domain to the evaluation."""
        add_configuration(self.dataset_dir, configuration)

    def add_unit(
        self,
        unit: Union[Unit, List[Unit]]
    ):
        """Add a unit to the evaluation."""
        add_unit(self.dataset_dir, unit)

    def add_variable(
        self,
        variable: Union[Variable, List[Variable]]
    ):
        """Add a unit to the evaluation."""
        add_variable(self.dataset_dir, variable)

    def add_attribute(
        self,
        attribute: Union[Attribute, List[Attribute]]
    ):
        """Add an attribute to the evaluation."""
        add_attribute(self.dataset_dir, attribute)

    def import_locations(
            self,
            in_path: Union[Path, str],
            field_mapping: dict = None,
            pattern: str = "**/*.parquet",
            **kwargs
    ):
        """Import geometry data.

        Parameters
        ----------
        in_path : Union[Path, str]
            The input file or directory path.
            Any file format that can be read by GeoPandas.
        field_mapping : dict, optional
            A dictionary mapping input fields to output fields.
            Format: {input_field: output_field}
        pattern : str, optional (default: "**/*.parquet")
            The pattern to match files.
            Only used when in_path is a directory.
        **kwargs
            Additional keyword arguments are passed to GeoPandas read_file().

        File is first read by GeoPandas, field names renamed and
        then validated and inserted into the dataset.
        """
        convert_locations(
            in_path,
            self.locations_cache_dir,
            field_mapping=field_mapping,
            pattern=pattern,
            **kwargs
        )
        validate_and_insert_locations(
            self.locations_cache_dir,
            self.dataset_dir
        )

    def import_location_crosswalks(
            self,
            in_path: Union[Path, str],
            field_mapping: dict = None,
            pattern: str = "**/*.parquet",
            **kwargs
    ):
        """Import location crosswalks.

        Parameters
        ----------
        in_path : Union[Path, str]
            The input file or directory path.
        field_mapping : dict, optional
            A dictionary mapping input fields to output fields.
            Format: {input_field: output_field}
        pattern : str, optional (default: "**/*.parquet")
            The pattern to match files.
            Only used when in_path is a directory.
        **kwargs
            Additional keyword arguments are passed to pd.read_csv().
        """
        convert_location_crosswalks(
            in_path,
            self.crosswalk_cache_dir,
            field_mapping=field_mapping,
            pattern=pattern,
            **kwargs
        )
        validate_and_insert_location_crosswalks(
            self.crosswalk_cache_dir, self.dataset_dir
        )

    def import_location_attributes(
            self,
            in_path: Union[Path, str],
            field_mapping: dict = None,
            pattern: str = "**/*.parquet",
            **kwargs
    ):
        """Import location_attributes.

        Parameters
        ----------
        in_path : Union[Path, str]
            The input file or directory path.
        field_mapping : dict, optional
            A dictionary mapping input fields to output fields.
            Format: {input_field: output_field}
        pattern : str, optional (default: "**/*.parquet")
            The pattern to match files.
            Only used when in_path is a directory.
        **kwargs
            Additional keyword arguments are passed to pd.read_csv().
        """
        convert_location_attributes(
            in_path,
            self.attributes_cache_dir,
            pattern=pattern,
            field_mapping=field_mapping,
            **kwargs
        )
        validate_and_insert_location_attributes(
            self.attributes_cache_dir, self.dataset_dir
        )

    def import_secondary_timeseries(
        self,
        in_path: Union[Path, str],
        pattern="**/*.parquet",
        field_mapping: dict = None,
        constant_field_values: dict = None
    ):
        """Import secondary timeseries data.

        Parameters
        ----------
        in_path : Union[Path, str]
            Path to the timeseries data (file or directory).
        pattern : str, optional (default: "**/*.parquet")
            The pattern to match files if in_path is a directory.
        field_mapping : dict, optional
            A dictionary mapping input fields to output fields.
            Format: {input_field: output_field}
        constant_field_values : dict, optional
            A dictionary mapping field names to constant values.
            Format: {field_name: value}

        Includes validation and importing data to database.
        """
        self.secondary_cache_dir.mkdir(parents=True, exist_ok=True)

        convert_timeseries(
            in_path=in_path,
            out_path=self.secondary_cache_dir,
            field_mapping=field_mapping,
            constant_field_values=constant_field_values,
            pattern=pattern
        )

        if pattern.endswith(".csv"):
            pattern = pattern.replace(".csv", ".parquet")

        validate_and_insert_timeseries(
            in_path=self.secondary_cache_dir,
            dataset_path=self.dataset_dir,
            timeseries_type="secondary",
            pattern=pattern,
        )

    def import_primary_timeseries(
        self,
        in_path: Union[Path, str],
        pattern="**/*.parquet",
        field_mapping: dict = None,
        constant_field_values: dict = None
    ):
        """Import primary timeseries data.

        Parameters
        ----------
        in_path : Union[Path, str]
            Path to the timeseries data (file or directory).
        pattern : str, optional (default: "**/*.parquet")
            The pattern to match files if in_path is a directory.
        field_mapping : dict, optional
            A dictionary mapping input fields to output fields.
            Format: {input_field: output_field}
        constant_field_values : dict, optional
            A dictionary mapping field names to constant values.
            Format: {field_name: value}

        Includes validation and importing data to database.
        """
        self.primary_cache_dir.mkdir(parents=True, exist_ok=True)

        convert_timeseries(
            in_path=in_path,
            out_path=self.primary_cache_dir,
            field_mapping=field_mapping,
            constant_field_values=constant_field_values,
            pattern=pattern
        )

        if pattern.endswith(".csv"):
            pattern = pattern.replace(".csv", ".parquet")

        validate_and_insert_timeseries(
            in_path=self.primary_cache_dir,
            dataset_path=self.dataset_dir,
            timeseries_type="primary",
            pattern=pattern
        )
