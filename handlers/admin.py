import logging
import os
from datetime import datetime
from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from handlers.catalog import get_workflows_from_db
from utils.watermark import add_watermark_to_workflow
from database.models import Purchase # To hint the type

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

class ResendFile(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_workflow_selection = State()

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
async def process_ban_reason(message: Message, state: FSMContext, bot: Bot):
    """
    Processes the reason, finalizes the ban, and cleans the state.
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
        # Instead of sending a new message, edit the one that started the flow
        # We need to save the message_id in the state when the flow starts.
        # For now, let's just send a new message to avoid breaking changes.
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

# --- Resend File FSM Handlers ---
@router.callback_query(F.data == "admin:send_file", IS_ADMIN)
async def start_resend_file(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Введите Telegram ID пользователя, которому нужно повторно отправить файл:")
    await state.set_state(ResendFile.waiting_for_user_id)

@router.message(ResendFile.waiting_for_user_id, IS_ADMIN)
async def process_user_id_for_resend(message: Message, state: FSMContext):
    try:
        user_id_to_resend = int(message.text.strip())
    except ValueError:
        await message.answer("Неверный формат ID. Пожалуйста, введите только цифры. Попробуйте еще раз.")
        return

    # Fetch the 5 most recent purchases for this user
    purchases_response = await supabase_http_client.select(
        "purchases",
        params={
            "user_id": f"eq.{user_id_to_resend}",
            "select": "*,workflow:workflows(name,slug,filepath,version)",
            "order": "purchased_at.desc",
            "limit": 5
        }
    )

    if not purchases_response:
        await message.answer(f"У пользователя {user_id_to_resend} не найдено покупок.")
        await state.clear()
        return

    await state.update_data(resend_user_id=user_id_to_resend)
    buttons = []
    for p in purchases_response:
        wf = p['workflow']
        # Format the date and time
        purchase_time = datetime.fromisoformat(p['purchased_at']).strftime('%d.%m.%Y %H:%M')
        
        button_text = f"{wf['name']} ({purchase_time}, {p['price']:.0f}₽)"
        callback_data = f"resend_purchase:{p['id']}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])

    buttons.append([InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin_panel")])
    
    await message.answer(
        f"5 последних покупок пользователя {user_id_to_resend}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(ResendFile.waiting_for_workflow_selection)

@router.callback_query(ResendFile.waiting_for_workflow_selection, F.data.startswith("resend_purchase:"), IS_ADMIN)
async def process_resend_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Processes the final selection, creates a watermarked file, and sends it.
    """
    await callback.answer("Готовлю файл...")
    purchase_id = int(callback.data.split(":")[1])
    
    try:
        # Fetch all necessary data using the purchase_id
        purchase_response = await supabase_http_client.select(
            "purchases",
            params={"id": f"eq.{purchase_id}", "select": "*,user_id,workflow:workflows(name,slug,filepath,version)", "limit": 1}
        )
        if not purchase_response:
            raise Exception(f"Purchase with ID {purchase_id} not found.")

        purchase = purchase_response[0]
        user_id_to_resend = purchase['user_id']
        workflow = purchase['workflow']

        # We don't have the user's current username, so we'll use a placeholder
        watermarked_file = add_watermark_to_workflow(
            original_filepath=workflow['filepath'],
            slug=workflow['slug'],
            user_id=user_id_to_resend,
            username="resend", # Placeholder
            payment_id=f"manual_resend_{int(datetime.now().timestamp())}",
            workflow_version=workflow['version']
        )

        if watermarked_file:
            try:
                await bot.send_document(
                    chat_id=user_id_to_resend,
                    document=FSInputFile(watermarked_file),
                    caption=f"✅ Повторная отправка вашего workflow: {workflow['name']}"
                )
                await callback.message.edit_text(f"✅ Файл `{workflow['name']}` успешно отправлен пользователю {user_id_to_resend}.")
                logging.info(f"Admin {callback.from_user.id} resent {workflow['slug']} to {user_id_to_resend}")
            finally:
                os.remove(watermarked_file)
                logging.info(f"Removed temporary file: {watermarked_file}")
        else:
            raise Exception("Watermarked file creation failed.")
    
    except Exception as e:
        await callback.message.edit_text(f"❌ Произошла ошибка при повторной отправке: {e}")
        logging.error(f"Failed to resend file to purchase ID {purchase_id}: {e}", exc_info=True)
    finally:
        await state.clear()
        await callback.message.answer(
            "<b>Панель администратора</b>",
            reply_markup=get_admin_panel_keyboard()
        )

