import click
from .commands import auto_config, init, get_file


@click.group()
def main():
    pass


main.add_command(init)
main.add_command(auto_config)
main.add_command(get_file)
