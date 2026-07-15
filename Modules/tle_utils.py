# Modules/tle_utils.py
"""
TLE Utility Functions
Handles TLE parsing, validation, and orbital calculations
"""

import numpy as np
import pytz
import ephem
from datetime import datetime, timedelta
import curses

# Constants
GM = 398600.4418
PI = np.pi
SQRT = np.sqrt
SIN = np.sin
COS = np.cos
PDT = pytz.timezone('US/Pacific')


def split_elem(tle):
    """
    Split TLE tuple into title, line1, line2
    
    Args:
        tle: Either a tuple (name, line1, line2) or a string with newlines
        
    Returns:
        tuple: (title, line1, line2) or (None, None, None) if invalid
    """
    if isinstance(tle, tuple) and len(tle) == 3:
        return tle[0], tle[1], tle[2]
    elif isinstance(tle, str):
        parts = tle.split('\n')
        if len(parts) >= 3:
            return parts[0].strip(), parts[1].strip(), parts[2].strip()
    return None, None, None


def checksum(line: str) -> int:
    """
    Calculate TLE checksum for a line
    
    The checksums for each line are calculated by adding all numerical digits 
    on that line, including the line number. One is added to the checksum for 
    each negative sign (-) on that line. All other non-digit characters are ignored.
    
    Args:
        line: TLE line to calculate checksum for
        
    Returns:
        int: Checksum value (0-9)
    """
    return sum(map(int, filter(lambda c: c >= '0' and c <= '9', 
                              line[:-1].replace('-', '1')))) % 10


def check_valid(tle) -> bool:
    """
    Check if TLE data is valid using checksums
    
    Args:
        tle: TLE data as tuple or string
        
    Returns:
        bool: True if valid, False otherwise
    """
    title, line1, line2 = split_elem(tle)
    
    if not all([title, line1, line2]):
        return False
    
    return (line1[0] == '1' and line2[0] == '2' and
            line1[2:7] == line2[2:7] and
            int(line1[-1]) == checksum(line1) and
            int(line2[-1]) == checksum(line2))


def scientific_notation_to_float(sn: str) -> float:
    """
    Convert specific scientific notation format to float
    
    Format is 5 digits, a + or -, and 1 digit
    Example: 01234-5 -> 0.01234e-5
    
    Args:
        sn: Scientific notation string
        
    Returns:
        float: Converted value
    """
    return 0.00001 * float(sn[5]) * 10 ** int(sn[6:])


def eccentric_anomaly_from_mean(mean_anomaly: float, eccentricity: float,
                                init_value: float, max_iter: int = 500,
                                max_accuracy: float = 0.0001) -> float:
    """
    Approximate Eccentric Anomaly from Mean Anomaly using Newton's method
    
    Args:
        mean_anomaly: Mean anomaly in radians
        eccentricity: Orbital eccentricity
        init_value: Initial guess for eccentric anomaly
        max_iter: Maximum iterations
        max_accuracy: Convergence tolerance
        
    Returns:
        float: Eccentric anomaly in radians
    """
    e0 = init_value
    for _ in range(max_iter):
        e1 = e0 - (e0 - eccentricity * SIN(e0) - mean_anomaly) / (1.0 - eccentricity * COS(e0))
        if abs(e1 - e0) < max_accuracy:
            return e1
        e0 = e1
    return e0


def calculate_orbital_elements(tle, stdscr=None, y_offset: int = 0):
    """
    Calculate and display orbital elements from TLE data
    
    Args:
        tle: TLE data as tuple or string
        stdscr: Curses screen object (optional)
        y_offset: Starting line offset (optional)
        
    Returns:
        dict: Orbital parameters if stdscr is None, otherwise displays in curses
    """
    title, line1, line2 = split_elem(tle)
    
    if not check_valid(tle):
        if stdscr:
            stdscr.addstr(y_offset, 0, "Invalid element.", curses.color_pair(1))
            stdscr.refresh()
            stdscr.getch()
        return None
    
    try:
        # Parse all values
        params = {
            'satellite_number': int(line1[2:7]),
            'classification': line1[7:8],
            'international_designator_year': int(line1[9:11]),
            'international_designator_launch_number': int(line1[11:14]),
            'international_designator_piece_of_launch': line1[14:17],
            'epoch_year': int(line1[18:20]),
            'epoch': float(line1[20:32]),
            'first_time_derivative': float(line1[33:43]),
            'second_time_derivative': scientific_notation_to_float(line1[44:52]),
            'bstar_drag_term': scientific_notation_to_float(line1[53:61]),
            'the_number_0': float(line1[62:63]),
            'element_number': float(line1[64:68]),
            'satellite': int(line2[2:7]),
            'inclination': float(line2[8:16]),
            'right_ascension': float(line2[17:25]),
            'eccentricity': float(line2[26:33]) * 0.0000001,
            'argument_perigee': float(line2[34:42]),
            'mean_anomaly': float(line2[43:51]),
            'mean_motion': float(line2[52:63]),
            'revolution': float(line2[63:68])
        }
        
        # Calculate derived values
        year = 2000 + params['epoch_year'] if params['epoch_year'] < 70 else 1900 + params['epoch_year']
        params['epoch_date'] = datetime(year=year, month=1, day=1, tzinfo=pytz.utc) + timedelta(days=params['epoch'] - 1)
        
        diff = datetime.now().replace(tzinfo=pytz.utc) + timedelta(hours=8) - params['epoch_date']
        diff_seconds = 24 * 60 * 60 * diff.days + diff.seconds + 1e-6 * diff.microseconds
        motion_per_sec = params['mean_motion'] * 2 * PI / (24 * 60 * 60)
        offset = diff_seconds * motion_per_sec
        params['mean_anomaly_updated'] = (params['mean_anomaly'] + offset * 180 / PI) % 360
        
        params['period'] = (24 * 60 * 60) / params['mean_motion']
        params['semi_major_axis'] = ((params['period'] / (2 * PI)) ** 2 * GM) ** (1. / 3)
        
        # Calculate anomalies
        mean_anomaly_rad = params['mean_anomaly_updated'] * PI / 180
        params['eccentric_anomaly'] = eccentric_anomaly_from_mean(
            mean_anomaly=mean_anomaly_rad,
            eccentricity=params['eccentricity'],
            init_value=mean_anomaly_rad
        )
        
        params['true_anomaly'] = 2 * np.arctan2(
            SQRT(1 + params['eccentricity']) * SIN(params['eccentric_anomaly'] / 2.0),
            SQRT(1 - params['eccentricity']) * COS(params['eccentric_anomaly'] / 2.0)
        )
        
        params['eccentric_anomaly_deg'] = params['eccentric_anomaly'] * 180 / PI
        params['true_anomaly_deg'] = params['true_anomaly'] * 180 / PI
        
        # Get position
        try:
            tle_rec = ephem.readtle(title, line1, line2)
            tle_rec.compute()
            params['longitude'] = tle_rec.sublong
            params['latitude'] = tle_rec.sublat
        except:
            params['longitude'] = 'N/A'
            params['latitude'] = 'N/A'
        
        if stdscr:
            return display_parameters(stdscr, params, title, y_offset)
        
        return params
        
    except Exception as e:
        if stdscr:
            stdscr.addstr(y_offset, 0, f"Error: {str(e)}", curses.color_pair(1))
            stdscr.refresh()
            stdscr.getch()
        return None


def display_parameters(stdscr, params, title, y_offset: int = 0):
    """
    Display orbital parameters in curses window
    
    Args:
        stdscr: Curses screen object
        params: Dictionary of orbital parameters
        title: Satellite name
        y_offset: Starting line offset
        
    Returns:
        bool: True if displayed successfully
    """
    max_y, max_x = stdscr.getmaxyx()
    current_line = y_offset
    
    def safe_addstr(y, x, text, attr=0):
        try:
            if 0 <= y < max_y and 0 <= x < max_x:
                text = text[:max_x - x]
                stdscr.addstr(y, x, text, attr)
                return True
        except curses.error:
            pass
        return False
    
    sections = [
        [
            "-" * 80,
            f"Satellite Name{' '*44}= {title}",
            f"Satellite number{' '*42}= {params['satellite_number']}",
            f"International Designator{' '*32}= YR: {params['international_designator_year']:02d}, LAUNCH #{params['international_designator_launch_number']}, PIECE: {params['international_designator_piece_of_launch']}",
            f"Epoch Date{' '*48}= {params['epoch_date'].strftime('%Y-%m-%d %H:%M:%S.%f %Z')}  (YR:{params['epoch_year']:02d} DAY:{params['epoch']:.11g})",
            f"First Time Derivative of the Mean Motion divided by two{' '*12}= {params['first_time_derivative']:g}",
            f"Second Time Derivative of Mean Motion divided by six{' '*14}= {params['second_time_derivative']:g}",
            f"BSTAR drag term{' '*46}= {params['bstar_drag_term']:g}",
            f"The number 0{' '*50}= {params['the_number_0']:g}",
            f"Element number{' '*47}= {params['element_number']:g}",
            "",
            f"Inclination [Degrees]{' '*40}= {params['inclination']:g}",
            f"Right Ascension of the Ascending Node [Degrees]{' '*20}= {params['right_ascension']:g}",
            f"Eccentricity{' '*49}= {params['eccentricity']:g}",
            f"Argument of Perigee [Degrees]{' '*33}= {params['argument_perigee']:g}",
            f"Mean Anomaly [Degrees] Anomaly{' '*30}= {params['mean_anomaly_updated']:g}",
            f"Eccentric Anomaly{' '*44}= {params['eccentric_anomaly_deg']:g}",
            f"True Anomaly{' '*49}= {params['true_anomaly_deg']:g}",
            f"Mean Motion [Revs per day] Motion{' '*25}= {params['mean_motion']:g}",
            f"Period{' '*55}= {timedelta(seconds=params['period'])}",
            f"Revolution number at epoch [Revs]{' '*28}= {params['revolution']:g}",
            "-" * 80,
            f"Semi-Major Axis (a){' '*42}= {params['semi_major_axis']:g}km",
            f"Eccentricity    (e){' '*42}= {params['eccentricity']:g}",
            f"Inclination     (i){' '*42}= {params['inclination']:g}",
            f"Argument of Periapsis (w){' '*35}= {params['argument_perigee']:g}",
            f"Right Ascension of the Ascending Node (Ω){' '*16}= {params['right_ascension']:g}",
            f"True Anomaly (v){' '*45}= {params['true_anomaly_deg']:g}",
            "-" * 80,
            f"Longitude{' '*52}= {params['longitude']}",
            f"Latitude{' '*53}= {params['latitude']}",
            "-" * 80
        ]
    ]
    
    LEFT_MARGIN = max(2, (max_x - 80) // 2)
    
    for section in sections:
        for line in section:
            if current_line >= max_y - 1:
                if not safe_addstr(max_y - 1, (max_x - 28) // 2, "-- MORE -- Press any key --", curses.A_BOLD):
                    break
                stdscr.getch()
                stdscr.clear()
                current_line = 0
                max_y, max_x = stdscr.getmaxyx()
            
            if line.startswith("-"):
                if not safe_addstr(current_line, (max_x - len(line)) // 2, line, curses.A_BOLD):
                    current_line += 1
                    continue
            else:
                if not safe_addstr(current_line, LEFT_MARGIN, line[:max_x - LEFT_MARGIN]):
                    current_line += 1
                    continue
            
            current_line += 1
    
    safe_addstr(min(current_line, max_y - 1), (max_x - 23) // 2, "Press any key to return...", curses.A_DIM)
    stdscr.refresh()
    stdscr.getch()
    return True
