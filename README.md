# OpenHexa CLI

![OpenHexa Logo](https://www.bluesquarehub.com/wp-content/uploads/2021/07/hexa-logo.svg)

Welcome to the `openhexa.cli` project!

This is a Command Line Interface (CLI) tool developed by the OpenHexa team, aimed at making your interactions with the OpenHexa platform. The CLI is built for developers who need to write and upload pipelines in OpenHexa.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Commands](#commands)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- Interact with the OpenHexa platform from the command line
- Create and update pipelines
- Cross-platform support: Windows, macOS, and Linux

## Installation

### Prerequisites

- Python 3.10 or later
- `pip` (Python package manager)

### Install with pip

To install the `openhexa.cli` tool, simply run:

```bash
pip install openhexa-cli
```

## Getting Started

After installation, you can use the `openhexa` command to interact with the platform. To check if the installation was successful and to see the available commands, run:

```bash
openhexa --help
```

## Commands

Here are some common commands you can use with the `openhexa` CLI:

* `openhexa workspaces add <slug>`: Configure the workspace to be used in local.
* `openhexa workspaces rm <slug>`: Remove the workspace form your local configuration
* `openhexa workspaces list`: List all workspaces configured locally
* `openhexa workspaces activate <slug>`: Make this workspace the one you're currently working on
* `openhexa config set_url <url>`: Set the backend url to use
* `openhexa pipelines list`: List all the workspace's pipelines
* `openhexa pipelines push <my_pipeline.py>`: Push a pipeline to the activated workspace


## Contributing

We appreciate and welcome any contributions to the openhexa.cli project! To contribute, please follow these steps:

1. Fork the repository on GitHub
2. Create a new branch for your feature or bugfix
3. Make your changes and write tests if necessary
4. Submit a pull request against the main branch

Once you have cloned the repository in local, you can install dependencies with the command:

```bash
pip install ".[dev]" # To just install deps
pip install -e ".[dev]" # To also install the leb as editable

```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.


## Contact

If you have any questions or need support, feel free to contact the OpenHexa team:

Email: tech@bluesquarehub.com
Website: https://www.bluesquarehub.com/openhexa/