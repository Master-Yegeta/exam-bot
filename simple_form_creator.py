"""
Simple form creator that generates a shareable Google Apps Script
This is a fallback method if the API approach continues to have issues
"""

def generate_apps_script_with_sharing(questions, form_title="Exam Questions"):
    """Generate Google Apps Script that creates and shares a form"""
    
    script = f'''function createAndShareForm() {{
  // Create the form
  var form = FormApp.create("{form_title}");
  var formId = form.getId();
  
  // Set description
  form.setDescription("Auto-generated exam form created by Exam Bot");
  
'''

    # Add questions to script
    for idx, q in enumerate(questions, start=1):
        question_title = q['text'].replace('"', '\\"')
        
        if q["type"].name == "TRUE_FALSE":
            script += f'''
  // Question {idx}: True/False
  var item{idx} = form.addMultipleChoiceItem();
  item{idx}.setTitle("{question_title}")
      .setChoices([
          item{idx}.createChoice("True"),
          item{idx}.createChoice("False")
      ]);
'''

        elif q["type"].name == "MULTIPLE_CHOICE":
            choices_code = []
            for choice in q.get("choices", []):
                if choice.startswith(('A.', 'B.', 'C.', 'D.')):
                    choice_text = choice[2:].strip().replace('"', '\\"')
                else:
                    choice_text = choice.strip().replace('"', '\\"')
                choices_code.append(f'item{idx}.createChoice("{choice_text}")')
            
            choices_str = ',\n          '.join(choices_code)
            
            script += f'''
  // Question {idx}: Multiple Choice
  var item{idx} = form.addMultipleChoiceItem();
  item{idx}.setTitle("{question_title}")
      .setChoices([
          {choices_str}
      ]);
'''

        elif q["type"].name == "CHECKBOX":
            choices_code = []
            for choice in q.get("choices", []):
                if choice.startswith(('A.', 'B.', 'C.', 'D.')):
                    choice_text = choice[2:].strip().replace('"', '\\"')
                else:
                    choice_text = choice.strip().replace('"', '\\"')
                choices_code.append(f'item{idx}.createChoice("{choice_text}")')
            
            choices_str = ',\n          '.join(choices_code)
            
            script += f'''
  // Question {idx}: Checkbox
  var item{idx} = form.addCheckboxItem();
  item{idx}.setTitle("{question_title}")
      .setChoices([
          {choices_str}
      ]);
'''

    # Add sharing and URL generation
    script += '''
  
  // Make the form publicly accessible
  var file = DriveApp.getFileById(formId);
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.EDIT);
  
  // Get URLs
  var editUrl = form.getEditUrl();
  var publishUrl = form.getPublishedUrl();
  
  // Log the results
  Logger.log("✅ Form created successfully!");
  Logger.log("📝 Edit URL: " + editUrl);
  Logger.log("📋 Share URL: " + publishUrl);
  Logger.log("📊 Form ID: " + formId);
  
  // Return the URLs
  return {
    editUrl: editUrl,
    publishUrl: publishUrl,
    formId: formId
  };
}

// Run this function to create your form
createAndShareForm();
'''

    return script
