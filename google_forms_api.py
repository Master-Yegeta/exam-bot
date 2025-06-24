import json
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from parser import QuestionType

# Google Forms API scopes - Added Drive scope for sharing
SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/forms.responses.readonly',
    'https://www.googleapis.com/auth/drive'
]

def create_google_form(questions, form_title="Exam Questions", user_email=None):
    """Create a Google Form using the Google Forms API"""
    try:
        # Load service account credentials
        if os.path.exists('service_account.json'):
            credentials = Credentials.from_service_account_file(
                'service_account.json', scopes=SCOPES)
        elif os.path.exists('exambot-155879-f9462666942b-424FWb4IpPapkTPtywk8rzWghfqH73.json'):
            credentials = Credentials.from_service_account_file(
                'exambot-155879-f9462666942b-424FWb4IpPapkTPtywk8rzWghfqH73.json', scopes=SCOPES)
        else:
            # Fallback to environment variable
            creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if creds_json:
                credentials = Credentials.from_service_account_info(
                    json.loads(creds_json), scopes=SCOPES)
            else:
                raise ValueError("No Google service account credentials found")

        # Build the Forms API service
        service = build('forms', 'v1', credentials=credentials)
        # Build Drive API service for sharing
        drive_service = build('drive', 'v3', credentials=credentials)

        # Step 1: Create the form with ONLY title
        form_body = {
            "info": {
                "title": form_title
            }
        }

        print(f"Creating form with title: {form_title}")

        # Create the form
        result = service.forms().create(body=form_body).execute()
        form_id = result['formId']
        form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
        response_url = f"https://docs.google.com/forms/d/{form_id}/viewform"

        print(f"Form created successfully with ID: {form_id}")

        # Step 2: Share the form with anyone (make it publicly editable by the creator)
        try:
            # Make the form publicly viewable and allow anyone with link to edit
            permission_body = {
                'type': 'anyone',
                'role': 'writer'  # This allows editing
            }
            
            drive_service.permissions().create(
                fileId=form_id,
                body=permission_body
            ).execute()
            
            print("Form shared successfully - anyone with link can edit")
            
        except Exception as e:
            print(f"Warning: Could not share form publicly: {e}")
            # Try alternative sharing method
            try:
                permission_body = {
                    'type': 'anyone',
                    'role': 'reader'  # At least make it viewable
                }
                
                drive_service.permissions().create(
                    fileId=form_id,
                    body=permission_body
                ).execute()
                
                print("Form made publicly viewable")
                
            except Exception as e2:
                print(f"Warning: Could not share form at all: {e2}")

        # Step 3: Add description using batchUpdate
        description_request = {
            "requests": [{
                "updateFormInfo": {
                    "info": {
                        "description": "Auto-generated exam form created by Exam Bot"
                    },
                    "updateMask": "description"
                }
            }]
        }

        try:
            service.forms().batchUpdate(
                formId=form_id, 
                body=description_request
            ).execute()
            print("Description added successfully")
        except Exception as e:
            print(f"Warning: Could not add description: {e}")

        # Step 4: Add questions using batchUpdate
        if questions:
            requests = []
            
            for idx, question in enumerate(questions):
                print(f"Processing question {idx + 1}: {question['text'][:50]}...")
                
                # Create the base question item
                question_item = {
                    "createItem": {
                        "item": {
                            "title": question['text'],
                            "questionItem": {
                                "question": {
                                    "required": True
                                }
                            }
                        },
                        "location": {
                            "index": idx
                        }
                    }
                }

                # Configure question type
                if question["type"] == QuestionType.MULTIPLE_CHOICE:
                    choices = []
                    for choice in question.get("choices", []):
                        if choice.startswith(('A.', 'B.', 'C.', 'D.')):
                            choice_text = choice[2:].strip()
                        else:
                            choice_text = choice.strip()
                        choices.append({"value": choice_text})
                    
                    question_item["createItem"]["item"]["questionItem"]["question"]["choiceQuestion"] = {
                        "type": "RADIO",
                        "options": choices
                    }

                elif question["type"] == QuestionType.TRUE_FALSE:
                    question_item["createItem"]["item"]["questionItem"]["question"]["choiceQuestion"] = {
                        "type": "RADIO",
                        "options": [
                            {"value": "True"},
                            {"value": "False"}
                        ]
                    }

                elif question["type"] == QuestionType.CHECKBOX:
                    choices = []
                    for choice in question.get("choices", []):
                        if choice.startswith(('A.', 'B.', 'C.', 'D.')):
                            choice_text = choice[2:].strip()
                        else:
                            choice_text = choice.strip()
                        choices.append({"value": choice_text})
                    
                    question_item["createItem"]["item"]["questionItem"]["question"]["choiceQuestion"] = {
                        "type": "CHECKBOX",
                        "options": choices
                    }

                elif question["type"] == QuestionType.DROPDOWN:
                    choices = []
                    for choice in question.get("choices", []):
                        if choice.startswith(('A.', 'B.', 'C.', 'D.')):
                            choice_text = choice[2:].strip()
                        else:
                            choice_text = choice.strip()
                        choices.append({"value": choice_text})
                    
                    question_item["createItem"]["item"]["questionItem"]["question"]["choiceQuestion"] = {
                        "type": "DROP_DOWN",
                        "options": choices
                    }

                elif question["type"] == QuestionType.SHORT_ANSWER:
                    question_item["createItem"]["item"]["questionItem"]["question"]["textQuestion"] = {
                        "paragraph": False
                    }

                requests.append(question_item)

            # Execute batch update to add all questions
            if requests:
                batch_update_body = {"requests": requests}
                print(f"Adding {len(requests)} questions to form...")
                
                service.forms().batchUpdate(
                    formId=form_id, 
                    body=batch_update_body
                ).execute()
                
                print("Questions added successfully!")

        return {
            "form_id": form_id,
            "edit_url": form_url,
            "response_url": response_url,
            "success": True
        }

    except HttpError as error:
        print(f"Google Forms API error: {error}")
        return {
            "success": False,
            "error": f"Google Forms API error: {str(error)}"
        }
    except Exception as error:
        print(f"Unexpected error: {error}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(error)}"
        }

def get_form_responses(form_id):
    """Get responses from a Google Form"""
    try:
        if os.path.exists('service_account.json'):
            credentials = Credentials.from_service_account_file(
                'service_account.json', scopes=SCOPES)
        elif os.path.exists('exambot-155879-f9462666942b-424FWb4IpPapkTPtywk8rzWghfqH73.json'):
            credentials = Credentials.from_service_account_file(
                'exambot-155879-f9462666942b-424FWb4IpPapkTPtywk8rzWghfqH73.json', scopes=SCOPES)
        else:
            creds_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if creds_json:
                credentials = Credentials.from_service_account_info(
                    json.loads(creds_json), scopes=SCOPES)
            else:
                raise ValueError("No Google service account credentials found")

        service = build('forms', 'v1', credentials=credentials)
        
        # Get form responses
        result = service.forms().responses().list(formId=form_id).execute()
        return result.get('responses', [])
        
    except Exception as error:
        print(f"Error getting form responses: {error}")
        return []
