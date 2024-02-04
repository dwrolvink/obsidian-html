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

## Running linting
To avoid easily avoidable errors, it is good to run a linter before commiting your code to be pulled.

### Run Ruff
> Ruff is a full linter for Python, which can find mistakes and auto-fix most of them

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
> Black is used mostly to get a consistent formatting of the code

For first time setup, run the following:
``` shell
pip install black
```

See pyproject.toml for configuration

Then, when ready to commit, run the following in the root of this repo:
``` shell
black obsidianhtml
```

### Linting automation

To keep yourself from forgetting, consider setting a pre-commit script:
``` bash
GITROOT="$(git rev-parse --show-toplevel)"

# create executable
touch $GITROOT/.git/hooks/pre-commit
chmod +x $GITROOT/.git/hooks/pre-commit

# add content
vim $GITROOT/.git/hooks/pre-commit
```

This is what I have configured (runs the two linters below):
``` bash
#!/bin/sh
# SETUP
# --------------------------------------------------
# uncomment to skip this script
# exit 0

GITROOT="$(git rev-parse --show-toplevel)"  

# Redirect output to stderr.
exec 1>&2

# first error line will be shown in vscode
echo "pre-commit-checks failed. edit $GITROOT/.git/hooks/pre-commit line 5 to skip checks."

# FAIL MSGS
# --------------------------------------------------
SCRIPT_FAILED=0
function fail_msg_black {
    echo -e "\n* Command 'black obsidianhtml --check' failed. Try running\n\t\tcd $GITROOT; black obsidianhtml\n  To fix this\n"
    SCRIPT_FAILED=1
}
function fail_msg_ruff {
    echo -e "\n* Command 'ruff check obsidianhtml' failed. Try running\n\t\tcd $GITROOT; ruff check obsidianhtml --fix\n  To fix this (some manual checks required).\n"
    SCRIPT_FAILED=1
}

# RUN CHECKS
# --------------------------------------------------
cd $GITROOT

echo -e '\n---------------------------------------------------\n\n$ black obsidianhtml --check'
black obsidianhtml --check || fail_msg_black

echo -e '\n---------------------------------------------------\n\n$ ruff check obsidianhtml \n'
ruff check obsidianhtml || fail_msg_ruff

# CANCEL MERGE ON FAIL
# --------------------------------------------------
[ $SCRIPT_FAILED -eq 1 ] && exit 1


```


# Architecture
[Architecture & Code standards](architecture.md)
