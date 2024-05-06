import discord, os, random, util
from discord import ApplicationContext
from PIL import Image
from concurrent import futures
from ui import SubmissionView
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

@bot.slash_command(name="generate", description="Generates a new impostor challenge.")
async def generate_cmd(ctx: ApplicationContext) -> None:
    await ctx.defer()

    impostor_loc = util.rand_locs(amount=1)[0]
    main_locs = [impostor_loc]
    while impostor_loc in main_locs:
        main_locs = util.rand_locs(amount=3)
    locs = main_locs.copy()
    locs.append(impostor_loc)
    random.shuffle(locs)

    image = Image.new("RGB", (1920, 1080))
    with futures.ThreadPoolExecutor() as executor:
        future_to_index = {
            executor.submit(locs[i].download): i for i in range(len(locs))
        }
        for future in futures.as_completed(future_to_index):
            i = future_to_index[future]
            pano = future.result()
            image.paste(pano, (i % 2 * pano.width, int(i / 2) * pano.height))
            pano.close()

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
