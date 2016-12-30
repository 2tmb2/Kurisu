import logging
import discord
import json
from discord.ext import commands
from sys import argv

log = logging.getLogger('discord')

class Logs:
    """
    Logs join and leave messages, bans and unbans, and member changes.
    """
    def __init__(self, bot):
        self.bot = bot
        print('Addon "{}" loaded'.format(self.__class__.__name__))

    async def on_member_join(self, member):
        msg = "✅ **Join**: {} | {}#{}\n🗓 __Creation__: {}".format(
            member.mention, member.name, member.discriminator, member.created_at
        )
        await self.bot.send_message(self.bot.serverlogs_channel, msg)
        with open("restrictions.json", "r") as f:
            rsts = json.load(f)
        if member.id in rsts:
            roles = []
            for rst in rsts[member.id]:
                roles.append(discord.utils.get(self.bot.server.roles, name=rst))
            await self.bot.add_roles(member, *roles)

    async def on_member_remove(self, member):
        if "uk:"+member.id in self.bot.actions:
            return
        msg = "{}: {} | {}#{}".format("👢 **Auto-kick**" if "wk:"+member.id in self.bot.actions else "⬅️ **Leave**", member.mention, member.name, member.discriminator)
        await self.bot.send_message(self.bot.serverlogs_channel, msg)
        if "wk:"+member.id in self.bot.actions:
            self.bot.actions.remove("wk:"+member.id)
            await self.bot.send_message(self.bot.modlogs_channel, msg)

    async def on_member_ban(self, member):
        msg = "⛔ **{}**: {} | {}#{}".format("Auto-ban" if "wb:"+member.id in self.bot.actions else "Ban", member.mention, member.name, member.discriminator)
        await self.bot.send_message(self.bot.serverlogs_channel, msg)
        if "wb:"+member.id in self.bot.actions:
            self.bot.actions.remove("wb:"+member.id)
        else:
            msg += "\nThe responsible staff member should add an explanation below."
        await self.bot.send_message(self.bot.modlogs_channel, msg)

    async def on_member_unban(self, server, user):
        msg = "⚠️ **Unban**: {} | {}#{}".format(user.mention, user.name, user.discriminator)
        await self.bot.send_message(self.bot.modlogs_channel, msg)

    async def on_member_update(self, member_before, member_after):
        do_log = False  # only nickname and roles should be logged
        dest = self.bot.modlogs_channel
        msg = "ℹ️ **Member update**: {} | {}#{}".format(member_after.mention, member_after.name, member_after.discriminator)
        if member_before.roles != member_after.roles:
            do_log = True
            # role removal
            if len(member_before.roles) > len(member_after.roles):
                msg += "\n👑 __Role removal__: "
                for index, role in enumerate(member_before.roles):
                    if role.name == "@everyone":
                        continue
                    if role not in member_after.roles:
                        msg += "_~~" + role.name + "~~_"
                    else:
                        msg += role.name
                    if index != len(member_before.roles) - 1:
                        msg += ", "
            # role addition
            elif len(member_before.roles) < len(member_after.roles):
                msg += "\n👑 __Role addition__: "
                for index, role in enumerate(member_after.roles):
                    if role.name == "@everyone":
                        continue
                    if role not in member_before.roles:
                        msg += "__**" + role.name + "**__"
                    else:
                        msg += role.name
                    if index != len(member_after.roles) - 1:
                        msg += ", "
        if member_before.name != member_after.name:
            do_log = True
            dest = self.bot.serverlogs_channel
            msg += "\n📝 __Username change__: {} → {}".format(member_before.name, member_after.name)
        if member_before.nick != member_after.nick:
            do_log = True
            if member_before.nick == None:
                msg += "\n🏷 __Nickname addition__"
            elif member_after.nick == None:
                msg += "\n🏷 __Nickname removal__"
            else:
                msg += "\n🏷 __Nickname change__"
            msg += ": {0} → {1}".format(member_before.nick, member_after.nick)
        if do_log:
            await self.bot.send_message(dest, msg)

def setup(bot):
    bot.add_cog(Logs(bot))
