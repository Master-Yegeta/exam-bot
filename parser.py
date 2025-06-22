import re
from enum import Enum

class QuestionType(Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    CHECKBOX = "CHECKBOX"
    DROPDOWN = "DROPDOWN"

def detect_question_type(question: str) -> QuestionType:
    question = question.lower()
    if any(kw in question for kw in ["true", "false", "yes", "no"]):
        return QuestionType.TRUE_FALSE
    elif "[short_answer]" in question:
        return QuestionType.SHORT_ANSWER
    elif "[checkbox]" in question:
        return QuestionType.CHECKBOX
    elif "[dropdown]" in question:
        return QuestionType.DROPDOWN
    else:
        return QuestionType.MULTIPLE_CHOICE

def format_choices(text: str) -> list:
    if not text or not isinstance(text, str):
        return []

    """Convert unformatted choices into properly formatted ones."""
    lines = [line.strip() for line in text.split('\n')]
    choices = []
    letters = ['A', 'B', 'C', 'D']
    
    for i, line in enumerate(lines):
        if not line:
            continue
        # Remove any existing numbering or lettering
        clean_line = re.sub(r'^[A-Da-d1-9][\.\)\-]\s*', '', line).strip()
        if i < len(letters):
            choices.append(f"{letters[i]}. {clean_line}")
    
    return choices

def parse_questions(text: str):
    if not text or not isinstance(text, str):
        raise ValueError("Input must be a non-empty string")

    # Clean input text
    text = text.strip()
    if not text:
        raise ValueError("Input contains no valid questions")

    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    
    questions = []
    current = None
    collecting_choices = False
    choice_buffer = []

    for line in lines:
        line_lower = line.lower()

        # Detect new question
        if (line.startswith(("Q:", "Question:", "1.", "Q.")) or 
            re.match(r"^[0-9]+[\)\.]|^[A-Z][a-z]", line)):
            
            # Save previous question if exists
            if current and (current["choices"] or choice_buffer):
                if choice_buffer:
                    current["choices"] = format_choices('\n'.join(choice_buffer))
                    choice_buffer = []
                questions.append(current)
                collecting_choices = False

            question_text = re.sub(r"^(Q:|Question:|[0-9]+[\)\.]|Q\.)\s*", "", line)
            q_type = detect_question_type(question_text)

            current = {
                "question": question_text,
                "type": q_type,
                "choices": [],
                "correct_letter": "",
                "correct_text": "",
                "correct_answers": []
            }
            collecting_choices = True

        # Detect choices
        elif collecting_choices and not line_lower.startswith(("correct:", "answer:", "ans:")):
            if re.match(r"^[A-Da-d][\.\)\-]|^[1-4][\.\)\-]", line):
                current["choices"].append(line)
            else:
                choice_buffer.append(line)

        # Detect choices
        # Detect correct answer
        elif any(line_lower.startswith(prefix) for prefix in ["correct:", "answer:", "ans:"]):
            # Format any remaining choices before processing the answer
            if choice_buffer:
                current["choices"] = format_choices('\n'.join(choice_buffer))
                choice_buffer = []

            answers = line.split(":")[1].strip().upper()

            # If the answer is TRUE/FALSE/YES/NO, and the question isn't already a checkbox type
            # (as checkbox items might legitimately have "True" or "False" as choice text),
            # then we should ensure the question type is TRUE_FALSE.
            if answers in ["TRUE", "FALSE", "YES", "NO"] and current["type"] != QuestionType.CHECKBOX:
                current["type"] = QuestionType.TRUE_FALSE
            
            # Handle different answer formats
            if current["type"] == QuestionType.CHECKBOX:
                # Convert text answers to letters if needed
                answer_texts = [a.strip() for a in answers.split(",")]
                answer_letters = []
                for text in answer_texts:
                    # If it's already a letter, use it
                    if len(text) == 1 and text in "ABCD":
                        answer_letters.append(text)
                    else:
                        # Find the choice that contains this text
                        for i, choice in enumerate(current["choices"]):
                            if text.lower() in choice.lower():
                                answer_letters.append(chr(65 + i))  # Convert to A, B, C, D
                                break
                current["correct_answers"] = answer_letters
            elif current["type"] == QuestionType.TRUE_FALSE:
                # For True/False, the answer is the text itself (e.g., "TRUE", "FALSE")
                if answers.upper() in ["TRUE", "FALSE", "YES", "NO"]:
                    # Normalize YES/NO to TRUE/FALSE for consistency if needed by Google Forms
                    if answers.upper() == "YES":
                        current["correct_text"] = "TRUE"
                    elif answers.upper() == "NO":
                        current["correct_text"] = "FALSE"
                    else:
                        current["correct_text"] = answers.upper()
                else:
                    # Or handle as an error/default if the value is unexpected
                    # For now, let's assume it's one of the valid options.
                    current["correct_text"] = answers.upper() # Fallback, might need validation
            else:
                # Handle single answer (convert text to letter if needed for MCQ, etc.)
                if len(answers) == 1 and answers in "ABCD":
                    current["correct_letter"] = answers
                else:
                    # Find the choice that contains this answer
                    for i, choice in enumerate(current["choices"]):
                        if answers.lower() in choice.lower():
                            current["correct_letter"] = chr(65 + i)  # Convert to A, B, C, D
                            break

    # Save the last question if exists
    if current and (current["choices"] or current.get("correct_text") or choice_buffer):
        if choice_buffer:
            current["choices"] = format_choices('\n'.join(choice_buffer))
        questions.append(current)

    # Extract correct answer text
    for q in questions:
        if q["type"] == QuestionType.CHECKBOX:
            q["correct_text"] = [choice[2:].strip() for i, choice in enumerate(q["choices"]) 
                                if chr(65 + i) in q["correct_answers"]]
        else:
            for choice in q["choices"]:
                if choice.startswith(f"{q['correct_letter']}."):
                    q["correct_text"] = choice[2:].strip()
                    break

    return questions