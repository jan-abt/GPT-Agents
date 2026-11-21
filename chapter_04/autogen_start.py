from autogen import ConversableAgent, UserProxyAgent, LLMConfig

# Load the configuration list from the config file.
# (AG2 0.14 replaced config_list_from_json() with LLMConfig.from_json().)
config_list = LLMConfig.from_json(path="OAI_CONFIG_LIST").config_list

# Create the agent that uses the LLM.
assistant = ConversableAgent("agent", llm_config={"config_list": config_list})

# Create the agent that represents the user in the conversation.
user_proxy = UserProxyAgent(
    "user",
    code_execution_config={
        "work_dir": "working",
        "use_docker": False,
    },
    human_input_mode="ALWAYS",
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
)

# Start the conversation.
user_proxy.initiate_chat(assistant, message="write a snake game using Pygame?")
