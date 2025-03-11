from openai import OpenAI
from typing import Dict, Any, List
import json
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AIFieldMapper:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def map_fields(
        self, user_metadata: Dict[str, Any], form_fields: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Map user metadata to form fields using AI."""
        try:
            # Construct the prompt
            prompt = self._construct_mapping_prompt(user_metadata, form_fields)

            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at mapping job application data and answering application questions.
                    You will receive user metadata and form fields, and you should:
                    1. Map the user data to the appropriate form fields
                    2. Generate appropriate responses for questions not covered by the metadata
                    3. Return the results in a valid JSON format
                    Be professional and honest in generating responses.""",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            # Parse the response
            response = completion.choices[0].message.content
            mapped_fields = json.loads(response)
            return mapped_fields

        except Exception as e:
            logger.error(f"Error in AI field mapping: {str(e)}")
            return {}

    def _construct_mapping_prompt(
        self, user_metadata: Dict[str, Any], form_fields: List[Dict[str, Any]]
    ) -> str:
        """Construct the prompt for the AI."""
        return f"""
        I have a user's job application metadata and a form with specific fields and questions.
        Please help map the data and generate appropriate responses.

        User Metadata:
        {json.dumps(user_metadata, indent=2)}

        Form Fields and Questions:
        {json.dumps(form_fields, indent=2)}

        Please provide a JSON response that:
        1. Maps user data to form fields where applicable
        2. Generates appropriate responses for questions not covered by the metadata
        3. Follows the exact format of the form fields

        Format the response as a JSON object where:
        - Keys are the field names from the form
        - Values are either mapped data from user metadata or generated responses
        - Include explanations for generated responses in a separate "explanations" field

        Example format:
        {{
            "mapped_fields": {{
                "field_name": "mapped_or_generated_value"
            }},
            "explanations": {{
                "field_name": "explanation for generated value"
            }}
        }}
        """
