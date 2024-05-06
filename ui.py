import discord, util
from svdl import Location
from db.classes import User

class SubmissionView(discord.ui.View):
    def __init__(self, main_locs: list[Location], imp_loc: Location, locs: list[Location]) -> None:
        super().__init__(timeout=None)
        self.main_locs = main_locs
        self.imp_loc = imp_loc
        self.locs = locs
        self.guessed = []

    @discord.ui.button(label="Submit", custom_id="submit", style=discord.ButtonStyle.blurple)
    async def confirm(self, _, interaction: discord.Interaction) -> None:
        if interaction.user.id in self.guessed:
            return await interaction.response.send_message("You have already submitted a guess for this challenge.", ephemeral=True)
        return await interaction.response.send_modal(SubmissionModal(self))

class SubmissionModal(discord.ui.Modal):
    def __init__(self, view: SubmissionView) -> None:
        super().__init__(
            discord.ui.InputText(
                label="Main Country",
                placeholder="Country code/name... (Example: 'fr' or 'France')",
                required=True
            ),
            discord.ui.InputText(
                label="Impostor Country",
                placeholder="Country code/name... (Example: 'fr' or 'France')",
                required=True
            ),
            discord.ui.InputText(
                label="Impostor Index",
                placeholder="1, 2, 3 or 4...",
                required=True
            ),
            title="Impostor Challenge",
            timeout=None
        )
        self.view = view
        self.country_codes = util.get_all_countries()
    
    async def callback(self, interaction: discord.Interaction) -> None:
        main_code = self.children[0].value.lower()
        correct_main_code = self.view.main_locs[0].country_code
        imp_code = self.children[1].value.lower()
        correct_imp_code = self.view.imp_loc.country_code
        if not main_code in self.country_codes:
            main_code = util.name_to_code(main_code)
            if main_code is None:
                return await interaction.response.send_message("Invalid country code/name for main.", ephemeral=True)
        if not imp_code in self.country_codes:
            imp_code = util.name_to_code(imp_code)
            if imp_code is None:
                return await interaction.response.send_message("Invalid country code/name for impostor.", ephemeral=True)
        imp_index = -1
        correct_imp_index = self.view.locs.index(self.view.imp_loc) + 1
        try:
            imp_index = int(self.children[2].value)
            if not imp_index in [1, 2, 3, 4]:
                return await interaction.response.send_message("There are only 4 panoramas, silly.", ephemeral=True)
        except:
            return await interaction.response.send_message("Invalid number for impostor index.", ephemeral=True)
        self.view.guessed.append(interaction.user.id)

        points = 0
        if main_code.lower() == correct_main_code: points += 1
        if imp_code.lower() == correct_imp_code: points += 1
        if imp_index == correct_imp_index: points +=1
        user_db = User(interaction.user.id)
        total_points = user_db.add_points(points)

        embed = discord.Embed(
            title="Results",
            description="".join(f"[Location {self.view.locs.index(loc) + 1}]({util.get_maps_link(loc)}), " for loc in self.view.locs)[:-2],
            color=0xFFFFFF
        )
        embed.add_field(name=f"Main Country ({'✅' if main_code.lower() == correct_main_code else '❌'})", value=f":flag_{correct_main_code}: {self.view.main_locs[0].country_name}", inline=False)
        embed.add_field(name=f"Impostor Country ({'✅' if imp_code.lower() == correct_imp_code else '❌'})", value=f":flag_{correct_imp_code}: {self.view.imp_loc.country_name}", inline=False)
        embed.add_field(name=f"Impostor Index ({'✅' if imp_index == correct_imp_index else '❌'})", value=f"`{correct_imp_index}`", inline=False)
        embed.set_footer(text=f"Points: {points}/3 | Total Points: {total_points}", icon_url=interaction.user.display_avatar.url)
        return await interaction.response.send_message(embed=embed, ephemeral=True)