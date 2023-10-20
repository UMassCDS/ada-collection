# ADA data processing tools

Scripts to download/transform pre- and post-disaster images, adapted from 
https://github.com/jmargutt/ADA_tools.


## Description of pipeline

### load-images
Download geotif images from the Maxar opendata website.

### create-index
Divide the area spanned by the downloaded images into tiles and
generate a json file assigning each tile to a the image it can be found in.

![Example of generated tiles](tiles.png?raw=true)

### setup-wd
TODO

## Major differences

- Data processing scripts moved one level up, directly into `ada_tools` folder
- Added new entrypoints in `setup.py`:
    
    - `load-images`: get images from Maxar
    - `filter-images`: filter images
    - `filter-buildings`: filter buildings
    - `final-layer`: final layer
    - `prepare-data`: transform for damage classification (after building detection)

    Run `<command> --help` to see available arguments.


## Notes on installation
- `GDAL` dependency often causes issues and has to be installed separately;
system requirements need to be installed first and `GDAL` python library version
has to match that of local installation.
See snippet of Dockerfile:

```
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN deps='build-essential cmake gdal-bin python-gdal libgdal-dev kmod wget apache2' && \
	apt-get update && \
	apt-get install -y $deps && \
	pip install --upgrade pip && \
	pip install GDAL==$(gdal-config --version)
```
## Running Tests

Tests for this project reside under `ada_collection/ada_tools/tests` and use the `pytest` module. You can install the necessary dependencies for testing by running:

```bash
pip install -e .[test]
```

To run the tests for `ada_tools`, navigate to the project's root directory and run the following command:

```bash
pytest ada_tools/tests/
```

This will automatically discover and run all tests in the project. If you want to run tests in a specific file, you can specify the file name:

```bash
pytest tests/test_setup_discount.py
```

### Checking Test Coverage

To check the test coverage for this project, you can use the `pytest-cov` plugin.

Then, run pytest with the `--cov` option, followed by the name of the package you want to check the coverage of, e.g.:

```bash
pytest --cov=ada_tools
```

This will print a coverage report in the terminal. If you want to generate a detailed HTML report, you can use the --cov-report option:

```bash
pytest --cov=ada_tools --cov-report html </path/to/tests/dir>
```

This will generate an HTML report in a directory named `htmlcov`. Open the `index.html` file in this directory in a web browser to view the report. Make sure you `.gitignore` the `htmlcov` directory.

### Updating Tests

You can add the tests under a `tests` folder for the module. Learn about how to write tests using pytest and its conventions, [here](https://pytest.org/en/7.4.x/explanation/goodpractices.html#conventions-for-python-test-discovery).

- When you modify the code or add new features, you should also update the tests to reflect these changes.
- Make sure that all functions are covered by at least one test, and that all edge cases are considered.
- Run the tests frequently during development to catch any issues early.
- Remember, the goal of testing is not to achieve 100% coverage, but to give you confidence that your code works as expected.