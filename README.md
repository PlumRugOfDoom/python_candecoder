# CAN Log Decoder

A Python utility for decoding CAN (Controller Area Network) bus log files using DBC (Database CAN) definition files. This tool converts raw CAN data from candump format into human-readable CSV files with decoded signal values.

## Features

- 📊 **DBC-based Decoding**: Automatically decodes CAN messages using DBC database files
- 🔧 **DLC Correction**: Handles mismatched Data Length Codes (DLC) by padding or truncating data
- 📈 **Statistical Analysis**: Provides comprehensive statistics on decoded messages and signals
- 📁 **CSV Export**: Outputs decoded data in wide-format CSV for easy analysis
- 🔍 **Error Reporting**: Detailed logging of DLC adjustments and decoding errors
- 📊 **Per-ID Statistics**: Breakdown of message counts, decoded messages, and corrections by CAN ID

## Requirements

- Python 3.6+
- Required packages:
  - `cantools` - CAN database and message handling
  - `pandas` - Data manipulation and CSV export
  - `argparse` - Command-line argument parsing

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd python_candecoder
```

2. Install dependencies:
```bash
pip install cantools pandas
```

## Usage

### Basic Command

```bash
python decode_can.py --log <logfile> --dbc <dbcfile> --out <output.csv>
```

### Arguments

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--log` | Yes | CAN log file in candump format | - |
| `--dbc` | Yes | DBC database file | - |
| `--out` | No | Output CSV file path | `decoded.csv` |

### Example

```bash
python decode_can.py --log candump.log --dbc vehicle.dbc --out decoded_data.csv
```

## Input Format

### CAN Log Format (candump)

The tool expects log files in candump format:

```
(1234567890.123456) can0 1A3#0102030405060708
(1234567890.234567) can0 2B4#AABBCCDD
```

Format: `(timestamp) interface CAN_ID#DATA`

- **timestamp**: Floating-point Unix timestamp
- **interface**: CAN interface name (e.g., can0, vcan0)
- **CAN_ID**: Hexadecimal CAN message ID
- **DATA**: Hexadecimal payload data

## Output

### CSV File

The tool generates a wide-format CSV file where:
- Each row represents a decoded CAN message
- The first column is the `timestamp`
- Subsequent columns are the decoded signal names from the DBC file
- Signal values are decoded according to DBC specifications (scaling, offset, units)

### Console Statistics

The tool provides detailed statistics including:

1. **Summary Statistics**
   - Total CAN messages in log
   - Total messages decoded (found in DBC)
   - Total signals decoded

2. **Per-CAN-ID Statistics**
   - Message counts per CAN ID
   - Number of successfully decoded messages
   - Number of DLC corrections performed

3. **DLC Adjustments**
   - Compressed overview of Data Length Code corrections
   - Shows original vs. adjusted data for troubleshooting

4. **Decoding Errors**
   - Lists first 30 decoding errors encountered
   - Includes timestamp, CAN ID, and error description

## How It Works

### 1. Log Parsing
- Parses each line of the candump log file
- Extracts timestamp, CAN ID, and hexadecimal data
- Converts hex strings to binary data

### 2. DBC Matching
- Loads the DBC file using cantools
- Matches CAN IDs from the log with message definitions in the DBC

### 3. DLC Correction
- Compares actual data length with expected length from DBC
- **Shorter data**: Pads with null bytes (`\x00`)
- **Longer data**: Truncates to expected length
- Logs all adjustments for verification

### 4. Message Decoding
- Decodes binary data into signal values using DBC definitions
- Applies scaling, offset, and unit conversions
- Handles both signed and unsigned integers, floats, and enums

### 5. Data Export
- Consolidates all decoded signals into a pandas DataFrame
- Sorts by timestamp
- Exports to CSV in wide format

## Error Handling

The tool gracefully handles:
- Invalid log line formats (skipped)
- Unknown CAN IDs not in DBC (logged but not decoded)
- DLC mismatches (corrected with logging)
- Decoding failures (logged with error details)

## Example Output

```
[INFO] Loading DBC file: vehicle.dbc
[INFO] Reading CAN log file: candump.log
[INFO] Generating DataFrame…
[INFO] Done! CSV exported to: decoded.csv

===== SUMMARY =====
  Total CAN messages in log: 15234
  Total messages decoded (found in DBC): 12891
  Total signals decoded: 45

Per-CAN-ID statistics:
  CAN-ID | Total Msgs |  Decoded | DLC Corrected
--------------------------------------------------
0x0001A3 |       2341 |     2341 |             0
0x0002B4 |       1823 |     1823 |            12
0x000315 |       3129 |     3129 |             0

DLC adjustments (compressed overview):
  CAN-ID 0x2B4: 12 messages corrected, first example:
    Timestamp: 1234567890.234567
    DLC: 4 → 8
    Original: aabbccdd
    Adjusted: aabbccdd00000000

===== END INFO =====
```

## Use Cases

- **Automotive diagnostics**: Analyze vehicle CAN bus data
- **Reverse engineering**: Understand CAN message patterns
- **Data logging**: Convert raw logs to structured datasets
- **Testing & validation**: Verify CAN message implementations

## Limitations

- Only supports candump log format
- Requires a complete and accurate DBC file
- Large log files may consume significant memory
- Error list limited to first 30 entries

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This code and documentation were generated with the assistance of AI. While effort has been made to ensure accuracy and functionality, users should review and test the code thoroughly before use in production environments.

---

**Note**: Ensure your DBC file accurately matches the CAN messages in your log file for optimal decoding results.
