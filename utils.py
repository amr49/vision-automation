import os
import requests
import logging

def fetch_posts(limit=10):
    """
    Fetches posts from JSONPlaceholder API.
    Returns the first 'limit' posts.
    """
    url = "https://jsonplaceholder.typicode.com/posts"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        posts = response.json()
        return posts[:limit]
    except requests.RequestException as e:
        logging.error(f"Error fetching posts: {e}")
        return []

def ensure_directory(path_str):
    """
    Ensures the specified directory exists.
    """
    if not os.path.exists(path_str):
        os.makedirs(path_str)
        logging.info(f"Created directory: {path_str}")
    else:
        logging.info(f"Directory already exists: {path_str}")

def format_post_content(post):
    """
    Formats the post content as per requirements.
    """
    return f"Title: {post['title']}\n\n{post['body']}"
