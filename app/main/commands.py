from . import module
import click
from .functions import clean_temp_files
from flask import current_app


@module.cli.command('clean-temp-files')
def clean_temp_files_command():
    """CLI command to remove temporary files that have expired."""
    clean_temp_files(current_app)
    click.echo('Temporary files cleaned successfully.')
