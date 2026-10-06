from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
import asyncio
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import ErrorEvent

import keyboards
import re
import config
import logic
API_URL = 'https://api.telegram.org/bot'
BOT_TOKEN = config.TELEGRAM_TOKEN
API_CATS_URL = 'https://api.thecatapi.com/v1/images/search'
LIMIT = 10


storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)


class FSMFilmsSearch(StatesGroup):
    waiting_for_keyword = State()
    waiting_for_genre = State()
    waiting_for_year_from = State()
    waiting_for_year_to = State()
    waiting_for_custom_params = State()
    show_films = State()
    in_statistics_menu = State()
    in_top_params_menu = State()


async def remove_old_keyboard(chat_id: int, message_id: int | None) -> None:
    """
    Remove the inline keyboard from the previous bot menu message.
    Failures are printed to the console only, the user is not notified.
    """
    if not message_id:
        return
    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=None
        )
    except Exception as e:
        print(f"Failed to remove old buttons: {e}")


@dp.errors()
async def handle_error(event: ErrorEvent):
    exception = event.exception
    if isinstance(exception, logic.DatabaseAccessError):
        print(f"Database access error: {exception!r}")
        text = ("Connection to database was interrupted."
                "\nPlease, try again later.\n<b>Main menu</b>")
    else:
        print(f"Unexpected error: {exception!r}")
        text = ("Something went wrong. Please, try again later."
                "\n<b>Main menu</b>")

    obj = event.update.event
    if isinstance(obj, Message):
        message = obj
    else:
        message = getattr(obj, "message", None)
    user = getattr(obj, "from_user", None)
    if message is None or user is None:
        return True

    key = StorageKey(bot_id=bot.id, chat_id=message.chat.id,
                     user_id=user.id)
    fsm = FSMContext(storage=storage, key=key)

    data = await fsm.get_data()
    await remove_old_keyboard(message.chat.id,
                              data.get("last_menu_message_id"))

    await fsm.clear()
    sent_msg = await bot.send_message(chat_id=message.chat.id, text=text,
                                      reply_markup=keyboards.keyboard_menu,
                                      parse_mode="HTML")
    await fsm.update_data(last_menu_message_id=sent_msg.message_id)
    return True

@dp.message(~F.text)
async def unexpected_message_type(message: Message):
    await message.reply(text="This content type is not supported")


@dp.callback_query(F.data == "top_params_click")
async def start_top_params_flow(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(FSMFilmsSearch.in_top_params_menu)
    try:
        sent_msg = await callback.message.edit_text(
            text="<b>Top Parameters</b>\nChoose query type for statistics:",
            reply_markup=keyboards.types_keyboard,
            parse_mode="HTML"
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(e)


@dp.callback_query(F.data == "show_popular_search_types")
async def show_popular_search_types(callback: CallbackQuery,
                                    state: FSMContext):
    await callback.answer()

    stat = await asyncio.to_thread(logic.get_popular)

    response = "<b>Popular search types</b>\n\n"
    for item in stat:
        response += (f"Type: <b>{item['_id']}</b> "
                     f"| Count: <code>{item['count']}</code>\n")
    try:
        await callback.message.edit_text(
            text=response,
            reply_markup=None,
            parse_mode="HTML"
        )
        sent_msg = await callback.message.answer(
            text="<b>Statistics Menu</b>\nSelect an option below:",
            reply_markup=keyboards.keyboard_stat_menu,
            parse_mode="HTML"
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(e)


@dp.callback_query(F.data == "by_client_click")
async def show_activity_by_client(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    clients = await asyncio.to_thread(logic.stat_by_client)
    response = "<b>Activity by client</b>\n\n"
    for item in clients:
        response += (f"Client: <b>{item['_id']}</b> | "
                     f"Query count: <b>{item['count']}</b>\n")
    try:
        await callback.message.edit_text(
            text=response,
            reply_markup=None,
            parse_mode="HTML"
        )
        sent_msg = await callback.message.answer(
            text="<b>Statistics Menu</b>\nSelect an option below:",
            reply_markup=keyboards.keyboard_stat_menu,
            parse_mode="HTML"
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(e)


@dp.callback_query(F.data == "show_recent_queries_click")
async def show_recent_queries(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    recent_params = await asyncio.to_thread(logic.get_recent_queries, 5)
    response = f"<b>Recent 5 queries</b>\n\n"
    if not recent_params:
        response += "<i>No recent queries found.</i>"
    else:
        for item in recent_params:
            timestamp = item.get('timestamp', 'N/A')
            client = item.get('client', 'N/A')
            search_type = item.get('search_type', 'N/A')
            params = item.get('params', {})
            count = item.get('count', 0)
            response += (
                f"<b>Time:</b> {timestamp}\n"
                f"<b>Client:</b> {client}\n"
                f"<b>Type:</b> {search_type}\n"
                f"<b>Params:</b> <code>{params}</code>\n"
                f"<b>Results:</b> {count}\n"
                f"-------------------\n"
            )
    try:
        await callback.message.edit_text(
            text=response,
            reply_markup=None,
            parse_mode="HTML"
        )
        sent_msg = await callback.message.answer(
            text="<b>Statistics Menu</b>\nSelect an option below:",
            reply_markup=keyboards.keyboard_stat_menu,
            parse_mode="HTML"
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(e)


@dp.callback_query(F.data.startswith("top_type_"))
async def process_top_type_chosen(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == "top_type_Keyword":
        q_type = "Keyword"
    elif callback.data == "top_type_Custom":
        q_type = "Custom"
    else:
        q_type = "genre_year"
    top_params = await asyncio.to_thread(logic.top_in_type, q_type, 5)
    response = f"<b>Top 5 parameters by {q_type}</b>\n\n"
    if not top_params:
        response += "<i>No data found.</i>"
    else:
        for item in top_params:
            if ('keyword' in item['_id'].get('params', {}) and
                    item['_id']['params']['keyword'] == ""):
                del item['_id']['params']['keyword']

            params_str = item['_id'].get('params', {})
            count = item.get('count_query', 0)
            response += (f"Params: <b>{params_str}</b>\n"
                         f"Count: <b>{count}</b>\n\n")
    try:
        await callback.message.edit_text(
            text=response,
            reply_markup=None,
            parse_mode="HTML"
        )
        sent_msg = await callback.message.answer(
            text="<b>Statistics Menu</b>\nSelect an option below:",
            reply_markup=keyboards.keyboard_stat_menu,
            parse_mode="HTML"
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(e)


@dp.callback_query(F.data == "show_stat_button_click")
async def show_stat_button_click(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(FSMFilmsSearch.in_statistics_menu)
    try:
        sent_msg = await callback.message.edit_text(
            text="Statistics Menu\nSelect an option below:",
            reply_markup=keyboards.keyboard_stat_menu
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(e)


@dp.callback_query(F.data == "back_to_main_menu_button_click")
async def back_to_main_menu_button_click(callback: CallbackQuery,
                                         state: FSMContext):
    await callback.answer()
    await state.clear()
    try:
        await bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
        sent_msg = await callback.message.answer(
            text="Main Menu\nSelect an option below:",
            reply_markup=keyboards.keyboard_menu
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(e)


@dp.callback_query(F.data == "keyword_search_click")
async def start_keyword_search(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    await state.set_state(FSMFilmsSearch.waiting_for_keyword)
    try:
        await callback.message.edit_text(
            text="<b>Search by keyword</b>\n\n"
                 "Please enter a keyword to search for movies or "
                 "return to main menu:",
            reply_markup=None,
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            print(e)
    sent_msg = await callback.message.answer(
        text="Send your keyword as a text message:",
        reply_markup=keyboards.back_main_keyboard
    )
    await state.update_data(last_menu_message_id=sent_msg.message_id)


@dp.callback_query(F.data == "back_to_films_button_click")
async def back_to_films_list(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        await bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
        data = await state.get_data()
        current_films_text = data.get("current_films_text", "")
        current_keyboard_markup = data.get("current_keyboard_markup")
        sent_msg = await callback.message.answer(
            text=current_films_text,
            reply_markup=current_keyboard_markup,
            parse_mode="HTML"
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(e)


@dp.callback_query(F.data == "genre_year_search_click")
async def start_genre_year_search(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(FSMFilmsSearch.waiting_for_genre)

    genres_limits = await asyncio.to_thread(logic.get_genres)
    await state.update_data(genres_limits=genres_limits)
    keyboard = keyboards.generate_genres_keyboard(list(genres_limits.keys()))
    try:
        sent_msg = await callback.message.edit_text(
            text="<b>Search by genre and year</b>\n\n"
                 "Choose a genre from the list:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            print(e)


@dp.callback_query(FSMFilmsSearch.waiting_for_genre,
                   F.data.startswith("genre_"))
async def process_genre_chosen(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    chosen_genre = callback.data.replace("genre_", "", 1)
    data = await state.get_data()
    genres_limits = data.get("genres_limits", {})

    if chosen_genre in genres_limits:
        min_year, max_year = genres_limits[chosen_genre]
    else:
        min_year, max_year = await asyncio.to_thread(logic.get_years)

    await state.update_data(
        genre=chosen_genre,
        min_year=min_year,
        max_year=max_year
    )

    await state.set_state(FSMFilmsSearch.waiting_for_year_from)
    try:
        sent_msg = await callback.message.edit_text(
            text=f"Chosen genre: <b>{chosen_genre}</b>\n\n"
                 f"Enter year <b>FROM</b> (available range: "
                 f"{min_year} - {max_year}):",
            reply_markup=keyboards.back_main_keyboard,
            parse_mode="HTML"
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            print(e)


@dp.message(FSMFilmsSearch.waiting_for_year_from)
async def process_year_from_input(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()

    await remove_old_keyboard(
        message.chat.id, data.get("last_menu_message_id"))

    if not text.isdigit():
        sent_msg = await message.answer(
            "Please enter a number (year). Try again:",
            reply_markup=keyboards.back_main_keyboard
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
        return

    year_from = int(text)
    min_year = data.get("min_year")
    max_year = data.get("max_year")

    if year_from < min_year or year_from > max_year:
        sent_msg = await message.answer(
            f"Year must be between {min_year} and {max_year}. Try again:",
            reply_markup=keyboards.back_main_keyboard
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
        return

    await state.update_data(year_from=year_from)
    await state.set_state(FSMFilmsSearch.waiting_for_year_to)

    sent_msg = await message.answer(
        text=f"Enter year <b>TO</b> (not later than {max_year}):",
        reply_markup=keyboards.back_main_keyboard,
        parse_mode="HTML"
    )
    await state.update_data(last_menu_message_id=sent_msg.message_id)


@dp.message(FSMFilmsSearch.waiting_for_year_to)
async def process_year_to_input(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()

    await remove_old_keyboard(
        message.chat.id, data.get("last_menu_message_id"))

    if not text.isdigit():
        sent_msg = await message.answer(
            "Please enter a number (year). Try again:",
            reply_markup=keyboards.back_main_keyboard
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
        return

    year_to = int(text)
    year_from = data.get("year_from")
    genre = data.get("genre")
    max_year = data.get("max_year")

    if year_to < year_from or year_to > max_year:
        sent_msg = await message.answer(
            f"Year 'to' cannot be less than year 'from' ({year_from}) "
            f"and greater than {max_year}. Repeat input:",
            reply_markup=keyboards.back_main_keyboard
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
        return

    params = {"year_from": year_from, "year_to": year_to, "genre": genre}

    films, count, is_saved = await asyncio.to_thread(
        logic.search, params, LIMIT, "genre_year", "tg_bot"
    )

    saved_txt = "" if is_saved else ("\nWarning: Search was successful, "
                                     "but logs could not be saved.")
    if count == 0:
        sent_msg = await message.answer(
            text=f"No results found for your query.{saved_txt}",
            reply_markup=keyboards.keyboard_menu
        )
        await state.clear()
        await state.update_data(last_menu_message_id=sent_msg.message_id)
        return

    await state.set_state(FSMFilmsSearch.show_films)
    text_page, markup, list_id = generate_films_page_layout(films, 0,
                                                            count)

    sent_msg = await message.answer(
        text=text_page + saved_txt,
        reply_markup=markup,
        parse_mode="HTML"
    )

    await state.update_data(
        params=params,
        total_count=count,
        current_film=0,
        current_films_text=text_page,
        current_keyboard_markup=markup,
        list_id=list_id,
        last_menu_message_id=sent_msg.message_id
    )


@dp.callback_query(F.data.in_(["main_menu_3_click"]))
async def unresolved_buttons_click(callback: CallbackQuery):
    await callback.answer()


@dp.message(Command(commands="start"))
@dp.message(lambda msg: msg.text and msg.text.lower() == 'menu')
async def process_start_command(message: Message, state: FSMContext):
    await state.clear()
    sent_msg = await message.answer(f'Hello '
                                    f'{message.from_user.full_name}!'
                                    f'\nWhat would you like to search for?',
                                    reply_markup=keyboards.keyboard_menu)
    await state.update_data(last_menu_message_id=sent_msg.message_id)


@dp.message(Command(commands="help"))
async def process_help_command(message: Message):
    await message.answer('I am a telegram bot that will help you '
                         f'find an interesting movie! \n'
                         f'To view the menu, enter '
                         f'"menu" or command "/start"')


@dp.callback_query(FSMFilmsSearch.show_films,
                   F.data.in_(["next_page_button_click",
                               "prev_page_button_click"]))
async def process_pagination(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    current_film = data.get("current_film")
    total_count = data.get("total_count")
    params = data.get("params")

    if not params:
        await remove_old_keyboard(
            callback.message.chat.id, data.get("last_menu_message_id"))
        await callback.message.answer(
            "Search session has expired. Please start over.",
            reply_markup=keyboards.keyboard_menu)
        return

    if callback.data == "next_page_button_click":
        new_current = current_film + LIMIT
    else:
        new_current = max(0, current_film - LIMIT)

    films = await asyncio.to_thread(
        logic.next_film, params, LIMIT, new_current
    )

    await state.update_data(current_film=new_current)
    text, markup, list_id = generate_films_page_layout(films, new_current,
                                                       total_count)
    await state.update_data(
        current_film=new_current,
        current_films_text=text,
        current_keyboard_markup=markup,
        list_id=list_id
    )
    try:
        sent_msg = await callback.message.edit_text(
            text=text,
            reply_markup=markup,
            parse_mode="HTML"
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            print(e)


@dp.message(FSMFilmsSearch.waiting_for_keyword)
async def keyword_input(message: Message, state: FSMContext):
    keyword = message.text.strip()
    pattern = r"^[a-zA-Zа-яА-ЯёЁ\s]+$"
    if re.match(pattern, keyword):
        params = {"keyword": keyword}
        films, count, is_saved = await asyncio.to_thread(
            logic.search, params, LIMIT, "Keyword", "tg_bot")
        saved_txt = ""
        if not is_saved:
            saved_txt = ("\nWarning: Search was successful, "
                         "but logs could not be saved.")
        data = await state.get_data()
        await remove_old_keyboard(
            message.chat.id, data.get("last_menu_message_id"))
        if count == 0:
            sent_msg = await message.answer(
                text=f"No results found for query <b>{keyword}</b>."
                     f"{saved_txt}"
                     f"\nMain menu",
                reply_markup=keyboards.keyboard_menu,
                parse_mode="HTML")
            await state.clear()
            await state.update_data(
                last_menu_message_id=sent_msg.message_id)
            return
        await state.set_state(FSMFilmsSearch.show_films)
        text, markup, list_id = generate_films_page_layout(films,
                                                           0, count)
        sent_msg = await message.answer(text=text + saved_txt,
                                        reply_markup=markup,
                                        parse_mode="HTML")
        await state.update_data(
            params=params,
            total_count=count,
            current_film=0,
            current_films_text=text,
            current_keyboard_markup=markup,
            list_id=list_id
        )

        await state.update_data(
            last_menu_message_id=sent_msg.message_id)
    else:
        data = await state.get_data()
        await remove_old_keyboard(
            message.chat.id, data.get("last_menu_message_id"))
        sent_msg = await message.answer(
            text="Keyword can contain only letters.\n"
                 "Send your keyword as a text message:",
            reply_markup=keyboards.back_main_keyboard
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)


def generate_films_page_layout(films, curr, total_count):
    response = (f"<b>Search results (found: {total_count})</b> \n"
                f"Showing from {curr + 1} to "
                f"{min(curr+LIMIT, total_count)}\n\n")
    list_id = []
    for film in films:
        response += f"ID:     {film[0]} \n"
        response += f"Title:  {film[1]} \n"
        response += f"Year:   {film[2]} \n"
        response += f"Rating: {film[3]} \n\n\n"
        list_id.append(film[0])
    return (response,
            keyboards.generate_navigation_keyboard(LIMIT, curr, total_count),
            list_id)


@dp.message(FSMFilmsSearch.show_films)
async def process_film_id_input(message: Message, state: FSMContext):
    data = await state.get_data()
    await remove_old_keyboard(
        message.chat.id, data.get("last_menu_message_id"))
    if message.text.strip().isdigit():
        film_id = int(message.text.strip())
    else:
        film_id = -1
    list_id = data.get("list_id", [])

    if film_id not in list_id:
        current_films_text = data.get("current_films_text", "")
        current_keyboard_markup = data.get("current_keyboard_markup")

        await message.answer(
            text="<b>Incorrect input.</b> This ID is not present on "
                 "the current page.",
            parse_mode="HTML"
        )
        sent_msg = await message.answer(
            text=current_films_text,
            reply_markup=current_keyboard_markup,
            parse_mode="HTML"
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
        return

    film = await asyncio.to_thread(logic.get_film, film_id)
    if film is None:
        await state.clear()
        sent_msg = await message.answer(
            text="Film was not found, sorry(\n<b>Main menu</b>",
            reply_markup=keyboards.keyboard_menu,
            parse_mode="HTML"
        )
        await state.update_data(last_menu_message_id=sent_msg.message_id)
        return

    title, description, release_year, length, rating, genres, actors = film
    response = f"<b>Detailed information</b>\n\n"
    response += f"<b>ID:</b> {film_id}\n"
    response += f"Title: {title}\n"
    response += f"Release year: {release_year}\n\n"
    response += f"Length: {length} min.\n"
    response += f"Age rating: {rating}\n"
    response += f"Genres: {genres if genres else 'Not specified'}\n"
    response += f"Actors: {actors if actors else 'No data'}\n\n"
    response += f"Description: {description}\n"

    sent_msg = await message.answer(
        text=response,
        reply_markup=keyboards.current_film_keyboard,
        parse_mode="HTML"
    )
    await state.update_data(last_menu_message_id=sent_msg.message_id)


@dp.message(
    ~StateFilter(FSMFilmsSearch.waiting_for_keyword),
    ~StateFilter(FSMFilmsSearch.show_films),
    ~StateFilter
        (FSMFilmsSearch.waiting_for_year_from),
    ~StateFilter(FSMFilmsSearch.waiting_for_year_to)
)
async def handle_unexpected_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    await remove_old_keyboard(
        message.chat.id, data.get("last_menu_message_id"))
    if current_state == FSMFilmsSearch.in_statistics_menu.state:
        target_menu = keyboards.keyboard_stat_menu
        menu_name = "<b>Statistics Menu</b>\nSelect an option below:"
    elif current_state == FSMFilmsSearch.in_top_params_menu.state:
        target_menu = keyboards.types_keyboard
        menu_name = "<b>Top Parameters</b>\nChoose query type for statistics:"
    else:
        await state.clear()
        target_menu = keyboards.keyboard_menu
        menu_name = "main menu"

    sent_msg = await message.answer(
        text=f"<b>Message not recognized.</b>\n"
             f"In this section you need to use buttons instead of "
             f"writing text.\n"
             f"Returning you to {menu_name}:",
        reply_markup=target_menu,
        parse_mode="HTML"
    )
    await state.update_data(last_menu_message_id=sent_msg.message_id)


if __name__ == '__main__':
    if not logic.init_app():
        print("Warning: MongoDB is unavailable, query statistics will not be saved.")
    dp.run_polling(bot)