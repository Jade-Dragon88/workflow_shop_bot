import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.supabase_http_client import supabase_http_client
from database.models import Workflow
from keyboards.inline import get_catalog_keyboard, get_workflow_card_keyboard

router = Router()

async def get_workflows_from_db(priority: int = None) -> list[Workflow]:
    """
    Fetches a list of active workflows from the database.
    Can be filtered by priority.
    """
    params = {"is_active": "eq.true", "order": "priority.asc,name.asc"}
    if priority:
        params["priority"] = f"eq.{priority}"
    
    try:
        response = await supabase_http_client.select(table="workflows", params=params)
        workflows = [Workflow(**wf) for wf in response]
        return workflows
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
async def show_catalog_menu(callback: CallbackQuery, priority: int = None):
    """
    Handles the 'catalog_menu' callback, showing the list of workflows.
    Can optionally show filtered workflows based on priority.
    """
    await callback.answer()
    
    workflows = await get_workflows_from_db(priority)
    
    if not workflows:
        text = "Каталог пока пуст. Скоро здесь появятся новые workflows!"
        if priority:
            text = f"Workflows с приоритетом {priority} пока нет."
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
            ])
        )
        return

    catalog_text = "🗂️ **Каталог Workflows**\n\nВыберите интересующий вас workflow:"
    
    await callback.message.edit_text(
        text=catalog_text,
        reply_markup=get_catalog_keyboard(workflows)
    )

@router.callback_query(F.data.startswith("filter_priority:"))
async def filter_workflows_by_priority(callback: CallbackQuery):
    """
    Handles filtering workflows by priority.
    """
    await callback.answer()
    filter_value = callback.data.split(":")[1]
    
    priority_filter = None
    if filter_value != "all":
        try:
            priority_filter = int(filter_value)
        except ValueError:
            logging.error(f"Invalid priority filter value: {filter_value}")
            # Fallback to showing all if filter is invalid
            pass

    workflows = await get_workflows_from_db(priority_filter)
    
    if not workflows:
        text = "К сожалению, workflows по выбранному фильтру не найдены."
        await callback.message.edit_text(
            text,
            reply_markup=get_catalog_keyboard(workflows=[]) # Pass empty list to ensure only nav buttons
        )
        return

    catalog_text = "🗂️ **Каталог Workflows**\n\n"
    if priority_filter:
        catalog_text += f"Показаны workflows с приоритетом {priority_filter}:\n\n"
    else:
        catalog_text += "Все доступные workflows:\n\n"
    
    await callback.message.edit_text(
        text=catalog_text,
        reply_markup=get_catalog_keyboard(workflows)
    )

@router.callback_query(F.data.startswith("workflow:"))
async def show_workflow_card(callback: CallbackQuery):
    """
    Handles a click on a specific workflow, showing its details card.
    """
    await callback.answer()
    slug = callback.data.split(":")[1]
    
    workflow = await get_workflow_by_slug(slug)
    
    if not workflow:
        await callback.message.edit_text(
            "😔 К сожалению, этот workflow не найден. Возможно, он был удален.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="catalog_menu")]
            ])
        )
        return
        
    card_text = (
        f"📄 **{workflow.name}**\n\n"
        f"<b>Описание:</b> {workflow.description}\n\n"
        f"<b>Версия:</b> {workflow.version}\n"
        f"<b>Цена:</b> {workflow.price:.0f}₽"
    )
    
    await callback.message.edit_text(
        text=card_text,
        reply_markup=get_workflow_card_keyboard(slug, workflow.price)
    )
