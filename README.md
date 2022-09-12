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