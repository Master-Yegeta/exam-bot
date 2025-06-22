from parser import QuestionType

def generate_google_form_script(questions):
    if not questions:
        raise ValueError("No questions provided to generate form")

    # Validate questions format
    for q in questions:
        if not isinstance(q, dict) or 'type' not in q or 'question' not in q:
            raise ValueError("Invalid question format")
    script = '''function createForm() {\n'''
    script += '  var form = FormApp.create("Exam Questions");\n\n'

    for idx, q in enumerate(questions, start=1):
        script += f"\n  // Question {idx}\n"

        if q["type"] == QuestionType.TRUE_FALSE:
            script += f'''  var item{idx} = form.addMultipleChoiceItem();
  item{idx}.setTitle("{q['question']}")
      .setChoices([
          item{idx}.createChoice("True"),
          item{idx}.createChoice("False")
      ])
      .setCorrectAnswers([item{idx}.createAnswer("{q['correct_letter']}")]);
  \n'''

        elif q["type"] == QuestionType.SHORT_ANSWER:
            script += f'''  var item{idx} = form.addTextItem();
  item{idx}.setTitle("{q['question']}");
  \n'''

        elif q["type"] == QuestionType.CHECKBOX:
            choices_code = ',\n          '.join([f'item{idx}.createChoice("{c[2:].strip()}")' for c in q["choices"]])
            correct_answers = [next(c[2:].strip() for c in q["choices"] if c.startswith(f"{letter}.")) for letter in q["correct_answers"]]
            correct_answers_code = ',\n          '.join([f'item{idx}.createAnswer("{ans}")' for ans in correct_answers])

            script += f'''  var item{idx} = form.addCheckboxItem();
  item{idx}.setTitle("{q['question']}")
      .setChoices([
          {choices_code}
      ])
      .setCorrectAnswers([
          {correct_answers_code}
      ]);
  \n'''

        elif q["type"] == QuestionType.DROPDOWN:
            choices_code = ',\n          '.join([f'item{idx}.createChoice("{c[2:].strip()}")' for c in q["choices"]])
            script += f'''  var item{idx} = form.addListItem();
  item{idx}.setTitle("{q['question']}")
      .setChoices([
          {choices_code}
      ]);
  \n'''

        else:  # MULTIPLE_CHOICE
            choices_code = ',\n          '.join([f'item{idx}.createChoice("{c[2:].strip()}")' for c in q["choices"]])
            correct_answer = q["correct_text"] if q["correct_text"] else q["choices"][0][2:].strip()
            script += f'''  var item{idx} = form.addMultipleChoiceItem();
  item{idx}.setTitle("{q['question']}")
      .setChoices([
          {choices_code}
      ])
      .setCorrectAnswers([item{idx}.createAnswer("{correct_answer}")]);
  \n'''

    script += '  Logger.log("Form created: " + form.getEditUrl());\n}'
    return script