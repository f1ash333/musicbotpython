import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta, timezone
import asyncio
import json
import os
import subprocess


intents = nextcord.Intents.default()
intents.members = True
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Список запрещенных слов
banned_words = ['саливер', 'хаунтед говно', 'saliver']

activity = 'Ёбле бруксов'

@bot.event
async def on_ready():
    print(f'Бот {bot.user} готов к работе!')
    await bot.change_presence(status=nextcord.Status.do_not_disturb, activity=nextcord.Activity(type=nextcord.ActivityType.competing, name=activity))
    print(f'Activity - {activity}')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if any(word in message.content.lower() for word in banned_words):
        await message.delete()
        await message.channel.send(f'{message.author.mention}, ваше сообщение было удалено из-за использования запрещенных слов.')

    await bot.process_commands(message)

    @bot.event
    async def on_member_join(member):
        autorole_id = 1181209672544424027
        autorole = member.guild.get_role(autorole_id)
        await member.add_roles(autorole)

    @bot.command(name='setautorole', description='Set the autorole for new members')
    @commands.has_permissions(administrator=True)
    async def set_autorole(ctx, role: nextcord.Role):
        with open('autorole.json', 'w') as f:
            json.dump({'autorole_id': role.id}, f)
        await ctx.send(f' Autorole set to {role.mention}')

    @bot.event
    async def on_ready():
        if os.path.exists('autorole.json'):
            with open('autorole.json', 'r') as f:
                autorole_data = json.load(f)
                autorole_id = autorole_data['autorole_id']
                print(f'Loaded autorole ID: {autorole_id}')
        else:
            autorole_id = None
        print(f'Logged in as {bot.user.name}')

    xp_per_message = 10
    level_up_threshold = 500
    levels_db = {}


    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        if message.author.id not in levels_db:
            levels_db[message.author.id] = {'level': 1, 'xp': 0}
        levels_db[message.author.id]['xp'] += xp_per_message

        if levels_db[message.author.id]['xp'] >= level_up_threshold:
            levels_db[message.author.id]['level'] += 1
            levels_db[message.author.id]['xp'] -= level_up_threshold
            await message.channel.send(
                f'Congratulations, {message.author.mention}! You leveled up to level {levels_db[message.author.id]["level"]}!')

        await bot.process_commands(message)

    @bot.command(name='level', description='Показать свой уровень')
    async def level_command(ctx):
        if ctx.author.id not in levels_db:
            levels_db[ctx.author.id] = {'level': 1, 'xp': 0}
        embed = nextcord.Embed(title=f'Уровень {ctx.author.name}',
                               description=f'Уровень: {levels_db[ctx.author.id]["level"]}\nXP: {levels_db[ctx.author.id]["xp"]}/{level_up_threshold}',
                               color=0x00ff00)
        await ctx.send(embed=embed)

    @bot.command(name='top', description='Показать топ уровней')
    async def top_command(ctx):
        top_users = sorted(levels_db.items(), key=lambda x: x[1]['level'], reverse=True)
        embed = nextcord.Embed(title='Топ уровней', description='Топ 10 пользователей по уровню', color=0x00ff00)
        for i, (user_id, user_data) in enumerate(top_users[:10]):
            user = bot.get_user(user_id)
            embed.add_field(name=f'{i + 1}. {user.name}',
                            value=f'Уровень: {user_data["level"]}\nXP: {user_data["xp"]}/{level_up_threshold}',
                            inline=False)
        await ctx.send(embed=embed)


def load_warnings():
    if os.path.exists('warnings.json'):
        try:
            with open('warnings.json', 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    else:
        return {}

def save_warnings(warns):
    with open('warnings.json', 'w') as f:
        json.dump(warns, f, indent=4)

warns = load_warnings()

def load_warnings():
    if os.path.exists('warnings.json'):
        try:
            with open('warnings.json', 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    else:
        return {}

def save_warnings(warns):
    with open('warnings.json', 'w') as f:
        json.dump(warns, f, indent=4)

warns = load_warnings()

@bot.command(name='warn')
async def warn(ctx, member: nextcord.Member, *, reason=None):
    if not ctx.author.guild_permissions.manage_messages:
        embed = nextcord.Embed(title='Ошибка', description='У вас нет прав на выдачу варна.', color=0xff000)
        await ctx.send(embed=embed)
        return

    if member.id not in warns:
        warns[member.id] = 1
    else:
        warns[member.id] += 1

    embed = nextcord.Embed(title='Варн', color=0xff0000)
    embed.add_field(name='Варненный пользователь', value=member.mention, inline=False)
    embed.add_field(name='Количество варнов', value=f'{warns[member.id]}/3', inline=False)
    embed.add_field(name='Причина варна', value=reason, inline=False)
    embed.add_field(name='Выдал варн', value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)

    dm_embed = nextcord.Embed(title='Варн', color=0xff0000)
    dm_embed.add_field(name='Вы получили варн на сервере', value=ctx.guild.name, inline=False)
    dm_embed.add_field(name='Причина варна', value=reason, inline=False)
    dm_embed.add_field(name='Выдал варн', value=ctx.author.mention, inline=False)
    if member.dm_channel is None:
        await member.create_dm()
    await member.dm_channel.send(embed=dm_embed)

    save_warnings(warns)

    if warns[member.id] == 3:
        role_id = 1269491285668925472
        role = ctx.guild.get_role(role_id)
        await member.add_roles(role)
        embed = nextcord.Embed(title='Внимание! Пользователь получил 3/3 warn', color=0xff0000)
        embed.add_field(name='Пользователь', value=f'{member.mention} получает роль <@&1269491285668925472>', inline=False)
        await ctx.send(embed=embed)

@bot.command(name='warnings')
async def warnings(ctx, member: nextcord.Member):
    if member.id not in warns:
        embed = nextcord.Embed(title='Варны', description=f'У {member.mention} нет варнов.', color=0x00ff00)
        await ctx.send(embed=embed)
        return

    embed = nextcord.Embed(title='Варны', description=f'Варны {member.mention}:', color=0x00ff00)
    embed.add_field(name='Количество варнов', value=f'{warns[member.id]}/3', inline=False)
    await ctx.send(embed=embed)

@bot.command(name='reset_warnings')
async def reset_warnings(ctx, member: nextcord.Member):
    if not ctx.author.guild_permissions.manage_messages:
        embed = nextcord.Embed(title='Ошибка', description='У вас нет прав на сброс варнов.', color=0xff0000)
        await ctx.send(embed=embed)
        return

    if member.id in warns:
        warns.pop(member.id)
        save_warnings(warns)
        embed = nextcord.Embed(title='Варны', description=f'Варны {member.mention} были сброшены.', color=0x00ff00)
        await ctx.send(embed=embed)
    else:
        embed = nextcord.Embed(title='Варны', description=f'У {member.mention} нет варнов.', color=0x00ff00)
        await ctx.send(embed=embed)

@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = nextcord.Embed(title='Ошибка', description='Неправильное использование команды. Используйте `!warn <@member> [reason]`', color=0xff0000)
        await ctx.send(embed=embed)


@bot.command(name='ban')
async def ban(ctx, user: nextcord.Member | int, duration: str, *, reason: str = None):
    if not ctx.author.guild_permissions.ban_members:
        embed = nextcord.Embed(title='🚫 | Ошибка', description='У вас нет прав на выдачу бана.', color=0xff0000)
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('🚫')
        return

    if isinstance(user, int):
        user_id = user
        user = ctx.guild.get_member(user_id)
        if user is None:
            embed = nextcord.Embed(title='🚫 | Ошибка', description='Пользователь не найден на сервере.', color=0xff0000)
            await ctx.send(embed=embed)
            return
    else:
        user_id = user.id

    if duration.endswith('d'):
        duration_in_seconds = int(duration[:-1]) * 86400
    elif duration.endswith('h'):
        duration_in_seconds = int(duration[:-1]) * 3600
    elif duration.endswith('m'):
        duration_in_seconds = int(duration[:-1]) * 60
    else:
        await ctx.send('Неправильный формат длительности бана. Используйте d, h или m.')
        return

    await ctx.guild.ban(nextcord.Object(id=user_id), reason=reason)
    embed = nextcord.Embed(title='Бан', color=0xff0000)
    embed.add_field(name='Забаненный пользователь', value=user.mention, inline=False)
    embed.add_field(name='Длительность бана', value=duration, inline=False)
    embed.add_field(name='Причина бана', value=reason, inline=False)
    embed.add_field(name='Забанил', value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)

    async def unban_member():
        await asyncio.sleep(duration_in_seconds)
        await ctx.guild.unban(nextcord.Object(id=user_id))
        embed = nextcord.Embed(title='Разбан', color=0x00ff00)
        embed.add_field(name='Разбаненный пользователь', value=user.mention, inline=False)
        embed.add_field(name='Разбанил', value=bot.user.mention, inline=False)
        await ctx.send(embed=embed)

    bot.loop.create_task(unban_member())

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = nextcord.Embed(title='🚫 | Ошибка', description='Неправильное использование команды. Используйте `!ban <@member или ID> <duration> [reason]`', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        raise error

@bot.command(name='unban')
async def unban(ctx, member_id: int):
    if not ctx.author.guild_permissions.ban_members:
        embed = nextcord.Embed(title='🚫 | Ошибка', description='У вас нет прав на снятие бана.', color=0xff0000)
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('🚫')
        return

    banned_users = await ctx.guild.bans().flatten()

    for ban_entry in banned_users:
        user = ban_entry.user

        if user.id == member_id:
            await ctx.guild.unban(user)
            embed = nextcord.Embed(title='Разбан', color=0x00ff00)
            embed.add_field(name='Разбаненный пользователь', value=user.mention, inline=False)
            embed.add_field(name='Разбанил', value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
            return
    else:
        embed = nextcord.Embed(title='Ошибка', description='Пользователь не найден в списке забаненных.', color=0xff0000)
        await ctx.send(embed=embed)

@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = nextcord.Embed(title='Ошибка', description='Неправильное использование команды. Используйте `!unban <ID пользователя>`', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        raise error


@bot.command(name='kick')
async def kick(ctx, member: nextcord.Member | int, *, reason=None):
    if not ctx.author.guild_permissions.kick_members:
        embed = nextcord.Embed(title='🚫 | Ошибка', description='У вас нет прав на кик пользователя.', color=0xff0000)
        await ctx.send(embed=embed)
        return
    if isinstance(member, int):
        member = ctx.guild.get_member(member)
        if member is None:
            embed = nextcord.Embed(title='🚫 | Ошибка', description=f'Пользователь с ID {member} не найден на сервере.', color=0xff0000)
            await ctx.send(embed=embed)
            return
    else:
        member = member
    await member.kick(reason=reason)
    embed = nextcord.Embed(title='Кик', description=f'{member.mention} был кикнут.', color=0x00ff00)
    embed.add_field(name='Кикнул:', value=f'{ctx.author.mention}', inline=False)
    embed.add_field(name='Причина', value=reason, inline=False)
    await ctx.send(embed=embed)

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = nextcord.Embed(title='Ошибка', description='Неправильное использование команды. Используйте `!kick <@member или ID> [reason]`', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        raise error


@bot.command(name='mute')
async def mute(ctx, member: nextcord.Member, time: int, *, reason=None):
    moderator_role_id = 1181249801526976582
    if ctx.author.guild_permissions.administrator or moderator_role_id in [role.id for role in ctx.author.roles]:
        if member.communication_disabled_until is not None:
            await ctx.send(f'{member.mention} already has a mute.')
            return
        await member.edit(timeout=nextcord.utils.utcnow() + timedelta(minutes=time), reason=reason)
        embed = nextcord.Embed(title='Мут', description=f'{member.mention} получил мут на {time} минут.', color=0x00ff00)
        embed.add_field(name='Выдал мут', value=f'{ctx.author.mention}', inline=False)
        embed.add_field(name='Причина', value=reason, inline=False)
        await ctx.send(embed=embed)
    else:
        embed = nextcord.Embed(title='🚫 | Ошибка', description='У вас нет прав на выдачу мута.', color=0xff0000)
        await ctx.send(embed=embed)

@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = nextcord.Embed(title='🚫 | Ошибка', description='Неправильное использование команды. Используйте `!mute <@member> <time> [reason]`', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        raise error

@bot.command(name='unmute')
async def unmute(ctx, member: nextcord.Member, *, reason=None):
    moderator_role_id = 1181249801526976582
    if ctx.author.guild_permissions.administrator or moderator_role_id in [role.id for role in ctx.author.roles]:
        if member.communication_disabled_until is None:
            embed = nextcord.Embed(title='Не удалось снять мут', description=f'{member.mention} не имеет мута.', color=0x00ff00)
            await ctx.send(embed=embed)
            return
        await member.edit(timeout=None, reason=reason)
        embed = nextcord.Embed(title='Размут', description=f'{member.mention} был размучен.', color=0x00ff00)
        embed.add_field(name='Размутил', value=f'{ctx.author.mention}', inline=False)
        embed.add_field(name='Причина', value=reason, inline=False)
        await ctx.send(embed=embed)
    else:
        embed = nextcord.Embed(title='Ошибка', description='У вас нет прав на снятие мута.', color=0xff0000)
        await ctx.send(embed=embed)

@unmute.error
async def unmute_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = nextcord.Embed(title='🚫 | Ошибка', description='Неправильное использование команды. Используйте `!unmute <@member> [reason]`', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        raise error

@bot.command(name='commands', description='Показать список команд')
async def commands_command(ctx):
    embed = nextcord.Embed(title='Список команд', description='Здесь вы можете увидеть все доступные команды бота.', color=0x00ff00)

    embed.add_field(name='!help /help', value='Вывести справку по командам.', inline=False)
    embed.add_field(name='!ping', value='Получить текущее latency бота.', inline=False)

    if ctx.author.guild_permissions.manage_messages:
        embed.add_field(name='!kick <@member или ID> [reason]', value='Кикнуть пользователя с сервера.', inline=False)
        embed.add_field(name='!ban <@member или ID> <duration> [reason]', value='Забанить пользователя на сервере.', inline=False)
        embed.add_field(name='!unban <ID пользователя>', value='Разбанить пользователя с сервера.', inline=False)
        embed.add_field(name='!mute <@member> <time> [reason]', value='Замутить пользователя на сервере.', inline=False)
        embed.add_field(name='!unmute <@member> [reason]', value='Размутить пользователя на сервере.', inline=False)
        embed.add_field(name='!warn <@member> [reason]', value='Выдать варн пользователю.', inline=False)
        embed.add_field(name='!warnings <@member>', value='Посмотреть все варны пользователя.', inline=False)
        embed.add_field(name='!reset_warnings <@member>', value='Сбросить все варны пользователя.', inline=False)

    await ctx.send(embed=embed)

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.balances = {}

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        try:
            with open('balances.json', 'r') as f:
                self.balances = json.load(f)
        except FileNotFoundError:
            pass

    async def on_disconnect(self):
        with open('balances.json', 'w') as f:
            json.dump(self.balances, f)


@bot.command(name='say')
async def say(ctx, *, text):
    await ctx.message.delete()
    await ctx.send(text)


@bot.event
async def on_voice_state_update(member, before, after, *, reason=None):

    if before.channel is None and after.channel is not None:
        if after.channel.id == 1269641468310585426:
            role_id = 1181215218995560519
            if any(role.id == role_id for role in member.roles):
                category = bot.get_channel(1181303037873098962)

                channel_name = f'Private - {member.name}'
                channel = await category.create_voice_channel(channel_name)

                await channel.edit(user_limit=1, bitrate=64000)

                await channel.set_permissions(member, manage_channels=True, manage_permissions=True)

                await member.move_to(channel)

                await member.send(f'Приватная комната `{channel_name}` успешно создана!')
            else:
                await member.send('У вас нет прав для создания привата')

    if before.channel is not None and after.channel is None:
        if before.channel.name.startswith('Private - '):
            if len(before.channel.members) == 0:
                await asyncio.sleep(180)
                if len(before.channel.members) == 0:
                    await before.channel.delete()
                    print(f'Deleted empty private channel {before.channel.name}')



def load_token():
    with open('token.json', 'r') as f:
        return json.load(f)['token']

def save_token(token):
    with open('token.json', 'w') as f:
        json.dump({'token': token}, f)

try:
    token = load_token()
except FileNotFoundError:
    token = input("token: ")
    save_token(token)


async def get_or_create_channel(guild, category_name, channel_name):
    category = nextcord.utils.get(guild.categories, name=category_name)
    if not category:
        category = await guild.create_category(category_name)

    channel = nextcord.utils.get(guild.text_channels, name=channel_name)
    if not channel:
        channel = await guild.create_text_channel(channel_name, category=category)

    return channel

@bot.event
async def on_member_update(before, after):
    guild = before.guild
    if before.nick!= after.nick:
        nick_channel = await get_or_create_channel(guild, "DISCORD LOGS", "🥽┃ники")
        embed = nextcord.Embed(title="Изменение никнейма", colour=nextcord.Colour.blue())
        embed.add_field(name="Пользователь", value=after.mention, inline=False)
        embed.add_field(name="Старый ник", value=before.nick, inline=False)
        embed.add_field(name="Новый ник", value=after.nick, inline=False)
        await nick_channel.send(embed=embed)
    if before.roles!= after.roles:
        log_channel = await get_or_create_channel(guild, "DISCORD LOGS", "🚉┃роли")
        await asyncio.sleep(1)
        async for entry in guild.audit_logs(limit=10, action=nextcord.AuditLogAction.member_role_update):
            if entry.target.id == after.id:
                time_difference = datetime.now(timezone.utc) - entry.created_at
                if time_difference < timedelta(seconds=10):
                    if entry.before.roles!= entry.after.roles:
                        for role in entry.after.roles:
                            if role not in entry.before.roles:
                                embed = nextcord.Embed(title="Роль добавлена", colour=role.colour)
                                embed.add_field(name="Пользователь", value=after.mention, inline=False)
                                embed.add_field(name="Роль", value=role.mention, inline=False)
                                embed.add_field(name="Выдал роль", value=entry.user.mention, inline=False)
                                await log_channel.send(embed=embed)
                        for role in entry.before.roles:
                            if role not in entry.after.roles:
                                embed = nextcord.Embed(title="Роль удалена", colour=role.colour)
                                embed.add_field(name="Пользователь", value=after.mention, inline=False)
                                embed.add_field(name="Роль", value=role.mention, inline=False)
                                embed.add_field(name="Убрал роль", value=entry.user.mention, inline=False)
                                await log_channel.send(embed=embed)


@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    voice_channel = await get_or_create_channel(guild, "DISCORD LOGS", "🔊┃войс")

    if before.channel!= after.channel:
        embed = nextcord.Embed(title="Изменение голосового канала", colour=nextcord.Colour.green(),
                               timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Пользователь", value=member.mention, inline=False)

        if before.channel:
            embed.add_field(name="Старый канал", value=before.channel.name, inline=False)
        else:
            embed.add_field(name="Старый канал", value="None", inline=False)

        if after.channel:
            embed.add_field(name="Новый канал", value=after.channel.name, inline=False)
        else:
            embed.add_field(name="Новый канал", value="Пользователь вышел из канала", inline=False)

        async for log in guild.audit_logs(action=nextcord.AuditLogAction.member_move, limit=10):
            if log.target and log.target.id == member.id and log.created_at > datetime.now(timezone.utc) - timedelta(seconds=20):
                embed.add_field(name="Кто переместил", value=log.user.mention, inline=False)
                break
        else:
            embed.add_field(name="Действие", value="Пользователь переместился сам", inline=False)

        await voice_channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    guild = message.guild
    message_channel = await get_or_create_channel(guild, "DISCORD LOGS", "📃┃сообщения")
    embed = nextcord.Embed(title="Удаление сообщения", colour=nextcord.Colour.red())
    embed.add_field(name="Пользователь", value=message.author.mention, inline=False)
    embed.add_field(name="Сообщение", value=message.content, inline=False)
    await message_channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    guild = before.guild
    message_channel = await get_or_create_channel(guild, "DISCORD LOGS", "📃┃сообщения")
    embed = nextcord.Embed(title="Редактирование сообщения", colour=nextcord.Colour.orange())
    embed.add_field(name="Пользователь", value=before.author.mention, inline=False)
    embed.add_field(name="Исходное сообщение", value=before.content, inline=False)
    embed.add_field(name="Новое сообщение", value=after.content, inline=False)
    await message_channel.send(embed=embed)

@bot.event
async def on_member_join(member):
    guild = member.guild
    user_channel = await get_or_create_channel(guild, "DISCORD LOGS", "🔗┃пользователи")
    embed = nextcord.Embed(title="Новый пользователь", colour=nextcord.Colour.blue())
    embed.add_field(name="Пользователь", value=member.mention, inline=False)
    await user_channel.send(embed=embed)

    @bot.event
    async def on_member_ban(guild, user):
        try:
            punishment_channel = await get_or_create_channel(guild, "DISCORD LOGS", "🔎┃наказания")
            embed = nextcord.Embed(title="Бан пользователя", colour=nextcord.Colour.red())
            embed.add_field(name="Пользователь", value=user.mention, inline=False)
            await punishment_channel.send(embed=embed)
        except Exception as e:
            print(f"Ошибка в on_member_ban: {e}")

    @bot.event
    async def on_member_unban(guild, user):
        try:
            punishment_channel = await get_or_create_channel(guild, "DISCORD LOGS", "🔎┃наказания")
            embed = nextcord.Embed(title="Разбан пользователя", colour=nextcord.Colour.green())
            embed.add_field(name="Пользователь", value=user.mention, inline=False)
            await punishment_channel.send(embed=embed)
        except Exception as e:
            print(f"Ошибка в on_member_unban: {e}")

    @bot.event
    async def on_member_timeout(member, until):
        try:
            guild = member.guild
            punishment_channel = await get_or_create_channel(guild, "DISCORD LOGS", "🔎┃наказания")
            embed = nextcord.Embed(title="Таймаут пользователя", colour=nextcord.Colour.orange())
            embed.add_field(name="Пользователь", value=member.mention, inline=False)
            embed.add_field(name="До", value=until.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
            await punishment_channel.send(embed=embed)
        except Exception as e:
            print(f"Ошибка в on_member_timeout: {e}")

    @bot.event
    async def on_member_update(before, after):
        try:
            if before.communication_disabled_until != after.communication_disabled_until:
                if after.communication_disabled_until is None:
                    punishment_channel = await get_or_create_channel(after.guild, "DISCORD LOGS", "🔎┃наказания")
                    embed = nextcord.Embed(title="Снятие таймаута", colour=nextcord.Colour.green())
                    embed.add_field(name="Пользователь", value=after.mention, inline=False)
                    await punishment_channel.send(embed=embed)
        except Exception as e:
            print(f"Ошибка в on_member_update: {e}")

    @bot.event
    async def on_guild_channel_create(channel):
        guild = channel.guild
        channel_log = await get_or_create_channel(guild, "DISCORD LOGS", "📱┃каналы")
        embed = nextcord.Embed(title="Создание канала", colour=nextcord.Colour.green())
        embed.add_field(name="Канал", value=channel.mention, inline=False)
        await channel_log.send(embed=embed)

    @bot.event
    async def on_guild_channel_delete(channel):
        guild = channel.guild
        channel_log = await get_or_create_channel(guild, "DISCORD LOGS", "📱┃каналы")
        embed = nextcord.Embed(title="Удаление канала", colour=nextcord.Colour.red())
        embed.add_field(name="Канал", value=channel.name, inline=False)
        await channel_log.send(embed=embed)

    @bot.event
    async def on_guild_channel_update(before, after):
        guild = before.guild
        channel_log = await get_or_create_channel(guild, "DISCORD LOGS", "📱┃каналы")
        embed = nextcord.Embed(title="Обновление канала", colour=nextcord.Colour.blue())
        embed.add_field(name="Старое название", value=before.name, inline=False)
        embed.add_field(name="Новое название", value=after.name, inline=False)
        await channel_log.send(embed=embed)

@bot.command(name='mclear', help='Delete multiple messages')
async def mclear(ctx, amount: int):
    if amount < 1:
        await ctx.send('Invalid amount. Please enter a positive integer.')
        return

    messages = await ctx.channel.history(limit=amount).flatten()
    await ctx.channel.delete_messages(messages)
    embed = nextcord.Embed(title="Deleted messages", description=f"Deleted {amount} messages.", color=nextcord.Colour.green())
    msg = await ctx.send(embed=embed)
    await asyncio.sleep(30)
    await msg.delete()


TOKEN = 'MTI2OTQwMzI3NjEwMTU1MDEwMw.GA6dva.KtHJdYjh9PCgU_pYAL-yLrM5jt2vVyJ_BJBZac'

subprocess.Popen(['python', 'bot.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

bot.run(TOKEN)