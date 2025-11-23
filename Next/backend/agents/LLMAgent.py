class LLMAgent:
    """Agent for interact with the LLM"""
    def inti(self):
        pass
    def message(self, user_prompt:str = "hi"):
        try:
            print("llm")
        except Exception as e:
            print("somthing went wrong")