import asyncio
import discord
import json
import re
from discord.ext import commands
from subprocess import call
from string import printable
from sys import argv

class Events:
    """
    Special event handling.
    """
    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))

    # don't add spaces or dashes to words
    piracy_tools = [
        'freeshop',
        'fr3eshop',
        'fr33shop',
        'fre3shop',
        'ciangel',
        'ciaangel',
        'tikdevil',
        'tikshop',
        'fr335h0p',
        'fr€€shop',
        'fr€€sh0p',
        'fr3esh0p',
        'fr//shop',
        'fr//sh0p',
        'free$hop',
        'fr$$hop',
        'friishop',
        'fr££shop',
        'fr£€shop',
        'fr£shop',
        'fr£eshop',
        'fre£shop',
        'fr€£shop',
        'threeshop',
        'thr33shop',
        'thr££shop',
        'thr£eshop',
        'thr33shop',
        'fr33sh0p',
        'freshop',
        'fresh0p',
        'fr$shop',
        'reeshop',
    ]

    charstocheck = re.sub('[ -]', '', printable)

    # I hate naming variables sometimes
    anti_spam_dict = {}

    async def add_restriction(self, member, rst):
        with open("restrictions.json", "r") as f:
            rsts = json.load(f)
        if member.id not in rsts:
            rsts[member.id] = []
        if rst not in rsts[member.id]:
            rsts[member.id].append(rst)
        with open("restrictions.json", "w") as f:
            json.dump(rsts, f)

    async def scan_message(self, message):
        embed = discord.Embed()
        embed.description = message.content
        if message.author.id in self.bot.watching:
            await self.bot.send_message(self.bot.messagelogs_channel, "**Watch log**: {} in {}".format(message.author.mention, message.channel.mention), embed=embed)
        is_help_channel = message.channel.name[0:5] == "help-"
        msg = ''.join(char for char in message.content.lower() if char in self.charstocheck)
        contains_invite_link = "discordapp.com/invite" in msg or "discord.gg" in msg or "join.skype.com" in msg
        # special check for a certain thing
        contains_piracy_site_mention = any(x in msg for x in ('3dsiso', '3dschaos'))
        contains_piracy_url_mention = any(x in msg for x in ('3ds.titlekeys', 'wiiu.titlekeys', 'titlekeys.com'))
        contains_piracy_tool_mention = any(x in msg for x in self.piracy_tools)
        contains_piracy_site_mention_indirect = any(x in msg for x in ('iso site', 'chaos site'))
        if contains_invite_link:
            await self.bot.send_message(self.bot.messagelogs_channel, "✉️ **Invite posted**: {} posted an invite link in {}\n------------------\n{}".format(message.author.mention, message.channel.mention, message.content))
        if contains_piracy_tool_mention:
            try:
                await self.bot.delete_message(message)
            except discord.errors.NotFound:
                pass
            try:
                await self.bot.send_message(message.author, "Please read {}. You cannot mention tools used for piracy, therefore your message was automatically deleted.".format(self.bot.welcome_channel.mention), embed=embed)
            except discord.errors.Forbidden:
                pass  # don't fail in case user has DMs disabled for this server, or blocked the bot
            await self.bot.send_message(self.bot.messagelogs_channel, "**Bad tool**: {} mentioned a piracy tool in {} (message deleted)".format(message.author.mention, message.channel.mention), embed=embed)
        if contains_piracy_site_mention or contains_piracy_url_mention:
            try:
                await self.bot.delete_message(message)
            except discord.errors.NotFound:
                pass
            try:
                await self.bot.send_message(message.author, "Please read {}. You cannot mention sites used for piracy directly, therefore your message was automatically deleted.".format(self.bot.welcome_channel.mention), embed=embed)
            except discord.errors.Forbidden:
                pass  # don't fail in case user has DMs disabled for this server, or blocked the bot
            await self.bot.send_message(self.bot.messagelogs_channel, "**Bad site**: {} mentioned a piracy site directly in {} (message deleted)".format(message.author.mention, message.channel.mention), embed=embed)
        elif contains_piracy_site_mention_indirect:
            if is_help_channel:
                try:
                    await self.bot.delete_message(message)
                except discord.errors.NotFound:
                    pass
                try:
                    await self.bot.send_message(message.author, "Please read {}. You cannot mention sites used for piracy in the help-and-questions channels directly or indirectly, therefore your message was automatically deleted.".format(self.bot.welcome_channel.mention), embed=embed)
                except discord.errors.Forbidden:
                    pass  # don't fail in case user has DMs disabled for this server, or blocked the bot
            await self.bot.send_message(self.bot.messagelogs_channel, "**Bad site**: {} mentioned a piracy site indirectly in {}{}".format(message.author.mention, message.channel.mention, " (message deleted)" if is_help_channel else ""), embed=embed)

    async def spam_check(self, message):
        if message.author.id not in self.anti_spam_dict:
            self.anti_spam_dict[message.author.id] = []
        self.anti_spam_dict[message.author.id].append(message)
        if len(self.anti_spam_dict[message.author.id]) == 6:  # it can trigger it multiple times if I use >. it can't skip to a number so this should work
            await self.bot.add_roles(message.author, self.bot.muted_role)
            await self.add_restriction(message.author, "Muted")
            print("{} is spamming".format(message.author))
            msg_user = "You were automatically muted for sending too many messages in a short period of time!\n\nIf you believe this was done in error, send a direct message to one of the staff in {}.".format(self.bot.welcome_channel.mention)
            try:
                await self.bot.send_message(message.author, msg_user)
            except discord.errors.Forbidden:
                pass  # don't fail in case user has DMs disabled for this server, or blocked the bot
            msg = "🔇 **Auto-muted**: {} muted for spamming | {}#{}".format(message.author.mention, message.author.name, message.author.discriminator)
            await self.bot.send_message(self.bot.modlogs_channel, msg)
            await self.bot.send_message(self.bot.mods_channel, msg)
            msgs_to_delete = self.anti_spam_dict[message.author.id][:]  # clone list so nothing is removed while going through it
            for msg in msgs_to_delete:
                try:
                    await self.bot.delete_message(msg)
                except discord.errors.NotFound:
                    pass  # don't fail if the message doesn't exist

        await asyncio.sleep(3)
        self.anti_spam_dict[message.author.id].remove(message)
        try:
            if len(self.anti_spam_dict[message.author.id]) == 0:
                self.anti_spam_dict.pop(message.author.id)
        except KeyError:
            pass  # if the array doesn't exist, don't raise an error

    async def on_message(self, message):
        if message.author.name == "GitHub" and message.author.discriminator == "0000":
            await self.bot.send_message(self.bot.helpers_channel, "Automatically pulling changes!")
            call(['git', 'pull'])
            await self.bot.close()
            return
        await self.bot.wait_until_ready()
        if message.author == self.bot.server.me or self.bot.staff_role in message.author.roles or message.channel == self.bot.helpers_channel:  # don't process messages by the bot or staff or in the helpers channel
            return
        await self.spam_check(message)
        await self.scan_message(message)

    async def on_message_edit(self, message_before, message_after):
        await self.bot.wait_until_ready()
        if message.author == self.bot.server.me or self.bot.staff_role in message.author.roles or message.channel == self.bot.helpers_channel:  # don't process messages by the bot or staff or in the helpers channel
            return
        await self.scan_message(message_after)

def setup(bot):
    bot.add_cog(Events(bot))
