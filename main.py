from dotenv import load_dotenv
import datetime
import aiosqlite
import requests
import asyncio
import discord
import qrcode
import json
import os
import re

# Ensures the 'secrets' directory exists, as well as the '.env' file
# This is where you store your sensitive information like API keys
if not os.path.exists("secrets"):
    os.makedirs("secrets")
    with open("secrets/.env", "w") as file:
        file.write("TOKEN=\nGUILD=\nCHANNEL=\nCOINBASE_API=")

# Loads environment variables from the .env file
load_dotenv("secrets/.env")
TOKEN = os.getenv("TOKEN")
GUILD = os.getenv("GUILD")
COINBASE_API = os.getenv("COINBASE_API")
OWNER_ID = os.getenv("OWNER_ID")
THEME_COLOUR = (155, 50, 205)

# If any variables are missing, warns the user and exits
if TOKEN == "" or GUILD == "" or OWNER_ID == "" or COINBASE_API == "":
    print("Oh no! It looks like you’ve forgotten to fill out your \"secrets/.env\" file. Please fill it out and try the script again.\n\nIf you need help, you can check out the setup guide here:\nhttps://example.com")
    exit()

# Initializes other variables
version = "1.0.0"
bot = discord.Bot()
headers = {"Content-Type": "application/json","X-CC-Api-Key": COINBASE_API}
db_path = "secrets/payments.db"

# Initializes the payments database
async def init_db():
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                invoice_id TEXT NOT NULL,
                status TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL
            )
        ''')
        await db.commit()

# Logs payments to the database when told to
async def log_payment(user_id, amount, invoice_id, status, date, time):
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
            INSERT INTO payments (user_id, amount, invoice_id, status, date, time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, invoice_id, status, date, time))
        await db.commit()

# Checks the status of incomplete payments, and updates them when there are changes
async def get_statuses():
    while True:
        async with aiosqlite.connect(db_path) as db:
            async with db.execute("SELECT user_id, amount, invoice_id FROM payments WHERE status != 'COMPLETED'") as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    user_id, amount, invoice_id = row
                    # Checks payment status with Coinbase API
                    response = requests.get(f"https://api.commerce.coinbase.com/charges/{invoice_id}", headers=headers)
                    if response.status_code == 200:
                        status = response.json()["data"]["timeline"][-1]["status"]
                        if status == "COMPLETED":
                            # Updates payment status and notifies owner
                            await db.execute("UPDATE payments SET status = ? WHERE invoice_id = ?", (status, invoice_id))
                            await db.commit()
                            os.remove(f"qrcodes/{invoice_id}.png")
                            dm = await bot.fetch_user(OWNER_ID)
                            user = await bot.fetch_user(user_id)
                            await dm.send(f"{await sanitize_text(user.display_name)} just paid you ${amount:.2f}!")
                    
                    else:
                        print(f"Oh no! I had trouble fetching the status for invoice {invoice_id}. They responded with {response.status_code}.")
        await asyncio.sleep(30) # Waits for 30 seconds before checking again

# Sanitizes text to prevent unexpected behaviour
async def sanitize_text(text):
    return re.sub(r"[{}'\"\$|;|*?<>\\&]", "", text)

# Handles events when the bot is ready
@bot.event
async def on_ready():
    await init_db()
    asyncio.create_task(get_statuses())
    print(f"Hugard version {version}, created by yourlocalvalerie\n\nYay, I'm logged in as {bot.user}")

# Tests the bot's response time
@bot.slash_command(guild_ids=[GUILD],description="Ping me to see how fast I respond!")
async def ping(ctx):
    await ctx.respond(f"Pong! {bot.latency * 1_000:.0f}ms", ephemeral=True)

#Provides information about the bot
@bot.slash_command(guild_ids=[GUILD], description="Find out a bit more about me!")
async def about(ctx):
    embed = discord.Embed(colour=discord.Colour.from_rgb(*THEME_COLOUR), title="Hi there, I'm Hugard", description=" \n \n**I Was Created By:** yourlocalvalerie \n\n**About Me:**\nI’m here to help subs send payments to their owners, in a super secure and anonymous way!\nI work with Coinbase Commerce directly to make sure nobody learns anything they shouldn't about you!\nI’m designed to be super reliable and easy to use!\n\n**My Amazing Features:**\n- **Secure & Anonymous Payments:** I don't collect or store any information about you!\n- **Easy Setup:** I connect with Coinbase Commerce directly to make things as smooth as possible!\n- **Global Reach:** Wherever you are in the world, I’ve got you covered!\n- **Notification System:** I'll notify you as soon as you receive payments from your subs!\n- **Submissive Licensing**: My Mistress put me under the BSD 3-Clause License, just so you can do anything you want with me! \n\nWant More Info?\n Check out my GitHub page: https://example.com")
    await ctx.respond(embed=embed, ephemeral=True)

# Shows payment metrics for a specific user or the entire server
@bot.slash_command(guild_ids=[GUILD], description="See payment metrics for a specific user or the entire server!")
async def metrics(ctx, user: discord.User = None):
    # Checks if the user has permission to view audit logs
    if ctx.author.guild_permissions.view_audit_log:
        if user != None:
            # If a user is specified, shows their payment statistics
            async with aiosqlite.connect(db_path) as db:
                async with db.execute('''
                    SELECT amount, date, time FROM payments
                    WHERE status = ? AND user_id = ?
                ''', ("COMPLETE", user.id)) as cursor:
                    rows = await cursor.fetchall()
                    result = "\n".join(f"Paid ${amount:.2f} on {date} at {time}" for amount, date, time in rows)
            user = await bot.fetch_user(user.id)
            embed = discord.Embed(colour=discord.Colour.from_rgb(*THEME_COLOUR))
            embed.title = f"Total Paid From {await sanitize_text(user.display_name)}\n"
            embed.description = f"\n{result}\n\n= ${sum(row[0] for row in rows):.2f}"
            await ctx.respond(embed=embed)
        else:
            # If no user is specified, shows server-wide payment statistics
            async with aiosqlite.connect(db_path) as db:
                async with db.execute('''
                    SELECT user_id, SUM(amount) as amount
                    FROM payments
                    WHERE status = ?
                    GROUP BY user_id
                    ORDER BY amount DESC
                ''', ("COMPLETE",)) as cursor:
                    rows = await cursor.fetchall()
            user = await bot.fetch_user(rows[0][0])
            embed = discord.Embed(colour=discord.Colour.from_rgb(*THEME_COLOUR))
            embed.title = f"Hugard's Incredible Statistics For {ctx.guild.name}\n"
            embed.description = f"\nTotal Income: ${sum(row[1] for row in rows):.2f}\nAverage Income: ${sum(row[1] for row in rows) / len(rows):.2f}\nTotal Subs: {len(rows)}\n Highest Paying Sub: {await sanitize_text(user.display_name)} (${rows[0][1]:.2f})"
            await ctx.respond(embed=embed)

    else:
        # If the user doesn't have permission, sends an error message
        await ctx.respond("Sorry, but you're not allowed to use this command.", ephemeral=True)

# Allows individual members to check their payment history
@bot.slash_command(guild_ids=[GUILD], description="Check your own payment history in the server!")
async def history(ctx):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute('''
            SELECT amount, date, time FROM payments
            WHERE status = ? AND user_id = ?
        ''', ("COMPLETE", ctx.user.id)) as cursor:
            rows = await cursor.fetchall()
            result = "\n".join(f"Paid ${amount:.2f} on {date} at {time}" for amount, date, time in rows)
    embed = discord.Embed(colour=discord.Colour.from_rgb(*THEME_COLOUR))
    embed.title = f"My Payment History"
    embed.description = f"\n{result}\n\nTotal Paid: ${sum(row[0] for row in rows):.2f}"
    await ctx.respond(embed=embed, ephemeral=True)

# Gives members an easy way to pay their owner
@bot.slash_command(guild_ids=[GUILD], description="Send your owner some money!")
async def pay(ctx, amount: float):
    # Formats and validates the payment amount
    amount = f"{round(abs(amount), 2):.2f}"
    amount = float(amount.replace(",", ""))  
    try:
        if amount < 1:
            await ctx.respond("The minimum payment is $1", ephemeral=True)
        else:
            user_id = ctx.user.id
            # Prepares data for the Coinbase API
            cb_data = {"name": f"Payment From {user_id}","description": "None","pricing_type": "fixed_price","local_price": {"amount": amount,"currency": "USD"}}
            # Creates a charge using the Coinbase API
            response = requests.post("https://api.commerce.coinbase.com/charges/", headers=headers, data=json.dumps(cb_data))
            if response.status_code == 201:
                invoice_id = response.json()["data"]["id"]
                status = "NEW"

                now = datetime.datetime.now()
                date = f"{now.date()}"
                time = f"{now.time().replace(microsecond=0)}"

                await log_payment(user_id, amount, invoice_id, status, date, time)

                # Generates an easily scannable QR code for the payment
                qr = qrcode.QRCode(version=4, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1,)
                qr.add_data(f"https://commerce.coinbase.com/pay/{invoice_id}")
                qr.make(fit=True)
                qr_img = qr.make_image(back_color=(255, 255, 255), fill_color=(0, 0, 0))
                qr_img.save(f"qrcodes/{invoice_id}.png")

                embed = discord.Embed(title="Click me or scan the QR code below!", description=f"Amount due: ${amount}!", colour=discord.Colour.from_rgb(*THEME_COLOUR))
                file = discord.File(f"qrcodes/{invoice_id}.png", filename=f"{invoice_id}.png")
                embed.set_image(url=f"attachment://{invoice_id}.png")
                embed.url=f"https://commerce.coinbase.com/pay/{invoice_id}"
                await ctx.respond(embed=embed, file=file, ephemeral=True)
            else:
                # Sends an error if the Coinbase API does something unexpected
                print(f"Error processing payment, received code {response.status_code}")
                await ctx.respond("Oh no, there was an error processing your payment! Please try again later.", ephemeral=True)

    except Exception as dumberror:
        # Catches and reports all unexpected errors
        print(f"Oh no, an error occured! \n{dumberror}")
        await ctx.respond(f"Oh no, an error occured! \n{dumberror}", ephemeral=True)

# Runs the bot
bot.run(TOKEN)