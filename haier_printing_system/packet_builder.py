# packet_builder.py
"""Phase 2: Translation script formatting variables into Sojet byte strings."""

# Hypothetical Sojet Command Syntax Mapping:
# STX (0x02)
# CMD: PRT (Print)
# FORMAT: X, Y, FONT_SIZE, "TEXT"
# ETX (0x03)

STX = b'\x02'
ETX = b'\x03'

def build_print_packet(product_data: dict) -> bytes:
    """
    Translates product data into a low-level Sojet byte array containing
    exact coordinate geometry and syntax tokens.
    """
    if not product_data:
        raise ValueError("No product data provided")
        
    product_name = product_data.get("Product_Name", "UNKNOWN")
    price = product_data.get("Price", 0.0)
    qc_status = product_data.get("QC_Status", "PENDING")
    
    # Coordinate Geometry Mapping (X, Y)
    # Line 1: Product Name at (10, 10) with font size 12
    # Line 2: Price at (10, 50) with font size 14
    # Line 3: QC Status at (10, 90) with font size 16
    
    lines = [
        f'10,10,12,"{product_name}"',
        f'10,50,14,"${price:.2f}"',
        f'10,90,16,"QC:{qc_status}"'
    ]
    
    # Construct the payload
    # Example format: PRT|10,10,12,"Name"|10,50,14,"$599.99"|...
    payload_str = "PRT|" + "|".join(lines)
    
    # Encode to bytes and wrap with control characters
    packet = STX + payload_str.encode('utf-8') + ETX
    
    return packet
