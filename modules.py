import numpy as np
from colorama import Fore
from datetime import datetime, timedelta
from curses import wrapper
import pytz
import sys
import curses
import textwrap
import time
from itertools import cycle
import ephem
import readline 

pdt = pytz.timezone('US/Pacific')

sqrt = np.sqrt
pi = np.pi
sin = np.sin
cos = np.cos

GM = 398600.4418



def splitElem(tle):
    """Split TLE tuple into title, line1, line2"""
    if isinstance(tle, tuple) and len(tle) == 3:
        return tle[0], tle[1], tle[2]
    elif isinstance(tle, str):
        parts = tle.split('\n')
        if len(parts) >= 3:
            return parts[0].strip(), parts[1].strip(), parts[2].strip()
    return None, None, None

def spinning_cursor():
    # The animation sequence
    frames = ["[-]", r"[\]", "[|]", "[/]"] 
    return cycle(frames)

def spinner(duration_sec=3, message="Loading"):
    spinner = spinning_cursor()
    end_time = time.time() + duration_sec
    
    while time.time() < end_time:
        # Spinner BEFORE message (changed order here)
        sys.stdout.write(f"\r{next(spinner)} {message}")
        sys.stdout.flush()
        time.sleep(0.1)  # Adjust speed here
    
    # Clear the spinner (updated spacing calculation)
    sys.stdout.write("\r" + " " * (len(message) + 5) + "\r")
    sys.stdout.flush()

def checkValid(tle):
    "Checks with checksum to make sure element is valid"
    title, line1, line2 =  splitElem(tle)

    return line1[0] == '1' and line2[0] == '2' and \
           line1[2:7] == line2[2:7] and \
           int(line1[-1]) == doChecksum(line1) and int(line2[-1]) == doChecksum(line2)

def stringScientificNotationToFloat(sn):
    "Specific format is 5 digits, a + or -, and 1 digit, ex: 01234-5 which is 0.01234e-5"
    return 0.00001*float(sn[5]) * 10**int(sn[6:])

def eccentricAnomalyFromMean(mean_anomaly, eccentricity, initValue,
                           maxIter=500, maxAccuracy=0.0001):
    """Approximates Eccentric Anomaly from Mean Anomaly
       All input and outputs are in radians"""
    e0 = initValue
    for _ in range(maxIter):
        e1 = e0 - (e0 - eccentricity * sin(e0) - mean_anomaly) / (1.0 - eccentricity * cos(e0))
        if abs(e1-e0) < maxAccuracy:
            return e1
        e0 = e1
    return e0

def pretty_print(tle, stdscr, y_offset=0):
    """Display TLE info with perfect formatting and error handling"""
    title, line1, line2 = splitElem(tle)
    max_y, max_x = stdscr.getmaxyx()
    current_line = y_offset
    
    # Safe write function
    def safe_addstr(y, x, text, attr=0):
        try:
            # Ensure we're within screen bounds
            if 0 <= y < max_y and 0 <= x < max_x:
                # Truncate text to fit available space
                text = text[:max_x - x]
                stdscr.addstr(y, x, text, attr)
                return True
        except curses.error:
            pass
        return False

    if not checkValid(tle):
        safe_addstr(current_line, 0, "Invalid element.", curses.color_pair(1))
        return

    try:
        # Parse all values
        satellite_number = int(line1[2:7])
        classification = line1[7:8]
        international_designator_year = int(line1[9:11])
        international_designator_launch_number = int(line1[11:14])
        international_designator_piece_of_launch = line1[14:17]
        epoch_year = int(line1[18:20])
        epoch = float(line1[20:32])
        first_time_derivative = float(line1[33:43])
        second_time_derivative = stringScientificNotationToFloat(line1[44:52])
        bstar_drag_term = stringScientificNotationToFloat(line1[53:61])
        the_number_0 = float(line1[62:63])
        element_number = float(line1[64:68])

        satellite = int(line2[2:7])
        inclination = float(line2[8:16])
        right_ascension = float(line2[17:25])
        eccentricity = float(line2[26:33]) * 0.0000001
        argument_perigee = float(line2[34:42])
        mean_anomaly = float(line2[43:51])
        mean_motion = float(line2[52:63])
        revolution = float(line2[63:68])

        # Calculate derived values
        year = 2000 + epoch_year if epoch_year < 70 else 1900 + epoch_year
        epoch_date = datetime(year=year, month=1, day=1, tzinfo=pytz.utc) + timedelta(days=epoch-1)
        diff = datetime.now().replace(tzinfo=pytz.utc) + timedelta(hours=8) - epoch_date
        diff_seconds = 24*60*60*diff.days + diff.seconds + 1e-6*diff.microseconds
        motion_per_sec = mean_motion * 2*pi / (24*60*60)
        offset = diff_seconds * motion_per_sec
        mean_anomaly_updated = (mean_anomaly + offset * 180/pi) % 360
        period = (24*60*60) / mean_motion
        semi_major_axis = ((period/(2*pi))**2 * GM)**(1./3)
        
        # Calculate anomalies
        mean_anomaly_rad = mean_anomaly_updated * pi/180
        eccentric_anomaly = eccentricAnomalyFromMean(
            mean_anomaly=mean_anomaly_rad,
            eccentricity=eccentricity,
            initValue=mean_anomaly_rad
        )
        true_anomaly = 2*np.arctan2(
            sqrt(1+eccentricity) * sin(eccentric_anomaly/2.0), 
            sqrt(1-eccentricity) * cos(eccentric_anomaly/2.0)
        )
        eccentric_anomaly_deg = eccentric_anomaly * 180/pi
        true_anomaly_deg = true_anomaly * 180/pi

        # Compute satellite position
        tle_rec = ephem.readtle(title, line1, line2)
        tle_rec.compute()
        
        # Prepare output with original exact formatting
        sections = [
            [
                "-"*80,
                f"Satellite Name{' '*44}= {title}",
                f"Satellite number{' '*42}= {satellite_number}",
                f"International Designator{' '*32}= YR: {international_designator_year:02d}, LAUNCH #{international_designator_launch_number}, PIECE: {international_designator_piece_of_launch}",
                f"Epoch Date{' '*48}= {epoch_date.strftime('%Y-%m-%d %H:%M:%S.%f %Z')}  (YR:{epoch_year:02d} DAY:{epoch:.11g})",
                f"First Time Derivative of the Mean Motion divided by two{' '*12}= {first_time_derivative:g}",
                f"Second Time Derivative of Mean Motion divided by six{' '*14}= {second_time_derivative:g}",
                f"BSTAR drag term{' '*46}= {bstar_drag_term:g}",
                f"The number 0{' '*50}= {the_number_0:g}",
                f"Element number{' '*47}= {element_number:g}",
                "",
                f"Inclination [Degrees]{' '*40}= {inclination:g}",
                f"Right Ascension of the Ascending Node [Degrees]{' '*20}= {right_ascension:g}",
                f"Eccentricity{' '*49}= {eccentricity:g}",
                f"Argument of Perigee [Degrees]{' '*33}= {argument_perigee:g}",
                f"Mean Anomaly [Degrees] Anomaly{' '*30}= {mean_anomaly_updated:g}",
                f"Eccentric Anomaly{' '*44}= {eccentric_anomaly_deg:g}",
                f"True Anomaly{' '*49}= {true_anomaly_deg:g}",
                f"Mean Motion [Revs per day] Motion{' '*25}= {mean_motion:g}",
                f"Period{' '*55}= {timedelta(seconds=period)}",
                f"Revolution number at epoch [Revs]{' '*28}= {revolution:g}",
                "-"*80,
                f"Semi-Major Axis (a){' '*42}= {semi_major_axis:g}km",
                f"Eccentricity    (e){' '*42}= {eccentricity:g}",
                f"Inclination     (i){' '*42}= {inclination:g}",
                f"Argument of Periapsis (w){' '*35}= {argument_perigee:g}",
                f"Right Ascension of the Ascending Node (Ω){' '*16}= {right_ascension:g}",
                f"True Anomaly (v){' '*45}= {true_anomaly_deg:g}",
                "-"*80,
                f"Longitude{' '*52}= {tle_rec.sublong}",
                f"Latitude{' '*53}= {tle_rec.sublat}",
                "-"*80
            ]
        ]

        # Calculate fixed left margin
        LEFT_MARGIN = max(2, (max_x - 80) // 2)
        
        # Display with error handling
        for section in sections:
            for line in section:
                if current_line >= max_y - 1:
                    if not safe_addstr(max_y-1, (max_x-28)//2, "-- MORE -- Press any key --", curses.A_BOLD):
                        break
                    stdscr.getch()
                    stdscr.clear()
                    current_line = 0
                    max_y, max_x = stdscr.getmaxyx()  # Refresh dimensions
                
                # Handle separator lines
                if line.startswith("-"):
                    if not safe_addstr(current_line, (max_x-len(line))//2, line, curses.A_BOLD):
                        current_line += 1
                        continue
                else:
                    if not safe_addstr(current_line, LEFT_MARGIN, line[:max_x-LEFT_MARGIN]):
                        current_line += 1
                        continue
                
                current_line += 1

        safe_addstr(min(current_line, max_y-1), (max_x-23)//2, "Press any key to return...", curses.A_DIM)
        stdscr.refresh()
        stdscr.getch()

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        safe_addstr(0, (max_x-len(error_msg))//2, error_msg, curses.color_pair(1))
        stdscr.refresh()
        stdscr.getch()
def doChecksum(line):
    """The checksums for each line are calculated by adding the all numerical digits on that line, including the 
       line number. One is added to the checksum for each negative sign (-) on that line. All other non-digit 
       characters are ignored.
       @note this excludes last char for the checksum thats already there."""
    return sum(map(int, filter(lambda c: c >= '0' and c <= '9', line[:-1].replace('-','1')))) % 10



if __name__ == "__main__":
    banner()

    name = input("Name of Satellite > ")
    lineOne = input("TLE Line One > ")
    lineTwo = input("TLE Line Two > ")
    constructedTLE = name + "\n" + lineOne + "\n" + lineTwo
    try:
        print()
        spinner(5, "Calculating the Information")
        pretty_print(constructedTLE)
    except IndexError:
        print("["+Fore.LIGHTRED_EX+"!"+Fore.RESET+"]"+f" Something's wrong with the name: {name}.")

