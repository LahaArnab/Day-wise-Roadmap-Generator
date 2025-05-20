import streamlit as st
import requests
import re
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# API
AZURE_API_KEY = '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'  # Replace with your Azure token
AZURE_ENDPOINT = "https://models.github.ai/inference"
AZURE_MODEL = "openai/gpt-4.1"
YOUTUBE_API_KEY = "AIzaSyB3wotkvjJCiRB3j29GopwAvzgsLnYgaQY"  # Replace with your YouTube Data API key

# AZURE OPENAI
client = ChatCompletionsClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_API_KEY),
)

# YouTube Video Search
def get_youtube_videos(api_key, query, max_results=2):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "key": api_key,
        "type": "video",
        "maxResults": max_results
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        return []
    data = resp.json()
    videos = []
    for item in data.get("items", []):
        title = item["snippet"]["title"]
        video_id = item["id"]["videoId"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        videos.append((title, url))
    return videos

# === Generate Roadmap from Azure OpenAI ===
def generate_roadmap(topic: str, days: int):
    prompt = (
        f"Create a {days}-day learning roadmap for {topic}. "
        f"Output strictly in this format:\n\n"
        f"Day 1: [task for day 1]\n"
        f"Day 2: [task for day 2]\n"
        f"...\n"
        f"Each day must begin with 'Day X:' and followed by a concise learning goal or task."
    )
    response = client.complete(
        messages=[
            SystemMessage("You are an expert educator and roadmap planner."),
            UserMessage(prompt),
        ],
        temperature=1,
        top_p=1,
        model=AZURE_MODEL
    )
    return response.choices[0].message.content

# === Extract Day-wise Tasks ===
def extract_day_tasks(text):
    pattern = re.compile(r"(?i)\bDay\s*(\d+)[\:\-]?\s*(.+)")
    day_tasks = []
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if match:
            day = f"Day {match.group(1)}"
            task = match.group(2).strip()
            day_tasks.append((day, task))
    return day_tasks

# Streamlit
st.set_page_config(page_title="Learning Roadmap Generator", layout="wide")
st.title(" Personalized Learning Roadmap Generator with YouTube Support")

with st.sidebar:
    st.header(" Settings")
    topic = st.text_input("Enter your learning topic", value="AI/ML")
    num_days = st.slider("Select number of days", min_value=1, max_value=60, value=30)
    max_videos = st.slider("YouTube videos per day", min_value=1, max_value=5, value=2)
    generate_button = st.button(" Generate Roadmap")

if generate_button:
    if not topic.strip():
        st.error("Please enter a valid topic.")
    else:
        with st.spinner("Generating roadmap from Azure OpenAI..."):
            roadmap_text = generate_roadmap(topic, num_days)
            day_tasks = extract_day_tasks(roadmap_text)

        if not day_tasks:
            st.error(" Couldn't parse roadmap days from the response.")
            st.markdown("###  Raw Response from Azure OpenAI:")
            st.code(roadmap_text)
        else:
            st.success(f" {len(day_tasks)}-Day Roadmap for: **{topic}**")
            for day, task in day_tasks:
                with st.expander(f"{day}: {task}"):
                    st.markdown(f"**Task**: {task}")
                    with st.spinner(f" Searching YouTube for: {task}"):
                        videos = get_youtube_videos(YOUTUBE_API_KEY, task, max_results=max_videos)
                        if videos:
                            for title, link in videos:
                                st.markdown(f"- [{title}]({link})")
                        else:
                            st.warning("No relevant YouTube videos found for this task.")
