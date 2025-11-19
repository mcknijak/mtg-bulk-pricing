# MTG Card Pricing Tool

A Python command-line tool for retrieving Magic: The Gathering card prices using the Scryfall API. This tool supports multiple modes of operation including simple card list pricing, set-filtered pricing, and efficient inventory management.

## Features

- 🔍 **Card Price Lookup**: Get current market prices for any MTG card
- 📊 **Min/Max Pricing**: Automatically finds cheapest and most expensive printings
- 🎯 **Specific Printing Support**: Look up exact printings by set and collector number
- ✨ **Foil/Nonfoil Support**: Handle different card finishes (nonfoil, foil, etched)
- 🎲 **Smart Defaults**: Defaults to nonfoil prices when finish not specified
- 🔤 **Case Insensitive**: Works with any capitalization for card names, sets, and finishes
- 📦 **Efficient Inventory Mode**: Generate set checklists with prices in one API pass
- 🎴 **Set Filtering**: Restrict searches to specific sets
- 📁 **CSV Export**: All results exported to convenient CSV format

## What's New in v1.1

### Recent Improvements

✨ **Nonfoil Default**: Script now defaults to nonfoil prices when finish isn't specified - the most common use case!

🔤 **Case Insensitive**: Card names, set codes, and finish types now work with any capitalization.

⚡ **Efficient Inventory Mode**: Prices are now fetched during template generation (single API pass) instead of requiring a separate processing step. This makes inventory management **much faster**!

🎯 **Better Workflow**: The new `--calculate-value` mode does instant calculations without hitting the API.

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install requests
```

3. Make the script executable (optional, Linux/Mac):
```bash
chmod +x mtg_pricer.py
```

## Usage

### Mode 1: Basic Card List Pricing

Price a list of cards from a text or CSV file. **By default, returns nonfoil prices only unless you specify otherwise.**

**Command:**
```bash
python mtg_pricer.py -i cards.txt -o prices.csv
```

**Input File Format** (`cards.txt`):
```
Lightning Bolt
Counterspell
Black Lotus
Tarmogoyf
```

**Output:** CSV with card names, min/max nonfoil prices, and printing details.

**Note:** Card names and set codes are **case insensitive** - "lightning bolt" works just as well as "Lightning Bolt"!

### Mode 2: Specific Card Printings

Look up exact card printings using set codes and collector numbers.

**Input File Format** (`specific_cards.txt`):
```
Lightning Bolt|LEA|161
Counterspell|ICE|64
Black Lotus|LEA|232
Tarmogoyf|FUT|153|foil
```

**Format Explanation:**
- `Card Name` - Just the card name (returns cheapest/most expensive **nonfoil** printings by default)
- `Card Name|SET` - Card from specific set (nonfoil by default)
- `Card Name|SET|123` - Specific printing by collector number (nonfoil by default)
- `Card Name|SET|123|foil` - Specific foil version
- `Card Name|SET|123|etched` - Specific etched version

**Case Insensitivity:** All of these work identically:
- `Lightning Bolt|mh2|130|foil`
- `lightning bolt|MH2|130|FOIL`
- `LIGHTNING BOLT|Mh2|130|Foil`

**Command:**
```bash
python mtg_pricer.py -i specific_cards.txt -o specific_prices.csv
```

### Mode 3: Set-Filtered Pricing

Restrict all card searches to a specific set.

**Command:**
```bash
python mtg_pricer.py -i cards.txt -o prices.csv --set MH3
```

This will only return prices for cards from Modern Horizons 3 (MH3), even if the card appears in other sets.

### Mode 4: Inventory Mode (Generate Template with Prices)

Generate a CSV template containing all cards from one or more sets **with prices already populated**. This is much more efficient than the old two-step process!

**Command:**
```bash
python mtg_pricer.py --inventory-mode --sets MH3 OTJ LCI -o inventory_template.csv
```

**Set Codes Examples:**
- `MH3` or `mh3` - Modern Horizons 3 (case insensitive!)
- `OTJ` or `otj` - Outlaws of Thunder Junction
- `LCI` or `lci` - The Lost Caverns of Ixalan
- `BLB` or `blb` - Bloomburrow
- `DSK` or `dsk` - Duskmourn: House of Horror

**Output:** CSV template with all cards from the specified sets, including:
- Card name, set, collector number, rarity
- **Finish type** (nonfoil, foil, or etched) - each finish gets its own row
- **Unit price** - already populated from the API!
- **Quantity** - empty column for you to fill in

**Key Improvement:** Prices are fetched in the same API call as card data, making this much faster than before!

### Mode 5: Calculate Inventory Value

After filling in quantities in the template from Mode 4, calculate the total value. **This step requires NO API calls** - it just does math on the existing data!

**Steps:**

1. Generate template with prices (see Mode 4)
2. Open the CSV in Excel or Google Sheets
3. Fill in the `quantity` column for cards you own
4. Save the file
5. Run the calculation command:

```bash
python mtg_pricer.py --calculate-value -i filled_inventory.csv -o inventory_value.csv
```

**Output:** CSV with:
- All your card details
- Quantity owned
- Unit price (already there from step 1)
- Total price (quantity × unit price)
- **Overall collection value** printed to console

**Why This Is Better:**
- ✅ Only hits the API once (during template generation)
- ✅ You can see prices while deciding what to inventory
- ✅ Value calculation is instant (no waiting for API calls)
- ✅ Each finish type has its own row (easier to track foils separately)

## Understanding Foil vs Nonfoil Behavior

### Default Behavior: Nonfoil Only

**When you don't specify a finish, the script defaults to nonfoil prices only.** This is the most common use case and avoids confusion.

**Example:**
```
# Input
Lightning Bolt

# Output
Returns only nonfoil prices (cheapest and most expensive nonfoil printings)
```

### Getting Foil Prices

To get foil prices, explicitly specify the finish:

**Example:**
```
# Input
Lightning Bolt|MH2|130|foil

# Output
Returns the foil price for that specific printing
```

### Getting All Finishes

To see prices for ALL finishes (nonfoil, foil, etched), search for the same card multiple times with different finish specifications, or use inventory mode which automatically creates separate rows for each finish.

**Example:**
```
# Input file
Lightning Bolt|MH2|130|nonfoil
Lightning Bolt|MH2|130|foil

# Output
Two rows with nonfoil and foil prices respectively
```

## Set Code Reference

Common set codes (case-insensitive):

| Code | Set Name |
|------|----------|
| MH3 | Modern Horizons 3 |
| OTJ | Outlaws of Thunder Junction |
| MKM | Murders at Karlov Manor |
| LCI | The Lost Caverns of Ixalan |
| WOE | Wilds of Eldraine |
| BLB | Bloomburrow |
| DSK | Duskmourn: House of Horror |
| FDN | Foundations |
| ONE | Phyrexia: All Will Be One |
| BRO | The Brothers' War |
| DMU | Dominaria United |

For a complete list, see [Scryfall's set list](https://scryfall.com/sets).

## Output Format

### Card List Output

```csv
card_name,set,collector_number,finish,min_price,max_price,min_printing,max_printing
Lightning Bolt,Multiple,Multiple,nonfoil,$0.15,$45.00,M11 #146 (nonfoil),LEA #161 (nonfoil)
Counterspell,ICE,64,nonfoil,$2.50,$2.50,ICE #64 (nonfoil),ICE #64 (nonfoil)
```

**Note:** When finish is not specified, only nonfoil prices are returned by default.

### Inventory Output

```csv
card_name,set,collector_number,rarity,finish,quantity,unit_price,total_price
Force of Will,ALL,55,rare,nonfoil,2,$84.50,$169.00
Tarmogoyf,FUT,153,mythic,foil,1,$125.00,$125.00
```

**Note:** Each finish type gets its own row in inventory mode.

## Advanced Examples

### Example 1: Price a Commander Deck

**deck.txt:**
```
Sol Ring
Arcane Signet
Commander's Sphere
Cultivate
Kodama's Reach
Swords to Plowshares
Path to Exile
Counterspell
Swan Song
Cyclonic Rift
```

**Command:**
```bash
python mtg_pricer.py -i deck.txt -o deck_prices.csv
```

### Example 2: Price Specific Valuable Cards

**expensive_cards.txt:**
```
Black Lotus|LEA|232
Mox Sapphire|LEA|265
Time Walk|LEA|290
Ancestral Recall|LEA|161
```

**Command:**
```bash
python mtg_pricer.py -i expensive_cards.txt -o expensive_prices.csv
```

### Example 3: Inventory Management for New Set (Efficient!)

```bash
# Step 1: Generate template with prices already included (single API pass)
python mtg_pricer.py --inventory-mode --sets FDN -o foundations_template.csv

# Step 2: Open foundations_template.csv, mark your pulls
# Prices are already there! Just fill in the 'quantity' column

# Step 3: Calculate your total value (instant, no API calls)
python mtg_pricer.py --calculate-value -i foundations_template.csv -o my_foundations_value.csv
```

**Why this is better:** Only hits the API once instead of twice!

### Example 4: Multiple Formats of Same Card (Case Insensitive!)

**comparison.txt:**
```
Lightning Bolt
lightning bolt|m11
LIGHTNING BOLT|lea|161
Lightning Bolt|2XM|141|FOIL
```

**Command:**
```bash
python mtg_pricer.py -i comparison.txt -o bolt_comparison.csv
```

This shows the price range across all printings, plus specific prices for M11, Alpha, and 2XM foil versions. Notice how case doesn't matter!

## Troubleshooting

### "Card Not Found"

- **Cause**: Card name misspelled or doesn't exist in the specified set
- **Solution**: Check spelling against [Scryfall](https://scryfall.com). Note: Case doesn't matter, but spelling does!

### "Getting foil prices when I want nonfoil" or vice versa

- **Cause**: Not specifying the finish type
- **Solution**: By default, the script returns **nonfoil only**. To get foil prices, add `|foil` or `|etched` to your card entry.

### "No Price Data"

- **Cause**: Card exists but has no market price (very new or very old)
- **Solution**: This is normal for some cards. Check Scryfall manually.

### Rate Limiting

The script includes built-in rate limiting to respect Scryfall's API guidelines (50-100ms between requests). For very large lists, the script may take several minutes.

### Set Code Not Recognized

- **Cause**: Invalid or incorrect set code (though case doesn't matter)
- **Solution**: Verify set codes at [Scryfall Sets](https://scryfall.com/sets). You can use any capitalization: `mh3`, `MH3`, or `Mh3` all work.

## API Information

This tool uses the **Scryfall API**, which is:
- Free to use
- No API key required
- Comprehensive and up-to-date
- Rate-limited to 10 requests per second

**Note on TCGPlayer/Card Kingdom:** While the script is designed to support multiple APIs, TCGPlayer and Card Kingdom APIs require merchant accounts and complex authentication. Scryfall provides the same pricing data (sourced from TCGPlayer) without authentication requirements.

## Data Source

Prices are sourced from:
- **USD prices**: TCGPlayer market prices (via Scryfall)
- **Updated**: Multiple times daily
- **Finishes**: Nonfoil, foil, and etched variants

## Tips and Best Practices

1. **Case Doesn't Matter**: Type card names, set codes, and finishes however you want - the script handles it
2. **Nonfoil is Default**: Unless you specify a finish, you'll only get nonfoil prices
3. **Use Exact Names for Best Results**: While case doesn't matter, spelling does - "Lightning Bolt" works, "Lightening Bolt" doesn't
4. **Comments in Input**: Lines starting with `#` are ignored, great for organizing
5. **Batch Processing**: Process large lists during off-peak hours if you have hundreds of cards
6. **Regular Updates**: Prices change frequently; re-run for current values
7. **Inventory Efficiency**: Use inventory mode's single-pass approach to save time
8. **Specific Printings**: For cards with multiple variants in a set (extended art, etc.), always use collector numbers

## File Formats

### Input Files
- **Plain text** (`.txt`): One card per line
- **CSV** (`.csv`): For inventory mode

### Output Files
- **CSV** (`.csv`): Compatible with Excel, Google Sheets, etc.

## Command Reference

### All Command-Line Options

```
-i, --input FILE            Input file with card list
-o, --output FILE           Output CSV file (required)
--set CODE                  Filter cards to specific set (case insensitive)
--inventory-mode            Generate inventory template with prices
--sets CODE [CODE ...]      Set codes for inventory mode (case insensitive)
--calculate-value           Calculate total value from filled inventory
-h, --help                  Show help message
```

### Usage Examples

```bash
# Basic price check
python mtg_pricer.py -i cards.txt -o prices.csv

# Set-specific pricing
python mtg_pricer.py -i cards.txt -o prices.csv --set mh3

# Generate inventory with prices (single API pass)
python mtg_pricer.py --inventory-mode --sets mh3 blb otj -o template.csv

# Calculate inventory value (no API calls, instant)
python mtg_pricer.py --calculate-value -i filled_template.csv -o value.csv
```

## Version History

- **v1.0** - Initial release with Scryfall API support

## License

This tool is provided as-is for personal use. Pricing data is provided by Scryfall and TCGPlayer.

## Support

For issues or questions:
1. Check this README first
2. Verify your input format matches examples
3. Test with a small sample (2-3 cards) first
4. Check [Scryfall's documentation](https://scryfall.com/docs/api)

## Acknowledgments

- **Scryfall** for providing an excellent free API
- **TCGPlayer** for pricing data
- The MTG community for feedback and support
