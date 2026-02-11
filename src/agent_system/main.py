"""Multi-Agent System - Clean CLI Entry Point"""

import typer
import asyncio
import httpx
from rich.console import Console
from rich.panel import Panel
from agent_system.config import settings

app = typer.Typer()
console = Console()

@app.command()
def telegram():
    """Start Telegram bot"""
    from agent_system.telegram.bot import TelegramBot
    
    # Check Ollama
    try:
        resp = asyncio.run(httpx.AsyncClient(timeout=5).get("http://localhost:11434/api/tags"))
        if resp.status_code != 200:
            console.print("[red]❌ Ollama not responding[/red]")
            raise typer.Exit(1)
    except:
        console.print("[red]❌ Ollama is not running[/red]")
        console.print("[yellow]💡 Start with: ollama serve[/yellow]")
        raise typer.Exit(1)
    
    # Check token
    if not settings.TELEGRAM_BOT_TOKEN or "your_telegram" in settings.TELEGRAM_BOT_TOKEN:
        console.print("[red]❌ Telegram token not configured[/red]")
        console.print("[yellow]💡 Add TELEGRAM_BOT_TOKEN to .env[/yellow]")
        raise typer.Exit(1)
    
    # Start bot
    bot = TelegramBot()
    bot.run()

@app.command()
def chat():
    """Start interactive chat (CLI)"""
    console.print(Panel.fit("🤖 Multi-Agent CLI Chat", style="bold cyan"))
    console.print("Type 'exit' to quit\n")
    
    # First, verify Ollama is working
    try:
        import httpx
        resp = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code != 200:
            console.print("[red]❌ Ollama is not responding[/red]")
            return
        console.print("[green]✅ Connected to Ollama[/green]\n")
    except:
        console.print("[red]❌ Cannot connect to Ollama[/red]")
        console.print("[yellow]💡 Start with: ollama serve[/yellow]")
        return
    
    async def chat_loop():
        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                user = console.input("[bold green]You:[/bold green] ")
                if user.lower() in ['exit', 'quit', 'q']:
                    break
                
                with console.status("Thinking..."):
                    try:
                        resp = await client.post("http://localhost:11434/api/chat", json={
                            "model": "gemma3:1b",
                            "messages": [{"role": "user", "content": user}],
                            "stream": False
                        }, timeout=30.0)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            reply = data["message"]["content"]
                            console.print(f"[bold blue]Agent:[/bold blue] {reply}\n")
                        else:
                            console.print(f"[red]Error: {resp.status_code}[/red]\n")
                    except httpx.TimeoutException:
                        console.print("[red]Timeout - Ollama is not responding[/red]")
                        console.print("[yellow]Try: ollama stop gemma3:1b && ollama run gemma3:1b[/yellow]\n")
                    except Exception as e:
                        console.print(f"[red]Error: {str(e)[:100]}[/red]\n")
    
    asyncio.run(chat_loop())

@app.command()
def status():
    """Quick system status"""
    try:
        resp = asyncio.run(httpx.AsyncClient(timeout=5).get("http://localhost:11434/api/tags"))
        models = len(resp.json().get("models", []))
        console.print(f"[green]✅ Ollama:[/green] {models} models")
        
        # Test gemma3:1b
        try:
            test = asyncio.run(httpx.AsyncClient(timeout=10).post(
                "http://localhost:11434/api/chat",
                json={"model": "gemma3:1b", "messages": [{"role": "user", "content": "hi"}], "stream": False}
            ))
            console.print(f"[green]✅ gemma3:1b:[/green] Responding")
        except:
            console.print(f"[yellow]⚠️ gemma3:1b:[/yellow] Not responding")
            
    except:
        console.print("[red]❌ Ollama: Not running[/red]")
    
    token = settings.TELEGRAM_BOT_TOKEN
    if token and "your_telegram" not in token:
        console.print(f"[green]✅ Telegram:[/green] Configured")
    else:
        console.print("[yellow]⚠️ Telegram:[/yellow] Token missing")

def main():
    app()

if __name__ == "__main__":
    main()
