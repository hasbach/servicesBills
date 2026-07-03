import os
from py_vapid import Vapid

def generate():
    vapid = Vapid()
    vapid.generate_keys()
    
    private_key = vapid.private_key
    public_key = vapid.public_key
    
    # py_vapid might not easily export to the right strings without decoding
    import base64
    def to_urlsafe(b):
        return base64.urlsafe_b64encode(b).decode('utf-8').rstrip('=')
    
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        priv_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
        pub_bytes = b'\x04' + public_key.public_numbers().x.to_bytes(32, 'big') + public_key.public_numbers().y.to_bytes(32, 'big')
        
        priv_b64 = to_urlsafe(priv_bytes)
        pub_b64 = to_urlsafe(pub_bytes)
        
        with open("vapid_keys.env", "w") as f:
            f.write(f"VAPID_PRIVATE_KEY={priv_b64}\n")
            f.write(f"VAPID_PUBLIC_KEY={pub_b64}\n")
            
        print("Keys generated successfully.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    generate()
