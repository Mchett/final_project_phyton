from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


back_to_statistics_button = InlineKeyboardButton(
    text="Back to statistics menu", callback_data="show_stat_button_click")

back_to_main_menu_button = InlineKeyboardButton(
    text="Return to Main Menu.", callback_data="back_to_main_menu_button_click"
)

back_to_film_results_button = InlineKeyboardButton(
    text="Return to Film Results.", callback_data="back_to_films_button_click"
)

next_page_button = InlineKeyboardButton(
    text="next >> ", callback_data="next_page_button_click")

prev_page_button = InlineKeyboardButton(
    text=" << previous", callback_data="prev_page_button_click")

back_statistic_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [back_to_statistics_button]
])


back_main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [back_to_main_menu_button]
])


current_film_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [back_to_film_results_button], [back_to_main_menu_button]
])


types_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Keyword",
                          callback_data="top_type_Keyword")],
    [InlineKeyboardButton(text="Custom", callback_data="top_type_Custom")],
    [InlineKeyboardButton(text="Genre & Year",
                          callback_data="top_type_genre_year")],
    [back_to_statistics_button]
])


keyboard_stat_menu = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(
        text="Popular search types.",
        callback_data="show_popular_search_types")],
        [InlineKeyboardButton(
            text="Top parameters by search type.",
            callback_data="top_params_click")],
        [InlineKeyboardButton(
            text="Activity by client.",
            callback_data="by_client_click")],
        [InlineKeyboardButton(
            text="Recent queries.",
            callback_data="show_recent_queries_click")],
        [back_to_main_menu_button]])


keyboard_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Search by keyword.",
                              callback_data="keyword_search_click")],
        [InlineKeyboardButton(text="Search by genre and year range.",
                              callback_data="genre_year_search_click")],
        #[InlineKeyboardButton(text="Perform custom search.",
        #                      callback_data="main_menu_3_click")],
        [InlineKeyboardButton(text="View popular or recent queries.",
                              callback_data="show_stat_button_click")]])


cancel_search_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[back_to_main_menu_button]]
)


def generate_navigation_keyboard(limit: int, current: int, count: int):
    navigation_keyboard = []
    if current > 0:
        navigation_keyboard.append(prev_page_button)
    if current + limit < count:
        navigation_keyboard.append(next_page_button)
    return InlineKeyboardMarkup(inline_keyboard=[
        navigation_keyboard,
        [back_to_main_menu_button]])


def generate_genres_keyboard(list_genres):
    genres_keyboard = []
    i = 0
    while i+1 < len(list_genres):
        genres_keyboard.append([InlineKeyboardButton(
            text=list_genres[i],
            callback_data="genre_"+list_genres[i]),
            InlineKeyboardButton(
                text=list_genres[i+1],
                callback_data="genre_"+list_genres[i+1])])
        i += 2
    if i < len(list_genres):
        genres_keyboard.append([InlineKeyboardButton(
            text=list_genres[i],
            callback_data="genre_"+list_genres[i])])
    genres_keyboard.append([back_to_main_menu_button])
    return InlineKeyboardMarkup(inline_keyboard=genres_keyboard)
