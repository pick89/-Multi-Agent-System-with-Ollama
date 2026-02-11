"""Clean Telegram Bot - Production Ready"""

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from agent_system.config import settings
import httpx
import asyncio
import time

class TelegramBot:
    """Production-ready Telegram bot with auto model selection"""
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.fast = "gemma3:1b"      # Ultra fast chat
        self.smart = "phi4:14b"      # Deep thinking  
        self.code = "qwen2.5-coder:3b"  # Code generation
        self.current = self.fast
        self.ollama_url = "http://localhost:11434/api/chat"
        self.smart_loaded = False
        
    async def start(self, update: Update, _):
        """Welcome message"""
        msg = (
            "🤖 **Multi-Agent System Ready**\n\n"
            "✅ 14 models installed\n"
            "🚀 Fast: gemma3:1b (instant)\n"
            "🧠 Smart: phi4:14b (first load ~60s)\n"
            "💻 Code: /code <prompt>\n\n"
            "Just chat with me!"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def code(self, update: Update, ctx):
        """Generate code"""
        prompt = ' '.join(ctx.args) if ctx.args else "hello world"
        await update.message.reply_text(f"💻 Generating...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.ollama_url, json={
                "model": self.code,
                "messages": [{"role": "user", "content": f"Write {prompt}. ONLY code."}],
                "stream": False
            })
            if resp.status_code == 200:
                code = resp.json()["message"]["content"]
                await update.message.reply_text(f"```\n{code}\n```", parse_mode='MarkdownV2')
    
    async def smart_mode(self, update: Update, _):
        """Force smart mode"""
        self.current = self.smart
        await update.message.reply_text("🧠 Smart mode - Using phi4:14b")
    
    async def fast_mode(self, update: Update, _):
        """Force fast mode"""
        self.current = self.fast
        await update.message.reply_text("🚀 Fast mode - Using gemma3:1b")
    
    async def status(self, update: Update, _):
        """System status"""
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            models = len(resp.json().get("models", []))
        
        status = (
            f"📊 **Status**\n"
            f"• Ollama: {models} models\n"
            f"• Mode: {'🧠 Smart' if self.current == self.smart else '🚀 Fast'}\n"
            f"• Smart loaded: {'✅' if self.smart_loaded else '⏳'}"
        )
        await update.message.reply_text(status, parse_mode='Markdown')
    
    async def chat(self, update: Update, ctx):
        """Main chat handler"""
        text = update.message.text.lower()
        use_smart = self.current == self.smart or any(
            k in text for k in ['pi', 'math', 'science', 'history', 'who', 'what', 'why']
        )
        model = self.smart if use_smart else self.fast
        timeout = 120 if model == self.smart and not self.smart_loaded else 30
        
        await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            start = time.time()
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(self.ollama_url, json={
                    "model": model,
                    "messages": [{"role": "user", "content": update.message.text}],
                    "stream": False
                })
                ms = int((time.time() - start) * 1000)
                
                if resp.status_code == 200:
                    reply = resp.json()["message"]["content"]
                    await update.message.reply_text(reply)
                    
                    if model == self.smart and not self.smart_loaded:
                        self.smart_loaded = True
                        await update.message.reply_text(f"_Loaded in {ms}ms_", parse_mode='MarkdownV2')
        except httpx.TimeoutException:
            if model == self.smart and not self.smart_loaded:
                await update.message.reply_text(
                    "⏳ Loading phi4:14b into memory...\n"
                    "Please wait 60s and try again."
                )
                self.smart_loaded = True
    
    def run(self):
        """Start bot"""
        # Create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Build app
        app = Application.builder().token(self.token).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.start))
        app.add_handler(CommandHandler("code", self.code))
        app.add_handler(CommandHandler("smart", self.smart_mode))
        app.add_handler(CommandHandler("fast", self.fast_mode))
        app.add_handler(CommandHandler("status", self.status))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat))
        
        print("\n" + "="*50)
        print("🤖 MULTI-AGENT SYSTEM - TELEGRAM")
        print("="*50)
        print("✅ Bot running! Press Ctrl+C to stop")
        print(f"📱 Token: {self.token[:10]}...")
        print(f"🚀 Fast: {self.fast}")
        print(f"🧠 Smart: {self.smart}")
        print(f"💻 Code: {self.code}")
        print("="*50 + "\n")
        
        app.run_polling()
