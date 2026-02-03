import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from database.supabase_http_client import supabase_http_client
from database.models import Workflow
# Import both keyboard functions
from keyboards.inline import get_main_catalog_keyboard, get_filtered_catalog_keyboard, get_workflow_card_keyboard

router = Router()

async def get_workflows_from_db(priority: int = None) -> list[Workflow]:
    """
    Fetches a list of active workflows from the database.
    """
    params = {"is_active": "eq.true", "order": "priority.asc,name.asc"}
    if priority:
        params["priority"] = f"eq.{priority}"
    
    try:
        response = await supabase_http_client.select(table="workflows", params=params)
        return [Workflow(**wf) for wf in response]
    except Exception as e:
        logging.error(f"Error fetching workflows from DB: {e}", exc_info=True)
        return []
        
async def get_workflow_by_slug(slug: str) -> Workflow | None:
    """
    Fetches a single workflow by its unique slug.
    """
    try:
        params = {"slug": f"eq.{slug}", "select": "*", "limit": 1}
        response = await supabase_http_client.select(table="workflows", params=params)
        if response:
            return Workflow(**response[0])
        return None
    except Exception as e:
        logging.error(f"Error fetching workflow by slug '{slug}': {e}", exc_info=True)
        return None

@router.callback_query(F.data == "catalog_menu")
async def show_catalog_menu(callback: CallbackQuery, **kwargs):
    """
    Shows the main catalog view with filter buttons (categories).
    """
    await callback.answer()
    
    catalog_text = "🗂️ **Каталог Workflows**\n\nВыберите категорию:"

    try:
        # Use the keyboard with filters (categories) here
        await callback.message.edit_text(
            text=catalog_text,
            reply_markup=get_main_catalog_keyboard()
        )
    except TelegramBadRequest:
        logging.warning("Tried to edit message with the same content in show_catalog_menu.")

@router.callback_query(F.data.startswith("filter_priority:"))
async def filter_workflows_by_priority(callback: CallbackQuery):
    """
    Shows a filtered list of workflows without filter buttons.
    """
    await callback.answer()
    filter_value = callback.data.split(":")[1]
    
    priority_filter = None
    if filter_value != "all":
        try:
            priority_filter = int(filter_value)
        except ValueError:
            logging.error(f"Invalid priority filter value: {filter_value}")
            pass

    workflows = await get_workflows_from_db(priority_filter)
    
    catalog_text = ""
    if priority_filter == 1:
        catalog_text = "❗️ **Крайне важные**\n\n"
    elif priority_filter == 2:
        catalog_text = "👍 **Рекомендуемые**\n\n"
    elif priority_filter == 3:
        catalog_text = "ℹ️ **Общая информация**\n\n"
    else:
        catalog_text = "🗂️ **Все Workflows**\n\n"

    if not workflows:
        catalog_text += "В этой категории пока нет workflows."
    else:
        catalog_text += "Выберите интересующий вас workflow:"

    try:
        # Use the keyboard WITHOUT filters here
        await callback.message.edit_text(
            text=catalog_text,
            reply_markup=get_filtered_catalog_keyboard(workflows)
        )
    except TelegramBadRequest:
        logging.warning("Tried to edit message with the same content in filter_workflows_by_priority.")

@router.callback_query(F.data.startswith("workflow:"))
async def show_workflow_card(callback: CallbackQuery):
    """
    Shows the details card for a specific workflow.
    """
    await callback.answer()
    slug = callback.data.split(":")[1]
    
    workflow = await get_workflow_by_slug(slug)
    
    if not workflow:
        # Simplified error message handling
        await callback.answer("😔 К сожалению, этот workflow не найден.", show_alert=True)
        return
        
    card_text = (
        f"📄 **{workflow.name}**\n\n"
        f"<b>Описание:</b> {workflow.description}\n\n"
        f"<b>Версия:</b> {workflow.version}\n"
        f"<b>Цена:</b> {workflow.price:.0f}₽"
    )
    
    try:
        await callback.message.edit_text(
            text=card_text,
            reply_markup=get_workflow_card_keyboard(slug, workflow.price)
        )
    except TelegramBadRequest:
        logging.warning("Tried to edit message with the same content in show_workflow_card.")
