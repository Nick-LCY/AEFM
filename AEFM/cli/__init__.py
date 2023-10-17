import click
from .commands import auto_config, init


@click.group()
def main():
    pass


main.add_command(init)
main.add_command(auto_config)
