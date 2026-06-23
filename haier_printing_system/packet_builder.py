# packet_builder.py
"""Phase 2: Translation script formatting variables into Sojet byte strings."""

# Control Characters
STX = b'\x02'
ETX = b'\x03'

def build_print_packet(product_data: dict) -> bytes:
    """
    Translates product data into a low-level network packet.
    Instead of hardcoding physical X/Y coordinates, this maps our database
    values directly to the "Dynamic Text" Variable IDs configured on the printer UI.
    """
    if not product_data:
        raise ValueError("No product data provided")
        
    product_name = product_data.get("ProductName", "UNKNOWN")
    price = product_data.get("ProductPrice", "0.00")
    qc_status = product_data.get("ProductStatus", "active")
    
    # Map our data to the Printer's Dynamic Variable IDs:
    # var1(ID:1) = Product Name
    # var2(ID:2) = Price
    # var3(ID:3) = QC Status
    
    # Typical industrial variable payload format (e.g. ID|Value)
    # Note: If your specific printer requires a different delimiter (like commas or semicolons),
    # you can easily adjust this list!
    variables = [
        f'1|{product_name}',
        f'2|{price}',
        f'3|STATUS:{qc_status}'
    ]
    
    # Construct the payload
    # Example format: UPDATE|1|HRF-186EBS|2|Rs.54000|3|STATUS:active
    payload_str = "UPDATE|" + "|".join(variables)
    
    # Encode to bytes and wrap with control characters so the printer knows when the message starts and ends
    packet = STX + payload_str.encode('utf-8') + ETX
    
    return packet
