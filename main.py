from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, 
                         CallbackQueryHandler, ContextTypes, filters, ConversationHandler)
from PyPDF2 import PdfReader
import tempfile
import os

# Import modules
from menu import main_menu_keyboard, back_button, format_menu_keyboard
from parser import parse_questions, format_choices
from generator import generate_google_form_script
import config

# Conversation states
CONVERTING, AWAITING_QUESTIONS = range(2)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        f"👋 Hi! I'm your friendly Exam-to-Google Form bot,\n"
        f"created by {config.BOT_CREATOR} — because who has time to click stuff manually? 😅\n\n"
        "I convert your exam questions into Google Form scripts.\n"
        "You can send me:\n"
        "1. A message with formatted questions\n"
        "2. A PDF with questions (formatted or free-form)\n\n"
        "Just pick an option below and paste/send your questions!"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

# Handle button clicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    msg = ""
    markup = None

    if query.data == 'back':
        await query.edit_message_text(
            text="Choose how you want to send your questions:",
            reply_markup=main_menu_keyboard()
        )

    elif query.data == 'mcq':
        msg = (
            "🖋 Here's how to send Multiple Choice Questions:\n\n"
            "Q: What is 2+2?\n"
            "A. 3\n"
            "B. 4\n"
            "C. 5\n"
            "D. 6\n"
            "Correct: B"
        )
        markup = back_button()

    elif query.data == 'true_false':
        msg = (
            "🖋 For True/False questions, just write:\n\n"
            "The Earth is flat.\n"
            "Correct: FALSE"
        )
        markup = back_button()

    elif query.data == 'checkbox':
        msg = (
            "🖋 For Checkbox questions:\n\n"
            "Which are mammals?\n"
            "Dog\nCat\nSnake\nWhale\n"
            "Correct: Dog, Cat, Whale"
        )
        markup = back_button()

    elif query.data == 'dropdown':
        msg = (
            "🖋 For Dropdown questions:\n\n"
            "Select your favorite color:\n"
            "Red\nBlue\nGreen\nYellow\n"
            "Correct: Red"
        )
        markup = back_button()

    elif query.data == 'pdf':
        msg = (
            "📄 To upload a PDF:\n\n"
            "1. Format your questions as above\n"
            "2. Save as PDF\n"
            "3. Send it here!\n\n"
            "I'll parse it like a pro."
        )
        markup = back_button()

    elif query.data == 'convert':
        msg = (
            "🔄 Let's format your questions! What type of questions do you want to create?"
            "\n\nJust paste your unformatted questions when ready, and I'll help format them."
            "\n\nFor example, if you have:\n"
            "What is the capital of France?\n"
            "Paris\n"
            "London\n"
            "Berlin\n"
            "\nI'll format it properly for you!"
        )
        markup = format_menu_keyboard()
        await query.edit_message_text(text=msg, reply_markup=markup)
        context.user_data['converting_type'] = None
        return CONVERTING

    elif query.data.startswith('convert_'):
        question_type = query.data.replace('convert_', '')
        context.user_data['converting_type'] = question_type
        msg = "📝 Great! Now paste your unformatted questions and I'll format them for you."
        markup = back_button()
        await query.edit_message_text(text=msg, reply_markup=markup)
        return AWAITING_QUESTIONS

    elif query.data == 'help':
        msg = (
            "📄 Supported Question Types:\n\n"
            "1. Multiple Choice:\n"
            "What is the capital of France?\n"
            "Paris\nLondon\nBerlin\nMadrid\n"
            "Correct: Paris\n\n"
            "2. True/False:\n"
            "The Earth is flat.\n"
            "Correct: FALSE\n\n"
            "3. Checkbox (multiple correct):\n"
            "Which are mammals?\n"
            "Dog\nCat\nSnake\nWhale\n"
            "Correct: Dog, Cat, Whale\n\n"
            "4. Dropdown:\n"
            "Select your favorite color:\n"
            "Red\nBlue\nGreen\nYellow\n"
            "Correct: Red"
        )
        markup = back_button()

    if msg:
        await query.edit_message_text(text=msg, reply_markup=markup)

# Handle PDF uploads
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf_file = await update.message.document.get_file()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        await pdf_file.download_to_drive(temp_file.name)

        reader = PdfReader(temp_file.name)
        text = '\n'.join([page.extract_text() for page in reader.pages])

    os.unlink(temp_file.name)

    try:
        questions = parse_questions(text)
        code = generate_google_form_script(questions)
        instructions = (
            "✅ Here's your Google Form script:\n\n```\n" + code + "\n```\n\n"
            "🛠️ How to Use This Code:\n\n"
            "Go to 👉 `https://script.google.com`\n\n"
            "Click \"New project\"\n\n"
            "Paste the code I gave you\n\n"
            "Click the ▶️ Run button\n\n"
            "Your Google Form will be created automatically!\n\n"
            "Find your form link in Logs or Google Drive\n\n"
            "💡 Tip: You need to be signed into your Google account."
        )
        await update.message.reply_text(instructions)
    except ValueError as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\nPlease make sure your PDF contains properly formatted questions.")
    except Exception as e:
        await update.message.reply_text("❌ Sorry, I couldn't process your PDF. Please check if it's properly formatted and try again.")

# Handle unformatted questions
async def handle_unformatted_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not text:
        await update.message.reply_text("❌ Please send me your questions as text.")
        return AWAITING_QUESTIONS

    converting_type = context.user_data.get('converting_type')
    if not converting_type:
        await update.message.reply_text("❌ Please select a question type first.")
        return ConversationHandler.END

    try:
        # Split questions by double newline
        raw_questions = text.split('\n\n')
        formatted_questions = []

        for q in raw_questions:
            lines = q.strip().split('\n')
            if not lines:
                continue

            question = lines[0]
            choices = lines[1:] if len(lines) > 1 else []

            if converting_type == 'mcq':
                if choices:
                    formatted_choices = format_choices('\n'.join(choices))
                    formatted_questions.append(f"{question}\n{formatted_choices}\nCorrect: A")
                else:
                    formatted_questions.append(f"{question}\nA. Yes\nB. No\nCorrect: A")

            elif converting_type == 'tf':
                formatted_questions.append(f"{question}\nCorrect: TRUE")

            elif converting_type == 'checkbox':
                if choices:
                    formatted_choices = format_choices('\n'.join(choices))
                    formatted_questions.append(f"{question}\n{formatted_choices}\nCorrect: A, B")
                else:
                    formatted_questions.append(f"{question}\nA. Option 1\nB. Option 2\nC. Option 3\nCorrect: A, B")

            elif converting_type == 'dropdown':
                if choices:
                    formatted_choices = '\n'.join(choices)
                    formatted_questions.append(f"{question}\n{formatted_choices}\nCorrect: {choices[0]}")
                else:
                    formatted_questions.append(f"{question}\nOption 1\nOption 2\nOption 3\nCorrect: Option 1")

        formatted_text = '\n\n'.join(formatted_questions)
        await update.message.reply_text(
            "✅ Here are your formatted questions:\n\n" + formatted_text + 
            "\n\nYou can now copy these and send them back to me to generate the Google Form!",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text(f"❌ Error formatting questions: {str(e)}")
        return ConversationHandler.END

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document and update.message.document.mime_type == 'application/pdf':
        await handle_pdf(update, context)
        return

    text = update.message.text
    if not text:
        await update.message.reply_text("❌ Please send me a text message with questions or a PDF file.")
        return

    try:
        questions = parse_questions(text)
        code = generate_google_form_script(questions)
        instructions = (
            "✅ Here's your Google Form script:\n\n```\n" + code + "\n```\n\n"
            "🛠️ How to Use This Code:\n\n"
            "Go to 👉 `https://script.google.com`\n\n"
            "Click \"New project\"\n\n"
            "Paste the code I gave you\n\n"
            "Click the ▶️ Run button\n\n"
            "Your Google Form will be created automatically!\n\n"
            "Find your form link in Logs or Google Drive\n\n"
            "💡 Tip: You need to be signed into your Google account."
        )
        await update.message.reply_text(instructions)
    except ValueError as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\nPlease check your question format and try again.")
    except Exception as e:
        await update.message.reply_text("❌ Something went wrong. Please make sure your questions follow the correct format and try again.\n\nNeed help? Click the 'Get Help / Sample Input' button in the main menu!")

# Run the bot
def main():
    # Configure the application with error handling and timeout settings
    try:
        app = ApplicationBuilder()\
            .token(config.TELEGRAM_BOT_TOKEN)\
            .build()
    except Exception as e:
        print(f"❌ Error initializing bot: {str(e)}")
        return

    # Create conversation handler for format converter
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_click, pattern='^convert$')],
        per_chat=True,
        states={
            CONVERTING: [CallbackQueryHandler(button_click, pattern='^convert_|back$')],
            AWAITING_QUESTIONS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unformatted_questions),
                CallbackQueryHandler(button_click, pattern='^back$')
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_pdf))

    print("✅ Bot is running...")
    # Run the bot with automatic reconnection
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()