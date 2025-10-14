from typing import TypedDict, Optional
from langchain_ollama import OllamaLLM
from langchain_core.messages import HumanMessage
from langgraph.graph import START, END, StateGraph
from langchain_community.tools import DuckDuckGoSearchResults

# Defining state of the agent
class AgentState(TypedDict, total=False):
    query: Optional[str]
    searchtype: Optional[str]
    duck_search: Optional[str]
    summarize_results: Optional[str]

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

def SearchType(state: AgentState):
    """
    Determines whether the user wants information or news. 
    """
    
    user_query = state['query']

    prompt = f"""
    Based on given query determine if the query is to search information or news.
    Output only a single word.

    Example 1: Results of a match or series.
    output: news

    Example 2: Indian National Cricket team. 
    output: information

    Example 3: Latest changes in Indian National team. 
    output: news

    Example 4: History of India.
    output: information

    User query: {user_query}

    Note: Based on the query output only one single word
    Output Option 1: information
    Output Option 2: news
    """

    messages = [HumanMessage(content=prompt)]
    response = model.invoke(messages)

    return {
        'searchtype': response
    }

def NewsSearch(state: AgentState):
    """Searches user query as a news search."""
    
    user_query = state['query']

    search = DuckDuckGoSearchResults(backend="news")
    results = search.invoke(user_query)

    return {
        'duck_search': results
    }

def InfoSearch(state: AgentState):
    """Searches user query as an information search.""" 

    user_query = state['query']

    search = DuckDuckGoSearchResults()
    results = search.invoke(user_query)

    return {
        'duck_search': results
    }

def RouteSearchType(state: AgentState) -> str:
    """Routing agent process."""
    if state['searchtype'].lower() == 'news':
        return "news"
    else:
        return "information"

def SummarizeResults(state: AgentState):
    """Summarize search results."""
    
    search_results = state['duck_search']
    search_type = state['searchtype']
    user_query = state['query']

    prompt = f"""
    You will be provided a query and its web search results. 
    I want you to summarize those results.
    Summarize in required format if stated in the user query. 
    Also use tabular formats wherever necessary. 
    
    user query: {user_query}
    search type: {search_type}

    web search results: {search_results}
    """

    messages = [HumanMessage(content=prompt)]
    summary = model.invoke(messages)

    print(summary)

    return {
        'summarize_results': summary
    }

# Creating Stategraph and defining edges
graph = StateGraph(AgentState)

# Add graph nodes
graph.add_node("UserQuery", UserQuery)
graph.add_node("SearchType", SearchType)
graph.add_node("NewsSearch", NewsSearch)
graph.add_node("InfoSearch", InfoSearch)
graph.add_node("SummarizeResults", SummarizeResults)

# Add edges connecting nodes
graph.add_edge(START, "UserQuery")
graph.add_edge("UserQuery", "SearchType")
graph.add_conditional_edges(
    "SearchType",
    RouteSearchType,
    {
        "news": "NewsSearch",
        "information": "InfoSearch"
    }
)
graph.add_edge("NewsSearch", "SummarizeResults")
graph.add_edge("InfoSearch", "SummarizeResults")
graph.add_edge("SummarizeResults", END)

# Compile the graph
compiled_graph = graph.compile()

web_summarize = compiled_graph.invoke({})

