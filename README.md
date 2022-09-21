# Plugin-Store
 

## Contributing

### Running in docker

As standard `docker-compose.yml` file is used for deployment, there is a separate `docker-compose.local.yml` file you 
can use. Just use `docker-compose -f docker-compose.local.yml up` to bring up the project. You can use any 
`docker-compose` commands normally as long as you add `-f docker-compose.local.yml` argument.

### Updating dependencies

This project is using Poetry to manage python packages required for the project. Poetry also keeps the lock file to make
sure every environment where the same version of project is used, is as consistent as possible.

If you want to add any dependency, preferably add it manually in the `pyproject.toml` file. Please keep dependencies
alphabetically sorted to avoid merge conflicts.

If adding or updating a single dependency inside the `pyproject.toml`, you need to update the lockfile. please run
`poetry lock --no-update` to do as little changes to the lockfile as possible, unless your intention is to refresh
every single dependency.

### Running tests

Simply run `pytest ./tests` to run tests on your local machine. If using development docker-compose file, you shall use
`docker-compose -f docker-compose.local.yml run plugin_store pytest /tests` - note the path change for tests directory.
As docker doesn't have the whole project directory mounted, only the sources root directory, tests are mounted 
separately and currently only for development docker-compose file. 

### Writing tests

This project uses `pytest` for running tests. Get familiar with it and fixtures system first. On top of `pytest`, async
tests are supported via `aiohttp` built-in decorator. As using `aiohttp` server and async DB, most of the tests need
to be async.

All tests and configuration for them lives in `tests` directory. You can find some useful fixtures in the `conftest.py`
file. If creating any more fixtures, please place them in this file unless you have a good reason not to do so.

There is one automatically applied fixture that patches over any external API calls, so they aren't really executed
when running tests. If adding any new external service dependencies to the project, please update that fixture to patch
them over as well.