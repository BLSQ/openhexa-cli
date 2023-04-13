import configparser
import click
import sys
import os
import io
import requests
import typing
from zipfile import ZipFile
import base64
import importlib
from . import __version__

CONFIGFILE_PATH = os.path.expanduser("~") + "/.openhexa.ini"


def is_debug(config: configparser.ConfigParser):
    return config.getboolean("openhexa", "debug", fallback=False)


def open_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIGFILE_PATH):
        config.read(CONFIGFILE_PATH)
    else:
        config.read_string(
            """
        [openhexa]
        url=https://api.openhexa.org

        [workspaces]
        """
        )
    return config


def save_config(config):
    with open(CONFIGFILE_PATH, "w") as configfile:
        config.write(configfile)


def graphql(config, query: str, variables=None, token=None):
    url = config["openhexa"]["url"] + "/graphql/"
    current_workspace = config["openhexa"]["current_workspace"]
    if token is None:
        token = config["workspaces"].get(current_workspace)

    if not token:
        raise Exception("No token found for workspace")

    if is_debug(config):
        click.echo("")
        click.echo("Graphql Query:")
        click.echo(f"URL: {url}")
        click.echo(f"Query: {query}")
        click.echo(f"Variables: {variables}")

    response = requests.post(
        url,
        headers={
            "User-Agent": f"openhexa-cli/{__version__}",
            "Authorization": f"Bearer {token}",
        },
        json={"query": query, "variables": variables},
    )
    response.raise_for_status()
    data = response.json()

    if is_debug(config):
        click.echo("Graphql Response:")
        click.echo(data)
        click.echo("")

    if data.get("errors"):
        if data.get("errors")[0].get("extensions", {}).get("code") == "UNAUTHENTICATED":
            raise Exception("Token is invalid, please update the token")
        raise Exception(data["errors"])
    return data["data"]


def get_workspace(config, slug: str, token: str):
    return graphql(
        config,
        """
            query getWorkspace($slug: String!) {
                workspace(slug: $slug) {
                    name
                    slug
                }
            }
            """,
        {"slug": slug},
        token,
    )["workspace"]


def get_pipelines(config):
    data = graphql(
        config,
        """
    query getWorkspacePipelines($workspaceSlug: String!) {
        pipelines(workspaceSlug: $workspaceSlug) {
            items {
                id
                code
                name
                currentVersion {
                    number
                }
            }
        }
    }
    """,
        {"workspaceSlug": config["openhexa"]["current_workspace"]},
    )
    return data["pipelines"]["items"]


def get_pipeline(config, pipeline_code: str):
    data = graphql(
        config,
        """
    query getWorkspacePipeline($workspaceSlug: String!, $pipelineCode: String!) {
        pipelineByCode (workspaceSlug: $workspaceSlug, code: $pipelineCode) {
            id
            code
            currentVersion {
                number
            }
        }
    }
    """,
        {
            "workspaceSlug": config["openhexa"]["current_workspace"],
            "pipelineCode": pipeline_code,
        },
    )
    return data["pipelineByCode"]


def create_pipeline(config, pipeline_code: str):
    data = graphql(
        config,
        """
    mutation createPipeline($input: CreatePipelineInput!) {
        createPipeline(input: $input) {
            success
            errors
            pipeline {
                id
                code
                name
            }
        }
    }
    """,
        {
            "input": {
                "workspaceSlug": config["openhexa"]["current_workspace"],
                "code": pipeline_code,
            }
        },
    )

    if not data["createPipeline"]["success"]:
        raise Exception(data["createPipeline"]["errors"])

    return data["createPipeline"]["pipeline"]


def get_pipeline_module(pipeline_path: str):
    python_module = pipeline_path.split("/")[-1]
    if python_module.endswith(".py"):
        python_module = python_module[:-3]

    return python_module


def import_pipeline(config, pipeline_path: str):
    pipeline_dir = os.path.abspath(os.path.dirname(pipeline_path))
    python_module = get_pipeline_module(pipeline_path)
    sys.path.append(pipeline_dir)
    pipeline_package = importlib.import_module(python_module)

    pipeline = next(
        v
        for _, v in pipeline_package.__dict__.items()
        if v and type(v).__name__ == "Pipeline"
    )
    return pipeline


def upload_pipeline(config, pipeline_path: str, files: typing.List[str] = []):
    python_module = get_pipeline_module(pipeline_path)
    pipeline = import_pipeline(config, pipeline_path)

    files = [pipeline_path, *files]

    all_files = []
    for path in files:
        if os.path.isfile(path):
            all_files.append(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    all_files.append(os.path.join(root, file))
        else:
            raise Exception(f"{path} is not a file nor a directory... Aborting")

    prefix = os.path.dirname(all_files[0])
    zipFile = io.BytesIO(b"")
    zipObj = ZipFile(zipFile, "w")
    for f in all_files:
        zipObj.write(f, f[len(prefix) :].strip("/"))
    zipObj.close()
    zipFile.seek(0)
    base64_content = base64.b64encode(zipFile.read()).decode("ascii")

    data = graphql(
        config,
        """
            mutation uploadPipeline($input: UploadPipelineInput!) {
                uploadPipeline(input: $input) {
                    success
                    errors
                    version
                }
            }
        """,
        {
            "input": {
                "workspaceSlug": config["openhexa"]["current_workspace"],
                "code": pipeline.code,
                "entrypoint": python_module,
                "zipfile": base64_content,
                "parameters": pipeline.ui_summary(),
            }
        },
    )

    if not data["uploadPipeline"]["success"]:
        raise Exception(data["uploadPipeline"]["errors"])

    return data["uploadPipeline"]["version"]
