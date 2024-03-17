# Plugin-Store

## 📖 About
The Decky Plugin Store powers the [built-in plugin storefront](https://plugins.deckbrew.xyz/) of [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader) for Steam Deck. It can be used to host Decky Loader compatible plugins for any use case, including hosting testing plugins and providing an alternative storefront.

For more information about Decky Loader as well as documentation and development tools, please visit [our wiki](https://deckbrew.xyz/).

### 🎨 Features

🐍 Backend written in [Python](https://www.python.org/) with the [FastAPI](https://fastapi.tiangolo.com/) and [SQLAlchemy](https://www.sqlalchemy.org/) ([SQLite](https://www.sqlite.org/index.html) database [in use](https://github.com/SteamDeckHomebrew/decky-plugin-store/blob/main/plugin_store/database/database.py)) frameworks.

[<ul> 🏤 <i>PostgreSQL support is currently in development.</i> </ul>](https://github.com/SteamDeckHomebrew/decky-plugin-store/pull/54)

🌐 [Frontend](https://github.com/SteamDeckHomebrew/decky-plugin-store/blob/main/plugin_store/templates/plugin_browser.html) (for web browsers) written in [JavaScript](https://developer.mozilla.org/en-US/docs/Web/javascript) with the [Vue.js](https://vuejs.org/) framework

📤 API [endpoints](https://github.com/SteamDeckHomebrew/decky-plugin-store/blob/main/plugin_store/api/__init__.py) for:
  <ul>

  📃 List of plugins 
  <ul>GET endpoint used by Decky Loader's built-in plugin browser</ul>

  📩 Uploading plugins
  
  ♻️ Updating plugins
  </ul>

🪣 [Backblaze B2 Cloud Storage](https://www.backblaze.com/cloud-storage) supported for hosting plugins & metadata as a [CDN](https://github.com/SteamDeckHomebrew/decky-plugin-store/blob/main/plugin_store/cdn.py).

<ul>

🖼️ Handling image types for preview screenshots

🔑 Handling uploads via an `APP_KEY` 

♻️ Handling uploading different available versions of plugins
</ul>

💬 [Discord webhook](https://discord.com/developers/docs/resources/webhook) support for [sending notifications](https://github.com/SteamDeckHomebrew/decky-plugin-store/blob/main/plugin_store/discord.py) for new uploaded plugin versions

📦 Available as a [GitHub Package](https://github.com/SteamDeckHomebrew/decky-plugin-store/pkgs/container/decky-plugin-store) & ready to go as a [Docker](https://www.docker.com/) deployment.

## 💾 Installation
⚠️ **You will need the following to host a plugin store**: a domain name (for external access) and [Backblaze B2 Cloud Storage](https://www.backblaze.com/cloud-storage) to use for plugin storage.   
  
- [Install Docker](https://docs.docker.com/get-docker/) on your preferred platform

- Make sure to have the required [Environment Variables](https://docs.docker.com/engine/reference/run/#environment-variables) ready in an `.env` file where the `docker-compose.yml` file is located at:

  - `DB_PATH`
    > Database path where to put the SQLite databases
  - `ANNOUNCEMENT_WEBHOOK`
    > URL for [Discord webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) for new plugins and updates
  - `SUBMIT_AUTH_KEY`
    > API key for REST API requests to use for authentication; other systems are required to use this API key to be able to use the authentication-locked API endpoints
  - `B2_APP_KEY_ID`
    >  Backblaze B2 Master [App Key ID](https://www.backblaze.com/docs/cloud-storage-application-keys) (per account) 
  - `B2_APP_KEY`
    > Backblaze B2 [App Key](https://www.backblaze.com/docs/cloud-storage-application-keys) 
  - `B2_BUCKET_ID`
    > Backblaze B2 [Bucket ID](https://www.backblaze.com/docs/cloud-storage-application-keys) for restricting access to a single bucket
    
- Run the Docker environment with the following command:
  
  `docker compose up`

  > Use `-d` after `docker compose up` to run it in the background, not taking the current terminal window for logs.
  
  > For local deployments, use the `-f docker-compose.local.yml` flag before `up`. The default API key for API requests is `deadbeef` for local deployments.

## 🤝 Contributing

### Running in docker

As standard `docker-compose.yml` file is used for deployment, there is a separate `docker-compose.local.yml` file you 
can use. Just use `docker-compose -f docker-compose.local.yml up` to bring up the project. You can use any 
`docker-compose` commands normally as long as you add `-f docker-compose.local.yml` argument.

### Using Makefile

There is a handy `Makefile` placed in the root directory of the project. It is not being used in a conventional way
(to build the code or install built software), it's just creates nice aliases for commands. Here is a list of them:

- `autoformat` - runs autoformatting on the whole Python codebase.
  - `autoformat/black` - runs only `black` command for autoformatting, which unifies codestyle.
  - `autoformat/isort` - runs only `isort` command for autoformatting, which reorders imports.
- `lint` - runs lint check on the whole project.
  - `lint/black` - runs only `black` in check mode. After running black autoformatting, this check should pass.
  - `lint/isort` - runs only `isort` in check mode. After running isort autoformatting, this check should pass.
  - `lint/flake8` - runs only `flake8` linter. This does not have its own autoformat command, but it should be more
    or less covered by `black` autoformatting. It's here to make sure black does not leave any gaps in pep8 compliance.
  - `lint/mypy` runs only `mypy` linter. This does not have its own autoformat command either and errors needs to be 
    fixed manually. 
- `deps/lock` - recreates lockfile without changing any package versions when possible. Needs to be executed after 
  changing project dependencies.
- `deps/upgrade` - recreates lockfile while trying to upgrade all packages to the newest compatible version.
- `test` - runs project tests.

All commands above can be prefixed with `dc/` to run them directly in a docker container. There are also additional,
docker only commands:
- `dc/build` - rebuilds docker images. Needs to be run after `Dockerfile` or project dependencies change. 

### Updating dependencies

This project is using Poetry to manage python packages required for the project. Poetry also keeps the lock file to make
sure every environment where the same version of project is used, is as consistent as possible.

If you want to add any dependency, preferably add it manually in the `pyproject.toml` file. Please keep dependencies
alphabetically sorted to avoid merge conflicts.

If adding or updating a single dependency inside the `pyproject.toml`, you need to update the lockfile. Please run
`make deps/lock` to do as little changes to the lockfile as possible, unless your intention is to refresh every single
dependency, then `make deps/upgrade` should be a better option. But you probably shouldn't use it unless you really
need to.

### Running tests

Simply run `make test` to run tests on your local machine. If using development docker-compose file, you shall use
`make dc/test` instead. 

### Writing tests

This project uses `pytest` for running tests. Get familiar with it and fixtures system first. On top of `pytest`, async
tests are supported via `pytest.mark.asyncio` decorator provided by `pytest-asyncio`. As project is using `fastapi` with
async views as well as async DB, most of the tests need to be async.

All tests and configuration for them lives in `tests` directory. You can find some useful fixtures in the `conftest.py`
file. If creating any more fixtures, please place them in this file unless you have a good reason not to do so.

There are two automatically applied fixtures, one patches over any external API calls, so they aren't really executed
when running tests, second one overrides constants specifying any external resources. If adding any new external service
dependencies to the project, please update those fixtures to patch them over as well.