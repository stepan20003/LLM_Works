"""Typer CLI entrypoint for the AI Development Team."""

import typer
from rich.console import Console
from app.settings.logging import setup_logging
from app.settings.settings import settings

app = typer.Typer(
    help="AI Development Team - Autonomous Multi-Agent Engineering Platform"
)
console = Console()


@app.command()
def init(
    prompt: str = typer.Argument(
        ..., help="Natural language description of the project"
    ),
    project_name: str = typer.Option(
        "my-ai-project", "--name", "-n", help="Project directory name"
    ),
) -> None:
    """Initialize and run an autonomous software project from a prompt."""
    setup_logging()
    console.print(
        f"[bold green]Initializing AI Development Team for project:[/bold green] {project_name}"
    )
    console.print(f"[bold cyan]Prompt:[/bold cyan] {prompt}")
    console.print(
        f"[yellow]Using LLM Model:[/yellow] {settings.llm_model} (Workspace: {settings.workspace_dir})"
    )
    console.print(
        "[bold blue]Pipeline starting... [Manager -> Developer -> Reviewer -> Tester][/bold blue]"
    )


if __name__ == "__main__":
    app()