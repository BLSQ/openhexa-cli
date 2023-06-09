import os
import sys

import click

from . import __version__
from .api import (
    create_pipeline,
    get_pipeline,
    get_pipelines,
    get_workspace,
    import_pipeline,
    is_debug,
    open_config,
    save_config,
    upload_pipeline,
)


@click.group()
@click.option("--debug/--no-debug", default=False, envvar="DEBUG")
@click.version_option(__version__)
@click.pass_context
def app(ctx, debug):
    """
    OpenHexa CLI
    """
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)

    user_config = open_config()
    user_config.set("openhexa", "debug", str(debug))
    save_config(user_config)


@app.group(invoke_without_command=True)
@click.pass_context
def workspaces(ctx):
    """
    Manage workspaces (add workspace, remove workspace, list workspaces, activate a workspace)
    """
    if ctx.invoked_subcommand is None:
        ctx.forward(workspaces_list)


@workspaces.command(name="add")
@click.argument("slug")
@click.option("--token", prompt=True, hide_input=True, confirmation_prompt=False)
def workspaces_add(slug, token):
    """
    Add a workspace to the configuration and activate it. The access token is required to access the workspace.
    """
    user_config = open_config()
    if slug in user_config["workspaces"]:
        click.echo(f"Workspace {slug} already exists. We will only update its token.")
    else:
        click.echo(f"Adding workspace {slug}")
    try:
        get_workspace(user_config, slug, token)
    except Exception as e:
        click.echo(
            "Error while getting workspace. Check the slug of the workspace and the access token.",
            err=True,
        )
        if is_debug(user_config):
            raise e

    user_config["workspaces"].update({slug: token})
    user_config["openhexa"].update({"current_workspace": slug})

    save_config(user_config)


@workspaces.command(name="activate")
@click.argument("slug")
def workspaces_activate(slug):
    """
    Activate a workspace that is already in the configuration. The activated workspace will be used for the 'pipelines' commands.
    """

    user_config = open_config()
    if slug not in user_config["workspaces"]:
        click.echo(f"Workspace {slug} does not exist. Available workspaces:")
        click.echo(", ".join(user_config["workspaces"].keys()))
        return
    click.echo(f"Activating workspace {slug}")
    user_config["openhexa"].update({"current_workspace": slug})

    save_config(user_config)


@workspaces.command(name="list")
def workspaces_list():
    """
    List the workspaces in the configuration.
    """
    user_config = open_config()

    click.echo("Workspaces:")
    for slug in user_config["workspaces"]:
        click.echo(
            click.style(f"* {slug} (active)", bold=True)
            if slug == user_config["openhexa"]["current_workspace"]
            else f"* {slug}"
        )

    save_config(user_config)


@workspaces.command(name="rm")
@click.argument("slug")
def workspaces_rm(slug):
    """
    Remove a workspace from the configuration.

    SLUG is the slug of the workspace to remove from the configuration.
    """
    user_config = open_config()
    if slug not in user_config["workspaces"]:
        click.echo(f"Workspace {slug} does not exist")
        return
    click.echo(f"Removing workspace {slug}")

    del user_config["workspaces"][slug]
    if f"pipelines.{slug}" in user_config.sections():
        del user_config[f"pipelines.{slug}"]

    if user_config["openhexa"]["current_workspace"] == slug:
        user_config["openhexa"].update({"current_workspace": ""})

    save_config(user_config)


@app.group(invoke_without_command=True)
def config():
    """
    Manage configuration of the CLI.
    """
    user_config = open_config()
    click.echo("Debug: " + ("True" if is_debug(user_config) else "False"))
    click.echo(f"Backend URL: {user_config['openhexa']['url']}")
    click.echo(f"Current workspace: {user_config['openhexa']['current_workspace']}")
    click.echo("\nWorkspaces:")
    click.echo("\n".join(user_config["workspaces"].keys()))


@config.command(name="set_url")
@click.argument("url")
@click.pass_context
def config_set_url(ctx, url):
    """
    Set the URL of the backend.

    """
    user_config = open_config()
    user_config["openhexa"].update({"url": url})
    save_config(user_config)


@app.group(invoke_without_command=True)
@click.pass_context
def pipelines(ctx):
    """
    Manage pipelines (list workspace's pipelines, push a pipeline to the backend)
    """
    if ctx.invoked_subcommand is None:
        ctx.forward(pipelines_list)


@pipelines.command("push")
@click.argument("path")
@click.option(
    "files",
    "--file",
    "-f",
    multiple=True,
    type=click.Path(exists=True),
    help="Files to upload (default: only the pipeline file)",
)
def pipelines_push(path, files):
    """
    Push a pipeline to the backend. If the pipeline already exists, it will be updated otherwise it will be created.

    PATH is the path to the pipeline file.
    """

    user_config = open_config()
    workspace = user_config["openhexa"]["current_workspace"]

    if workspace == "":
        click.echo("No workspace activated", err=True)
        sys.exit(1)

    # Do the pipeline main file exist?
    if not os.path.exists(path):
        click.echo(f"{path}: file not found", err=True)
        sys.exit(1)

    try:
        pipeline = import_pipeline(user_config, path)
    except Exception as e:
        click.echo("Error while importing pipeline", err=True)
        if is_debug(user_config):
            raise e
        sys.exit(1)
    else:
        workspace_pipelines = get_pipelines(user_config)
        if is_debug(user_config):
            click.echo(workspace_pipelines)

        if get_pipeline(user_config, pipeline.code) is None:
            click.echo(
                f"Pipeline {click.style(pipeline.code, bold=True)} found in {path} does not exist in workspace {click.style(workspace, bold=True)}"
            )
            click.confirm(
                f"Create pipeline {click.style(pipeline.code, bold=True)} in workspace {click.style(workspace, bold=True)}?",
                True,
                abort=True,
            )
            create_pipeline(user_config, pipeline.code)

        click.echo(
            f"Pushing pipeline {click.style(pipeline.code, bold=True)} to workspace {click.style(workspace, bold=True)}"
        )

        new_version = upload_pipeline(user_config, path, files)
        click.echo(f"Version: {new_version}")

        url = f"{user_config['openhexa']['url']}/workspaces/{workspace}/pipelines/{pipeline.code}"
        click.echo(
            f"Done! You can view the pipeline in OpenHexa on {click.style(url, fg='bright_blue', underline=True)}"
        )


@pipelines.command("list")
def pipelines_list():
    """
    List all the remote pipelines of the current workspace.
    """
    user_config = open_config()
    workspace = user_config["openhexa"]["current_workspace"]

    if workspace == "":
        click.echo("No workspace activated", err=True)
        sys.exit(1)

    workspace_pipelines = get_pipelines(user_config)
    if len(workspace_pipelines) == 0:
        click.echo(f"No pipelines in workspace {workspace}")
        return
    click.echo("Pipelines:")
    for pipeline in workspace_pipelines:
        version = pipeline["currentVersion"].get("number")
        if version:
            version = f"v{version}"
        else:
            version = "N/A"
        click.echo(f"* {pipeline['code']} - {pipeline['name']} ({version})")
