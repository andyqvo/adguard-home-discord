import asyncio
import base64
from datetime import datetime
import discord
from dotenv import load_dotenv
import os
import requests

load_dotenv()

SERVER = os.getenv("SERVER")
UPDATE_FREQUENCY = os.getenv("UPDATE_FREQUENCY")
TOKEN = os.getenv("TOKEN")
ADGUARD_ACCOUNT = os.getenv("ADGUARD_ACCOUNT")
ADGUARD_PASSWORD = os.getenv("ADGUARD_PASSWORD")

DECIMAL_PLACES = 2

ICON_PATH = "src/icon.png"
ICON = open(ICON_PATH, "rb")
ICON_BYTES = ICON.read()

intents = discord.Intents(guilds=True, messages=True, message_content=True)
client = discord.Client(intents=intents)


def encode_auth(account, password):
    auth_string = f"{account}:{password}"
    auth_bytes = auth_string.encode()
    auth64_bytes = base64.b64encode(auth_bytes)

    return auth64_bytes


def fetch_info(account, password):
    auth = encode_auth(account, password)
    base64_auth = auth.decode('ascii')
    headers = {"Authorization": f"Basic {base64_auth}"}
    res = requests.get(f"{SERVER}/control/stats", headers=headers)

    if res.status_code == 200:
        return res.json()


def build_embed(title="", description="", fields=[], color=0x239dd1):
    embed = discord.Embed(title=title, description=description, color=color)

    for field in fields:
        embed.add_field(name=field.get("name"), value=field.get("value"), inline=field.get("inline"))

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    embed.set_footer(text=f"AdGuard Home Discord | {current_time}")

    return embed


async def help_command(channel_id):
    embed = build_embed("All Commands", "`!stats - Get All Stats`")
    await client.get_channel(channel_id).send(embed=embed)


async def show_stats(channel_id):
    info = fetch_info(ADGUARD_ACCOUNT, ADGUARD_PASSWORD)

    num_dns_queries = "`{:,}`".format(info.get("num_dns_queries"))
    num_blocked_filtering = "`{:,}`".format(info.get("num_blocked_filtering"))
    num_replaced_parental = "`{:,}`".format(info.get("num_replaced_parental"))
    num_replaced_safebrowsing = "`{:,}`".format(info.get("num_replaced_safebrowsing"))
    num_replaced_safesearch = "`{:,}`".format(info.get("num_replaced_safesearch"))
    avg_processing_time = "`{:,.2f}s`".format(info.get("avg_processing_time"))

    fields = [
        {"name": "DNS Queries", "value": num_dns_queries, "inline": False},
        {"name": "Blocked by Filters", "value": num_blocked_filtering, "inline": False},
        {"name": "Blocked malware/phishing", "value": num_replaced_safebrowsing, "inline": False},
        {"name": "Blocked adult websites", "value": num_replaced_parental, "inline": False},
        {"name": "Enforced safe search", "value": num_replaced_safesearch, "inline": False},
        {"name": "Average Processing Time", "value": avg_processing_time, "inline": False}
    ]

    embed = build_embed(title="Stats", fields=fields)

    await client.get_channel(channel_id).send(embed=embed)


async def update_bot():
    info = fetch_info(ADGUARD_ACCOUNT, ADGUARD_PASSWORD)
    num_blocked_filtering = "{:,}".format(info.get("num_blocked_filtering"))

    ads_blocked = f"AdGuard Home | {num_blocked_filtering} queries blocked today."

    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=ads_blocked))
    await asyncio.sleep(int(UPDATE_FREQUENCY))


@client.event
async def on_message(message):
    commands = {
        "!help": help_command,
        "!stats": show_stats
    }

    content = message.content
    channel_id = message.channel.id

    if content in commands:
        await commands[content](channel_id)


@client.event
async def on_ready():
    print(f"Logged in as Username: {client.user.name}")
    print(f"User ID: {client.user.id}")
    print("-----------")

    while True:
        await update_bot()

while True:
    client.run(TOKEN)
    client.user.edit(avatar=ICON_BYTES)
