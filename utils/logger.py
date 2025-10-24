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

def log_start(ticket_id: str, trade_type: str, platform: str):
    console.print(f"[bold blue]Starting QA for Ticket {ticket_id}[/bold blue] - {trade_type} on {platform}")

def log_complete(status: str, duration: float, total: int, failed: int):
    status_color = "green" if status == "PASS" else "red"
    console.print(f"[bold {status_color}]QA Complete: {status}[/bold {status_color}] - {total} checks, {failed} failed ({duration:.2f}s)")

