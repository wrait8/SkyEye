# skyeye.py
"""
SkyEye - A curses-based terminal application for viewing and analyzing satellite TLE data
"""

import curses
import urllib.request
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import ephem

# Import from modules
from modules import (
    check_valid, split_elem, checksum, 
    calculate_orbital_elements, spinner,
    PDT, PI, SIN, COS, SQRT, GM
)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class Satellite:
    """Represents a satellite with its TLE data and orbital parameters"""
    name: str
    line1: str
    line2: str
    
    # Calculated parameters (lazy loaded)
    _parameters: Optional[Dict[str, Any]] = None
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Get or calculate orbital parameters"""
        if self._parameters is None:
            self._parameters = calculate_orbital_elements((self.name, self.line1, self.line2))
        return self._parameters
    
    def is_valid(self) -> bool:
        """Check if TLE data is valid"""
        return check_valid((self.name, self.line1, self.line2))
    
    def __str__(self) -> str:
        return f"{self.name}\n{self.line1}\n{self.line2}"


# =============================================================================
# TLE Data Fetcher
# =============================================================================

class TLEFetcher:
    """Fetches and parses TLE data from Celestrak"""
    
    TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    
    @classmethod
    def fetch(cls) -> List[Satellite]:
        """Fetch and parse TLE data from Celestrak"""
        try:
            with urllib.request.urlopen(cls.TLE_URL) as response:
                raw_data = response.read().decode('utf-8')
            return cls._parse(raw_data)
        except Exception as e:
            raise ConnectionError(f"Failed to fetch TLE data: {str(e)}")
    
    @staticmethod
    def _parse(raw_data: str) -> List[Satellite]:
        """Parse raw TLE data into Satellite objects"""
        lines = raw_data.split('\n')
        satellites = []
        
        i = 0
        while i < len(lines) - 2:
            if (lines[i].strip() and 
                lines[i + 1].startswith('1 ') and 
                lines[i + 2].startswith('2 ')):
                
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                satellite = Satellite(name, line1, line2)
                if satellite.is_valid():
                    satellites.append(satellite)
                i += 3
            else:
                i += 1
        
        return satellites


# =============================================================================
# UI Components
# =============================================================================

class UI:
    """Handles all UI rendering and interaction"""
    
    # Color pairs
    COLOR_RED = 1
    COLOR_YELLOW = 2
    COLOR_GREEN = 3
    COLOR_BLUE = 4
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.max_y, self.max_x = stdscr.getmaxyx()
        self._init_colors()
        
    def _init_colors(self):
        """Initialize color pairs"""
        curses.start_color()
        curses.init_pair(self.COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(self.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.curs_set(0)  # Hide cursor
        
    def refresh_dimensions(self):
        """Refresh screen dimensions"""
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        
    def clear(self):
        """Clear the screen"""
        self.stdscr.clear()
        
    def refresh(self):
        """Refresh the screen"""
        self.stdscr.refresh()
        
    def getch(self) -> int:
        """Get a character from the user"""
        return self.stdscr.getch()
        
    def add_text(self, y: int, x: int, text: str, attr: int = 0) -> bool:
        """Safely add text to the screen"""
        try:
            if 0 <= y < self.max_y and 0 <= x < self.max_x:
                text = text[:self.max_x - x]
                self.stdscr.addstr(y, x, text, attr)
                return True
        except curses.error:
            pass
        return False
    
    def display_banner(self, y_offset: int = 0):
        """Display the SkyEye banner"""
        banner = [
            "  ___________           ___________             ",
            " /   _____/  | _____.__.\\_   _____/__.__. ____  ",
            " \\_____  \\|  |/ <   |  | |    __)<   |  |/ __ \\ ",
            " /        \\    < \\___  | |        \\___  \\  ___/ ",
            "/_______  /__|_ \\/ ____|/_______  / ____|\\___  >",
            "        \\/     \\/\\/             \\/\\/         \\/ "
        ]
        
        start_y = y_offset
        for i, line in enumerate(banner):
            if start_y + i < self.max_y - 1:
                x = (self.max_x - len(line)) // 2
                self.add_text(start_y + i, x, line, 
                            curses.A_BOLD | curses.color_pair(self.COLOR_BLUE))
    
    def display_loading(self, message: str = "Loading...", y_offset: int = 7):
        """Display a loading message with spinner"""
        self.add_text(y_offset, 0, f"⏳ {message}", 
                     curses.A_BOLD | curses.color_pair(self.COLOR_BLUE))
        self.refresh()


# =============================================================================
# Application
# =============================================================================

class SkyEyeApp:
    """Main application class"""
    
    def __init__(self, stdscr):
        self.ui = UI(stdscr)
        self.satellites: List[Satellite] = []
        self.current_selection: int = 0
        
    def run(self):
        """Run the main application loop"""
        self.ui.clear()
        self.ui.display_banner()
        
        # Fetch TLE data
        self.ui.display_loading("Fetching TLE data from Celestrak...")
        
        try:
            self.satellites = TLEFetcher.fetch()
        except Exception as e:
            self.ui.clear()
            self.ui.display_banner()
            self.ui.add_text(7, 0, f"Error: {str(e)}", 
                           curses.A_BOLD | curses.color_pair(self.ui.COLOR_RED))
            self.ui.add_text(9, 0, "Press any key to exit...")
            self.ui.refresh()
            self.ui.getch()
            return
        
        # Main loop
        while True:
            self._display_list()
            key = self.ui.getch()
            
            if not self._handle_key(key):
                break
    
    def _display_list(self):
        """Display the satellite list"""
        self.ui.clear()
        self.ui.display_banner()
        
        self.ui.refresh_dimensions()
        max_y, max_x = self.ui.max_y, self.ui.max_x
        
        # Header
        if max_y > 7:
            header = "Active Satellite TLE Data (↑/↓ to navigate, ENTER to select, q to quit)"
            self.ui.add_text(7, 0, header[:max_x - 1], curses.A_BOLD)
            self.ui.add_text(8, 0, "-" * (max_x - 1))
        
        # Calculate visible range
        items_start_y = 9
        items_per_page = max_y - items_start_y - 2
        start_index = max(0, self.current_selection - items_per_page // 2)
        end_index = min(len(self.satellites), start_index + items_per_page)
        
        # Display satellites
        for i in range(start_index, end_index):
            y_pos = items_start_y + (i - start_index)
            if y_pos >= max_y - 1:
                continue
            
            name = self.satellites[i].name
            if i == self.current_selection:
                self.ui.add_text(y_pos, 0, f"> {name[:max_x - 3]}", curses.A_REVERSE)
            else:
                self.ui.add_text(y_pos, 0, f"  {name[:max_x - 3]}")
        
        # Footer
        if max_y > 1:
            footer = f"Showing {start_index + 1}-{end_index} of {len(self.satellites)} satellites"
            self.ui.add_text(max_y - 1, 0, footer[:max_x - 1], curses.A_DIM)
        
        self.ui.refresh()
    
    def _handle_key(self, key: int) -> bool:
        """Handle keyboard input, return False to exit"""
        items_per_page = self.ui.max_y - 9 - 2
        
        if key == curses.KEY_UP and self.current_selection > 0:
            self.current_selection -= 1
        elif key == curses.KEY_DOWN and self.current_selection < len(self.satellites) - 1:
            self.current_selection += 1
        elif key in [curses.KEY_ENTER, 10, 13]:  # Enter
            self._display_satellite_detail(self.satellites[self.current_selection])
        elif key == ord('q'):
            return False
        elif key == curses.KEY_HOME:
            self.current_selection = 0
        elif key == curses.KEY_END:
            self.current_selection = len(self.satellites) - 1
        elif key == curses.KEY_PPAGE:
            self.current_selection = max(0, self.current_selection - items_per_page)
        elif key == curses.KEY_NPAGE:
            self.current_selection = min(len(self.satellites) - 1, 
                                        self.current_selection + items_per_page)
        return True
    
    def _display_satellite_detail(self, satellite: Satellite):
        """Display detailed satellite information"""
        self.ui.clear()
        self.ui.display_banner()
        
        self.ui.refresh_dimensions()
        current_line = 7
        
        # Use the calculate_orbital_elements function from modules
        calculate_orbital_elements(
            (satellite.name, satellite.line1, satellite.line2),
            self.ui.stdscr,
            current_line
        )


# =============================================================================
# Entry Point
# =============================================================================

def main(stdscr):
    """Main entry point for curses wrapper"""
    app = SkyEyeApp(stdscr)
    app.run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nExiting SkyEye...")
        import sys
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import sys
        sys.exit(1)
