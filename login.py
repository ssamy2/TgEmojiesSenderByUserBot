#!/usr/bin/env python3
"""
Telegram Session Login Script
Run this script to create and authorize a Telegram session.
The session will be stored securely and used by the API.
"""

import asyncio
import sys
from pathlib import Path

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, BadRequest

from config import settings


def main():
    session_dir = Path(settings.SESSIONS_DIR)
    session_dir.mkdir(exist_ok=True)
    session_path = settings.get_session_path("main")
    
    print(f"\n[INFO] API ID: {settings.API_ID}")
    print(f"[INFO] Session path: {session_path}")
    
    PHONE = input("Enter your phone number (with country code, e.g., +201234567890): ").strip()
    print(f"[INFO] Phone: {PHONE}")
    
    client = Client(
        name=str(session_path).replace(".session", ""),
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
        workdir=settings.WORKDIR
    )
    
    async def login():
        await client.connect()
        
        try:
            sent_code = await client.send_code(PHONE)
            print(f"\n[INFO] Code sent to {PHONE}")
            
            code = input("Enter the verification code: ").strip()
            
            try:
                await client.sign_in(
                    phone_number=PHONE,
                    phone_code_hash=sent_code.phone_code_hash,
                    phone_code=code
                )
                print("\n[SUCCESS] Successfully signed in!")
                
            except SessionPasswordNeeded:
                password = input("Two-step verification is enabled. Enter your password: ").strip()
                await client.sign_in(
                    phone_number=PHONE,
                    password=password,
                    phone_code_hash=sent_code.phone_code_hash
                )
                print("\n[SUCCESS] Successfully signed in with 2FA!")
                
        except BadRequest as e:
            print(f"\n[ERROR] Verification failed: {e}")
            await client.disconnect()
            sys.exit(1)
        
        await client.disconnect()
        
        me = await client.get_me()
        print(f"\n[INFO] Logged in as: {me.first_name} (@{me.username})")
        print(f"[INFO] Premium: {me.is_premium}")
        print(f"[INFO] User ID: {me.id}")
        print("\n[SUCCESS] Session created! You can now use the API.")
        
    asyncio.run(login())


if __name__ == "__main__":
    main()
