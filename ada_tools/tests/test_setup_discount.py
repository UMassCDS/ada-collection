""" Test module for ada_tools.setup_discount module """
import pytest
from pathlib import Path
import click.testing
import os
import geopandas as gpd

import json
from shapely.geometry import box
from ada_tools.setup_discount import (
    get_tile_bounds,
    get_url,
    get_tiff_url,
    get_image_dir_contents,
)
from ada_tools.setup_discount import main


@pytest.fixture
def mock_rasterio_open(mocker):
    mock = mocker.patch("ada_tools.setup_discount.rasterio.open", autospec=True)
    mock.return_value.__enter__.return_value.crs = "epsg:4326"
    mock.return_value.__enter__.return_value.bounds = (120.480, 18.075, 120.485, 18.078)
    return mock


@pytest.fixture
def mock_pathlib_glob(mocker):
    mock = mocker.patch("ada_tools.setup_discount.Path.glob", autospec=True)
    mock.return_value = [mocker.Mock()(name=f"{i}.tif") for i in range(3)]
    return mock


@pytest.fixture
def mock_gpd_read_file(mocker):
    mock = mocker.patch("ada_tools.setup_discount.gpd.read_file", autospec=True)
    mock.return_value = mocker.Mock()
    return mock


@pytest.fixture
def mock_os_makedirs(mocker):
    return mocker.patch("ada_tools.setup_discount.os.makedirs", autospec=True)


# Test get_tile_bounds function from typhoon-mangkhut_test_data/tiles/109402_58842_17.geojson
@pytest.mark.parametrize(
    "tile_id, expected",
    [
        (
            "109402_58842_17",
            (
                120.4815673828125,
                18.07536797002466,
                120.48431396484375,
                18.07797898663566,
            ),
        ),
    ],
)
def test_get_tile_bounds(tile_id, expected):
    # print(f"Debug: Testing with Tile ID -> {tile_id}")
    result = get_tile_bounds(tile_id)
    # print(f"Debug: Obtained bounds -> {result}, Expected bounds -> {expected}")

    if hasattr(result, "to_tuple"):
        result = result.to_tuple()

    assert result == pytest.approx(expected, 0.0001)


# Test get_url function with possible filenames
@pytest.mark.parametrize(
    "filename, expected",
    [
        (
            "https:--some-domain-events-somefile.tif",
            "https://some-domain/events/somefile.tif",
        ),
        (
            "https:--some-domain-pre-event-somefile.tif",
            "https://some-domain/pre-event/somefile.tif",
        ),
        (
            "https:--some-domain-post-event-somefile.tif",
            "https://some-domain/post-event/somefile.tif",
        ),
        (
            "https:--some-domain-2022-01-01-somefile.tif",
            "https://some-domain-2022-01-01/somefile.tif",
        ),
        (
            "https:--some-domain-somefile.tif",
            "https://some-domain/somefile.tif",
        ),
    ],
)
def test_get_url(filename, expected):
    result = get_url(filename)
    print(f"Expected ({len(expected)}): '{expected}'")
    print(f"Actual ({len(result)}): '{result}'")
    assert result == expected


def test_get_tiff_url():
    """Test the get_tiff_url function with a mock tile_bounds and bounds_and_urls from typhoon-mangkhut_test_data/tiles/109402_58842_17.geojson"""
    tile_bounds = (
        120.4815673828125,
        18.07536797002466,
        120.48431396484375,
        18.07797898663566,
    )
    bounds_and_urls = [
        (box(120.480, 18.075, 120.485, 18.078), "some_url_1"),
        (box(120.481, 18.070, 120.490, 18.080), "some_url_2"),
    ]
    expected = "some_url_1"
    result = get_tiff_url(tile_bounds, bounds_and_urls)
    assert result == expected


def test_get_image_dir_contents(mocker):
    """Test the get_image_dir_contents function using pyest-mock"""

    mock_path = mocker.patch("ada_tools.setup_discount.Path", autospec=True)
    mock_path.return_value.exists.return_value = True
    mock_path.return_value.is_dir.return_value = True
    mock_path.return_value.glob.return_value = [Path("test1.tif"), Path("test2.tif")]

    mocker.patch(
        "ada_tools.setup_discount.get_url", side_effect=lambda x: f"url_for_{x}"
    )

    mock_rasterio_open = mocker.patch(
        "ada_tools.setup_discount.rasterio.open", autospec=True
    )
    mock_rasterio_open.return_value.__enter__.return_value.crs = "epsg:4326"
    mock_rasterio_open.return_value.__enter__.return_value.bounds = (
        120.480,
        18.075,
        120.485,
        18.078,
    )

    mocker.patch(
        "ada_tools.setup_discount.transform_bounds",
        return_value=(120.480, 18.075, 120.485, 18.078),
    )

    # Call the function with the mocks
    result = get_image_dir_contents("mock_dir")

    # Check the result
    expected = [
        (box(120.480, 18.075, 120.485, 18.078), "url_for_test1.tif"),
        (box(120.480, 18.075, 120.485, 18.078), "url_for_test2.tif"),
    ]
    assert result == expected


# WIP: Test the main function, look for alternate strategies if testing with click CLI and mocker is too complicated and not worth the effort

# # note: this test only to check the function call, not the actual output because it
# # involves lots of file ops and might induce side effects
# def test_main(mocker):
#     # Mock the functions that have side effects
#     mocker.patch("ada_tools.setup_discount.os.makedirs")
#     mocker.patch("ada_tools.setup_discount.gpd.read_file")

#     # mocker.patch("ada_tools.setup_discount.get_image_dir_contents")
#     # DEBUG 1: AssertionError: get_image_dir_contents('pre_images') call not found
#     # so, mocking the function with the same name in the test module
#     mock_get_image_dir_contents = mocker.patch(
#         "ada_tools.setup_discount.get_image_dir_contents"
#     )

#     mocker.patch("ada_tools.setup_discount.get_tiff_url")
#     mocker.patch("ada_tools.setup_discount.get_tile_bounds")
#     mocker.patch("ada_tools.setup_discount.open", mocker.mock_open())

#     mock_df = mocker.patch("ada_tools.setup_discount.pd.DataFrame")
#     mock_df.to_csv.return_value = None
#     mock_df.to_json.return_value = "{}"

#     # Important: Call the function with click CLI arguments not positional arguments
#     runner = click.testing.CliRunner()
#     result = runner.invoke(
#         main,
#         [
#             "--input",
#             "input",
#             "--pre-images",
#             "pre_images",
#             "--post-images",
#             "post_images",
#             "--outdir",
#             "outdir",
#             "--out-csv",
#             "out_csv",
#         ],
#     )

#     # os.makedirs.assert_called_once_with("outdir", exist_ok=True)
#     # DEBUG 2: above call doesn't reach and printing the call_args_list returns empty list
#     print(os.makedirs.call_args_list)

#     gpd.read_file.assert_called_once_with("input")

#     # DEBUG 1:
#     mock_get_image_dir_contents.assert_any_call("pre_images")

#     # get_image_dir_contents.assert_any_call("pre_images")
#     get_image_dir_contents.assert_any_call("post_images")
#     get_tiff_url.assert_called()
#     get_tile_bounds.assert_called()

#     # Check the exit code of the CLI command
#     assert result.exit_code == 0
