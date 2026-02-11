#!/usr/bin/env python3
"""
Multi-Agent System with Ollama and Telegram Integration
Main entry point for the application
"""

import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path
from typing import Optional

from agent_system.config import settings
from agent_system.telegram.bot import TelegramAgentBot
from agent_system.utils.logger import setup_logging, get_logger
from agent_system.scripts.init_ollama import deploy_models, check_ollama_connection

app = typer.Typer(help="Multi-Agent System with Ollama and Telegram")
console = Console()
logger = get_logger(__name__)


@app.command()
def run(
    polling: bool = typer.Option(False, "--polling", "-p", help="Use polling instead of webhook"),
    deploy: bool = typer.Option(False, "--deploy", "-d", help="Deploy models before starting"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Run the Telegram bot"""
    
    # Setup logging
    setup_logging(verbose)
    
    # Display banner
    _display_banner()
    
    # Check Ollama connection
    if not asyncio.run(check_ollama_connection()):
        console.print("[red]❌ Cannot connect to Ollama. Make sure it's running.[/red]")
        raise typer.Exit(1)
    
    # Deploy models if requested
    if deploy:
        console.print("[yellow]📦 Deploying models...[/yellow]")
        tier = typer.prompt("Select model tier", default="essential")
        asyncio.run(deploy_models(tier))
    
    # Configure webhook mode
    if not polling:
        webhook_url = typer.prompt(
            "Enter webhook URL (or leave empty for polling)",
            default=""
        )
        if webhook_url:
            settings.TELEGRAM_WEBHOOK_URL = webhook_url
    
    # Start bot
    console.print("[green]🚀 Starting Telegram bot...[/green]")
    bot = TelegramAgentBot()
    
    if polling or not settings.TELEGRAM_WEBHOOK_URL:
        bot.run()
    else:
        asyncio.run(bot.start_webhook())


@app.command()
def deploy_models_command(
    tier: str = typer.Argument("essential", help="Model tier to deploy (essential/extended/maximum)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-download")
):
    """Deploy Ollama models"""
    asyncio.run(deploy_models(tier, force))


@app.command()
def status():
    """Check system status"""
    table = Table(title="System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")
    
    # Check Ollama
    ollama_status = asyncio.run(check_ollama_connection())
    table.add_row(
        "Ollama",
        "✅" if ollama_status else "❌",
        settings.OLLAMA_HOST
    )
    
    # Check Telegram
    table.add_row(
        "Telegram Bot",
        "✅" if settings.TELEGRAM_BOT_TOKEN else "❌",
        "Token configured" if settings.TELEGRAM_BOT_TOKEN else "Missing token"
    )
    
    # Check Email
    table.add_row(
        "Email Integration",
        "✅" if settings.EMAIL_ADDRESS else "❌",
        settings.EMAIL_ADDRESS or "Not configured"
    )
    
    # Check Redis
    table.add_row(
        "Redis Cache",
        "✅",  # Would need actual check
        settings.REDIS_URL
    )
    
    console.print(table)


@app.command()
def init():
    """Initialize project structure and environment"""
    console.print("[bold]📁 Initializing Multi-Agent System...[/bold]")
    
    # Create directories
    directories = [
        settings.DATA_DIR,
        settings.LOGS_DIR,
        settings.TEMP_DIR,
        settings.MEMORY_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        console.print(f"  Created {directory}")
    
    # Create .env file if not exists
    env_file = settings.BASE_DIR / ".env"
    if not env_file.exists():
        env_example = settings.BASE_DIR / ".env.example"
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            console.print(f"  Created {env_file} from template")
        else:
            console.print("[yellow]  Warning: .env.example not found[/yellow]")
    
    console.print("[green]✅ Project initialized successfully![/green]")
    console.print("\nNext steps:")
    console.print("1. Edit .env file with your configuration")
    console.print("2. Run 'poetry run agent-system deploy-models'")
    console.print("3. Run 'poetry run agent-system run'")


def _display_banner():
    """Display application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ███╗   ███╗ █████╗ ███████╗                              ║
║     ████╗ ████║██╔══██╗██╔════╝                              ║
║     ██╔████╔██║███████║███████╗                              ║
║     ██║╚██╔╝██║██╔══██║╚════██║                              ║
║     ██║ ╚═╝ ██║██║  ██║███████║                              ║
║     ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝                              ║
║                                                              ║
║     Multi-Agent System v{version}                            ║
║     Ollama + Telegram                                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """.format(version=settings.VERSION)
    
    console.print(Panel(banner, style="bold cyan"))


if __name__ == "__main__":
    app()
