import asyncio
import logging
from typing import Dict, Optional
from pathlib import Path

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from agent_system.config import settings
from agent_system.core.orchestrator import AgentOrchestrator
from agent_system.telegram.handlers import TelegramHandlers
from agent_system.telegram.callbacks import CallbackHandler
from agent_system.utils.logger import get_logger

logger = get_logger(__name__)


class TelegramAgentBot:
    """Telegram bot for the multi-agent system"""
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.orchestrator = AgentOrchestrator()
        self.handlers = TelegramHandlers(self.orchestrator)
        self.callback_handler = CallbackHandler(self.orchestrator)
        self.application: Optional[Application] = None
        
        # User sessions
        self.user_sessions: Dict[int, Dict] = {}
    
    async def initialize(self):
        """Initialize the bot and set up commands"""
        self.application = Application.builder().token(self.token).build()
        
        # Register command handlers
        await self._register_commands()
        
        # Register message handlers
        self._register_handlers()
        
        logger.info("Telegram bot initialized successfully")
    
    async def _register_commands(self):
        """Register bot commands"""
        commands = [
            BotCommand("start", "Start the bot and show welcome message"),
            BotCommand("help", "Show help information"),
            BotCommand("check_email", "Check your emails"),
            BotCommand("generate_code", "Generate code in any language"),
            BotCommand("analyze", "Deep analysis of text or documents"),
            BotCommand("vision", "Process and analyze images"),
            BotCommand("reminder", "Set a reminder"),
            BotCommand("search", "Search and summarize information"),
            BotCommand("status", "Check system status")
        ]
        
        await self.application.bot.set_my_commands(commands)
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(CommandHandler("check_email", self.handlers.check_email_command))
        self.application.add_handler(CommandHandler("generate_code", self.handlers.generate_code_command))
        self.application.add_handler(CommandHandler("analyze", self.handlers.analyze_command))
        self.application.add_handler(CommandHandler("vision", self.handlers.vision_command))
        self.application.add_handler(CommandHandler("reminder", self.handlers.reminder_command))
        self.application.add_handler(CommandHandler("search", self.handlers.search_command))
        self.application.add_handler(CommandHandler("status", self.handlers.status_command))
    
    def _register_handlers(self):
        """Register message and callback handlers"""
        # Message handlers
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message)
        )
        self.application.add_handler(
            MessageHandler(filters.PHOTO, self.handlers.handle_photo)
        )
        self.application.add_handler(
            MessageHandler(filters.Document.ALL, self.handlers.handle_document)
        )
        
        # Callback query handler
        self.application.add_handler(
            CallbackQueryHandler(self.callback_handler.handle_callback)
        )
        
        # Error handler
        self.application.add_error_handler(self.handlers.error_handler)
    
    async def start_webhook(self):
        """Start the bot in webhook mode"""
        webhook_url = settings.TELEGRAM_WEBHOOK_URL
        port = settings.TELEGRAM_PORT
        
        await self.application.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to {webhook_url}")
        
        await self.application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url
        )
    
    async def start_polling(self):
        """Start the bot in polling mode"""
        logger.info("Starting bot in polling mode...")
        await self.application.initialize()
        await self.application.start()
        
        # Start polling
        await self.application.updater.start_polling()
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
    
    def run(self):
        """Run the bot"""
        try:
            if settings.TELEGRAM_WEBHOOK_URL:
                asyncio.run(self.start_webhook())
            else:
                asyncio.run(self.start_polling())
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
