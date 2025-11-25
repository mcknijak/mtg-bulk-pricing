# MTG Card Pricing Tool

A Python command-line tool for retrieving Magic: The Gathering card prices using the Scryfall API. This tool supports multiple modes of operation including simple card list pricing, set-filtered pricing, and set-based bulk pricing.

## Features

- 🔍 **Card Price Lookup**: Get current market prices for any MTG card or card list
- 📊 **Min/Max Pricing**: Automatically finds cheapest and most expensive printings
- 🎯 **Specific Printing Support**: Look up exact printings by set and collector number
- ✨ **Foil/Nonfoil Support**: Handle different card finishes (nonfoil, foil, etched)
- 🔤 **Case Insensitive**: Works with any capitalization for card names, sets, and finishes
- 📦 **Inventory Mode**: Generate set checklists with prices to get ROI on a box or get an estimated price for cards you are looking to sell.
- 🎴 **Set Filtering**: Restrict searches to specific sets
- 📁 **CSV Export**: All results exported to CSV format

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

# Generate inventory with prices
python mtg_pricer.py --inventory-mode --sets mh3 blb otj -o template.csv

# Calculate inventory value 
python mtg_pricer.py --calculate-value -i filled_template.csv -o value.csv
```

**Note: FILEs provided must have the absolute file path or relative file path from the python script. For ease of use, keep files in the same directory as the script.**

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

*Note: Runs at a rate of 10 cards/sec to respect Scryfall API Rate Limiting*

### Mode 2: Specific Card Printings

Look up card printings using set codes and collector numbers.

**Input File Format** (`specific_cards.txt`):
```
Lightning Bolt|LEA|161
Counterspell|ICE|64
Black Lotus|LEA|232
Tarmogoyf|FUT|153|foil
```

**Format Explanation:**
- `Card Name` - Just the card name (returns cheapest/most expensive **nonfoil** printings by default)
- `Card Name|SET` - Card from specific set
- `Card Name|SET|123` - Specific printing by collector number
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

Generate a CSV template containing all cards from one or more sets.

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
- **Unit price** - the current price from the Scryfall API!
- **Quantity** - empty column for you to fill in

### Mode 5: Calculate Inventory Value

After filling in quantities in the template from Mode 4, calculate the total value.

**Steps:**

1. Generate template with prices (see Mode 4)
2. Open the CSV in an editor like Excel or Google Sheets
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

### Mode 6: Generate Buylist (Missing Cards)

Generate a list of cards you DON'T have yet.

**Basic buylist:**
```bash
python mtg_pricer.py --buylist -i my_inventory.csv --sets MH3 -o buylist.csv
```

**Filter by finish:**
```bash
# Only nonfoil cards
python mtg_pricer.py --buylist --sets MH3 --finish nonfoil -o nonfoil_buylist.csv

# Only foil cards
python mtg_pricer.py --buylist --sets MH3 --finish foil -o foil_buylist.csv

# Multiple finishes (foil and etched, exclude nonfoil)
python mtg_pricer.py --buylist --sets MH3 --finish foil etched -o premium_buylist.csv

# Exclude specific finishes
python mtg_pricer.py --buylist --sets MH3 --exclude-finish etched -o no_etched.csv
```

**Filter by price:**
```bash
# Only cards under $10
python mtg_pricer.py --buylist --sets MH3 --max-price 10.00 -o budget_buylist.csv

# Only cards under $5
python mtg_pricer.py --buylist --sets BLB --max-price 5.00 -o cheap_cards.csv
```

**Combine filters:**
```bash
# Nonfoil cards under $5
python mtg_pricer.py --buylist --sets BLB --finish nonfoil --max-price 5.00 -o budget_nonfoils.csv

# Foil or etched cards under $20
python mtg_pricer.py --buylist --sets MH3 --finish foil etched --max-price 20.00 -o premium_budget.csv

# Multiple sets, nonfoil only, under $10
python mtg_pricer.py --buylist --sets MH3 BLB DSK --finish nonfoil --max-price 10.00 -o affordable_complete.csv
```

**Filter Options:**
- `--finish nonfoil` - Only include nonfoil cards
- `--finish foil` - Only include foil cards
- `--finish etched` - Only include etched cards
- `--finish foil etched` - Include both foil and etched (excludes nonfoil)
- `--exclude-finish etched` - Exclude etched cards
- `--exclude-finish foil etched` - Exclude foil and etched (only nonfoil)
- `--max-price 10.00` - Exclude cards over $10.00

**Note:** You cannot use both `--finish` and `--exclude-finish` at the same time.

**Uses:**
- Budget-conscious collecting ("show me cards under $5")
- Avoiding premium versions ("exclude etched foils")
- Focusing on playsets ("nonfoil only")
- Completing specific finish collections ("foil only")

**Apply minimum prices (vendor minimums):**
```bash
# All cards have minimum $0.25 price
python mtg_pricer.py --buylist --sets MH3 --min-price 0.25 -o buylist.csv

# Rarity-specific minimums (realistic vendor pricing)
python mtg_pricer.py --buylist --sets MH3 \
  --min-common 0.10 \
  --min-uncommon 0.25 \
  --min-rare 0.50 \
  --min-mythic 1.00 \
  -o buylist_realistic.csv

# Combine with other filters: min $0.25, max $10, nonfoil only
python mtg_pricer.py --buylist --sets BLB \
  --min-price 0.25 \
  --max-price 10.00 \
  --finish nonfoil \
  -o buylist_budget.csv
```

**Why use minimum prices?**
- Many card vendors (TCGPlayer, Card Kingdom, etc.) have minimum prices for bulk cards
- Commons often have a floor of $0.10-$0.25
- Helps calculate realistic total costs when buying from vendors
- Accounts for shipping, handling, and vendor overhead

**Minimum Price Options:**
- `--min-price 0.25` - Apply same minimum to all cards
- `--min-common 0.10` - Minimum for common cards only
- `--min-uncommon 0.25` - Minimum for uncommon cards only
- `--min-rare 0.50` - Minimum for rare cards only
- `--min-mythic 1.00` - Minimum for mythic cards only

**Note:** Rarity-specific minimums override the general `--min-price` if both are provided.

**Typical Vendor Minimums:**
```bash
# TCGPlayer-style pricing (conservative)
python mtg_pricer.py --buylist --sets MH3 \
  --min-common 0.15 \
  --min-uncommon 0.25 \
  --min-rare 0.50 \
  --min-mythic 1.00 \
  -o buylist_tcgplayer_style.csv

# Budget store pricing (aggressive)
python mtg_pricer.py --buylist --sets BLB \
  --min-common 0.10 \
  --min-uncommon 0.15 \
  --min-rare 0.25 \
  --min-mythic 0.50 \
  -o buylist_budget_store.csv

# Premium store pricing (high minimum)
python mtg_pricer.py --buylist --sets MH3 \
  --min-price 0.50 \
  -o buylist_premium_store.csv
```

**Example Output:**
```csv
card_name,set,collector_number,rarity,finish,owned,needed,unit_price,total_price
"Flare of Denial",MH3,12,rare,nonfoil,0,1,$8.50,$8.50
"Flare of Denial",MH3,12,rare,foil,0,1,$25.00,$25.00
"Emrakul the World Anew",MH3,6,mythic,nonfoil,1,0,$45.00,$0.00
```

The script will also print these statistics:
```
Total cards needed: 245
Total estimated cost: $1,234.56

Breakdown by rarity:
  Common: 80
  Uncommon: 90
  Rare: 60
  Mythic: 15
```


## Supported File Formats

### Standard Text Format (.txt)

Simple pipe-delimited format:
```
Card Name
Card Name|SET
Card Name|SET|123
Card Name|SET|123|foil
```

**Comments:** Lines starting with `#` are ignored.

### Archidekt Export

#### Text Export (Recommended)
1. Open your deck or collection in Archidekt
2. Click **Export**
3. Select **Text** as file type
4. Under **Format**, choose the default format (can include set code and collector number)
5. Download the file

**Format detected:** `1 Card Name (SET) 123`

#### CSV Export
1. Open your collection in Archidekt
2. Click **Export**
3. Select **CSV** as file type
4. **Important:** Include these columns:
   - Count (or Quantity)
   - Card Name
   - Edition (set name)
   - Collector Number (optional but recommended)
   - Foil (optional)
5. Download the file

**Example Archidekt CSV:**
```csv
Count,Card Name,Edition,Collector Number,Foil
4,Lightning Bolt,Modern Horizons 2,130,No
1,Ragavan Nimble Pilferer,Modern Horizons 2,138,Yes
```

### Moxfield Export

#### Text Export (Recommended)
1. Open your deck in Moxfield
2. Click **Export**
3. Select **Text** format
4. Check off set codes, collector numbers, and/or foil status if you want to include them
5. Copy or download the text

**Format detected:** `1 Card Name (SET) 123`

#### CSV Export
1. Go to your collection in Moxfield
2. Click **Export**
3. Select **CSV** format
4. **Important:** The export should include these columns:
   - Count
   - Name
   - Edition (set code)
   - Collector Number
   - Foil (optional)
5. Download the file

**Example Moxfield CSV:**
```csv
Count,Tradelist Count,Name,Edition,Condition,Language,Foil,Tags,Last Modified,Collector Number
4,0,Lightning Bolt,MH2,Near Mint,English,,2024-01-15 12:00:00,130
1,0,Ragavan Nimble Pilferer,MH2,Near Mint,English,foil,2024-01-15 12:00:00,138
```

**Note:** Extra columns (Condition, Language, Tags, etc.) are fine - the script will ignore them

### Generic CSV Format

Any CSV with at minimum these columns (in order):
```csv
Quantity,Card Name,Set Code,Collector Number,Finish
4,Lightning Bolt,MH2,130,nonfoil
1,Tarmogoyf,FUT,153,foil
```
### Examples

**Archidekt Text Export:**
```
1 Gylwain, Casting Director (WOC) 4
4 Lightning Bolt (MH2) 130
1 Ragavan, Nimble Pilferer (MH2) 138 *F*
1 Solitude (MH2) 32 *E*
```

**Moxfield Text Export:**
```
1 Gylwain, Casting Director (WOC) 4
4 Lightning Bolt (MH2) 130
1 Ragavan, Nimble Pilferer (MH2) 138 *F*
1 Solitude (MH2) 32 *E*
```

**Standard Format:**
```
Gylwain, Casting Director|WOC|4
Lightning Bolt|MH2|130
Ragavan, Nimble Pilferer|MH2|138|foil
Solitude|MH2|32|etched
```
**Finish Markers Supported:**
- `*F*` or `[F]` or `foil` → Foil
- `*E*` or `[E]` or `etched` → Etched
- No marker → Nonfoil (default)


## Foil vs Nonfoil

### Default Behavior: Nonfoil Only

**When you don't specify a finish, the script defaults to nonfoil prices only.**

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

### Example 3: Inventory Management for New Set

```bash
# Step 1: Generate template with prices already included (single API pass)
python mtg_pricer.py --inventory-mode --sets FDN -o foundations_template.csv

# Step 2: Open foundations_template.csv, mark your pulls
# Prices are already there! Just fill in the 'quantity' column

# Step 3: Calculate your total value (instant, no API calls)
python mtg_pricer.py --calculate-value -i foundations_template.csv -o my_foundations_value.csv
```

### Example 4: Multiple Formats of Same Card

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

This shows the price range across all printings, plus specific prices for M11, Alpha, and 2XM foil versions.

## Troubleshooting

### "Card Not Found"

- **Cause**: Card name misspelled or doesn't exist in the specified set
- **Solution**: Check spelling against [Scryfall](https://scryfall.com). Note: Case doesn't matter, but spelling does

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
  
### File Format Not Detected

**Problem:** Script doesn't recognize your file format  
**Solutions:**
- For Archidekt text exports: Make sure format includes `(SET)` in parentheses
- For Moxfield text exports: Same requirement - `(SET)` must be present
- For CSV files: Check that you have a header row with column names
- If all else fails: Convert to standard format using `|` delimiters

### Cards Not Found from Archidekt/Moxfield Export

**Problem:** Some cards show "Not Found"  
**Possible causes:**
- Set code in parentheses might be non-standard
- Card name might include special characters that need cleaning
**Solution:** Check the card on Scryfall.com to verify set code and exact name

## API Information

This tool uses the **Scryfall API**, which is:
- Free to use
- No API key required
- Comprehensive and up-to-date
- Rate-limited to 10 requests per second

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
