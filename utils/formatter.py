from enum import Enum
from typing import List, Optional, Union
from pyrogram import types


class ParseMode(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    NONE = "none"


class MessageFormatter:
    @staticmethod
    def format_markdown(text: str) -> str:
        return text
    
    @staticmethod
    def format_html(text: str) -> str:
        replacements = {
            "**": "<b>",
            "**": "</b>",
            "__": "<i>",
            "__": "</i>",
            "||": "<span class=\"spoiler\">",
            "||": "</span>",
            "`": "<code>",
            "`": "</code>",
        }
        
        result = text
        result = result.replace("**", "**").replace("**", "**")
        result = result.replace("__", "__").replace("__", "__")
        
        import re
        bold_pattern = re.compile(r'\*\*(.*?)\*\*')
        result = bold_pattern.sub(r'<b>\1</b>', result)
        
        italic_pattern = re.compile(r'__(.*?)__')
        result = italic_pattern.sub(r'<i>\1</i>', result)
        
        code_pattern = re.compile(r'`(.*?)`')
        result = code_pattern.sub(r'<code>\1</code>', result)
        
        spoiler_pattern = re.compile(r'\|\|(.*?)\|\|')
        result = spoiler_pattern.sub(r'<span class="spoiler">\1</span>', result)
        
        return result
    
    @staticmethod
    def extract_entities(text: str, parse_mode: ParseMode) -> Optional[List[types.MessageEntity]]:
        entities = []
        
        import re
        
        if parse_mode == ParseMode.MARKDOWN:
            patterns = [
                (r'\*\*(.+?)\*\*', types.MessageEntityType.BOLD),
                (r'__(.+?)__', types.MessageEntityType.ITALIC),
                (r'``(.+?)``', types.MessageEntityType.CODE),
                (r'\|\|(.+?)\|\|', types.MessageEntityType.SPOILER),
                (r'\[(.+?)\]\((.+?)\)', types.MessageEntityType.TEXT_LINK),
            ]
        elif parse_mode == ParseMode.HTML:
            patterns = [
                (r'<b>(.+?)</b>', types.MessageEntityType.BOLD),
                (r'<strong>(.+?)</strong>', types.MessageEntityType.BOLD),
                (r'<i>(.+?)</i>', types.MessageEntityType.ITALIC),
                (r'<em>(.+?)</em>', types.MessageEntityType.ITALIC),
                (r'<code>(.+?)</code>', types.MessageEntityType.CODE),
                (r'<span class="spoiler">(.+?)</span>', types.MessageEntityType.SPOILER),
                (r'<a href="(.+?)">(.+?)</a>', types.MessageEntityType.TEXT_LINK),
                (r'<pre>(.+?)</pre>', types.MessageEntityType.PRE),
            ]
        else:
            return None
        
        for pattern, entity_type in patterns:
            regex = re.compile(pattern, re.DOTALL)
            for match in regex.finditer(text):
                entities.append(
                    types.MessageEntity(
                        type=entity_type,
                        offset=match.start(),
                        length=len(match.group(1)) if entity_type != types.MessageEntityType.TEXT_LINK else len(match.group(2)),
                        url=match.group(2) if entity_type == types.MessageEntityType.TEXT_LINK else None
                    )
                )
        
        return entities if entities else None
    
    @staticmethod
    def prepare_message(
        text: str,
        parse_mode: Union[str, ParseMode] = ParseMode.MARKDOWN,
        entities: Optional[List[types.MessageEntity]] = None
    ) -> dict:
        parse_mode = ParseMode(parse_mode) if isinstance(parse_mode, str) else parse_mode
        
        if parse_mode == ParseMode.NONE:
            return {"text": text, "entities": None}
        
        if parse_mode == ParseMode.HTML:
            cleaned_text = text
            for tag in ['<b>', '</b>', '<i>', '</i>', '<code>', '</code>', '<pre>', '</pre>']:
                cleaned_text = cleaned_text.replace(tag, '')
            cleaned_text = cleaned_text.replace('<span class="spoiler">', '').replace('</span>', '')
            return {"text": cleaned_text, "entities": entities}
        
        if parse_mode == ParseMode.MARKDOWN:
            cleaned_text = text
            for char in ['*', '_', '`', '|']:
                cleaned_text = cleaned_text.replace(char, '')
            return {"text": cleaned_text, "entities": entities}
        
        return {"text": text, "entities": None}


def parse_target(target: str) -> Union[str, int]:
    target = target.strip()
    
    if target.startswith('@'):
        return target[1:]
    
    if target.startswith('-100'):
        return int(target)
    
    if target.startswith('-'):
        return int(target)
    
    if target.isdigit():
        return int(target)
    
    return target
