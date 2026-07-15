# SkyEye

<img width="2281" height="501" alt="SkyEye" src="https://github.com/user-attachments/assets/9862899a-993c-4016-b5eb-869b58f76e83" />

*A curses-based terminal application for viewing and analyzing satellite Two-Line Element (TLE) data*

## Features

- 📡 Real-time TLE data fetching from Celestrak
- 📊 Detailed orbital parameter analysis with live calculations
- 🖥️ Terminal-based UI with curses interface
- 🛰️ Supports all active satellites
- 🧮 Advanced orbital mechanics calculations including:
  - Epoch dates and time derivatives
  - Mean, eccentric, and true anomalies
  - Orbital elements (inclination, eccentricity, etc.)
  - Position tracking (longitude/latitude)
  - Period and semi-major axis calculations
- 🔍 Checksum validation for TLE data integrity
- ⌨️ Full keyboard navigation with scrolling

## Screenshots

<img width="1156" height="677" alt="MainMenu" src="https://github.com/user-attachments/assets/22ed18ec-431f-4ef8-90ea-e78fa059aab7" />
<img width="1156" height="670" src="https://github.com/user-attachments/assets/5cff5f18-b2c8-4195-a701-dd430efd04b2" />
<img width="1156" height="670" src="https://github.com/user-attachments/assets/f7e22dd0-3cc9-462d-b45c-d54765b4c959" />
<img width="1156" height="670" src="https://github.com/user-attachments/assets/d1d93e74-ccf7-4e1d-b65b-120f86b7a618" />

## Installation

### Prerequisites
- Python 3.6+
- pip (Python package manager)

### Install Dependencies

```bash
pip install numpy ephem pytz
```

### Clone and Run

```bash
git clone https://github.com/WR117H/SkySploit.git
cd SkySploit
python3 skyeye.py
```

## Usage

### Keyboard Controls

| Key | Action |
|-----|--------|
| ↑ / ↓ | Navigate satellite list |
| Enter | View satellite details |
| Page Up / Page Down | Scroll through list |
| Home / End | Jump to first/last satellite |
| q | Quit application |

### Navigation Tips

- Use arrow keys to browse through the list of active satellites
- Press Enter to view detailed orbital parameters for a selected satellite
- The detailed view shows:
  - Satellite name and TLE lines
  - Orbital parameters (inclination, eccentricity, etc.)
  - Current position (longitude/latitude)
  - Period and semi-major axis

## Code Structure

The application is organized into clear, modular components:

- **modules.py**: Helper functions for TLE processing and orbital calculations
- **Satellite Class**: Handles TLE data storage and orbital calculations
- **TLEFetcher**: Fetches and parses data from Celestrak
- **UI Class**: Manages all screen rendering and user interaction
- **SkyEyeApp**: Main application controller

### Key Improvements

1. **Object-Oriented Design**: Clean separation of concerns
2. **Type Hints**: Better code documentation and IDE support
3. **Error Handling**: Robust error handling throughout
4. **Modularity**: Easy to extend or modify individual components
5. **Performance**: Lazy calculation of orbital parameters
6. **Validation**: Checksum validation for TLE data integrity

## Troubleshooting

### Common Issues

1. **Connection Error**: Ensure you have an internet connection to fetch TLE data
2. **Missing Dependencies**: Install required packages: `pip install numpy ephem pytz`
3. **Terminal Size**: Minimum terminal size of 80x24 recommended for optimal display

### Error Messages

- `Failed to fetch TLE data`: Internet connection or Celestrak service issue
- `Invalid TLE data`: Data corruption or format mismatch
- `Failed to calculate parameters`: Invalid TLE format or calculation error

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Data provided by [Celestrak](https://celestrak.org/)
- Built with Python and the curses library
- Orbital mechanics calculations based on standard TLE algorithms
```
