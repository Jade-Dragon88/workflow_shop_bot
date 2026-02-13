import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from handlers.catalog import get_workflows_from_db # To get workflows for selection

from config import ADMIN_IDS
from keyboards.inline import get_admin_panel_keyboard
from database.supabase_http_client import supabase_http_client

router = Router()

IS_ADMIN = F.from_user.id.in_(ADMIN_IDS)

# --- FSM States for Banning a User ---
class BanUser(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_reason = State()

class ChangePrice(StatesGroup):
    waiting_for_workflow_slug = State()
    waiting_for_new_price = State()

@router.callback_query(F.data == "admin_panel", IS_ADMIN)
async def cmd_admin_panel(callback: CallbackQuery, state: FSMContext):
    """
    Handles the "admin_panel" button, showing the main admin menu.
    """
    await state.clear() # Clear any previous states just in case
    logging.info(f"Admin user {callback.from_user.id} accessed the admin panel.")
    
    admin_text = "<b>Панель администратора</b>"
    
    await callback.message.edit_text(admin_text, reply_markup=get_admin_panel_keyboard())
    await callback.answer()

# --- Ban User FSM Handlers ---

@router.callback_query(F.data == "admin:ban_user", IS_ADMIN)
async def start_ban_user(callback: CallbackQuery, state: FSMContext):
    """
    Starts the process of banning a user.
    """
    await callback.answer()
    await callback.message.edit_text("Введите Telegram ID пользователя для бана:")
    await state.set_state(BanUser.waiting_for_user_id)

@router.message(BanUser.waiting_for_user_id, IS_ADMIN)
async def process_ban_user_id(message: Message, state: FSMContext):
    """
    Processes the user ID for the ban.
    """
    try:
        user_id_to_ban = int(message.text.strip())
        await state.update_data(user_id_to_ban=user_id_to_ban)
        await message.answer("ID принят. Теперь введите причину бана (можно отправить '-' для пропуска):")
        await state.set_state(BanUser.waiting_for_reason)
    except ValueError:
        await message.answer("Неверный формат ID. Пожалуйста, введите только цифры. Попробуйте еще раз.")
        return

@router.message(BanUser.waiting_for_reason, IS_ADMIN)
async def process_ban_reason(message: Message, state: FSMContext):
    """
    Processes the reason, finalizes the ban, and clears the state.
    """
    reason = message.text.strip()
    if reason == '-':
        reason = None # No reason provided

    user_data = await state.get_data()
    user_id_to_ban = user_data['user_id_to_ban']
    
    try:
        await supabase_http_client.insert("banned_users", {
            "telegram_id": user_id_to_ban,
            "reason": reason,
            "banned_by": str(message.from_user.id)
        })
        await message.answer(f"✅ Пользователь {user_id_to_ban} успешно забанен.")
        logging.info(f"Admin {message.from_user.id} banned user {user_id_to_ban} with reason: {reason}")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при бане пользователя: {e}")
        logging.error(f"Failed to ban user {user_id_to_ban}: {e}")
    finally:
        await state.clear()
        # Optionally, show the admin panel again
        await message.answer("<b>Панель администратора</b>", reply_markup=get_admin_panel_keyboard())


# This handler will catch attempts by non-admins to use admin commands.
@router.message(Command("stats", "unban"), ~IS_ADMIN)
async def cmd_access_denied(message: Message):
    """
    Handles attempts by non-admins to use admin commands.
    """
    logging.warning(f"User {message.from_user.id} tried to use an admin command: {message.text}")
    await message.answer("У вас нет доступа к этой команде.")


# --- Change Price FSM Handlers ---

@router.callback_query(F.data == "admin:change_price", IS_ADMIN)
async def start_change_price(callback: CallbackQuery, state: FSMContext):
    """
    Starts the process of changing a workflow's price by showing a list of workflows.
    """
    await callback.answer()
    
    workflows = await get_workflows_from_db()
    if not workflows:
        await callback.message.edit_text("В базе данных нет workflows для изменения цены.")
        return

    buttons = []
    for wf in workflows:
        buttons.append([InlineKeyboardButton(
            text=f"{wf.name} (Текущая цена: {wf.price:.0f}₽)",
            callback_data=f"changeprice_wf:{wf.slug}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")])
    
    await callback.message.edit_text(
        "Выберите workflow, для которого хотите изменить цену:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(ChangePrice.waiting_for_workflow_slug)

@router.callback_query(ChangePrice.waiting_for_workflow_slug, F.data.startswith("changeprice_wf:"), IS_ADMIN)
async def process_workflow_selection_for_price_change(callback: CallbackQuery, state: FSMContext):
    """
    Handles the selection of a workflow to change its price.
    """
    await callback.answer()
    slug = callback.data.split(":")[1]
    
    await state.update_data(workflow_slug_to_change=slug)
    
    await callback.message.edit_text(f"Введите новую цену для workflow `{slug}` (только цифры):")
    await state.set_state(ChangePrice.waiting_for_new_price)

@router.message(ChangePrice.waiting_for_new_price, IS_ADMIN)
async def process_new_price(message: Message, state: FSMContext):
    """
    Processes the new price, updates the database, and clears the state.
    """
    try:
        new_price = float(message.text.strip())
        if new_price < 0:
            raise ValueError("Price cannot be negative.")
            
    except ValueError:
        await message.answer("Неверный формат цены. Пожалуйста, введите число (например, `600` или `550.5`). Попробуйте еще раз.")
        return

    user_data = await state.get_data()
    slug = user_data['workflow_slug_to_change']
    
    try:
        await supabase_http_client.update(
            "workflows",
            match={"slug": slug},
            new_data={"price": new_price}
        )
        
        await message.answer(f"✅ Цена для workflow `{slug}` успешно изменена на {new_price}₽.")
        logging.info(f"Admin {message.from_user.id} changed price for {slug} to {new_price}")

    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при изменении цены: {e}")
        logging.error(f"Failed to change price for {slug}: {e}")
    finally:
        await state.clear()
        await message.answer(
            "<b>Панель администратора</b>",
            reply_markup=get_admin_panel_keyboard()
        )
