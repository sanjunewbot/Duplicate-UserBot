@app.on_message(filters.command("add", prefixes=".") & filters.me)
async def add_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.edit_text("❌ Please reply to a media message.")
        return

    unique_id = get_media_unique_id(message.reply_to_message)
    if not unique_id:
        await message.edit_text("❌ The replied message does not contain supported media.")
        return

    chat_id = message.chat.id
    existing = await media_collection.find_one({
        "file_unique_id": unique_id,
        "chat_id": chat_id
    })

    if existing:
        await message.edit_text("✅ Media is already in the database.")
    else:
        await media_collection.insert_one({
            "file_unique_id": unique_id,
            "chat_id": chat_id,
            "msg_id": message.reply_to_message.id
        })
        await message.edit_text("✅ Media added to the database.")


@app.on_message(filters.command("remove", prefixes=".") & filters.me)
async def remove_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.edit_text("❌ Please reply to a media message.")
        return

    unique_id = get_media_unique_id(message.reply_to_message)
    if not unique_id:
        await message.edit_text("❌ The replied message does not contain supported media.")
        return

    chat_id = message.chat.id
    existing = await media_collection.find_one({
        "file_unique_id": unique_id,
        "chat_id": chat_id
    })

    if existing:
        await media_collection.delete_one({"_id": existing["_id"]})
        await message.edit_text("✅ Media removed from the database.")
    else:
        await message.edit_text("❌ Media is not in the database.")


@app.on_message(filters.group | filters.channel | filters.private, group=1)
async def new_message_handler(client: Client, message: Message):
    if message.text and message.text.startswith(".scan"):
        return

    unique_id = get_media_unique_id(message)
    if unique_id:
        chat_id = message.chat.id
        
        existing = await media_collection.find_one({
            "file_unique_id": unique_id,
            "chat_id": chat_id
        })
        
        if existing:
            await delete_queue.put((chat_id, message.id))
        else:
            await media_collection.insert_one({
                "file_unique_id": unique_id,
                "chat_id": chat_id,
                "msg_id": message.id
            })

if name == "main":
    emit_positive_health()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_database())
    loop.create_task(delete_worker(app))
    app.run()
