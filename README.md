# Plugin-Store
 

## Contributing

### Running in docker

As standard `docker-compose.yml` file is used for deployment, there is a separate `docker-compose.local.yml` file you 
can use. Just use `docker-compose -f docker-compose.local.yml up` to bring up the project. You can use any 
`docker-compose` commands normally as long as you add `-f docker-compose.local.yml` argument.

### Using Makefile

There is a handy `Makefile` placed in the root directory of the project. It is not being used in a conventional way
(to build the code or install built software), it's just creates nie aliases for commands. Here is a list of them:

- `autoformat` - runs autoformatting on the whole Python codebase
  - `autoformat/black` - runs only `black` command for autoformatting, which unifies codestyle
  - `autoformat/isort` - runs only `isort` command for autoformatting, which reorders imports
- `lint` - runs lint check on the whole project
  - `lint/black` - runs only `black` in check mode. After running black autoformatting, this check should pass
  - `lint/isort` - runs only `isort` in check mode. After running isort autoformatting, this check should pass
  <!-- - `lint/flake8` - runs only `flake8` linter. This does not have its own autoformat command, but it should be more
    or less covered by `black` autoformatting. It's here to make sure black does not leave any gaps in pep8 compliance. -->
- `deps/lock` - recreates lockfile without changing any package versions when possible. Needs to be executed after 
  changing project dependencies.
- `deps/upgrade` - recreates lockfile while trying to upgrade all packages to the newest compatible version.
<!--
All commands above can be prefixed with `dc/` to run them directly in a docker container. There are also additional,
docker only commands:
-->
- `dc/build` - rebuilds docker images. Needs to be run after `Dockerfile` or project dependencies change. 

### Updating dependencies

This project is using Poetry to manage python packages required for the project. Poetry also keeps the lock file to make
sure every environment where the same version of project is used, is as consistent as possible.

If you want to add any dependency, preferably add it manually in the `pyproject.toml` file. Please keep dependencies
alphabetically sorted to avoid merge conflicts.

If adding or updating a single dependency inside the `pyproject.toml`, you need to update the lockfile. please run
`make deps/lock` to do as little changes to the lockfile as possible, unless your intention is to refresh every single
dependency, then `make deps/upgrade` should be a better option. But you probably shouldn't use it unless you really
need to.

### Running tests

Simply run `make test` to run tests on your local machine. If using development docker-compose file, you shall use
`docker-compose -f docker-compose.local.yml run plugin_store pytest /tests` - note the path in this command is absolute.
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