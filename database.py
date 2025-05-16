async def save_post(self, post_data):
    """Save post with chat title"""
    try:
        existing = await self.posts.find_one({
            "chat_id": post_data["chat_id"],
            "message_id": post_data["message_id"]
        })
        
        if not existing:
            # Add chat title if available
            if "chat_title" not in post_data:
                post_data["chat_title"] = "Unknown"
            await self.posts.insert_one(post_data)
            return True
        return False
    except Exception as e:
        logger.error(f"Save post error: {e}")
        return False
