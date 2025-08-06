import logging
from pyrogram import Client, emoji, filters
from pyrogram.errors.exceptions.bad_request_400 import QueryIdInvalid
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultCachedDocument,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent
)
from database.ia_filterdb import get_search_results
from utils import is_subscribed, get_size, temp
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION
from database.connections_mdb import active_connection

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME

async def inline_users(query: InlineQuery):
    if AUTH_USERS:
        if query.from_user and query.from_user.id in AUTH_USERS:
            return True
        else:
            return False
    if query.from_user and query.from_user.id not in temp.BANNED_USERS:
        return True
    return False

@Client.on_inline_query()
async def answer(bot, query):
    """Show search results for given inline query"""
    chat_id = await active_connection(str(query.from_user.id))

    if not await inline_users(query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text='okDa',
            switch_pm_parameter="hehe"
        )
        return

    invite_links = await is_subscribed(bot, query=query)
    if AUTH_CHANNEL and len(invite_links) >= 1:
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text='You have to subscribe my channel to use the bot',
            switch_pm_parameter="subscribe"
        )
        return

    results = []

    if '|' in query.query:
        string, file_type = query.query.split('|', maxsplit=1)
        string = string.strip()
        file_type = file_type.strip().lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(query=string)

    files, next_offset, total = await get_search_results(
        chat_id,
        string,
        file_type=file_type,
        max_results=10,
        offset=offset
    )

    for index, file in enumerate(files):
        title = file.file_name
        size = get_size(file.file_size)
        f_caption = file.caption or f"{title}"

        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(
                    file_name=title or '',
                    file_size=size or '',
                    file_caption=f_caption or ''
                )
            except Exception as e:
                logger.exception(e)

        # Add custom update channel promotion article
        if index == len(files) // 2:
            results.append(
                InlineQueryResultArticle(
                    title="📣 CT- Updatez... 🍿",
                    input_message_content=InputTextMessageContent(
                        message_text="📣 Join our updates channel: @CTUpdatez"
                    ),
                    description="Click to join our update channel!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🚀 Join Now", url="https://t.me/+KJHSwIdswKUwZjU1")]
                    ])
                )
            )

        # Add the actual cached document result
        results.append(
            InlineQueryResultCachedDocument(
                title=title,
                document_file_id=file.file_id,
                caption=f_caption,
                description=f'Size: {size}\nType: {file.file_type}',
                reply_markup=reply_markup
            )
        )

    if results:
        switch_pm_text = f"{emoji.FILE_FOLDER} Results - {total}"
        if string:
            switch_pm_text += f" for {string}"

        try:
            await query.answer(
                results=results,
                is_personal=True,
                cache_time=cache_time,
                switch_pm_text=switch_pm_text,
                switch_pm_parameter="start",
                next_offset=str(next_offset)
            )
        except QueryIdInvalid:
            pass
        except Exception as e:
            logger.exception(str(e))
    else:
        switch_pm_text = f'{emoji.CROSS_MARK} No results'
        if string:
            switch_pm_text += f' for "{string}"'

        await query.answer(
            results=[],
            is_personal=True,
            cache_time=cache_time,
            switch_pm_text=switch_pm_text,
            switch_pm_parameter="okay"
        )

def get_reply_markup(query):
    buttons = [
        [InlineKeyboardButton('Search again', switch_inline_query_current_chat=query)]
    ]
    return InlineKeyboardMarkup(buttons)
                        



