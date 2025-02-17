import pytest
import pandas as pd
from pathlib import Path
from teehr.visualization.dataframe_accessor import TEEHRDataFrameAccessor
import logging
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def sample_dataframe():
    """Create sample data for test object."""
    data = {
        'location_id': [1, 2, 1, 2],
        'variable_name': ['var1', 'var1', 'var2', 'var2'],
        'configuration_name': ['config1', 'config2', 'config1', 'config2'],
        'unit_name': ['unit1', 'unit1', 'unit2', 'unit2'],
        'value_time': pd.date_range(start='1/1/2022', periods=4, freq='D'),
        'value': [10, 20, 30, 40],
        'reference_time': [None, None, None, None]
    }
    df = pd.DataFrame(data)
    df.attrs['table_type'] = 'timeseries'
    df.attrs['fields'] = df.columns
    return df


def test_initialization(sample_dataframe):
    """Initialize test object."""
    # Test that the accessor initializes correctly
    accessor = sample_dataframe.teehr
    assert isinstance(accessor, TEEHRDataFrameAccessor)


def test_validation(sample_dataframe):
    """Test validation method of TEEHRDataFrameAccessor."""
    # Test for missing field in 'timeseries' table_type
    with pytest.raises(AttributeError):
        df_invalid = sample_dataframe.drop(columns=['location_id'])
        df_invalid.attrs['table_type'] = 'timeseries'
        df_invalid.attrs['fields'] = sample_dataframe.columns
        df_invalid.teehr

    # Test for empty DataFrame in 'timeseries' table_type
    with pytest.raises(AttributeError):
        df_empty = pd.DataFrame(columns=sample_dataframe.columns)
        df_empty.attrs['table_type'] = 'timeseries'
        df_empty.attrs['fields'] = sample_dataframe.columns
        df_empty.teehr

    # Test for missing 'table_type' attribute
    with pytest.raises(AttributeError):
        df_no_table_type = sample_dataframe.copy()
        del df_no_table_type.attrs['table_type']
        df_no_table_type.teehr

    # Test for invalid 'table_type' attribute
    with pytest.raises(AttributeError):
        df_invalid_table_type = sample_dataframe.copy()
        df_invalid_table_type.attrs['table_type'] = 'invalid_type'
        df_invalid_table_type.teehr

    # Test for 'joined_timeseries' table_type (NotImplementedError)
    with pytest.raises(NotImplementedError):
        df_joined_timeseries = sample_dataframe.copy()
        df_joined_timeseries.attrs['table_type'] = 'joined_timeseries'
        df_joined_timeseries.teehr

    # Test for 'location' table_type (NotImplementedError)
    with pytest.raises(NotImplementedError):
        df_location = sample_dataframe.copy()
        df_location.attrs['table_type'] = 'location'
        df_location.teehr

    # Test for 'metrics' table_type (NotImplementedError)
    with pytest.raises(NotImplementedError):
        df_metrics = sample_dataframe.copy()
        df_metrics.attrs['table_type'] = 'metrics'
        df_metrics.teehr


def test_get_unique_values(sample_dataframe):
    """Test unique values method."""
    accessor = sample_dataframe.teehr
    unique_values = accessor._get_unique_values(sample_dataframe)
    expected_values = {
        'location_id': [1, 2],
        'variable_name': ['var1', 'var2'],
        'configuration_name': ['config1', 'config2'],
        'unit_name': ['unit1', 'unit2'],
        'value_time': list(sample_dataframe['value_time'].unique()),
        'value': [10, 20, 30, 40],
        'reference_time': [None]
    }
    assert unique_values == expected_values


def test_timeseries_schema(sample_dataframe):
    """Test generation of default schema."""
    accessor = sample_dataframe.teehr
    schema = accessor._timeseries_schema()
    expected_schema = {
        'var1': [('config1', 1), ('config2', 2)],
        'var2': [('config1', 1), ('config2', 2)]
    }
    assert schema == expected_schema


def test_timeseries_generate_plot(sample_dataframe):
    """Test plot generation."""
    accessor = sample_dataframe.teehr
    schema = accessor._timeseries_schema()

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdirname:
        output_dir = Path(tmpdirname)
        accessor._timeseries_generate_plot(schema,
                                           sample_dataframe,
                                           'var1',
                                           output_dir)

        # Check if the file exists in the temporary directory
        plot_file = output_dir / 'timeseries_plot_var1.html'
        logger.info(f"Checking if {plot_file} exists.")
        assert plot_file.exists()

        # Clean up the file
        plot_file.unlink()


def test_timeseries_plot(sample_dataframe):
    """Test timeseries plot with a custom output directory."""
    accessor = sample_dataframe.teehr

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdirname:
        output_dir = Path(tmpdirname)
        accessor.timeseries_plot(output_dir=output_dir)

        # Check if the files exist
        var1_file = output_dir / "timeseries_plot_var1.html"
        var2_file = output_dir / "timeseries_plot_var2.html"
        logger.info(f"Checking if {var1_file} exists.")
        assert var1_file.exists()
        logger.info(f"Checking if {var2_file} exists.")
        assert var2_file.exists()

        # Clean up the files
        var1_file.unlink()
        var2_file.unlink()
