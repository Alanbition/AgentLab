from typing import Dict, List
from autogen import ConversableAgent
import sys
import os
import math

def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    # This function takes in a restaurant name and returns the reviews for that restaurant. 
    # The output should be a dictionary with the key being the restaurant name and the value being a list of reviews for that restaurant.
    # The "data fetch agent" should have access to this function signature, and it should be able to suggest this as a function call. 
    # Example:
    # > fetch_restaurant_data("Applebee's")
    # {"Applebee's": ["The food at Applebee's was average, with nothing particularly standing out.", ...]}
    reviews = []
    try:
        with open('restaurant-data.txt', 'r') as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    parts = line.strip().split('.')
                    if len(parts) >= 2:
                        rest_name = parts[0].strip()
                        review = '.'.join(parts[1:]).strip()
                        if rest_name.lower() == restaurant_name.lower():
                            reviews.append(line.strip())
        print(reviews)
        return {restaurant_name: reviews}
    except:
        print("No reviews found for the restaurant")
        return {restaurant_name: []}

def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    # TODO
    # This function takes in a restaurant name, a list of food scores from 1-5, and a list of customer service scores from 1-5
    # The output should be a score between 0 and 10, which is computed as the following:
    # SUM(sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(N * sqrt(125)) * 10
    # The above formula is a geometric mean of the scores, which penalizes food quality more than customer service. 
    # Example:
    # > calculate_overall_score("Applebee's", [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    # {"Applebee's": 5.048}
    # NOTE: be sure to that the score includes AT LEAST 3  decimal places. The public tests will only read scores that have 
    # at least 3 decimal places.
    N = len(food_scores)
    if N == 0:
        result = {restaurant_name: 0.000}
        print(f"{result[restaurant_name]:.3f}")  # Explicit print
        return result
    
    total = 0
    for i in range(N):
        total += math.sqrt(food_scores[i]**2 * customer_service_scores[i])
    
    score = total * (1/(N * math.sqrt(125))) * 10
    result = {restaurant_name: float(f"{score:.3f}")}
    print(f"{result[restaurant_name]:.3f}")  # Explicit print
    return result

def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    # TODO
    # It may help to organize messages/prompts within a function which returns a string. 
    # For example, you could use this function to return a prompt for the data fetch agent 
    # to use to fetch reviews for a specific restaurant.
    return f"""You are a data fetch agent that talk with the entrypoint agent Your task is to fetch reviews for a specific restaurant name from the query with fetch_restaurant_data function.
    You need to extract the restaurant name from the query and use it as the input of the the fetch_restaurant_data function to get its reviews as a dictionary with the restaurant name as the key and a list of reviews as the value.
    The restaurant name in the query may not exactly match the name in the data, so try to find the closest match. The response you give back to the entrypoint agent should be a dictionary with the restaurant name as the key and a list of reviews as the value."""

# TODO: feel free to write as many additional functions as you'd like.
def get_review_analyzer_prompt() -> str:
    return """You are a review analyzer agnet. You can analyze the restaurant reviews and extract food_score and customer_service_score for each review. You should be provided with a dictionary with the restaurant name as the key and a list of reviews as the value. If you are not provided with those, you should ask the entrypoint agent for it.
    Use these keyword mappings:
    Score 1/5: awful, horrible, disgusting
    Score 2/5: bad, unpleasant, offensive  
    Score 3/5: average, uninspiring, forgettable
    Score 4/5: good, enjoyable, satisfying
    Score 5/5: awesome, incredible, amazing
    
    You will be provided with a dictionary with the restaurant name as the key and a list of reviews as the value.
    For each review:
    1. Find the keyword describing food quality and assign food_score
    2. Find the keyword describing service and assign customer_service_score
    3. Return all scores in two lists. The length of the two lists must be the same.
    4. Output format example: food_scores = [1, 2, 3, 4, 5] customer_service_scores = [1, 2, 3, 4, 5]. You should return the two lists in the response."""


def get_scoring_agent_prompt() -> str:
    return """You are a scoring agent. You take the food scores and customer service scores from all reviews and calculate the overall score using the calculate_overall_score function.
    If you are not provided with the restaurant name, food scores and customer service scores, you should ask the entrypoint agent for it.
    The function takes:
    - restaurant_name (str)
    - food_scores (list of ints 1-5) 
    - customer_service_scores (list of ints 1-5)
    The function returns a dictionary with the restaurant name as the key and the overall score as the value.
    Return ONLY the numeric score with at least 3 decimal places.
    For example: "8.945" or "10.000"
    You should return the dictionary in the response."""

# Do not modify the signature of the "main" function.
def main(user_query: str):
    print (user_query)
    entrypoint_agent_system_message = "You are a supervisor agent that coordinates between data fetch, review analysis and scoring agents to evaluate restaurant reviews. The entrypoint agent should not call the function directly. It should only pass the query to the data fetch agent. The data fetch agent should return a list of reviews to you and you should then pass a list of reviews to the review analyzer agent. The review analyzer agent should return the food scores and customer service scores to you and you should then pass two lists of scores to the scoring agent. The scoring agent should return the overall score to you and you should then return the overall score to the user."
    # example LLM config for the entrypoint agent
    llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.getenv('OPENAI_API_KEY')}]}
    # the main entrypoint/supervisor agent
    entrypoint_agent = ConversableAgent("entrypoint_agent", 
                                        system_message=entrypoint_agent_system_message, 
                                        llm_config=llm_config)
    # entrypoint_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)
    entrypoint_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)

    # TODO
    # Create more agents here.
    data_fetch_agent = ConversableAgent(
        "data_fetch_agent",
        system_message=get_data_fetch_agent_prompt(user_query),
        llm_config=llm_config,
        # is_termination_msg=lambda msg: "END CHAT" in msg["content"].lower(),
    )

    data_fetch_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    data_fetch_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)

    review_analyzer_agent = ConversableAgent(
        "review_analyzer_agent",  
        system_message=get_review_analyzer_prompt(),
        llm_config=llm_config,
        # is_termination_msg=lambda msg: "END CHAT" in msg["content"].lower(),
    )
    
    scoring_agent = ConversableAgent(
        "scoring_agent",
        system_message=get_scoring_agent_prompt(),
        llm_config=llm_config,
        # is_termination_msg=lambda msg: "END CHAT" in msg["content"].lower(),
    )
    scoring_agent.register_for_llm(name="calculate_overall_score", description="Calculates overall score from food and service scores")(calculate_overall_score)
    scoring_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)
    
    # TODO
    # Fill in the argument to `initiate_chats` below, calling the correct agents sequentially.
    # If you decide to use another conversation pattern, feel free to disregard this code.
    
    # Uncomment once you initiate the chat with at least one agent.
    result = entrypoint_agent.initiate_chats([
        {
            "sender": entrypoint_agent,
            "recipient": data_fetch_agent,
            "summary_method": "last_msg",
            "max_turns": 3,
            "message": f"Please fetch restaurant data for the following query: {user_query}"
        },
        {
            "sender": entrypoint_agent,
            "recipient": review_analyzer_agent,
            "summary_method": "reflection_with_llm",
            "max_turns": 3,
            "message": "Please analyze the restaurant reviews from the data fetch agent and extract food scores and customer service scores on a scale of 1-5 from the reviews"
        },
        {
            "sender": entrypoint_agent,
            "recipient": scoring_agent,
            "summary_method": "reflection_with_llm", 
            "max_turns": 3,
            "message": "Please calculate the overall score using the food scores and customer service scores provided by the review analyzer agent"
        }
    ])

    # More verbose result handling with debug prints
    print(f"Query: {user_query}")  # Print the query we're processing
    
    if result and isinstance(result, list):
        print(f"Found {len(result)} chat results")  # Debug print
        
        for chat_idx, chat in enumerate(reversed(result)):
            print(f"Checking chat {chat_idx}")  # Debug print
            
            if isinstance(chat, dict):
                if 'messages' in chat:
                    messages = chat['messages']
                    print(f"Found {len(messages)} messages")  # Debug print
                    
                    for msg in reversed(messages):
                        content = msg.get('content', '')
                        print(f"Message content: {content}")  # Debug print
                        
                        if isinstance(content, str) and re.search(r'\d+\.\d{3,}', content):
                            print(f"Found score: {content}")
                            return
                elif 'summary' in chat:
                    print(f"Summary content: {chat['summary']}")
                    if re.search(r'\d+\.\d{3,}', chat['summary']):
                        print(chat['summary'])
                        return
    else:
        print("No results returned from chat")  # Debug print
    
# DO NOT modify this code below.
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])