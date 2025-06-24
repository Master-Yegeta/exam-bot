from parser import QuestionType

def generate_google_form_script(questions):
    if not questions:
        raise ValueError("No questions provided to generate form")

    # Validate questions format
    for q_idx, q_item in enumerate(questions):
        if not isinstance(q_item, dict) or 'type' not in q_item or 'text' not in q_item: # Changed 'question' to 'text'
            raise ValueError(f"Invalid question format for question at index {q_idx}")
    script = '''function createForm() {\n'''
    script += '  var form = FormApp.create("Exam Questions");\n\n'

    for idx, q in enumerate(questions, start=1):
        question_title = q['text'].replace('"', '\\"') # Escape quotes in question title

        script += f"\n  // Question {idx}: {q['type'].name}\n"

        if q["type"] == QuestionType.TRUE_FALSE:
            script += f'''  var item{idx} = form.addMultipleChoiceItem();
  item{idx}.setTitle("{question_title}")
      .setChoices([
          item{idx}.createChoice("True"),
          item{idx}.createChoice("False")
      ])
      .setCorrectAnswers([item{idx}.createAnswer("{q['correct_text']}")]); // Assumes correct_text is "TRUE" or "FALSE"
  \n'''

        elif q["type"] == QuestionType.SHORT_ANSWER:
            script += f'''  var item{idx} = form.addTextItem();
  item{idx}.setTitle("{question_title}");
  \n''' # No explicit correct answer setting in form script for short answer

        elif q["type"] == QuestionType.CHECKBOX:
            # Choices are expected to be like "A. Choice Text", strip prefix for display
            choices_code = ',\n          '.join([f'item{idx}.createChoice("{choice_str[choice_str.find(".") + 1:].strip().replace("\"", "\\\"")}")' for choice_str in q.get("choices", [])])
            
            # Use pre-derived correct_text_list from parser
            correct_answers_texts = q.get("correct_text_list", [])
            correct_answers_code = ',\n          '.join([f'item{idx}.createAnswer("{ans_text.replace("\"", "\\\"")}")' for ans_text in correct_answers_texts])

            script += f'''  var item{idx} = form.addCheckboxItem();
  item{idx}.setTitle("{question_title}")
      .setChoices([
          {choices_code}
      ])
      .setCorrectAnswers([
          {correct_answers_code}
      ]);
  \n'''

        elif q["type"] == QuestionType.DROPDOWN:
            choices_code = ',\n          '.join([f'item{idx}.createChoice("{choice_str[choice_str.find(".") + 1:].strip().replace("\"", "\\\"")}")' for choice_str in q.get("choices", [])])
            # Dropdowns typically don't have a single "correct" answer marked in Google Forms UI in the same way MCQs do.
            # If a correct answer needs to be stored, it might be for grading outside the form.
            # The parser now stores q['correct_text'] for dropdown if a correct answer was specified.
            # However, addListItem().setCorrectAnswers() doesn't exist.
            # If grading/feedback is desired, it would be via item.setFeedbackForCorrect(FormApp.createFeedback().setText("...").build());
            # For now, just creating the dropdown.
            script += f'''  var item{idx} = form.addListItem();
  item{idx}.setTitle("{question_title}")
      .setChoices([
          {choices_code}
      ]);
  \n'''

        else:  # MULTIPLE_CHOICE
            choices_code = ',\n          '.join([f'item{idx}.createChoice("{choice_str[choice_str.find(".") + 1:].strip().replace("\"", "\\\"")}")' for choice_str in q.get("choices", [])])
            
            # Parser now aims to always provide correct_text if a valid correct answer was parsed
            correct_answer_text = q.get("correct_text", "") 
            if not correct_answer_text and q.get("choices"): # Fallback if parser somehow missed it (shouldn't happen)
                correct_answer_text = q["choices"][0][q["choices"][0].find(".") + 1:].strip()
            
            script += f'''  var item{idx} = form.addMultipleChoiceItem();
  item{idx}.setTitle("{question_title}")
      .setChoices([
          {choices_code}
      ])
      .setCorrectAnswers([item{idx}.createAnswer("{correct_answer_text.replace("\"", "\\\"")}")]);
  \n'''

    script += '  Logger.log("Form created: " + form.getEditUrl());\n}'
    return script