# Developer documentation
## Install custom code
These steps describe how to install the requirements and use obsidianhtml from the code, instead of installing it as a package. This way you can quickly test changes.

``` bash
# Get the code
# Note that the master branch is work in progress! Code might be broken. 
# Move into a release branch if you want fully tested code instead.
git clone git@github.com:obsidian-html/obsidian-html.git

# Move into folder
cd obsidian-html

# Install all the dependencies of the package, but not the package itself.
# You only need to do this once.
pip install .

# Run ObsidianHtml from code (so not via the package)
python -m obsidianhtml -i /path/to/config.yml
```

## Contribute to Obsidianhtml
## Introduction
When contributing code to the project, please take into consideration the following requirements:
- Run a linter to avoid obvious errors
- Run black to apply standardizes formatting, so that we don't pollute PR's with format changes

### Running linting
To avoid easily avoidable errors, it is good to run a linter before commiting your code to be pulled.


### Run Ruff
For first time setup, run the following:
``` shell
pip install ruff
```

See pyproject.toml for configuration

Then, when ready to commit, run the following in the root of this repo:
``` shell
ruff check obsidianhtml  
```

If you think the errors should be fixed, you can opt to run `ruff check obsidianhtml --fix` to auto fix the issues.
Note that this might break your code, and this cannot fix every error, but often it is a quick option.

### Run black
For first time setup, run the following:
``` shell
pip install black
```

See pyproject.toml for configuration

Then, when ready to commit, run the following in the root of this repo:
``` shell
black obsidianhtml
```

# Architecture
[Architecture & Code standards](architecture.md)
