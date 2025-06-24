from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, 
                         CallbackQueryHandler, ContextTypes, filters, ConversationHandler)
from PyPDF2 import PdfReader
import tempfile
import os
import pytz
from datetime import datetime

# Import modules
from menu import main_menu_keyboard, back_button, format_menu_keyboard, success_menu_keyboard, form_creation_method_keyboard
from parser import parse_questions, format_choices
from google_forms_api import create_google_form
from professional_script_generator import generate_simple_apps_script, split_script_into_parts
import config

# Conversation states
CONVERTING, AWAITING_QUESTIONS, CHOOSING_METHOD = range(3)

# Enable logging
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        f"👋 Heeeeelllllllloooooooooo! I'm your hacker Exam-to-Google Form bot!\n"
        f"Created by @Anon_0x1 — because who has time to click stuff manually? 😅\n\n"
        "🚀 **What I can do:**\n"
        "• Convert Multiple Choice Questions into Google Forms\n"
        "• Parse PDF files with MCQ questions\n"
        "• Generate clean Google Apps Scripts\n"
        "• Support for formatted and unformatted questions\n\n"
        "📝 **Currently Supported:**\n"
        "✅ Multiple Choice Questions (MCQ)\n"
        "🔄 True/False, Checkbox, Dropdown (Coming Soon!)\n\n"
        "⚡ **We're working hard to deliver more features for you!**\n\n"
        "Just pick an option below and let's get started!"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

# Handle button clicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'back':
        # Clear any conversation state
        context.user_data.clear()
        await query.edit_message_text(
            text="Choose how you want to send your questions:",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END

    elif query.data == 'mcq':
        msg = (
            "📝 **Multiple Choice Questions Format:**\n\n"
            "**Method 1 - With Q: prefix:**\n"
            "Q: What is 2+2?\n"
            "A. 3\n"
            "B. 4\n"
            "C. 5\n"
            "D. 6\n"
            "Correct: B\n\n"
            "**Method 2 - Simple format:**\n"
            "What is the capital of France?\n"
            "A. Paris\n"
            "B. London\n"
            "C. Berlin\n"
            "D. Madrid\n"
            "Answer: A\n\n"
            "💡 **Tips:**\n"
            "• Use 'Correct:' or 'Answer:' for the right choice\n"
            "• You can use A, B, C, D or the actual text\n"
            "• Separate multiple questions with blank lines\n\n"
            "✨ **Created by @Anon_0x1**"
        )
        await query.edit_message_text(text=msg, reply_markup=back_button())

    elif query.data == 'true_false':
        msg = (
            "🔄 **True/False Questions - Coming Soon!**\n\n"
            "We're working hard to bring you True/False question support!\n\n"
            "📅 **Expected Release:** Very Soon\n"
            "🚀 **Current Status:** In Development\n\n"
            "For now, please use **Multiple Choice Questions** which are fully supported.\n\n"
            "✨ **Created by @Anon_0x1**\n"
            "⚡ **We're working hard to deliver more features for you!**"
        )
        await query.edit_message_text(text=msg, reply_markup=back_button())

    elif query.data == 'checkbox':
        msg = (
            "🔄 **Checkbox Questions - Coming Soon!**\n\n"
            "We're working hard to bring you Checkbox (Multiple Answers) support!\n\n"
            "📅 **Expected Release:** Very Soon\n"
            "🚀 **Current Status:** In Development\n\n"
            "For now, please use **Multiple Choice Questions** which are fully supported.\n\n"
            "✨ **Created by @Anon_0x1**\n"
            "⚡ **We're working hard to deliver more features for you!**"
        )
        await query.edit_message_text(text=msg, reply_markup=back_button())

    elif query.data == 'dropdown':
        msg = (
            "🔄 **Dropdown Questions - Coming Soon!**\n\n"
            "We're working hard to bring you Dropdown question support!\n\n"
            "📅 **Expected Release:** Very Soon\n"
            "🚀 **Current Status:** In Development\n\n"
            "For now, please use **Multiple Choice Questions** which are fully supported.\n\n"
            "✨ **Created by @Anon_0x1**\n"
            "⚡ **We're working hard to deliver more features for you!**"
        )
        await query.edit_message_text(text=msg, reply_markup=back_button())

    elif query.data == 'pdf':
        msg = (
            "📄 **PDF Upload Instructions:**\n\n"
            "✅ **Currently Supported:**\n"
            "• Multiple Choice Questions (MCQ) only\n"
            "• Questions with A, B, C, D choices\n"
            "• Mixed MCQ formats in one PDF\n\n"
            "📝 **Example layout:**\n"
            "```\n"
            "1. What is the capital of France?\n"
            "   A. Paris  B. London  C. Berlin  D. Madrid\n\n"
            "2. What is 2+2?\n"
            "   A. 3  B. 4  C. 5  D. 6\n\n"
            "Answer Key:\n"
            "1. A\n"
            "2. B\n"
            "```\n\n"
            "🚀 **Just upload your PDF with MCQ questions!**\n\n"
            "🔄 **Other question types coming soon!**\n"
            "✨ **Created by @Anon_0x1**"
        )
        await query.edit_message_text(text=msg, reply_markup=back_button())

    elif query.data == 'convert':
        msg = (
            "🔄 **Question Formatter Tool**\n\n"
            "Transform your unformatted MCQ questions into proper exam format!\n\n"
            "**What it does:**\n"
            "• Adds proper numbering (Q1, Q2, etc.)\n"
            "• Formats choices with A, B, C, D\n"
            "• Adds answer placeholders\n"
            "• Structures everything correctly\n\n"
            "**Example transformation:**\n"
            "```\n"
            "Input: What is Python?\n"
            "Programming language\n"
            "Snake\n"
            "Food\n\n"
            "Output: Q1: What is Python?\n"
            "A. Programming language\n"
            "B. Snake\n"
            "C. Food\n"
            "Correct: A\n"
            "```\n\n"
            "📝 **Currently supports MCQ only**\n"
            "🔄 **More types coming soon!**\n"
            "✨ **Created by @Anon_0x1**"
        )
        await query.edit_message_text(text=msg, reply_markup=format_menu_keyboard())
        context.user_data['converting_type'] = None
        return CONVERTING

    elif query.data.startswith('convert_'):
        question_type = query.data.replace('convert_', '')
        
        if question_type != 'mcq':
            msg = (
                f"🔄 **Feature Coming Soon!**\n\n"
                f"We're working hard to bring you this feature!\n\n"
                f"📅 **Expected Release:** Very Soon\n"
                f"🚀 **Current Status:** In Development\n\n"
                f"For now, please use **Multiple Choice Questions** formatter.\n\n"
                f"✨ **Created by @Anon_0x1**\n"
                f"⚡ **We're working hard to deliver more features for you!**"
            )
            await query.edit_message_text(text=msg, reply_markup=back_button())
            return ConversationHandler.END
        
        context.user_data['converting_type'] = question_type
        
        msg = (
            f"📝 **Multiple Choice Formatter**\n\n"
            f"Paste your unformatted MCQ questions below and I'll format them professionally!\n\n"
            f"**Example input:**\n"
            f"What is the capital of France?\n"
            f"Paris\n"
            f"London\n"
            f"Berlin\n"
            f"Madrid\n\n"
            f"I'll convert this into proper MCQ format for you! 🚀\n\n"
            f"✨ **Created by @Anon_0x1**"
        )
        
        await query.edit_message_text(text=msg, reply_markup=back_button())
        return AWAITING_QUESTIONS

    elif query.data == 'help':
        msg = (
            "📚 **Complete Question Format Guide**\n\n"
            "**🔹 Multiple Choice (Currently Supported):**\n"
            "Q: What is 2+2?\n"
            "A. 3  B. 4  C. 5  D. 6\n"
            "Answer: B\n\n"
            "**🔄 Coming Soon:**\n"
            "• True/False Questions\n"
            "• Checkbox (Multiple Answers)\n"
            "• Dropdown Questions\n"
            "• Short Answer Questions\n\n"
            "**📄 PDF Features:**\n"
            "• Auto-detection of MCQ questions\n"
            "• Separated answer keys supported\n"
            "• Bulk processing of multiple questions\n\n"
            "**💡 Pro Tips:**\n"
            "• Use consistent formatting\n"
            "• Separate questions with blank lines\n"
            "• Use 'Correct:' or 'Answer:' for solutions\n"
            "• Test with a few questions first\n\n"
            "✨ **Created by @Anon_0x1**\n"
            "⚡ **We're working hard to deliver more features for you!**"
        )
        await query.edit_message_text(text=msg, reply_markup=back_button())

    elif query.data == 'method_direct':
        # User chose direct form creation
        context.user_data['creation_method'] = 'direct'
        questions = context.user_data.get('parsed_questions', [])
        form_title = context.user_data.get('form_title', 'Exam Questions')
        
        await query.edit_message_text("🔄 Creating direct Google Form link...")
        await handle_direct_form_creation(query, questions, form_title)
        return ConversationHandler.END

    elif query.data == 'method_script':
        # User chose Google Apps Script
        context.user_data['creation_method'] = 'script'
        questions = context.user_data.get('parsed_questions', [])
        form_title = context.user_data.get('form_title', 'Exam Questions')
        
        await query.edit_message_text("📝 Generating Google Apps Script...")
        await handle_script_generation(query, questions, form_title)
        return ConversationHandler.END

async def handle_direct_form_creation(query, questions, form_title):
    """Handle direct form creation with limitations notice"""
    # Filter only MCQ questions
    mcq_questions = [q for q in questions if q["type"].name == "MULTIPLE_CHOICE"]
    
    if not mcq_questions:
        message = (
            f"❌ **No MCQ Questions Found**\n\n"
            f"Currently, we only support Multiple Choice Questions.\n\n"
            f"🔄 **Other question types coming soon!**\n"
            f"✨ **Created by @Anon_0x1**\n"
            f"⚡ **We're working hard to deliver more features for you!**"
        )
        await query.message.reply_text(message, reply_markup=success_menu_keyboard())
        return
    
    form_result = create_google_form(mcq_questions, form_title)
    
    if form_result["success"]:
        message = (
            f"✅ **Direct Google Form Created!**\n\n"
            f"📋 **Student Link:** {form_result['response_url']}\n\n"
            f"⚠️ **Important Limitations:**\n"
            f"• This form is VIEW-ONLY for responses\n"
            f"• You cannot edit questions after creation\n"
            f"• Limited customization options\n\n"
            f"📊 **Form Details:**\n"
            f"• Total MCQ Questions: {len(mcq_questions)}\n"
            f"• Form ID: {form_result['form_id']}\n\n"
            f"💡 **For full edit access, use Google Apps Script method!**\n\n"
            f"✨ **Created by @Anon_0x1**"
        )
    else:
        message = (
            f"❌ **Direct form creation failed**\n\n"
            f"Error: {form_result['error']}\n\n"
            f"🔧 **Recommended Solution:**\n"
            f"Use the Google Apps Script method for reliable form creation.\n\n"
            f"✨ **Created by @Anon_0x1**"
        )
    
    await query.message.reply_text(message, reply_markup=success_menu_keyboard())

async def handle_script_generation(query, questions, form_title):
    """Handle Google Apps Script generation - FIXED VERSION"""
    try:
        # Filter only MCQ questions
        mcq_questions = [q for q in questions if q["type"].name == "MULTIPLE_CHOICE"]
        
        if not mcq_questions:
            message = (
                f"❌ **No MCQ Questions Found**\n\n"
                f"Currently, we only support Multiple Choice Questions.\n\n"
                f"🔄 **Other question types coming soon!**\n"
                f"✨ **Created by @Anon_0x1**\n"
                f"⚡ **We're working hard to deliver more features for you!**"
            )
            await query.message.reply_text(message, reply_markup=success_menu_keyboard())
            return
            
        print(f"Generating script for {len(mcq_questions)} MCQ questions...")
        
        # Generate the script
        script = generate_simple_apps_script(mcq_questions, form_title)
        
        if not script:
            await query.message.reply_text("❌ Failed to generate script. Please try again.")
            return
        
        print("Script generated successfully!")
        
        # Send header message first
        header_message = (
            f"✅ **Google Apps Script Ready!**\n\n"
            f"📊 **{len(mcq_questions)} MCQ questions** • **{form_title}**\n\n"
            f"🚀 **Steps:**\n"
            f"1. Go to: script.google.com\n"
            f"2. Click 'New project'\n"
            f"3. Delete default code\n"
            f"4. Copy & paste the code below\n"
            f"5. Click ▶️ Run button\n"
            f"6. Check execution logs for your form links!\n\n"
            f"🔗 https://script.google.com\n\n"
            f"✨ **Created by @Anon_0x1**"
        )
        
        await query.message.reply_text(header_message, reply_markup=success_menu_keyboard())
        
        # Split script into parts if needed
        script_parts = split_script_into_parts(script, max_length=3500)
        
        if len(script_parts) == 1:
            # Single message
            script_message = f"📝 **Copy this code:**\n\n```javascript\n{script}\n```"
            await query.message.reply_text(script_message, parse_mode='Markdown')
        else:
            # Multiple messages
            await query.message.reply_text(f"📝 **Script Code ({len(script_parts)} parts):**")
            
            for i, part in enumerate(script_parts, 1):
                part_message = f"**Part {i}/{len(script_parts)}:**\n\n```javascript\n{part}\n```"
                await query.message.reply_text(part_message, parse_mode='Markdown')
        
        # Send final instructions
        final_message = (
            f"🎯 **After running the script:**\n\n"
            f"Look for these messages in the execution log:\n"
            f"• Edit: [Your edit link]\n"
            f"• Share: [Your share link]\n\n"
            f"📋 **Share link** = Give to students\n"
            f"📝 **Edit link** = For you to modify\n\n"
            f"✨ **Created by @Anon_0x1**"
        )
        
        await query.message.reply_text(final_message)
        
    except Exception as e:
        print(f"Script generation error: {str(e)}")
        error_message = (
            f"❌ **Script generation failed:** {str(e)}\n\n"
            f"Please try again or contact @Anon_0x1 for support.\n\n"
            f"✨ **Created by @Anon_0x1**"
        )
        await query.message.reply_text(error_message, reply_markup=success_menu_keyboard())

# Handle PDF uploads
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("📄 Processing your PDF... Please wait!")
        
        pdf_file = await update.message.document.get_file()

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            await pdf_file.download_to_drive(temp_file.name)

            reader = PdfReader(temp_file.name)
            text = '\n'.join([page.extract_text() for page in reader.pages])

        os.unlink(temp_file.name)

        if not text.strip():
            await update.message.reply_text("❌ Could not extract text from PDF. Please make sure it's not a scanned image.")
            return

        questions = parse_questions(text)
        
        # Filter only MCQ questions
        mcq_questions = [q for q in questions if q["type"].name == "MULTIPLE_CHOICE"]
        
        if not mcq_questions:
            message = (
                f"❌ **No MCQ Questions Found in PDF**\n\n"
                f"Currently, we only support Multiple Choice Questions.\n\n"
                f"🔄 **Other question types coming soon!**\n"
                f"✨ **Created by @Anon_0x1**\n"
                f"⚡ **We're working hard to deliver more features for you!**"
            )
            await update.message.reply_text(message)
            return

        # Store questions and show method selection
        context.user_data['parsed_questions'] = mcq_questions
        context.user_data['form_title'] = "PDF Exam Questions"
        
        method_message = (
            f"✅ **PDF Processed Successfully!**\n\n"
            f"📊 **Found:** {len(mcq_questions)} MCQ questions\n"
            f"📝 **Type:** Multiple Choice Questions\n\n"
            f"🎯 **Choose your preferred creation method:**\n\n"
            f"🔗 **Direct Link:** Quick form creation, but view-only access\n"
            f"📝 **Google Script:** Full edit access, clean code (Recommended)\n\n"
            f"⚠️ **Note:** Direct links have editing limitations. We recommend Google Script!\n\n"
            f"✨ **Created by @Anon_0x1**"
        )
        
        await update.message.reply_text(method_message, reply_markup=form_creation_method_keyboard())
        return CHOOSING_METHOD
            
    except ValueError as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\nPlease make sure your PDF contains properly formatted MCQ questions.\n\n✨ Created by @Anon_0x1")
    except Exception as e:
        await update.message.reply_text(f"❌ Sorry, I couldn't process your PDF. Error: {str(e)}\n\n✨ Created by @Anon_0x1")

# Handle unformatted questions
async def handle_unformatted_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if not text:
        await update.message.reply_text("❌ Please send me your questions as text.")
        return AWAITING_QUESTIONS

    converting_type = context.user_data.get('converting_type')
    if not converting_type or converting_type != 'mcq':
        await update.message.reply_text("❌ Currently only MCQ formatting is supported.\n\n✨ Created by @Anon_0x1")
        return ConversationHandler.END

    try:
        # Split questions by double newline or single newline for simple cases
        raw_questions = [q.strip() for q in text.split('\n\n') if q.strip()]
        if len(raw_questions) == 1:
            raw_questions = [q.strip() for q in text.split('\n') if q.strip()]
        
        formatted_questions = []

        for i, q in enumerate(raw_questions):
            lines = q.strip().split('\n')
            if not lines:
                continue

            question = lines[0]
            choices = lines[1:] if len(lines) > 1 else []

            if choices:
                formatted_choices = format_choices('\n'.join(choices))
                if formatted_choices:
                    formatted_questions.append(f"Q{i+1}: {question}\n" + '\n'.join(formatted_choices) + "\nCorrect: A")
                else:
                    formatted_questions.append(f"Q{i+1}: {question}\nA. Option 1\nB. Option 2\nC. Option 3\nD. Option 4\nCorrect: A")
            else:
                formatted_questions.append(f"Q{i+1}: {question}\nA. Option 1\nB. Option 2\nC. Option 3\nD. Option 4\nCorrect: A")

        formatted_text = '\n\n'.join(formatted_questions)
        
        success_message = (
            f"✅ MCQ Questions Formatted Successfully!\n\n"
            f"📊 Processed: {len(formatted_questions)} questions\n"
            f"📝 Type: Multiple Choice Questions\n\n"
            f"Formatted Questions:\n"
            f"```\n{formatted_text[:1000]}{'...' if len(formatted_text) > 1000 else ''}\n```\n\n"
            f"📋 Next Step: Copy these formatted questions and send them back to me to create your Google Form!\n\n"
            f"✨ Created by @Anon_0x1"
        )
        
        await update.message.reply_text(success_message, parse_mode='Markdown', reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text(f"❌ Error formatting questions: {str(e)}\n\n✨ Created by @Anon_0x1")
        return ConversationHandler.END

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document and update.message.document.mime_type == 'application/pdf':
        await handle_pdf(update, context)
        return

    text = update.message.text
    if not text:
        await update.message.reply_text("❌ Please send me a text message with questions or a PDF file.\n\n✨ Created by @Anon_0x1")
        return

    try:
        await update.message.reply_text("🔄 Processing your questions...")
        
        questions = parse_questions(text)
        
        # Filter only MCQ questions
        mcq_questions = [q for q in questions if q["type"].name == "MULTIPLE_CHOICE"]
        
        if not mcq_questions:
            message = (
                f"❌ **No MCQ Questions Found**\n\n"
                f"Currently, we only support Multiple Choice Questions.\n\n"
                f"🔄 **Other question types coming soon!**\n"
                f"✨ **Created by @Anon_0x1**\n"
                f"⚡ **We're working hard to deliver more features for you!**"
            )
            await update.message.reply_text(message)
            return

        # Store questions and show method selection
        context.user_data['parsed_questions'] = mcq_questions
        context.user_data['form_title'] = "Exam Questions"
        
        method_message = (
            f"✅ **Questions Processed Successfully!**\n\n"
            f"📊 **Found:** {len(mcq_questions)} MCQ questions\n"
            f"📝 **Type:** Multiple Choice Questions\n\n"
            f"🎯 **Choose your preferred creation method:**\n\n"
            f"🔗 **Direct Link:** Quick form creation, but view-only access\n"
            f"📝 **Google Script:** Full edit access, clean code (Recommended)\n\n"
            f"⚠️ **Note:** Direct links have editing limitations. We recommend Google Script!\n\n"
            f"✨ **Created by @Anon_0x1**"
        )
        
        await update.message.reply_text(method_message, reply_markup=form_creation_method_keyboard())
            
    except ValueError as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\nPlease check your MCQ question format and try again.\n\n✨ Created by @Anon_0x1")
    except Exception as e:
        await update.message.reply_text(f"❌ Something went wrong: {str(e)}\n\nNeed help? Contact @Anon_0x1!")

# Define a simple keyboard for success/failure actions
def success_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data='back'),
            InlineKeyboardButton("📝 New Form", callback_data='back'),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# Run the bot
def main():
    try:
        app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
        print("✅ Bot initialized successfully!")
        print("✨ Created by @Anon_0x1")
        
    except Exception as e:
        print(f"❌ Error initializing bot: {str(e)}")
        print("Please check your TELEGRAM_BOT_TOKEN in the .env file")
        return

    # Create conversation handler for format converter
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_click, pattern='^convert$')],
        per_chat=True,
        states={
            CONVERTING: [
                CallbackQueryHandler(button_click, pattern='^convert_|back$')
            ],
            AWAITING_QUESTIONS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unformatted_questions),
                CallbackQueryHandler(button_click, pattern='^back$')
            ],
            CHOOSING_METHOD: [
                CallbackQueryHandler(button_click, pattern='^method_|back$')
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
            CallbackQueryHandler(button_click, pattern='^back$')
        ],
    )

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_pdf))

    print("🚀 Starting bot polling...")
    print("Press Ctrl+C to stop the bot")
    
    try:
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        print("✨ Created by @Anon_0x1")
    except Exception as e:
        print(f"❌ Error running bot: {str(e)}")

if __name__ == "__main__":
    main()
