""" Test module for ada_tools.setup_discount module """
import pytest
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
    print(f"Debug: Testing with Tile ID -> {tile_id}")
    result = get_tile_bounds(tile_id)
    print(f"Debug: Obtained bounds -> {result}, Expected bounds -> {expected}")

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
