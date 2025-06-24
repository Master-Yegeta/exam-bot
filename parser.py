import re
from enum import Enum

class QuestionType(Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    CHECKBOX = "CHECKBOX"
    DROPDOWN = "DROPDOWN"

def detect_question_type(question: str) -> QuestionType:
    """Detect question type from the question text"""
    question_lower = question.lower()
    
    # Check for explicit type markers
    if "[true_false]" in question_lower or "[tf]" in question_lower:
        return QuestionType.TRUE_FALSE
    elif "[short_answer]" in question_lower or "[sa]" in question_lower:
        return QuestionType.SHORT_ANSWER
    elif "[checkbox]" in question_lower or "[cb]" in question_lower:
        return QuestionType.CHECKBOX
    elif "[dropdown]" in question_lower or "[dd]" in question_lower:
        return QuestionType.DROPDOWN
    # Auto-detect based on content
    elif any(kw in question_lower for kw in ["true", "false", "yes", "no"]) and "?" in question:
        return QuestionType.TRUE_FALSE
    else:
        return QuestionType.MULTIPLE_CHOICE

def clean_question_text(question: str) -> str:
    """Remove type markers and numbering from question text"""
    # Remove type markers
    question = re.sub(r'\[(?:TRUE_FALSE|SHORT_ANSWER|CHECKBOX|DROPDOWN|TF|SA|CB|DD)\]\s*', '', question, flags=re.IGNORECASE)
    # Remove question numbering
    question = re.sub(r'^(\d+[\.\)]|Q\d*[\.\:]|Question\s*\d*[\.\:])\s*', '', question, flags=re.IGNORECASE)
    return question.strip()

def parse_inline_choices_bulletproof(text: str) -> list:
    """BULLETPROOF choice parser - handles all formats"""
    if not text:
        return []
    
    print(f"DEBUG: BULLETPROOF parsing: '{text}'")
    
    # Clean the text
    text = text.strip()
    
    # Method 1: Direct regex for A. text B. text C. text D. text
    pattern1 = r'A\.\s*([^B]*?)B\.\s*([^C]*?)C\.\s*([^D]*?)D\.\s*(.*)$'
    match1 = re.search(pattern1, text, re.IGNORECASE | re.DOTALL)
    
    if match1:
        choices = []
        for i, choice_text in enumerate(match1.groups()):
            choice_text = choice_text.strip()
            if choice_text:
                letter = chr(65 + i)  # A, B, C, D
                choices.append(f"{letter}. {choice_text}")
        
        if len(choices) == 4:
            print(f"DEBUG: Method 1 SUCCESS: {choices}")
            return choices
    
    # Method 2: Find all A., B., C., D. patterns individually
    choices = []
    for letter in ['A', 'B', 'C', 'D']:
        # Look for this letter followed by a dot and text
        pattern = rf'{letter}\.\s*([^A-D]*?)(?=[A-D]\.|$)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            choice_text = matches[0].strip()
            # Clean up common artifacts
            choice_text = re.sub(r'\s+', ' ', choice_text)
            choice_text = re.sub(r'[^\w\s\-().,!?]+$', '', choice_text)  # Remove trailing junk
            if choice_text:
                choices.append(f"{letter}. {choice_text}")
    
    if len(choices) >= 2:
        print(f"DEBUG: Method 2 SUCCESS: {choices}")
        return choices
    
    # Method 3: Split by multiple spaces and look for patterns
    parts = re.split(r'\s{2,}', text)
    choices = []
    for part in parts:
        part = part.strip()
        match = re.match(r'^([A-D])\.\s*(.+)', part, re.IGNORECASE)
        if match:
            letter, choice_text = match.groups()
            choice_text = choice_text.strip()
            if choice_text:
                choices.append(f"{letter.upper()}. {choice_text}")
    
    if len(choices) >= 2:
        print(f"DEBUG: Method 3 SUCCESS: {choices}")
        return choices
    
    # Method 4: Manual extraction for your specific format
    # Handle: "A. Isaac Newton  B. Albert Einstein  C. Galileo Galilei  D. Nikola Tesla"
    if 'A.' in text and 'B.' in text:
        # Find positions of each letter
        positions = {}
        for letter in ['A', 'B', 'C', 'D']:
            pos = text.find(f'{letter}.')
            if pos != -1:
                positions[letter] = pos
        
        # Sort by position
        sorted_letters = sorted(positions.keys(), key=lambda x: positions[x])
        
        choices = []
        for i, letter in enumerate(sorted_letters):
            start_pos = positions[letter] + 2  # Skip "A."
            
            # Find end position (next letter or end of string)
            if i + 1 < len(sorted_letters):
                next_letter = sorted_letters[i + 1]
                end_pos = positions[next_letter]
            else:
                end_pos = len(text)
            
            choice_text = text[start_pos:end_pos].strip()
            if choice_text:
                choices.append(f"{letter}. {choice_text}")
        
        if len(choices) >= 2:
            print(f"DEBUG: Method 4 SUCCESS: {choices}")
            return choices
    
    print(f"DEBUG: ALL METHODS FAILED for: '{text}'")
    return []

def extract_answer_key(text: str) -> dict:
    """Extract answer key from text like 'Answer Key: 1. B 2. C 3. B'"""
    answers = {}
    
    # Look for answer key section
    answer_key_match = re.search(r'Answer\s+Key\s*:?\s*(.*)', text, re.IGNORECASE | re.DOTALL)
    if answer_key_match:
        answer_section = answer_key_match.group(1)
        print(f"DEBUG: Found answer section: {answer_section}")
        
        # Parse individual answers like "1. B", "2. C", etc.
        answer_matches = re.findall(r'(\d+)\.\s*([A-D])', answer_section, re.IGNORECASE)
        for q_num, answer_letter in answer_matches:
            answers[int(q_num)] = answer_letter.upper()
            print(f"DEBUG: Question {q_num} -> Answer {answer_letter}")
    
    return answers

def parse_questions(text: str):
    if not text or not isinstance(text, str):
        raise ValueError("Input must be a non-empty string")

    # Clean input text
    text = text.strip()
    if not text:
        raise ValueError("Input contains no valid questions")

    print(f"DEBUG: Starting to parse text with {len(text)} characters")

    # Extract answer key first
    answer_key = extract_answer_key(text)
    print(f"DEBUG: Extracted answer key: {answer_key}")

    # Remove answer key section from text to avoid confusion
    text_without_answers = re.sub(r'Answer\s+Key\s*:.*$', '', text, flags=re.IGNORECASE | re.DOTALL).strip()

    # Split by numbered questions (1., 2., 3., etc.)
    question_pattern = r'\n\s*(\d+)\.\s*'
    parts = re.split(question_pattern, text_without_answers)
    
    print(f"DEBUG: Split into {len(parts)} parts")
    
    questions = []
    
    # Skip the first part (usually intro text like "Example layout:")
    i = 1
    while i < len(parts) - 1:
        question_num = parts[i]
        question_content = parts[i + 1]
        
        print(f"DEBUG: ===== PROCESSING QUESTION {question_num} =====")
        print(f"DEBUG: Raw content: '{question_content}'")
        
        # Split question content into lines
        lines = [line.strip() for line in question_content.strip().split('\n') if line.strip()]
        if not lines:
            i += 2
            continue
        
        # First line is the question text
        question_text = lines[0].strip()
        print(f"DEBUG: Question text: '{question_text}'")
        
        # Combine all remaining lines for choice parsing
        choice_lines = lines[1:] if len(lines) > 1 else []
        combined_choice_text = ' '.join(choice_lines)
        
        print(f"DEBUG: Combined choice text: '{combined_choice_text}'")
        
        # Use bulletproof parser
        choices = parse_inline_choices_bulletproof(combined_choice_text)
        
        # If still no choices, create default ones
        if not choices:
            print("DEBUG: BULLETPROOF PARSER FAILED - Using defaults")
            choices = [
                "A. Option 1",
                "B. Option 2", 
                "C. Option 3",
                "D. Option 4"
            ]
        
        print(f"DEBUG: Final choices for question {question_num}: {choices}")
        
        # Create question object
        q_type = detect_question_type(question_text)
        question_obj = {
            "text": question_text,
            "type": q_type,
            "choices": choices,
            "correct_letter": "",
            "correct_text": "",
            "correct_answers": []
        }
        
        # Add correct answer if available
        q_num = int(question_num)
        if q_num in answer_key:
            correct_letter = answer_key[q_num]
            question_obj["correct_letter"] = correct_letter
            
            # Find the correct text
            for choice in choices:
                if choice.startswith(f"{correct_letter}."):
                    question_obj["correct_text"] = choice[2:].strip()
                    break
        
        questions.append(question_obj)
        print(f"DEBUG: ===== QUESTION {question_num} COMPLETE =====\n")
        
        i += 2  # Move to next question

    print(f"DEBUG: Final result: {len(questions)} questions parsed")

    if not questions:
        raise ValueError("No valid questions found in the input")

    return questions

def format_choices(text: str) -> list:
    """Convert unformatted choices into properly formatted ones."""
    if not text or not isinstance(text, str):
        return []

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    choices = []
    letters = ['A', 'B', 'C', 'D']
    
    for i, line in enumerate(lines):
        if not line:
            continue
        # Remove any existing numbering or lettering
        clean_line = re.sub(r'^[A-Da-d1-9][\.\)\-]\s*', '', line).strip()
        if i < len(letters) and clean_line:
            choices.append(f"{letters[i]}. {clean_line}")
    
    return choices

def extract_answers_from_text(text: str) -> dict:
    """Extract answers that might be separated from questions"""
    answer_patterns = [
        r'answer[s]?\s*:?\s*([^\n]+)',
        r'correct\s*:?\s*([^\n]+)',
        r'ans\s*:?\s*([^\n]+)',
        r'solution\s*:?\s*([^\n]+)',
        r'key\s*:?\s*([^\n]+)'
    ]
    
    answers = {}
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Look for question numbers followed by answers
        question_match = re.match(r'^(\d+)[\.\)\-\s]*(.+)', line_lower)
        if question_match:
            q_num = int(question_match.group(1))
            answer_text = question_match.group(2).strip()
            
            # Check if this looks like an answer
            for pattern in answer_patterns:
                if re.search(pattern, answer_text, re.IGNORECASE):
                    answer_content = re.sub(pattern, '', answer_text, flags=re.IGNORECASE).strip()
                    if answer_content:
                        answers[q_num] = answer_content
                    break
            else:
                # Direct answer format like "1. A" or "1. True"
                if len(answer_text) <= 10:  # Short answers are likely answer keys
                    answers[q_num] = answer_text
    
    return answers
