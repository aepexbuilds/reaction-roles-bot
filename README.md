# Reaction Roles Bot

A small Discord bot that lets members give themselves roles by reacting to a message.
React to get the role, remove the reaction to lose it.

Built with [discord.py](https://discordpy.readthedocs.io/).

## Features

- Assign and remove roles through reactions
- Works with unicode and custom server emoji
- Mappings are stored in a JSON file and survive a restart
- Slash commands, restricted to members with *Manage Roles*
- Refuses to assign roles it cannot manage instead of failing silently

## Commands

| Command | What it does |
| --- | --- |
| `/reactionrole add <message_id> <emoji> <role>` | Link an emoji on a message to a role |
| `/reactionrole remove <message_id> <emoji>` | Remove a link |
| `/reactionrole list` | Show every reaction role on the server |

## Setup

**1. Create the bot**

Go to the [Discord Developer Portal](https://discord.com/developers/applications),
create an application, open the **Bot** tab and copy the token.

**2. Install**

```bash
git clone https://github.com/YOUR-NAME/reaction-roles-bot.git
cd reaction-roles-bot
pip install -r requirements.txt
```

**3. Add your token**

Copy `.env.example` to `.env` and paste your token:

```
DISCORD_TOKEN=your_token_here
```

**4. Invite the bot**

In the Developer Portal under **OAuth2 > URL Generator**, select the scopes
`bot` and `applications.commands`, and the permission **Manage Roles**.
Open the generated link and add the bot to your server.

**5. Run it**

```bash
python bot.py
```

## Usage

1. Post the message members should react to
2. Enable **Developer Mode** in Discord (User Settings > Advanced)
3. Right-click the message and choose **Copy Message ID**
4. Run `/reactionrole add`, passing the ID, the emoji and the role
5. Add that reaction to the message yourself so members can click it

## Requirements

- Python 3.10 or newer
- The bot's role must sit **above** every role it should assign.
  Drag it up in *Server Settings > Roles* if assignments do not work.

## License

MIT
