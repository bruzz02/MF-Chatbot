import re

def mask_pii(text):
    """
    Detects and masks common PII (emails, phone numbers, etc.) from the text.
    """
    if not text:
        return text

    # Mask Email Addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    text = re.sub(email_pattern, "[EMAIL]", text)

    # Mask Phone Numbers (Common formats: +91 9999999999, 999-999-9999, etc.)
    # This is a broad regex to catch various formats
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    text = re.sub(phone_pattern, "[PHONE]", text)

    # Mask potential Credit Card numbers (Basic 13-16 digit sequence)
    card_pattern = r'\b(?:\d[ -]*?){13,16}\b'
    text = re.sub(card_pattern, "[CARD]", text)
    
    # Mask Indian PAN Card (Format: ABCDE1234F)
    pan_pattern = r'[A-Z]{5}[0-9]{4}[A-Z]{1}'
    text = re.sub(pan_pattern, "[PAN]", text)

    return text

if __name__ == "__main__":
    test_text = "My email is test@example.com and my phone is +91 9876543210. My PAN is ABCDE1234F."
    print(f"Original: {test_text}")
    print(f"Masked:   {mask_pii(test_text)}")
