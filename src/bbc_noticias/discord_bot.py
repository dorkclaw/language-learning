"""
Discord bot — responds to slash commands and button clicks.
Runs alongside the cron container; they communicate via a shared queue file.
"""

import logging
import os
import sys
from pathlib import Path

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import discord
from dotenv import load_dotenv

from src.bbc_noticias.config import load as load_config
from src.bbc_noticias.rss import fetch_stories
from src.bbc_noticias.scraper import fetch_article
from src.bbc_noticias.selector import select_best_story
from src.bbc_noticias.simplifier import simplify_article
from src.bbc_noticias.llm import LLM
from src.bbc_noticias.queue import enqueue_story, pop_story, pending_count

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# --- Discord UI components ---

class StoryButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="📰 Nueva historia",
            style=discord.ButtonStyle.primary,
            custom_id="request_story",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        story = pop_story()
        if not story:
            # No queued story — fetch one live
            await interaction.followup.send(
                "⏳ No hay historias en cola, buscando una nueva...", ephemeral=True
            )
            try:
                story = await fetch_and_pick_story(interaction.client.llm)
            except Exception as e:
                await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
                return
        await send_story_thread(interaction, story)
        await interaction.followup.send("✅ ¡Historias enviadas!", ephemeral=True)


class StoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StoryButton())


async def fetch_and_pick_story(llm: LLM) -> dict:
    """Fetch RSS stories and let LLM pick the best one."""
    stories = fetch_stories(max_age_hours=48)
    if not stories:
        raise RuntimeError("No se encontraron historias en las últimas 48 horas.")
    return select_best_story(stories, llm)


async def send_story_thread(interaction: discord.Interaction, story: dict) -> None:
    """Send a story as a message in the current channel, then create a thread on it."""
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        await interaction.followup.send("❌ Este comando solo funciona en un canal de texto.", ephemeral=True)
        return

    message_content = (
        f"📰 **{story['title']}**\n"
        f"🔗 {story['link']}\n\n"
        f"_Fuente: {story.get('source', 'BBC')} — {story.get('pub_date', '')[:10]}_"
    )

    # Post the message
    msg = await channel.send(message_content)

    # Create a thread on that message
    thread_name = story["title"][:100]
    thread = await channel.create_thread(
        name=thread_name,
        type=discord.ChannelType.public_thread,
        message=msg,
        auto_archive_duration=60,
    )

    # Simplify and post full article in the thread
    try:
        article_text = fetch_article(story["link"])
        if article_text:
            simplified = simplify_article(article_text, interaction.client.llm)
        else:
            simplified = story.get("description", "Sin descripción disponible.")
        await thread.send(f"📖 **{story['title']}**\n\n{simplified}")
    except Exception as e:
        logger.warning("[bot] Failed to simplify story: %s", e)
        await thread.send(f"📖 {story.get('description', 'Sin descripción disponible.')}")


# --- Bot setup ---

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.messages = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@tree.command(
    name="historia",
    description="Obtén una nueva historia de BBC Mundo (en español)",
)
async def historia(interaction: discord.Interaction):
    """Slash command: pick a story and send it with a thread."""
    await interaction.response.defer(ephemeral=False)

    story = pop_story()
    if not story:
        try:
            story = await fetch_and_pick_story(client.llm)
        except Exception as e:
            await interaction.followup.send(f"❌ No se pudo obtener historia: {e}")
            return

    await send_story_thread(interaction, story)


@tree.command(
    name="cola",
    description="Muestra cuántas historias hay pendientes en la cola",
)
async def cola(interaction: discord.Interaction):
    count = pending_count()
    await interaction.response.send_message(
        f"📋 Hay **{count}** historia{'s' if count != 1 else ''} en cola.",
        ephemeral=True,
    )


@client.event
async def on_ready() -> None:
    logger.info("[bot] Logged in as %s", client.user)
    # Register persistent view (for button)
    client.add_view(StoryView())
    logger.info("[bot] Views registered")

    # Init LLM
    config = load_config()
    client.llm = LLM(api_key=config.openrouter_api_key, model=config.openrouter_model)
    logger.info("[bot] LLM ready")


def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        logger.error("[bot] DISCORD_BOT_TOKEN not set")
        sys.exit(1)

    client.run(token, log_handler=None)


if __name__ == "__main__":
    main()