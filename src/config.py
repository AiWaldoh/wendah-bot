import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_NAME = os.getenv("BOT_NAME")
    API_URL = os.getenv("API_URL")
    ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
    SESSION_FILE = os.getenv("COOKIE_FILE_NAME")
    DISCORD_CHANNEL_URL = os.getenv("DISCORD_CHANNEL_URL")
    USERNAME = os.getenv("DISCORD_EMAIL")
    PASSWORD = os.getenv("DISCORD_PASSWORD")
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    JAVASCRIPT_SCR = """
                var target = document.querySelector('main[class^="chatContent"]');
                var observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        if (mutation.type === 'childList') {
                            mutation.addedNodes.forEach(function(node) {
                                window.onNewMessage(JSON.stringify(node.outerHTML));
                            });
                        }
                    });
                });
                var config = { childList: true, subtree: true };
                observer.observe(target, config);
            """
