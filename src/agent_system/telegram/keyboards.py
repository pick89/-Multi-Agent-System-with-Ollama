from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any


class KeyboardBuilder:
    """Build inline keyboards for Telegram bot"""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("💻 Code", callback_data="menu_code"),
                InlineKeyboardButton("📧 Email", callback_data="menu_email")
            ],
            [
                InlineKeyboardButton("🖼️ Vision", callback_data="menu_vision"),
                InlineKeyboardButton("🔍 Analyze", callback_data="menu_analyze")
            ],
            [
                InlineKeyboardButton("🔎 Search", callback_data="menu_search"),
                InlineKeyboardButton("⏰ Reminder", callback_data="menu_reminder")
            ],
            [
                InlineKeyboardButton("ℹ️ Help", callback_data="menu_help"),
                InlineKeyboardButton("📊 Status", callback_data="menu_status")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def email_actions(email_id: str) -> InlineKeyboardMarkup:
        """Email action buttons"""
        keyboard = [
            [
                InlineKeyboardButton("✉️ Reply", callback_data=f"reply_{email_id}"),
                InlineKeyboardButton("📌 Important", callback_data=f"important_{email_id}")
            ],
            [
                InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{email_id}"),
                InlineKeyboardButton("📂 Archive", callback_data=f"archive_{email_id}")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def code_actions(language: str) -> InlineKeyboardMarkup:
        """Code generation action buttons"""
        keyboard = [
            [
                InlineKeyboardButton("▶️ Run", callback_data=f"run_code_{language}"),
                InlineKeyboardButton("📋 Copy", callback_data=f"copy_code_{language}")
            ],
            [
                InlineKeyboardButton("🔄 Regenerate", callback_data=f"regenerate_{language}"),
                InlineKeyboardButton("📝 Explain", callback_data=f"explain_code_{language}")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirmation_buttons(action: str, item_id: str) -> InlineKeyboardMarkup:
        """Confirmation buttons"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}_{item_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{action}_{item_id}")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def pagination_buttons(current_page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
        """Pagination buttons"""
        keyboard = []
        
        row = []
        if current_page > 1:
            row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"{prefix}_page_{current_page-1}"))
        
        row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop"))
        
        if current_page < total_pages:
            row.append(InlineKeyboardButton("Next ▶️", callback_data=f"{prefix}_page_{current_page+1}"))
        
        keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def language_selector() -> InlineKeyboardMarkup:
        """Programming language selector"""
        keyboard = [
            [InlineKeyboardButton("🐍 Python", callback_data="lang_python")],
            [InlineKeyboardButton("📘 JavaScript", callback_data="lang_javascript")],
            [InlineKeyboardButton("📗 TypeScript", callback_data="lang_typescript")],
            [InlineKeyboardButton("🔷 Go", callback_data="lang_go")],
            [InlineKeyboardButton("⚙️ Rust", callback_data="lang_rust")],
            [InlineKeyboardButton("☕ Java", callback_data="lang_java")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
