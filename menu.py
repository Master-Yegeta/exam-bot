from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 Send MCQ Questions", callback_data='mcq')],
        [InlineKeyboardButton("✅ Send True/False Questions", callback_data='true_false')],
        [InlineKeyboardButton("☑️ Send Checkbox Questions", callback_data='checkbox')],
        [InlineKeyboardButton("🔽 Send Dropdown Questions", callback_data='dropdown')],
        [InlineKeyboardButton("📄 Upload PDF with Questions", callback_data='pdf')],
        [InlineKeyboardButton("🔄 Convert Unformatted Questions", callback_data='convert')],
        [InlineKeyboardButton("❓ Get Help / Sample Input", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]]
    return InlineKeyboardMarkup(keyboard)

def format_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Multiple Choice", callback_data='convert_mcq')],
        [InlineKeyboardButton("True/False", callback_data='convert_tf')],
        [InlineKeyboardButton("Checkbox", callback_data='convert_checkbox')],
        [InlineKeyboardButton("Dropdown", callback_data='convert_dropdown')],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)