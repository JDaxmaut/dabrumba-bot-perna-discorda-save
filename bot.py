import asyncio
import json
import os
import re

import discord
from discord.ext import commands

MAX_FILE_SIZE = 25 * 1024 * 1024
DONE_FILE = "done.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

active_prompts = {}

#NO SKIBIDI HERE DOP
def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
    return json.loads(text)


CONFIG = load_config("config.json")


def load_done():
    if os.path.exists(DONE_FILE):
        with open(DONE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_done(done):
    with open(DONE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(done), f, ensure_ascii=False, indent=2)


def sanitize_channel_name(name):
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^0-9a-zA-Zа-яА-ЯёЁ_-]", "", name)
    name = name.strip("-_").lower()[:100]
    return name or "channel"


def iter_files(root):
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            yield os.path.join(dirpath, fname)


class CategorySelect(discord.ui.Select):
    def __init__(self, categories, folder_path, folder_name, done):
        self.folder_path = folder_path
        self.folder_name = folder_name
        self.done = done
        options = [
            discord.SelectOption(label=cat.name, value=str(cat.id))
            for cat in categories
        ]
        options.append(discord.SelectOption(label="без категории", value="none"))
        super().__init__(
            placeholder="выбери категорию для канала...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction):
        if self.disabled:
            return
        self.disabled = True
        await interaction.response.edit_message(
            content="создаю канал и заливаю файлы...", view=self.view
        )

        value = self.values[0]
        category = interaction.guild.get_channel(int(value)) if value != "none" else None

        name = sanitize_channel_name(self.folder_name)
        if category is not None:
            channel = await category.create_text_channel(name, topic=self.folder_name)
        else:
            channel = await interaction.guild.create_text_channel(name, topic=self.folder_name)

        await self._upload(channel)

    async def _upload(self, channel):
        files = list(iter_files(self.folder_path))
        sent = 0
        await channel.send(f"заливаю файлы из `{self.folder_name}`...")
        for path in files:
            size = os.path.getsize(path)
            if size > MAX_FILE_SIZE:
                await channel.send(f"файл больше 25 мб, пропустил: `{path}`")
                continue
            try:
                await channel.send(file=discord.File(path))
                sent += 1
            except discord.HTTPException as e:
                await channel.send(f"не смог залить `{path}`: {e}")
            await asyncio.sleep(CONFIG.get("upload_delay_seconds", 0.4))
        await channel.send(f"готово, залил {sent} из {len(files)} файлов")
        self.done.add(self.folder_name)
        save_done(self.done)
        active_prompts.pop(self.folder_name, None)


class UploadView(discord.ui.View):
    def __init__(self, categories, folder_path, folder_name, done):
        super().__init__(timeout=None)
        self.add_item(CategorySelect(categories, folder_path, folder_name, done))

    async def on_error(self, interaction, error, item):
        print(f"Ошибка: {error}", flush=True)
        try:
            await interaction.followup.send(f"упс, косяк: {error}", ephemeral=True)
        except Exception:
            pass
        active_prompts.pop(self.children[0].folder_name, None)


async def watch_loop():
    watch = os.path.expanduser(CONFIG["watch_folder"])
    os.makedirs(watch, exist_ok=True)
    print(f"Слежу за папкой: {watch}", flush=True)
    guild = bot.get_guild(CONFIG["guild_id"])
    if guild is None and bot.guilds:
        guild = bot.guilds[0]
        print(
            f"guild_id в конфиге не найден, использую первый доступный сервер: "
            f"{guild.name} ({guild.id})",
            flush=True,
        )
    log_channel = guild.get_channel(CONFIG["log_channel_id"]) if guild else None
    print(
        f"Канал для промптов: {log_channel} (id {CONFIG['log_channel_id']})",
        flush=True,
    )
    done = load_done()

    while True:
        try:
            if guild and log_channel and os.path.isdir(watch):
                categories = list(guild.categories)
                for entry in sorted(os.listdir(watch)):
                    entry_path = os.path.join(watch, entry)
                    if not os.path.isdir(entry_path):
                        continue
                    if entry in done or entry in active_prompts:
                        continue
                    view = UploadView(categories, entry_path, entry, done)
                    embed = discord.Embed(
                        title="нашёл новую папку",
                        description=f"**`{entry}`**\n\nвыбери, в какую категорию пихнуть канал.",
                        color=discord.Color.blue(),
                    )
                    message = await log_channel.send(embed=embed, view=view)
                    active_prompts[entry] = message.id
                await asyncio.sleep(0.5)
        except Exception as e:
            print("watch loop:", e)
        await asyncio.sleep(CONFIG.get("poll_interval_seconds", 5))


@bot.event
async def on_ready():
    guilds = [f"{g.name} ({g.id})" for g in bot.guilds]
    print(f"Логин: {bot.user} (ID: {bot.user.id})", flush=True)
    print(f"Серверы, где есть бот: {guilds}", flush=True)
    bot.loop.create_task(watch_loop())


if __name__ == "__main__":
    bot.run(CONFIG["token"])
