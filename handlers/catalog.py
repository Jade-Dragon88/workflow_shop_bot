import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.supabase_http_client import supabase_http_client
from database.models import Workflow
from keyboards.inline import get_catalog_keyboard, get_workflow_card_keyboard # Import new keyboard

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
async def show_catalog_menu(callback: CallbackQuery, **kwargs):
    """
    Handles the 'catalog_menu' callback, showing the list of workflows.
    """
    await callback.answer()
    
    workflows = await get_workflows_from_db()
    
    if not workflows:
        await callback.message.edit_text(
            "Каталог пока пуст. Скоро здесь появятся новые workflows!",
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