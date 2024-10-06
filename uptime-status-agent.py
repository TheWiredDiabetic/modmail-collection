# Discord.py
import discord
from discord.ext import commands, tasks

# Necessary Imports
import aiohttp
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_configuration():
    # Check if environment variables exist
    heartbeat_uri = os.getenv("HEARTBEAT_URI")
    heartbeat_interval = os.getenv("HEARTBEAT_INTERVAL")

    # If not, fall back to config.json
    if not heartbeat_uri or not heartbeat_interval:
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                heartbeat_uri = heartbeat_uri or config.get("heartbeat_uri", "https://your-status-server.com/api/heartbeat")
                heartbeat_interval = heartbeat_interval or config.get("heartbeat_interval", 60)
                return {"heartbeat_uri": heartbeat_uri, "heartbeat_interval": int(heartbeat_interval)}
        except:
            # Fallback if both config.json and env are not available
            return {
                "heartbeat_uri": "https://your-status-server.com/api/heartbeat",
                "heartbeat_interval": 60
            }
    else:
        return {
            "heartbeat_uri": heartbeat_uri,
            "heartbeat_interval": int(heartbeat_interval)
        }

def save_configuration(config):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

class Uptime_Status_Agent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_configuration()
        self.heartbeat_uri = self.config.get("heartbeat_uri")
        self.heartbeat_interval = self.config.get("heartbeat_interval", 60)
        self.heartbeat.start()

    def cog_unload(self):
        print("Unloading Uptime Status Agent.")
        self.heartbeat.cancel()

    @tasks.loop(seconds=60)
    async def heartbeat(self):
        async with aiohttp.ClientSession() as session:
            try: 
                async with session.get(self.heartbeat_uri) as response:
                    if response.status == 200:
                        print("Heartbeat Sent")
                    else:
                        print(f"Failed to send heartbeat - {response.status}")
            except Exception as e:
                print(f"An error occurred: {e}")

    @heartbeat.before_loop
    async def before_heartbeat(self):
        await self.bot.wait_until_ready()

    @commands.command(name="set_heartbeat_uri")
    @commands.is_owner()
    async def set_heartbeat_uri(self, ctx, uri):
        self.heartbeat_uri = uri
        self.config["heartbeat_uri"] = uri
        save_configuration(self.config)
        
        embed = discord.Embed(
            title="Heartbeat URI Updated",
            description=f"Heartbeat URI has been set to:\n`{uri}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="set_heartbeat_interval")
    @commands.is_owner()
    async def set_heartbeat_interval(self, ctx, interval: int):
        self.heartbeat_interval = interval
        self.heartbeat.change_interval(seconds=interval)
        self.config["heartbeat_interval"] = interval
        save_configuration(self.config)
        
        embed = discord.Embed(
            title="Heartbeat Interval Updated",
            description=f"Heartbeat interval has been set to `{interval}` seconds.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name="get_configuration")
    @commands.is_owner()
    async def get_configuration(self, ctx):
        embed = discord.Embed(
            title="Current Configuration",
            description=json.dumps(self.config, indent=4),
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)
        print("Sent configuration!")

    @commands.command(name="dump_configuration") 
    @commands.is_owner()
    async def dump_configuration(self, ctx):
        embed = discord.Embed(
            title="Configuration Dump",
            description=json.dumps(self.config, indent=4),
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        print("Dumped configuration!")

# Initialize plugin 
async def setup(bot):
    await bot.add_cog(Uptime_Status_Agent(bot))
    print("Loaded 'uptime-status-agent' plugin!")

# Uninitialize plugin
async def teardown(bot):
    await bot.remove_cog("Uptime_Status_Agent")
    print("Unloaded 'uptime-status-agent' plugin!")
