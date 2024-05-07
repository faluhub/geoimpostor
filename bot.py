import discord, os, random, util, asyncio
from discord import ApplicationContext
from PIL import Image
from ui import SubmissionView
from svdl import Location
from db.classes import User

debug = int(os.environ.get("DEBUG", 0)) == 1
print(f"Debug mode: {debug}")

bot = discord.AutoShardedBot(
    intents=discord.Intents.default(),
    debug_guilds=[1018128160962904114] if debug else None,
    owner_ids=[810863994985250836]
)

@bot.event
async def on_connect() -> None:
    await bot.register_commands()
    if bot.auto_sync_commands:
        await bot.sync_commands()
    print("Connected")

@bot.event
async def on_ready() -> None:
    print("Ready")

async def generate_image(locs: list[Location]):
    tasks = [loc.download() for loc in locs]
    downloaded_images = await asyncio.gather(*tasks)
    image = Image.new("RGB", (1920, 1080))
    for i, pano in enumerate(downloaded_images):
        x = i % 2 * pano.width
        y = (i // 2) * pano.height
        image.paste(pano, (x, y))
        pano.close()
    return image

@bot.slash_command(name="generate", description="Generates a new impostor challenge.")
async def generate_cmd(ctx: ApplicationContext) -> None:
    await ctx.defer()

    main_locs = util.rand_locs(amount=3)
    impostor_loc = util.rand_locs(amount=1)[0]
    while impostor_loc.country_code == main_locs[0].country_code:
        impostor_loc = util.rand_locs(amount=1)[0]
    locs = main_locs.copy()
    locs.append(impostor_loc)
    random.shuffle(locs)

    image = await generate_image(locs)
    image_path = f"./images/{ctx.guild.id}.png"
    image.save(image_path, "png")
    file = discord.File(image_path, filename="challenge.png")
    embed = discord.Embed(
        title="Impostor Challenge",
        description="Click `Submit` to submit a guess.",
        color=0xFFFFFF
    )
    embed.set_image(url="attachment://challenge.png")
    return await ctx.followup.send(
        embed=embed,
        file=file,
        view=SubmissionView(
            main_locs,
            impostor_loc,
            locs
        )
    )

@bot.slash_command(name="leaderboard", description="Shows the points leaderboard.")
@discord.option(
    name="amount",
    type=int,
    description="The amount of users to fetch",
    required=False
)
async def leaderboard_cmd(ctx: ApplicationContext, amount: int) -> None:
    await ctx.defer()
    amount = 5 if amount is None else amount

    users = User.get_top(amount)
    leaderboard = ""
    rank = 0
    for user in users:
        user_id, points = user
        user = await bot.get_or_fetch_user(user_id)
        if not user is None:
            rank += 1
            leaderboard += f"**{rank}.** *{user.name}* - `{points}`\n"

    if len(leaderboard) == 0:
        return await ctx.followup.send(
            embed=discord.Embed(
                description="The leaderboard couldn't be processed.",
                color=discord.Color.red()
            )
        )
    return await ctx.followup.send(
        embed=discord.Embed(
            title=f"Top {min(amount, len(users))} Players",
            description=leaderboard,
            color=0xFFFFFF
        )
    )

@bot.slash_command(name="points", description="Shows the points for the given user.")
@discord.option(
    name="member",
    type=discord.Member,
    description="The user whose points you want to view",
    required=False
)
async def points_cmd(ctx: ApplicationContext, member: discord.Member):
    await ctx.defer()

    user = ctx.author if member is None else member
    user_db = User(user.id)
    if not user_db.exists():
        return await ctx.followup.send(
            embed=discord.Embed(
                description="This user hasn't played yet.",
                color=discord.Color.red()
            )
        )
    embed = discord.Embed(color=0xFFFFFF)
    embed.set_author(name=user.name, icon_url=user.display_avatar.url)
    embed.add_field(name="Points:", value=f"`{user_db.get_points()}`", inline=False)
    return await ctx.followup.send(embed=embed)

def run():
    bot.run(os.environ.get("DISCORD_TOKEN"))
