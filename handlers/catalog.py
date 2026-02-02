import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.supabase_http_client import supabase_http_client
from database.models import Workflow

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

def get_catalog_keyboard(workflows: list[Workflow]) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard with a list of workflows.
    """
    buttons = []
    for wf in workflows:
        # Each workflow gets its own button
        button_text = f"{wf.name} - {wf.price:.0f}₽"
        callback_data = f"workflow:{wf.slug}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    # Add navigation buttons
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "catalog_menu")
async def show_catalog_menu(callback: CallbackQuery):
    """
    Handles the 'catalog_menu' callback, showing the list of workflows.
    """
    await callback.answer() # Acknowledge the callback
    
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
