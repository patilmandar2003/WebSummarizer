import base64
from typing import List, TypedDict, Annotated, Optional, Dict, Any
from langchain_ollama import OllamaLLM
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
import pypdf
import asyncio
from IPython.display import Image, display
import requests
from bs4 import BeautifulSoup
import json
import re

# Defining state of the agent
class AgentState(TypedDict, total=False):
    query: Optional[str]
    web_text: Optional[str]
    output: Optional[str]  
    url: Optional[str]
    search_item: Optional[str]
    title: Optional[str]
    text: Optional[str]
    web_content: Optional[str]
    filename: "web_content.json"

# Defining LLM
model = OllamaLLM(
    model = 'phi3:mini'
)

def UserQuery(state: AgentState):
    """
    Takes input from the user.
    Determines what the users wants to search.
    Scraps the webpage (wikipedia).
    Provides summary.
    """
    query = str(input(">>"))

    return {
        "query": query

    }

def DetermineSearch(state: AgentState):
    """
    Takes input from the user.
    LLM parses it and determines what the user wants to search.
    """

    query = state['query']
                                                                                             
    prompt = f"""
    Parse throught the user query and determine what the user wants to search, just one word from it which carries more weight of the search.

    Example: 
    user query: Which hemiphere is India located?
    output: India

    User_Query: {query}
    """

    # Call the LLM
    messages = [HumanMessage(content=prompt)]
    response = model.invoke(messages)
    
    return {
        "search_item": response
    }

def GenerateURL(state: AgentState):
    """
    This function generates URL.
    """
    base_url = "https://en.wikipedia.org/wiki/"
    search = str(state['search_item'])

    url = base_url+search

    return {
        "url": url
    }

def FetchWebpage(state: AgentState):
    """Fetch webpage content using requests."""
    url = state['url']
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return {
        'web_text': requests
    }

def ExtractText(state: AgentState):
    """Extract and clean visible text from HTML"""
    html = state['web_text']
    soup = BeautifulSoup(html, 'html-parser')


    # Remove unwanted tags
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()

    # Extract title and paragraphs
    title = soup.title.string if soup.title else "No Title"
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]

    text = ' '.join(paragraphs)

    # Clean text
    text = re.sub(r'\s+', ' ', text)

    return {
        'text': text,
        'title': title
    }

def SaveJSON(state: AgentState):
    """Save extracted data as JSON"""
    data = {
        "url": state['url'],
        "title": state['title'],
        "content": state['text']
    }

    with open(state['filename'], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def SummarizeWeb(state: AgentState):
    """Summarizes web content by reading data from json."""

    with open(state['filename'], "r", encoding="utf-8") as f:
        data = json.load(f)

    prompt = f"""
    Summarize the following webpage by providing requried information to the user from the user prompt.

    Data: {data['content']}

    user_prompt = {state['query']}
    """        

    messages = [HumanMessage(content=prompt)]
    response = model.invoke(messages)

    print(f"{response}")

    return {
        'output': response
    }

# Creating Stategraph and defining edges
graph = StateGraph(AgentState)

# Add graph nodes
graph.add_node("UserQuery", UserQuery)
graph.add_node("DetermineSearch", DetermineSearch)
graph.add_node("GenerateURL", GenerateURL)
graph.add_node("FetchWebpage", FetchWebpage)
graph.add_node("ExtractText", ExtractText)
graph.add_node("SaveJSON", SaveJSON)
graph.add_node("SummarizeWeb", SummarizeWeb)

# Add edges connecting nodes
graph.add_edge(START, "UserQuery")
graph.add_edge("UserQuery", "DetermineSearch")
graph.add_edge("DetermineSearch", "GenerateURL")
graph.add_edge("GenerateURL", "FetchWebpage")
graph.add_edge("FetchWebpage", "ExtractText")
graph.add_edge("ExtractText", "SaveJSON")
graph.add_edge("SaveJSON", "SummarizeWeb")
graph.add_edge("SummarizeWeb", END)

# Compile the graph
compiled_graph = graph.compile()

web_summarize = compiled_graph.invoke({})

