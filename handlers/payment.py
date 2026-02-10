import logging
import os
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from utils.watermark import add_watermark_to_workflow

from config import YUKASSA_TOKEN, PRIVATE_CHANNEL_ID
from handlers.catalog import get_workflow_by_slug
from database.supabase_http_client import supabase_http_client
from utils.pricing import get_current_price, PRICE_EARLY_BIRD
from utils.watermark import add_watermark_to_workflow # Import watermarking function
from aiogram.types import FSInputFile # Import for sending files

router = Router()

@router.callback_query(F.data.startswith("buy:"))
async def handle_buy_workflow(callback: CallbackQuery, bot: Bot):
    """
    Handles the 'buy' button click.
    Fetches workflow details and sends an invoice to the user.
    """
    slug = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    logging.info(f"User {user_id} initiated purchase for slug: {slug}")
    
    workflow = await get_workflow_by_slug(slug)
    
    if not workflow:
        await callback.answer("😔 Товар не найден. Возможно, он был удален.", show_alert=True)
        return

    # Get the current dynamic price
    price = await get_current_price()
    
    await bot.send_invoice(
        chat_id=user_id,
        title=f"Покупка: {workflow.name}",
        description=f"Доступ к n8n workflow: {workflow.description}",
        payload=f"workflow_purchase:{slug}:{user_id}",
        provider_token=YUKASSA_TOKEN,
        currency="RUB",
        prices=[
            LabeledPrice(
                label=f"Workflow: {workflow.name}",
                amount=int(price * 100)  # Price in kopecks
            )
        ],
        start_parameter=f"buy_{slug}", # Deep link parameter for the invoice
        provider_data=None, # Optional: JSON object with data for the provider
        need_name=False,
        need_phone_number=False,
        need_email=True, # We want to get user's email for updates
        need_shipping_address=False,
        is_flexible=False,
        disable_notification=False,
        protect_content=False,
        reply_to_message_id=None,
        reply_markup=None,
        request_timeout=15,
    )
    await callback.answer() # Acknowledge the button press

@router.pre_checkout_query()
async def handle_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    """
    Handles the pre-checkout query. This is a final check before payment.
    You can perform checks here like item availability.
    """
    # For now, we'll always approve the transaction.
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    logging.info(f"Pre-checkout query approved for user {pre_checkout_query.from_user.id}")

import os

# ... (other imports) ...

@router.message(F.successful_payment)
async def handle_successful_payment(message: Message, bot: Bot):
    """
    Handles a successful payment, saves the purchase, creates a watermark, and delivers the product.
    """
    payment_info = message.successful_payment
    payload_str = payment_info.invoice_payload
    user_id = message.from_user.id
    username = message.from_user.username or "user"

    logging.info(f"SUCCESSFUL PAYMENT from user {user_id} for payload: {payload_str}")

    try:
        _, slug, _ = payload_str.split(":")
        
        workflow = await get_workflow_by_slug(slug)
        if not workflow:
            logging.error(f"FATAL: Workflow '{slug}' not found after successful payment!")
            await message.answer("Произошла критическая ошибка. Свяжитесь с поддержкой.")
            return

        # Save purchase to DB
        purchase_data = {
            "user_id": user_id, "workflow_id": workflow.id,
            "price": payment_info.total_amount / 100,
            "payment_id": payment_info.telegram_payment_charge_id,
            "email": payment_info.order_info.email if payment_info.order_info else None,
        }
        await supabase_http_client.insert(table="purchases", data=purchase_data)
        logging.info(f"Purchase by user {user_id} for workflow {workflow.id} saved to DB.")

        # Increment Early Bird counter if applicable
        if (payment_info.total_amount / 100) == PRICE_EARLY_BIRD:
            await supabase_http_client.rpc('increment_setting_value', params={'setting_key': 'early_bird_counter', 'increment_value': 1})
            logging.info("Incremented early_bird_counter.")

        # --- Deliver the product ---
        await message.answer("🎉 Спасибо за покупку! Готовлю ваш персональный файл...")

        watermarked_file = add_watermark_to_workflow(
            original_filepath=workflow.filepath, slug=workflow.slug,
            user_id=user_id, username=username,
            payment_id=payment_info.telegram_payment_charge_id,
            workflow_version=workflow.version
        )

        if watermarked_file:
            try:
                await bot.send_document(
                    chat_id=user_id,
                    document=FSInputFile(watermarked_file),
                    caption="✅ Ваш workflow готов! Спасибо за использование нашего сервиса."
                )
                logging.info(f"Successfully sent watermarked file to user {user_id}")
            finally:
                # Cleanup the temporary watermarked file
                os.remove(watermarked_file)
                logging.info(f"Removed temporary file: {watermarked_file}")
        else:
            raise Exception("Watermarked file creation failed.")

        # --- Send Invite Link ---
        try:
            if PRIVATE_CHANNEL_ID:
                expire_date = datetime.now() + timedelta(days=1)
                invite_link = await bot.create_chat_invite_link(
                    chat_id=PRIVATE_CHANNEL_ID,
                    expire_date=expire_date,
                    member_limit=1
                )
                await bot.send_message(
                    chat_id=user_id,
                    text=f"🎁 В качестве бонуса, вот ваше персональное приглашение в наш приватный канал. Ссылка действует 24 часа:\n{invite_link.invite_link}"
                )
                logging.info(f"Sent invite link to user {user_id}")
            else:
                logging.warning("PRIVATE_CHANNEL_ID is not set. Skipping invite link generation.")
        except Exception as e:
            logging.error(f"Failed to create or send invite link for user {user_id}: {e}")
            # Do not block the user, just inform them
            await bot.send_message(user_id, "Не удалось создать пригласительную ссылку в приватный канал. Если проблема повторится, пожалуйста, обратитесь в поддержку.")

    except Exception as e:
        logging.error(f"Failed to process successful payment for user {user_id}: {e}", exc_info=True)
        await message.answer("😔 Произошла ошибка при обработке вашей покупки. Пожалуйста, свяжитесь с поддержкой, и мы все решим.")
        return

    # Final confirmation message with a button
    await message.answer(
        "Все готово! Если у вас возникнут вопросы, обращайтесь в поддержку.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 На главную", callback_data="main_menu"),
                InlineKeyboardButton(text="💬 Поддержка", callback_data="support_menu")
            ]
        ])
    )
