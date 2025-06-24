"""
FIXED Google Apps Script generator - Multi-message approach
"""

def generate_simple_apps_script(questions, form_title="Exam Questions"):
    """Generate a working Google Apps Script - optimized for length"""
    
    safe_title = form_title.replace('"', '\\"')
    
    # Filter only MCQ questions
    mcq_questions = [q for q in questions if q["type"].name == "MULTIPLE_CHOICE"]
    
    script = f'''function createForm() {{
  var form = FormApp.create("{safe_title}");
  form.setDescription("Created by @Anon_0x1");
  form.setIsQuiz(true);
  
'''

    # Add questions - COMPACT but complete
    for idx, q in enumerate(mcq_questions, start=1):
        question_text = q['text'].replace('"', '\\"').replace('\n', ' ')
        choices = q.get("choices", [])
        correct_letter = q.get("correct_letter", "")
        
        script += f'''  var q{idx} = form.addMultipleChoiceItem();
  q{idx}.setTitle("{question_text}").setRequired(true).setPoints(1);
  var choices{idx} = ['''
        
        # Add choices and track correct one
        choice_parts = []
        correct_index = -1
        
        for i, choice in enumerate(choices):
            if choice.startswith(('A.', 'B.', 'C.', 'D.')):
                choice_letter = choice[0]
                choice_text = choice[2:].strip().replace('"', '\\"')
            else:
                choice_text = choice.strip().replace('"', '\\"')
                choice_letter = chr(65 + i)
            
            if choice_text:
                choice_parts.append(f'q{idx}.createChoice("{choice_text}")')
                if correct_letter and choice_letter.upper() == correct_letter.upper():
                    correct_index = i
        
        script += ', '.join(choice_parts)
        script += f'''];
  q{idx}.setChoices(choices{idx});'''
        
        # Add correct answer feedback if available
        if correct_index >= 0:
            script += f'''
  choices{idx}[{correct_index}].setFeedback(FormApp.createFeedback().setText("✅ Correct!").build());'''
        
        script += f'''
'''

    # Simple ending
    script += f'''  
  DriveApp.getFileById(form.getId()).setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  Logger.log("Edit: " + form.getEditUrl());
  Logger.log("Share: " + form.getPublishedUrl());
  return form.getPublishedUrl();
}}

createForm();'''

    return script

def split_script_into_parts(script, max_length=3000):
    """Split script into manageable parts for Telegram"""
    if len(script) <= max_length:
        return [script]
    
    parts = []
    lines = script.split('\n')
    current_part = ""
    
    for line in lines:
        if len(current_part + line + '\n') > max_length:
            if current_part:
                parts.append(current_part.strip())
                current_part = line + '\n'
            else:
                # Line too long, force split
                parts.append(line)
        else:
            current_part += line + '\n'
    
    if current_part.strip():
        parts.append(current_part.strip())
    
    return parts
