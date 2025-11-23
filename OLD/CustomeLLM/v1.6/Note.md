01. first add the .gguf file.

02. then edit the modelfile(in this case you do not need to edit this)

03. then open this main folder on terminal
~~~
streamlit-ai-chat-app-with-ollama\CustomeLLM\v1.6>
~~~

04. then run these lines

~~~
ollama create FinanceModelV1.6 -f Modelfile
~~~
~~~
ollama run FinanceModelV1.6
~~~