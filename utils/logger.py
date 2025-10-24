from rich.console import Console
from rich.panel import Panel

console = Console()

def section(title: str):
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", border_style="cyan"))

def success(msg: str):
    console.print(f"[bold green]✓[/bold green] {msg}")

def failure(msg: str):
    console.print(f"[bold red]✗[/bold red] {msg}")

def info(msg: str):
    console.print(f"[bold]•[/bold] {msg}")

