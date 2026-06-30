"""
classifier/scanner.py
─────────────────────────────────────────────────────────────
Document Scanner — uses a HuggingFace vision-language model to:
  1. OCR the image (extract all text)
  2. Identify document type
  3. Extract key metadata (date, from, to, subject/re)
  4. Detect internal vs external communication
  5. Suggest priority from content

Requires:
  HF_API_TOKEN — HuggingFace API token (set in .env)
  HF_MODEL     — defaults to Qwen/Qwen2.5-VL-7B-Instruct

No tesseract installation needed.
Works with photos of physical letters, printed forms, or scanned PDFs.
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

SCAN_PROMPT = """You are an expert document analyst for Apayao State College (ASC) in the Philippines.

A staff member has photographed or scanned a document. Your job is to:
1. Extract ALL text from the image (OCR)
2. Identify what type of document it is
3. Extract key metadata
4. Determine if it's internal (between ASC offices) or external (from/to outside organizations)
5. Suggest a title and priority

Respond ONLY with a valid JSON object — no markdown, no explanation, no code fences. Use this exact structure:

{
  "extracted_text": "full text from the document",
  "suggested_title": "short descriptive title (max 100 chars)",
  "doc_type": one of ["Memorandum","Request Letter","Report","Research Proposal","Certificate","Purchase Request","Travel Order","Leave Form","Complaint","Grievance","Communication Letter","Other"],
  "comm_type": one of ["internal","external","n/a"],
  "comm_type_reason": "brief explanation of why internal or external",
  "priority": one of ["low","normal","high","urgent"],
  "priority_reason": "brief explanation",
  "confidence": float between 0 and 1,
  "metadata": {
    "date": "date found in document or null",
    "from": "sender name/office or null",
    "to": "recipient name/office or null",
    "subject": "subject/re line or null",
    "reference_number": "document number if any or null",
    "signatories": ["list of people who signed"]
  },
  "summary": "2-3 sentence plain English summary of what this document is about",
  "is_readable": true or false,
  "low_quality_note": "if image is blurry/unreadable, explain here, otherwise empty string"
}

Rules for comm_type:
- "internal" = document is between ASC offices, departments, or personnel
- "external" = document involves entities outside ASC (DepEd, CHED, LGU, suppliers, other schools, etc.)
- "n/a" = not a communication letter (e.g. reports, proposals, purchase requests)

Rules for doc_type:
- "Memorandum" = official memo, office order, circular from within ASC
- "Communication Letter" = formal letter (internal or external)
- "Complaint" = complaint or grievance letter
- Use context clues from the letterhead, salutation, and content.
"""


def scan_document(image_data: str, media_type: str = 'image/jpeg') -> dict:
    """
    Scan a document image using a HuggingFace vision-language model.

    Args:
        image_data: base64-encoded image string
        media_type: 'image/jpeg', 'image/png', 'image/webp', or 'image/gif'

    Returns:
        dict with extracted_text, suggested_title, doc_type, comm_type,
        priority, metadata, summary, confidence
    """
    hf_token = os.getenv('HF_API_TOKEN', '')
    hf_model = os.getenv('HF_MODEL', 'Qwen/Qwen2.5-VL-7B-Instruct')

    if not hf_token:
        logger.error('HF_API_TOKEN is not configured.')
        return _error_result('Document scanning is not configured. Contact the system administrator.')

    try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(api_key=hf_token)

        response = client.chat.completions.create(
            model=hf_model,
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:{media_type};base64,{image_data}',
                            },
                        },
                        {
                            'type': 'text',
                            'text': SCAN_PROMPT,
                        },
                    ],
                }
            ],
            max_tokens=2000,
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model added them anyway
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        raw = raw.strip().rstrip('`').strip()

        result = json.loads(raw)

        # Run local TF-IDF classifier as a second opinion
        from classifier.service import classify_document

        class _FakeDoc:
            def __init__(self, title, text):
                self.title       = title
                self.description = text[:500]

        local_label, local_conf = classify_document(
            _FakeDoc(
                result.get('suggested_title', ''),
                result.get('extracted_text', ''),
            )
        )

        result['local_ai_label']      = local_label
        result['local_ai_confidence'] = round(local_conf, 2)

        # Note when local classifier strongly disagrees with the vision model
        if local_label != result.get('doc_type') and local_conf > 0.75:
            result['classification_note'] = (
                f'Local classifier suggests "{local_label}" ({local_conf:.0%}) — '
                f'Vision model suggests "{result.get("doc_type")}". Records staff should verify.'
            )

        return result

    except json.JSONDecodeError as e:
        logger.error(f'Scanner JSON parse error: {e}')
        return _error_result('Could not parse the AI response. Please try again.')
    except Exception as e:
        logger.error(f'Scanner error: {e}')
        return _error_result('Document scan failed. Please try again.')


def _error_result(msg: str) -> dict:
    return {
        'extracted_text':   '',
        'suggested_title':  '',
        'doc_type':         'Other',
        'comm_type':        'n/a',
        'priority':         'normal',
        'confidence':       0.0,
        'metadata':         {},
        'summary':          '',
        'is_readable':      False,
        'low_quality_note': msg,
        'error':            msg,
    }
