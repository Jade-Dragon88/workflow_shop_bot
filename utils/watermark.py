import json
import os
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo # For timezone-aware timestamps
import logging

from config import WATERMARKED_DIR

def add_watermark_to_workflow(
    original_filepath: str,
    slug: str,
    user_id: int,
    username: str,
    payment_id: str,
    workflow_version: str
) -> str | None:
    """
    Adds a watermark to a workflow JSON file.

    Args:
        original_filepath: Path to the original workflow file.
        slug: The unique slug of the workflow.
        user_id: The Telegram ID of the user.
        username: The Telegram username of the user.
        payment_id: The payment charge ID from Telegram.
        workflow_version: The version of the workflow being purchased.

    Returns:
        The path to the watermarked file, or None if an error occurred.
    """
    try:
        with open(original_filepath, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)

        # 1. Add the 'license' section
        workflow_data['license'] = {
            "purchased_by": f"TG_USER_ID_{user_id}",
            "username": f"@{username}",
            "purchase_date": datetime.now().isoformat(),
            "payment_id": payment_id,
            "update_token": uuid.uuid4().hex,
            "version": workflow_version,
        }

        # 2. Create a unique, human-readable filename and save the watermarked file
        now_msk = datetime.now(ZoneInfo("Europe/Moscow"))
        time_str = now_msk.strftime("%Y-%m-%d_%H-%M-%S")
        watermarked_filename = f"{user_id}_{slug}_{time_str}.json"
        watermarked_filepath = os.path.join(WATERMARKED_DIR, watermarked_filename)

        # Ensure the watermarked directory exists
        os.makedirs(WATERMARKED_DIR, exist_ok=True)

        with open(watermarked_filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow_data, f, indent=4, ensure_ascii=False)
        
        logging.info(f"Successfully created watermarked file: {watermarked_filepath}")
        return watermarked_filepath

    except FileNotFoundError:
        logging.error(f"Original workflow file not found at: {original_filepath}")
        return None
    except Exception as e:
        logging.error(f"Failed to add watermark to {original_filepath}: {e}", exc_info=True)
        return None
