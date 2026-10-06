import logic
import re
from typing import Any, Optional

LIMIT = 10


def input_by_list(values: list[str], text: str) -> Optional[str]:
    """
    Prompt the user to select an item from a list by its index or value.
    :return: selected value, or None if the list is empty.
    """
    if len(values) > 0:
        while True:
            print(text)
            for element in enumerate(values, start=1):
                print(f"{element[0]}. {element[1]}")
            element = input("Enter number or value:").strip()
            if element in values:
                return element
            if element.isdigit() and 0 < int(element) <= len(values):
                return values[int(element) - 1]
            print("[!] Error!\nValue must match the list.")
    else:
        print("Parameter was not found. This filter will be skipped.")
        return None


def ask_yes(prompt: str) -> bool:
    """
    Ask the user a yes/no question.
    :return: True if the user answered "y", False otherwise.
    """
    return input(prompt).strip().lower() == "y"


def input_limit(prompt: str, default: int = 5, max_limit: int = 10) -> int:
    """
    Asc user to input limit value and check it
    :return: validated limit value.
    """
    limit_num = input(prompt).strip()
    lim = int(limit_num) if limit_num.isdigit() else default
    return lim if 0 < lim <= max_limit else default


def input_year(min_year: int, max_year: int, text: str) -> int:
    """
    Prompt the user to enter a year within the specified range, or press
    Enter to skip.
    :return: valid year integer, or -1 if skipped.
    """
    while True:
        y = input(text).strip()
        if y == "":
            return -1
        if y.isdigit() and min_year <= int(y) <= max_year:
            return int(y)
        print("[!] Error!\n[!] Year must be a number and within the range",
              f"{min_year} - {max_year}.\n[!] Or enter an empty line.")


def check_year(min_year: int, max_year: int) -> tuple[int, int, str]:
    """
    Interactive helper to check and get a range of release years
    from the user.
    :return: tuple of start and end years and info about changes.
    """
    print(f"Available year range: {min_year} - {max_year}")
    print("If only one year is entered, search will be performed",
          "within that year.")
    print("If no years are specified, search will be performed",
          "within the entire available period.")
    s = "Enter start year or press Enter to skip: "
    y1 = input_year(min_year, max_year, s)
    s = "Enter end year or press Enter to skip: "
    y2 = input_year(min_year, max_year, s)
    changed = ""
    if y1 == -1 and y2 == -1:
        y1 = min_year
        y2 = max_year
        changed = (f"Years was not input by user. "
                   f"Search will use max range {y1} - {y2}")
    elif y1 == -1 and y2 != -1:
        y1 = y2
        changed = (f"One of the years was not input by user. "
                   f"Search will use one year as range {y1}")
    elif y2 == -1 and y1 != -1:
        changed = (f"Years was not input by user. "
                   f"Search will use one year as range {y1}")
        y2 = y1
    elif y2 < y1:
        changed = (f"The years input was incorrect 'from {y1} -  to {y2} '"
                   f"Years will be changed to 'from {y2} to {y1}'")
        y1, y2 = y2, y1
    return y1, y2, changed


def input_text() -> str:
    """
    Prompt the user to enter a keyword containing only letters and spaces.
    :return: validated keyword string.
    """
    print("-" * 41)
    pattern = r"^[a-zA-Zа-яА-ЯёЁ\s]+$"
    while True:
        word = input("Enter keyword: ").strip()
        if re.match(pattern, word):
            print("-" * 41)
            return word
        print(f"[!] Error!\n[!] Keyword cannot be empty and can only contain "
              f"letters and spaces.")


def show_film(film_id: int) -> str:
    """
    Display detailed information about a specific film and prompt
    for navigation choice.
    :return: user choice string (e.g., 'm' for main menu).
    """
    film = logic.get_film(film_id)
    if not film:
        print("Film not found")
    else:
        title, description, release_year, length, rating, genres, actors = film
        print()
        print("-" * 60)
        print(f"Title: {title}")
        print(f"Release year: {release_year}")
        print("-" * 60)
        print(f"Length: {length} min.")
        print(f"Age rating: {rating}")
        print(f"Genres: {genres if genres else 'Not specified'}")
        print(f"Actors: {actors if actors else 'No data'}")
        print("-" * 60)
        print(f"Description: {description}")
        print("-" * 60)
    return input("Press [m] to main menu, else you will return to film list")


def show_result(films: tuple[Any, ...], size: int, params: dict[str, Any])\
        -> None:
    """
    Display search results in a paginated table format with navigation options.
    """
    count_cur = 0
    if not films:
        print("No movies found matching your request")
    else:
        while count_cur <= size:
            ids = []
            print()
            print(f"Found {size} movies. Showing movies from {count_cur + 1}",
                  f"to {count_cur + len(films)}.")
            print("-" * 41)
            print(f"|{'ID':<4}|{'Title':<20}|{'Year':<6}|{'Rating':<6}|")
            print("-" * 41)
            for film in films:
                ids.append(film[0])
                title = (
                    film[1] if len(film[1]) <= 19 else film[1][:16] + "...")
                print(f"|{film[0]:<4}|{title:<20}|{film[2]:<6}|{film[3]:<6}|")
            print("-" * 41)
            text = "Navigation:"
            text += (" [p] Previous page |" if count_cur > 0 else "")
            text += (
                " [n] Next page |" if count_cur + len(films) < size
                else "")
            text += " [m] Return to menu"
            while True:
                print(text)
                print("Or enter ID of the selected movie for detailed info")
                user_choice = input("Your choice: ").strip().lower()
                if user_choice == "p" and count_cur > 0:
                    count_cur -= LIMIT
                    films = logic.next_film(params, LIMIT, count_cur)
                    break
                elif user_choice == "n" and count_cur + len(films) < size:
                    count_cur += LIMIT
                    films = logic.next_film(params, LIMIT, count_cur)
                    break
                elif user_choice == "m":
                    count_cur = size + 1
                    break
                elif user_choice.isdigit() and int(user_choice) in ids:
                    if show_film(int(user_choice)).strip().lower() == "m":
                        count_cur = size + 1
                    break
                else:
                    print("Invalid menu item selected. Please try again.")


def is_saved_state(status: bool) -> None:
    """
    Notify the user if logging the search query into MongoDB failed.
    """
    if not status:
        print("[!] Warning: Search was successful, "
              "but logs could not be saved.")


def run_search(params: dict[str, Any], search_type: str) -> None:
    """
    Perform a search for the given params/search type
    """
    films, count, is_saved = logic.search(params, LIMIT, search_type)
    is_saved_state(is_saved)
    show_result(films, count, params)


def key_word() -> None:
    """
    Handle keyword-based search workflow.
    """
    print("--- Keyword search ---")
    params = {"keyword": input_text()}
    run_search(params, "Keyword")


def custom_search() -> None:
    """
    Handle custom interactive multi-filter search workflow.
    """
    print("--- Custom search ---")
    params = {}
    genres_limits = {}
    print("Enter [y] for the filters you want to add")
    if ask_yes("Add genre filter? [y] "):
        genres_limits = logic.get_genres()
        s = "Available genre list:"
        g = input_by_list(list(genres_limits.keys()), s)
        if g is not None:
            params["genre"] = g
    if ask_yes("Add year filter? [y] "):
        if len(genres_limits) > 0:
            min_year, max_year = genres_limits[params["genre"]]
        else:
            min_year, max_year = logic.get_years()
        y1, y2, changed = check_year(min_year, max_year)
        params["year_from"] = y1
        params["year_to"] = y2
        if changed != "":
            print(changed)
            params["exception"] = changed
    if ask_yes("Add keyword filter? [y] "):
        params["keyword"] = input_text()
    if ask_yes("Add age rating filter? [y] "):
        r = input_by_list(logic.get_rating(),
                          "Available age rating list:")
        if r is not None:
            params["rating"] = r
    run_search(params, "Custom")


def stat_menu() -> None:
    """
    Display the statistics menu options.
    """
    print()
    print("-" * 14 + "STATISTIC MENU" + "-" * 14)
    print("1. Popular search types.")
    print("2. Top parameters by search type.")
    print("3. Activity by client.")
    print("4. Recent queries.")
    print("5. Return to Main Menu.")
    print("-" * 42)


def format_row(cells: list[Any], widths: list[int]) -> str:
    """
    Format one table row
    """
    return "|" + "|".join(f"{str(c):<{w}}"
                          for c, w in zip(cells, widths)) + "|"


def print_table(headers: list[str], rows: list[list[Any]]) -> None:
    """
    Print rows as a text table
    """
    widths = [max(len(str(v)) for v in col) for col in zip(headers, *rows)]
    line = "-" * (sum(widths) + len(widths) + 1)

    print(line)
    print(format_row(headers, widths))
    print(line)
    for row in rows:
        print(format_row(row, widths))
    print(line)


def statistic() -> None:
    """
    Handle viewing various application statistics and analytics options.
    """
    while True:
        stat_menu()
        user_choice = input("Select menu item: ").strip()
        print()
        try:
            match user_choice:
                case "1":
                    stat = logic.get_popular()
                    print("--- Popular search types ---")
                    if not stat:
                        print("No statistics yet.")
                    else:
                        rows = [[item['_id'], item['count']] for item in stat]
                        print_table(["Type", "Query count"], rows)
                case "2":
                    t = "Choose query type for statistics."
                    q_type = input_by_list(["Keyword", "Custom",
                                            "genre_year"], t)
                    lim = input_limit(
                        "How many top queries to show? (default 5, max 10): ")
                    print(f"--- Top {lim} parameters by {q_type} ---")
                    top_params = logic.top_in_type(q_type, lim)
                    if not top_params:
                        print("No statistics yet.")
                    else:
                        rows = []
                        for item in top_params:
                            if ('keyword' in item['_id']['params'] and
                                    item['_id']['params']['keyword'] == ""):
                                del item['_id']['params']['keyword']
                            rows.append([str(item['_id']['params']),
                                         item['count_query']])
                        print_table(["Params", "Query count"], rows)
                    input("Press ENTER to return to the statistics menu...")
                case "3":
                    clients = logic.stat_by_client()
                    print("--- Activity by client ---")
                    if not clients:
                        print("No statistics yet.")
                    else:
                        rows = [[item['_id'], item['count']]
                                for item in clients]
                        print_table(["Client", "Query count"], rows)
                case "4":
                    lim = input_limit(
                        "How many recent queries to show? "
                        "(default 5, max 10): ")
                    print(f"--- Recent {lim} queries ---")
                    recent_params = logic.get_recent_queries(lim)
                    if not recent_params:
                        print("No statistics yet.")
                    else:
                        rows = []
                        for item in recent_params:
                            ts = item['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                            rows.append([ts, item['client'],
                                         item['search_type'],
                                         str(item['params']),
                                         item['count'],
                                         'User entered incorrect years'
                                         if item.get('exception') else ''])
                        print_table(["Timestamp", "Client", "Search type",
                                     "Params", "Results", "Exception"], rows)
                    input("Press ENTER to return to the statistics menu...")
                case "5":
                    break
                case _:
                    print("Invalid menu item selected. Please try again.")
        except logic.MongoError as e:
            print(f"[!] Could not load statistics: {e}")


def genre_years() -> None:
    """
    Handle search by genre and release year range workflow.
    """
    print("--- Search by genre and year range ---")
    genres_limits = logic.get_genres()
    g = input_by_list(list(genres_limits.keys()),
                      "Available genre list:")
    if g is not None:
        min_year, max_year = genres_limits[g]
    else:
        min_year, max_year = logic.get_years()
    y1, y2, changed = check_year(min_year, max_year)
    params = {"year_from": y1, "year_to": y2, "genre": g}
    if changed != "":
        print(changed)
        params["exception"] = changed
    run_search(params, "genre_year")


def menu() -> None:
    """
    Display the main menu options.
    """
    print("-" * 19 + "MENU" + "-" * 19)
    print("1. Search by keyword.")
    print("2. Search by genre and year range.")
    print("3. Perform custom search.")
    print("4. View popular or recent queries.")
    print("5. Exit application.")
    print("-" * 42)


def main() -> None:
    """
    Main entry point for running the application CLI.
    """
    print("Initializing application...")
    try:
        mongo_available = logic.init_app()
    except Exception as e:
        print(f"[!] Cannot connect to MySQL: {e}")
    else:
        if mongo_available:
            print("All databases successfully loaded!")
        else:
            print("[!] Warning: could not reach MongoDB during startup. "
                  "There may be issues saving or viewing search statistics.")
        while True:
            menu()
            choice = input("Select menu item: ").strip()
            try:
                match choice:
                    case "1":
                        key_word()
                    case "2":
                        genre_years()
                    case "3":
                        custom_search()
                    case "4":
                        statistic()
                    case "5":
                        print("Program terminated.")
                        break
                    case _:
                        print("Invalid menu item selected. Please try again.")
            except logic.DatabaseAccessError as e:
                print(f"[!] Cannot connect to MySQL: {e}")
                break
            except Exception as e:
                print(e)
                break


if __name__ == "__main__":
    main()
