import os
import re
from bs4 import BeautifulSoup
import asyncio
from config import Config
from dataclasses import dataclass
from playwright.async_api import async_playwright
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)


@dataclass
class ProcessedResponse:
    chat_memory_response: str = ""
    chat_response: str = ""


class MessageExtractor:
    def extract_message_data(self, message_soup):
        user_id = self._extract_user_id(message_soup)
        has_mention = self._contains_mention(message_soup)
        username = self._extract_username(message_soup)
        message_text = self._extract_message_text(message_soup, has_mention)
        return {
            "user_id": user_id,
            "username": username,
            "has_mention": has_mention,
            "message_text": message_text.strip(),
        }

    def _extract_user_id(self, message_soup):
        img_src = message_soup.find("img")["src"] if message_soup.find("img") else None
        return self._parse_user_id(img_src)

    def _contains_mention(self, message_soup):
        mention = message_soup.select_one('span[class*="mention"]')
        return mention and mention.text.startswith(Config.BOT_NAME)

    def _extract_username(self, message_soup):
        username_element = message_soup.find(
            "span", class_=lambda x: x and "username" in x
        )
        return username_element.text.strip() if username_element else None

    def _extract_message_text(self, message_soup, has_mention):
        message_div = self._find_message_div(message_soup)
        if message_div:
            message_spans = self._find_message_spans(message_div)
            mention_span = self._find_mention_span(message_div) if has_mention else None
            return self._combine_message_text(message_spans, mention_span).strip()
        else:
            return ""

    def _find_message_div(self, message_soup):
        return message_soup.select_one('div[class*="markup"]')

    def _find_message_spans(self, message_div):
        return message_div.find_all("span")

    def _find_mention_span(self, message_div):
        return message_div.select_one('span[class*="mention"]')

    def _combine_message_text(self, message_spans, mention_span=None):
        if mention_span:
            return (
                mention_span.get_text()
                + " "
                + " ".join(
                    span.get_text() for span in message_spans if span != mention_span
                )
            )
        else:
            return " ".join(span.get_text() for span in message_spans)

    def _parse_user_id(self, img_src):
        if img_src:
            img_src = img_src.strip('"\\')
            match = re.search(r"/avatars/(\d+)/", img_src)
            return match.group(1) if match else None
        return None

    async def login(self):
        session_file = os.path.join("secret", self.config.SESSION_FILE)

        if not os.path.exists("secret"):
            os.makedirs("secret")

        if os.path.exists(session_file):
            self.context = await self.browser.new_context(storage_state=session_file)
            self.page = await self.context.new_page()
        else:
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            await self.page.goto("https://discord.com/login")
            await self._submit_login_form()
            await self._update_settings()
            await self.context.storage_state(path=session_file)

    async def _update_settings(self):
        await self.page.wait_for_selector(".flex_f18b02")
        await self.page.click('button[aria-label="User Settings"]')
        await self.page.click('div[aria-label="Appearance"]')
        await self.page.click('label:has-text("Show avatars in Compact mode")')
        await self.page.click('div[aria-label="Close"]')

    async def _submit_login_form(self):
        await self.page.fill('input[name="email"]', self.config.USERNAME)
        await self.page.fill('input[name="password"]', self.config.PASSWORD)
        await self.page.click('button[type="submit"]')

    async def load_channel(self):
        print(f"Loading {self.config.DISCORD_CHANNEL_URL}")
        await self.page.goto(self.config.DISCORD_CHANNEL_URL)
        await self.page.wait_for_selector("div[role='textbox']")
        await asyncio.sleep(5)

    async def expose_on_message_function(self, on_message_callback):
        await self.page.expose_function("onNewMessage", on_message_callback)
        await self.page.evaluate(Config.JAVASCRIPT_SCR)
        print("Listening for new messages...")

    async def close(self):
        await self.browser.close()


class MessageValidator:
    def is_valid_message(self, message_html):
        return message_html.strip().startswith('"<li')


class MessageParser:
    def __init__(
        self, message_extractor: MessageExtractor, message_validator: MessageValidator
    ):
        self.message_extractor = message_extractor
        self.message_validator = message_validator

    def parse_message(self, message_html):
        if not self.message_validator.is_valid_message(message_html):
            return None

        message_soup = BeautifulSoup(message_html, "html.parser")
        return self.message_extractor.extract_message_data(message_soup)


class DiscordBrowser:
    def __init__(self, config: Config):
        self.config = config
        self.browser = None
        self.page = None

    async def launch(self, playwright):
        self.browser = await playwright.chromium.launch(headless=True)


class DiscordClient:
    def __init__(self, config: Config, message_parser: MessageParser):
        self.config: Config = config
        self.message_parser: MessageParser = message_parser
        self.browser: DiscordBrowser = DiscordBrowser(config)

    async def start(self):
        async with async_playwright() as playwright:
            await self.browser.launch(playwright)
            await self.browser.login()
            await self.browser.load_channel()
            await self.browser.expose_on_message_function(self._on_message)
            await self._keep_alive()

    async def _keep_alive(self):
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Script terminated by user.")
        finally:
            await self.browser.close()

    async def _on_message(self, raw_message):
        message = await asyncio.to_thread(
            self.message_parser.parse_message, raw_message
        )
        if message:
            await self._process_message(message)

    async def _process_message(self, message):
        logging.info(message)

        if message["has_mention"]:
            response_data = {
                "message": message["message_text"].replace(f"@{Config.BOT_NAME}", "")
            }
            logging.info(f"Question: {response_data}")
            logging.info(f"Doing a POST to {Config.API_URL}/ask")

            try:
                # Add a placeholder character to show "is typing"
                await self._add_typing_placeholder()

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{Config.API_URL}/ask", json=response_data
                    ) as api_response:
                        if api_response.status == 200:
                            processed_response = await api_response.json()
                            # Clear the placeholder character before sending the response
                            await self._clear_typing_placeholder()
                            await self._send_response(processed_response["text"])
                        else:
                            logging.error(
                                f"Failed to get response from JSON server: {api_response.status}"
                            )
                            # Clear the placeholder character in case of error
                            await self._clear_typing_placeholder()
            except aiohttp.ClientError as e:
                logging.error(f"HTTP request failed: {e}")
                # Clear the placeholder character in case of exception
                await self._clear_typing_placeholder()

    async def _add_typing_placeholder(self):
        await self.browser.page.type('div[role="textbox"]', ".")

    async def _clear_typing_placeholder(self):
        await self.browser.page.press('div[role="textbox"]', "Backspace")

    async def _send_response(self, message):
        if not message:
            logging.info("Empty message. Skipping sending to Discord.")
            return

        message_chunks = self._split_message_into_chunks(message)
        for chunk in message_chunks:
            await self._type_and_send_chunk(chunk)

    def _split_message_into_chunks(
        self, message, max_length=1900, preferred_length=1800
    ):
        """Split the message into chunks of up to max_length characters, preferring natural break points around preferred_length."""
        chunks = []
        while len(message) > max_length:
            # Find the preferred break point around preferred_length
            break_point = self._find_break_point(message, preferred_length, max_length)
            chunks.append(message[:break_point].strip())
            message = message[break_point:].strip()
        chunks.append(message)
        return chunks

    def _find_break_point(self, message, preferred_length, max_length):
        """Find a natural break point (newline or end of sentence) around the preferred_length."""
        # Look for a newline character within the preferred range
        newline_pos = message.rfind("\n", preferred_length, max_length)
        if newline_pos != -1:
            return newline_pos + 1

        # Look for the end of a sentence within the preferred range
        sentence_end_pos = message.rfind(".", preferred_length, max_length)
        if sentence_end_pos != -1:
            return sentence_end_pos + 1

        # If no natural break point is found, break at max_length
        return max_length

    async def _clear_textbox(self):
        await self.browser.page.click('div[role="textbox"]', click_count=3)
        await self.browser.page.press('div[role="textbox"]', "Backspace")

    async def _type_and_send_chunk(self, chunk):
        logging.info("Typing and sending")

        lines = chunk.split("\n")
        for i, line in enumerate(lines):
            await self.browser.page.type('div[role="textbox"]', line)
            if i < len(lines) - 1:
                await self._press_shift_enter()
            else:
                await self.browser.page.keyboard.press("Enter")

    async def _press_shift_enter(self):
        await self.browser.page.keyboard.down("Shift")
        await self.browser.page.keyboard.press("Enter")
        await self.browser.page.keyboard.up("Shift")


class DiscordBot:
    def __init__(self, config: Config):
        self.config = config
        message_extractor = MessageExtractor()
        message_validator = MessageValidator()
        self.message_parser = MessageParser(message_extractor, message_validator)
        self.discord_client = DiscordClient(config, self.message_parser)

    async def start(self):
        await self.discord_client.start()
