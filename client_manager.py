import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from pyrogram import Client
from pyrogram.types import User, Chat

from config import settings
from utils.errors import SessionNotFoundError, SessionNotAuthorizedError, handle_telegram_error, APIError, ErrorCode
from utils.retry import exponential_backoff_retry


@dataclass
class AccountStatus:
    ready: bool
    authorized: bool
    premium: bool
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    user_id: Optional[int]


class ClientManager:
    def __init__(self):
        self._client: Optional[Client] = None
        self._lock = asyncio.Lock()
    
    @property
    def client(self) -> Client:
        if self._client is None:
            raise SessionNotFoundError()
        return self._client
    
    async def initialize(self, session_name: str = "main") -> None:
        async with self._lock:
            if self._client is not None:
                return
            
            session_path = settings.get_session_path(session_name)
            
            if not session_path.exists():
                raise SessionNotFoundError()
            
            self._client = Client(
                name=str(session_path).replace(".session", ""),
                api_id=settings.API_ID,
                api_hash=settings.API_HASH,
                workdir=settings.WORKDIR,
                in_memory=False
            )
            
            await self._client.start()
            
            try:
                me = await self._client.get_me()
                if not me:
                    raise SessionNotAuthorizedError()
            except Exception:
                await self._client.stop()
                self._client = None
                raise SessionNotAuthorizedError()
    
    async def close(self) -> None:
        async with self._lock:
            if self._client:
                await self._client.stop()
                self._client = None
    
    async def get_status(self) -> AccountStatus:
        if not self._client:
            raise SessionNotAuthorizedError()
        
        try:
            me: User = await self._client.get_me()
            if not me:
                raise SessionNotAuthorizedError()
        except Exception:
            raise SessionNotAuthorizedError()
        
        me: User = await self._client.get_me()
        
        return AccountStatus(
            ready=True,
            authorized=True,
            premium=me.is_premium or False,
            username=me.username,
            first_name=me.first_name,
            last_name=me.last_name,
            phone=me.phone_number if hasattr(me, 'phone_number') else None,
            user_id=me.id
        )
    
    async def join_chat(self, link: str) -> Dict[str, Any]:
        if not self._client:
            raise SessionNotAuthorizedError()
        
        try:
            async def _join():
                if link.startswith('https://t.me/'):
                    username = link.split('https://t.me/')[-1].strip('/')
                    if '+' in username:
                        chat = await self._client.join_chat(username)
                    else:
                        try:
                            chat = await self._client.get_chat(username)
                        except:
                            chat = await self._client.join_chat(username)
                elif link.startswith('@'):
                    chat = await self._client.join_chat(link[1:])
                elif link.startswith('+'):
                    chat = await self._client.join_chat(link[1:])
                else:
                    chat = await self._client.join_chat(link)
                
                return chat
            
            chat = await exponential_backoff_retry(
                _join,
                max_attempts=settings.MAX_RETRIES,
                base_delay=settings.RETRY_BASE_DELAY,
                max_delay=settings.RETRY_MAX_DELAY
            )
            
            return {
                "success": True,
                "chat_id": str(chat.id),
                "title": chat.title if hasattr(chat, 'title') else chat.first_name,
                "type": str(chat.type)
            }
            
        except Exception as e:
            raise handle_telegram_error(e)
    
    async def send_message(
        self,
        target: str,
        text: str,
        parse_mode: str = "markdown"
    ) -> Dict[str, Any]:
        if not self._client:
            raise SessionNotAuthorizedError()
        
        from utils.formatter import parse_target
        import re
        
        try:
            target = parse_target(target)
            
            # --- CUSTOM EMOJI CONVERSION ---
            # Telethon-style <tg-emoji emoji-id="123"> -> Pyrogram-style <emoji id="123">
            if parse_mode.lower() == "html":
                text = re.sub(
                    r'<tg-emoji\s+emoji-id=["\'](\d+)["\']>(.*?)</tg-emoji>', 
                    r'<emoji id="\1">\2</emoji>', 
                    text, 
                    flags=re.IGNORECASE
                )
            # -------------------------------
            
            from pyrogram.enums import ParseMode as PyrogramParseMode
            async def _send():
                # Map the string parse_mode to Pyrogram's Enum
                pm = None
                if parse_mode.lower() == "html":
                    pm = PyrogramParseMode.HTML
                elif parse_mode.lower() == "markdown":
                    pm = PyrogramParseMode.MARKDOWN

                return await self._client.send_message(
                    chat_id=target,
                    text=text,
                    parse_mode=pm
                )
            
            message = await exponential_backoff_retry(
                _send,
                max_attempts=settings.MAX_RETRIES,
                base_delay=settings.RETRY_BASE_DELAY,
                max_delay=settings.RETRY_MAX_DELAY
            )
            
            return {
                "success": True,
                "message_id": message.id,
                "chat_id": str(message.chat.id),
                "date": message.date.isoformat() if message.date else None
            }
            
        except Exception as e:
            raise handle_telegram_error(e)


client_manager = ClientManager()
