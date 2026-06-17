import curses
import urllib.request
from curses import wrapper
import textwrap
from modules import pretty_print, splitElem, checkValid  # Import needed functions
import pytz

def fetch_tle_data():
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    with urllib.request.urlopen(url) as response:
        return response.read().decode('utf-8')

def parse_tle_data(raw_data):
    lines = raw_data.split('\n')
    satellites = []
    
    i = 0
    while i < len(lines) - 2:
        if lines[i].strip() and lines[i+1].startswith('1 ') and lines[i+2].startswith('2 '):
            name = lines[i].strip()
            line1 = lines[i+1].strip()
            line2 = lines[i+2].strip()
            satellites.append((name, line1, line2))
            i += 3
        else:
            i += 1
    
    return satellites
 
def display_banner(stdscr, y_offset=0):
    banner = [
        "  ___________           ___________             ",
        " /   _____/  | _____.__.\\_   _____/__.__. ____  ",
        " \\_____  \\|  |/ <   |  | |    __)<   |  |/ __ \\ ",
        " /        \\    < \\___  | |        \\___  \\  ___/ ",
        "/_______  /__|_ \\/ ____|/_______  / ____|\\___  >",
        "        \\/     \\/\\/             \\/\\/         \\/ "
    ]
    
    max_y, max_x = stdscr.getmaxyx()
    start_y = y_offset
    
    for i, line in enumerate(banner):
        if start_y + i < max_y - 1:
            stdscr.addstr(start_y + i, (max_x - len(line)) // 2, line, curses.A_BOLD | curses.color_pair(4))

def display_satellite(stdscr, satellite, show_basic=True):
    stdscr.clear()
    name, line1, line2 = satellite
    
    # Display banner at top
    display_banner(stdscr)
    
    max_y, max_x = stdscr.getmaxyx()
    current_line = 7  # Below banner
    
    if show_basic:
        # Basic TLE display
        if current_line < max_y - 1:
            stdscr.addstr(current_line, 0, name, curses.A_BOLD)
            current_line += 2
        
        if current_line < max_y - 1:
            stdscr.addstr(current_line, 0, line1)
            current_line += 1
        
        if current_line < max_y - 1:
            stdscr.addstr(current_line, 0, line2)
            current_line += 2
        
        if current_line < max_y - 1:
            stdscr.addstr(current_line, 0, "Press 'd' for detailed view, any other key to return", curses.A_DIM)
    else:
        # Detailed TLE display
        pretty_print(satellite, stdscr, current_line)
        if max_y - 1 > current_line:
            stdscr.addstr(max_y - 1, 0, "Press any key to return to list", curses.A_DIM)
    
    stdscr.refresh()
    key = stdscr.getch()
    
    # Toggle between basic and detailed view
    if show_basic and key == ord('d'):
        display_satellite(stdscr, satellite, show_basic=False)

def main(stdscr):
    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    
    # Initialize curses
    curses.curs_set(0)  # Hide cursor
    stdscr.clear()
    
    # Display loading message with banner
    display_banner(stdscr)
    max_y, max_x = stdscr.getmaxyx()
    if max_y > 7:
        stdscr.addstr(7, 0, "[*] Fetching TLE data from Celestrak...", curses.A_BOLD | curses.color_pair(4))
    stdscr.refresh()
    
    try:
        # Fetch and parse data
        raw_data = fetch_tle_data()
        satellites = parse_tle_data(raw_data)
    except Exception as e:
        stdscr.clear()
        display_banner(stdscr)
        if max_y > 7:
            stdscr.addstr(7, 0, f"Error fetching data: {str(e)}", curses.A_BOLD | curses.color_pair(1))
            stdscr.addstr(9, 0, "Press any key to exit...")
        stdscr.refresh()
        stdscr.getch()
        return
    
    # Main UI loop
    current_selection = 0
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        # Display banner
        display_banner(stdscr)
        
        # Display header below banner
        if max_y > 7:
            header = "Active Satellite TLE Data (↑/↓ to navigate, ENTER to select, q to quit)"
            stdscr.addstr(7, 0, header[:max_x-1], curses.A_BOLD)
            stdscr.addstr(8, 0, "-" * (max_x-1))
        
        # Calculate how many items we can display
        items_start_y = 9
        items_per_page = max_y - items_start_y - 2  # Leave space for footer
        start_index = max(0, current_selection - items_per_page // 2)
        end_index = min(len(satellites), start_index + items_per_page)
        
        # Display satellite list
        for i in range(start_index, end_index):
            y_pos = items_start_y + (i - start_index)
            if y_pos >= max_y - 1:
                continue
                
            name = satellites[i][0]
            
            # Highlight current selection
            if i == current_selection:
                stdscr.addstr(y_pos, 0, "> " + name[:max_x-3], curses.A_REVERSE)
            else:
                stdscr.addstr(y_pos, 0, "  " + name[:max_x-3])
        
        # Display footer info
        if max_y > 1:
            footer = f"Showing {start_index+1}-{end_index} of {len(satellites)} satellites"
            stdscr.addstr(max_y-1, 0, footer[:max_x-1], curses.A_DIM)
        
        # Get user input
        key = stdscr.getch()
        
        # Handle navigation
        if key == curses.KEY_UP and current_selection > 0:
            current_selection -= 1
        elif key == curses.KEY_DOWN and current_selection < len(satellites) - 1:
            current_selection += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:  # Enter key
            display_satellite(stdscr, satellites[current_selection])
        elif key == ord('q'):
            break
        elif key == curses.KEY_HOME:
            current_selection = 0
        elif key == curses.KEY_END:
            current_selection = len(satellites) - 1
        elif key == curses.KEY_PPAGE:  # Page up
            current_selection = max(0, current_selection - items_per_page)
        elif key == curses.KEY_NPAGE:  # Page down
            current_selection = min(len(satellites) - 1, current_selection + items_per_page)

if __name__ == "__main__":
    wrapper(main)
