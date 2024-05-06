import discord, os, dotenv, random, util
from discord import ApplicationContext
from PIL import Image
from concurrent import futures
from ui import SubmissionView

dotenv.load_dotenv()

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
async def generate(ctx: ApplicationContext) -> None:
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

bot.run(os.environ.get("DISCORD_TOKEN"))
