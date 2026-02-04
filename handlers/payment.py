import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery

from config import YUKASSA_TOKEN
from handlers.catalog import get_workflow_by_slug
from database.supabase_http_client import supabase_http_client
from utils.pricing import get_current_price, PRICE_EARLY_BIRD

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

@router.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    """
    Handles a successful payment.
    Logs the purchase in the database and prepares for product delivery.
    """
    payment_info = message.successful_payment
    payload_str = payment_info.invoice_payload
    
    logging.info(
        f"SUCCESSFUL PAYMENT: User {message.from_user.id} paid {payment_info.total_amount / 100} {payment_info.currency} "
        f"for payload: {payload_str}"
    )

    # --- Save purchase to DB ---
    try:
        # Extract data from payload: "workflow_purchase:{slug}:{user_id}"
        _, slug, user_id_str = payload_str.split(":")
        user_id = int(user_id_str)
        
        # Get workflow_id from slug
        workflow = await get_workflow_by_slug(slug)
        if not workflow:
            logging.error(f"FATAL: Workflow with slug '{slug}' not found after successful payment!")
            await message.answer("Произошла критическая ошибка. Пожалуйста, свяжитесь с поддержкой.")
            return

        purchase_data = {
            "user_id": user_id,
            "workflow_id": workflow.id,
            "price": payment_info.total_amount / 100,
            "payment_id": payment_info.telegram_payment_charge_id, # Encrypt this later
            "email": payment_info.order_info.email if payment_info.order_info else None,
            "ip_address": None, # Cannot get IP from Telegram Payments
        }
        
        await supabase_http_client.insert(table="purchases", data=purchase_data)
        logging.info(f"Purchase by user {user_id} for workflow {workflow.id} saved to DB.")

        # Increment Early Bird counter using the RPC function
        # We only increment if the price paid was the Early Bird price
        if (payment_info.total_amount / 100) == PRICE_EARLY_BIRD:
            await supabase_http_client.rpc('increment_setting_value', params={'setting_key': 'early_bird_counter', 'increment_value': 1})
            logging.info("Incremented early_bird_counter.")

    except Exception as e:
        logging.error(f"Failed to save purchase to DB for user {message.from_user.id}: {e}", exc_info=True)
        # Even if DB save fails, we should try to deliver the product
        await message.answer("Произошла ошибка при сохранении вашей покупки, но не волнуйтесь! "
                             "Мы уже работаем над этим. Ваш workflow скоро будет доставлен.")

    # --- TODO: Deliver the product ---
    # 1. Add watermark to the file
    # 2. Send the watermarked file to the user
    
    await message.answer(
        "🎉 Спасибо за покупку! Ваш workflow уже в пути. Сейчас я его подготовлю и отправлю."
    )
