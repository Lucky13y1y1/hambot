from aiogram import F, types, Router, html
from aiogram.utils.formatting import as_list, Bold, as_numbered_section, Code

from bot.logic import send_menu_reponse, check_user_channel_subscription
from bot.keyboards import get_subscription_check_markup, delmsg_markup
from bot.i18n import i18n_manager
from common.database import db
from common.tools.utils import get_date
from config import GamePromoTypes

router = Router()


@router.callback_query(F.data.startswith("lang"))
async def lang_selector_handler(callback: types.CallbackQuery):
    lang_code = callback.data[5:]
    await db.users_data.set_user_language(callback.from_user.id, lang_code)
    await callback.message.delete()
    await callback.message.answer(text=await i18n_manager.get_translation(lang_code, "LANG_SELECTED"))
    await send_menu_reponse(callback.message, callback.from_user.id)


@router.callback_query(F.data == 'check_subscription')
async def check_subscription(callback: types.CallbackQuery):
    access = await check_user_channel_subscription(callback.bot, callback.from_user.id)
    lang_code = await db.users_data.get_user_language(callback.from_user.id)
    if not access:
        await callback.answer(text=await i18n_manager.get_translation(lang_code, "NOT_SUBSCRIBED"),
                              show_alert=True)
    else:
        await callback.answer(text=await i18n_manager.get_translation(lang_code, "SUBSCRIBE_CONFIRMED"),
                              show_alert=True)
        await callback.message.delete()
        await send_menu_reponse(callback.message, callback.from_user.id)


@router.callback_query(F.data.in_([game.value for game in GamePromoTypes]))
async def get_game_key_handler(callback: types.CallbackQuery):
    access = await check_user_channel_subscription(callback.bot, callback.from_user.id)
    lang_code = await db.users_data.get_user_language(callback.from_user.id)
    if not access:
        await callback.message.answer(
            text=await i18n_manager.get_translation(lang_code, "MUST_SUBSCRIBE_REQUIRED_CHANNEL"),
            reply_markup=await get_subscription_check_markup(lang_code))
    else:
        game = GamePromoTypes.__getitem__(callback.data)
        user_available_keys, _ = await db.users_data.get_pool_limit(game, callback.from_user.id)
        game_key_pool_size = await db.keys_pool.count_key_pool(game)

        if game_key_pool_size <= 0:
            return await callback.answer(
                text=await i18n_manager.get_translation(lang_code, "GAME_POOL_EMPTY"),
                show_alert=True)
        if user_available_keys <= 0:
            return await callback.answer(
                await i18n_manager.get_translation(lang_code, "DAILY_KEY_LIMIT_REACHED"),
                show_alert=True)

        key = await db.keys_pool.get_key(game)
        await db.users_data.count_key_receive(game, callback.from_user.id, key)

        await callback.message.answer(
            text=(await i18n_manager.get_translation(lang_code, "KEY_RECEIVED")).format(
                game_name=callback.data,
                key=html.code(key)
            ),
            reply_markup=delmsg_markup)
        await callback.answer()


@router.callback_query(F.data == "update_menu")
async def update_menu_handler(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
        await send_menu_reponse(callback.message, callback.from_user.id)
        await callback.answer()
    except Exception as e:
        lang_code = await db.users_data.get_user_language(callback.from_user.id)
        await callback.answer(
            text=(await i18n_manager.get_translation(lang_code, "MENU_UPDATE_FAILED")).format(error=e),
            show_alert=True)


@router.callback_query(F.data == 'delete_message')
async def delete_message_handler(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        lang_code = await db.users_data.get_user_language(callback.from_user.id)
        await callback.answer(
            text=(await i18n_manager.get_translation(lang_code, "MESSAGE_DELETE_FAILED")).format(error=e),
            show_alert=True)


@router.callback_query(F.data == 'history_menu')
async def history_menu_handler(callback: types.CallbackQuery):
    history_data = await db.users_data.get_history_data(callback.from_user.id)
    lang_code = await db.users_data.get_user_language(callback.from_user.id)
    response = as_list(
        Bold((await i18n_manager.get_translation(lang_code, "KEY_COLLECTION_HISTORY")).format(date=get_date())),
        *[as_numbered_section(Bold(game.value), *[Code(key)
                                                  for key in history_data.get(game.value) or
                                                  [await i18n_manager.get_translation(lang_code, "EMPTY")]])
          for game in GamePromoTypes
          ],
        sep='\n\n'
    )
    await callback.message.answer(text=response.as_html(), reply_markup=delmsg_markup)
    await callback.answer()


def register_callback_queries_handler(dp):
    dp.include_router(router)
