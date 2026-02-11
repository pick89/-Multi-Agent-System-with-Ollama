import asyncio
from typing import Dict, Any
from pathlib import Path
import tempfile

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from agent_system.core.orchestrator import AgentOrchestrator
from agent_system.telegram.keyboards import KeyboardBuilder
from agent_system.utils.logger import get_logger
from agent_system.config import settings

logger = get_logger(__name__)


class TelegramHandlers:
    """Handlers for Telegram bot commands and messages"""
    
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
        self.keyboards = KeyboardBuilder()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 **Multi-Agent System v{version}**

I'm an intelligent assistant powered by **multiple specialized AI models** running locally via Ollama.

**✨ Available Capabilities:**
• 💻 **Code Generation** - Python, JavaScript, Go, Rust, Java
• 📧 **Email Management** - Check, prioritize, suggest replies
• 🔍 **Deep Analysis** - Text analysis, reasoning, problem-solving
• 🖼️ **Vision Processing** - Image analysis, OCR, document processing
• 🔎 **Web Search** - Search and summarize information
• ⏰ **Reminders** - Set notifications and alerts

**🚀 Quick Commands:**
/check_email - Check your emails
/generate_code - Create code in any language
/analyze - Deep text analysis
/vision - Process images
/search - Web search
/reminder - Set reminders

**💡 How to use:**
Simply type your request naturally, and I'll route it to the best specialist!

*Example: "Write a Python script to parse CSV files"*
        """.format(version=settings.VERSION)
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboards.main_menu()
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📚 **Help & Documentation**

**Available Commands:**
• /start - Initialize the bot
• /help - Show this message
• /check_email - Fetch and analyze emails
• /generate_code [prompt] - Generate code
• /analyze [text] - Deep analysis
• /vision - Process an image (send with photo)
• /search [query] - Web search
• /reminder [time] [message] - Set reminder
• /status - Check system health

**Natural Language Examples:**
• "Check my emails from yesterday"
• "Write a REST API in Python"
• "Summarize this article: [URL]"
• "Set a reminder for 3pm to call John"
• "Search for AI news this week"

**Model Stack:**
• Router: gemma3:1b (50ms response)
• Code: qwen2.5-coder (3b/7b/16b)
• Vision: gemma3:4b, llama3.2-vision:11b
• Analysis: phi4:14b, qwen2.5:14b
• Synthesis: aya:8b

Need help? Just ask! 🚀
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Send typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        try:
            # Get user session
            session = self._get_user_session(user_id)
            
            # Process through orchestrator
            result = await self.orchestrator.process_request(
                user_input=user_message,
                user_id=str(user_id),
                session=session
            )
            
            # Update session
            self._update_user_session(user_id, result.get("session", {}))
            
            # Handle different response types
            if result.get("requires_clarification"):
                await self._send_clarification(update, context, result)
            elif result.get("actions"):
                await self._send_with_actions(update, context, result)
            else:
                await self._send_response(update, context, result)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ I encountered an error processing your request. Please try again."
            )
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages for vision processing"""
        user_id = update.effective_user.id
        
        await update.message.reply_text("🖼️ Processing your image...")
        
        try:
            # Get the largest photo
            photo_file = await update.message.photo[-1].get_file()
            
            # Save temporarily
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                await photo_file.download_to_drive(tmp_file.name)
                
                # Process with vision agent
                result = await self.orchestrator.process_request(
                    user_input=update.message.caption or "Analyze this image",
                    user_id=str(user_id),
                    session=self._get_user_session(user_id),
                    attachments=[{"type": "image", "path": tmp_file.name}]
                )
                
                await self._send_response(update, context, result)
                
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            await update.message.reply_text(
                "❌ Failed to process the image. Please try again."
            )
    
    async def generate_code_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /generate_code command"""
        prompt = ' '.join(context.args) if context.args else ""
        
        if not prompt:
            await update.message.reply_text(
                "💻 **Code Generation**\n\n"
                "Please specify what code you want to generate.\n\n"
                "Example: `/generate_code Python script to download files from URL`\n"
                "Example: `/generate_code REST API with FastAPI`\n"
                "Example: `/generate_code JavaScript function to validate email`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await update.message.reply_text("💻 Generating code... This may take a moment.")
        
        result = await self.orchestrator.process_request(
            user_input=f"Generate code: {prompt}",
            user_id=str(update.effective_user.id),
            session={}
        )
        
        await self._send_response(update, context, result)
    
    async def check_email_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check_email command"""
        if not settings.EMAIL_ADDRESS:
            await update.message.reply_text(
                "❌ Email integration is not configured.\n"
                "Please set EMAIL_ADDRESS and EMAIL_PASSWORD in .env file."
            )
            return
        
        await update.message.reply_text("📧 Checking your emails...")
        
        result = await self.orchestrator.process_request(
            user_input="Check my emails",
            user_id=str(update.effective_user.id),
            session={}
        )
        
        await self._send_response(update, context, result)
    
    async def _send_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: Dict):
        """Send formatted response"""
        response = result.get("response", "")
        
        # Split long messages
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await update.message.reply_text(
                    chunk,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
        else:
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
    
    async def _send_with_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: Dict):
        """Send response with action buttons"""
        response = result.get("response", "")
        actions = result.get("actions", [])
        
        keyboard = []
        for action in actions[:3]:  # Max 3 actions
            keyboard.append([
                InlineKeyboardButton(
                    action.get("label", "Action"),
                    callback_data=action.get("callback_data", "")
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    
    def _get_user_session(self, user_id: int) -> Dict:
        """Get user session from context or initialize new one"""
        # This would typically be stored in Redis
        return {}
    
    def _update_user_session(self, user_id: int, session: Dict):
        """Update user session"""
        # This would typically be stored in Redis
        pass
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the telegram bot"""
        logger.error(f"Update {update} caused error {context.error}")
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again later."
                )
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
